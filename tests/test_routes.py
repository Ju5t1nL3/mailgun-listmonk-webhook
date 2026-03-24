from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.schemas import (
    EventData,
    EventType,
    MailgunPayload,
    MailgunSignature,
    WebhookResponse,
    WebhookStatus,
)


@pytest.fixture
def valid_payload() -> MailgunPayload:
    return MailgunPayload(
        signature=MailgunSignature(timestamp="123", token="123", signature="123"),
        event_data=EventData(event=EventType.FAILED, recipient="hi"),
    )


@pytest.mark.asyncio
@patch("app.route.verify_mailgun_signature", return_value=False)
@patch("app.route.forward_bounce", new_callable=AsyncMock)
async def test_webhook_rejects_invalid_signature(
    mock_forward: AsyncMock,
    mock_verify: MagicMock,
    valid_payload: MailgunPayload,
    dev_client: AsyncClient,
) -> None:
    response = await dev_client.post(
        "/webhook", json=valid_payload.model_dump(exclude_none=True)
    )

    mock_forward.assert_not_awaited()
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.route.verify_mailgun_signature", return_value=True)
@patch("app.route.forward_bounce", new_callable=AsyncMock)
async def test_webhook_accepts_valid_signature(
    mock_forward: AsyncMock,
    mock_verify: MagicMock,
    valid_payload: MailgunPayload,
    dev_client: AsyncClient,
) -> None:
    mock_forward.return_value = WebhookResponse(
        webhook_status=WebhookStatus.SUCCESS, message="Webhook forwarded"
    )

    response = await dev_client.post(
        "/webhook", json=valid_payload.model_dump(exclude_none=True)
    )

    mock_forward.assert_awaited_once()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_rejects_malformed_json(dev_client: AsyncClient) -> None:
    bad_payload = {"hi": "123"}
    response = await dev_client.post("/webhook", json=bad_payload)

    assert response.status_code == 422


@pytest.mark.asyncio
@patch("app.route.verify_mailgun_signature", return_value=True)
@patch("app.route.forward_bounce", new_callable=AsyncMock)
async def test_webhook_returns_500_on_failure(
    mock_forward: AsyncMock,
    mock_verify: MagicMock,
    valid_payload: MailgunPayload,
    dev_client: AsyncClient,
) -> None:
    detail = "Listmonk timeout"
    mock_forward.side_effect = HTTPException(status_code=500, detail=detail)

    response = await dev_client.post(
        "/webhook", json=valid_payload.model_dump(exclude_none=True)
    )

    assert response.status_code == 500
    assert response.json() == {"detail": detail}
