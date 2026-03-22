from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import EventData, EventType, MailgunPayload, MailgunSignature


@pytest.fixture
def valid_payload() -> MailgunPayload:
    return MailgunPayload(
        signature=MailgunSignature(timestamp="123", token="123", signature="123"),
        event_data=EventData(event=EventType.FAILED, recipient="hi"),
    )


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
@patch("app.main.verify_mailgun_signature", return_value=False)
@patch("app.main.forward_bounce", new_callable=AsyncMock)
async def test_webhook_rejects_invalid_signature(
    mock_forward, mock_verify, valid_payload, async_client
):
    response = await async_client.post(
        "/webhook", json=valid_payload.model_dump(exclude_none=True)
    )

    mock_forward.assert_not_awaited()
    assert response.status_code == 401
