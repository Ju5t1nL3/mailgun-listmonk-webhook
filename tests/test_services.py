from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    WebhookErrorCode,
    WebhookStatus,
)
from app.schemas.listmonk import ListmonkSeverity
from app.services import forward_bounce
from app.utils.config import settings


# ---------------------------------------- #
#  Tests: ignore irrelevant events         #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_ignore_irrelevant_events(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
):
    event_type = EventType.ACCEPTED
    event = event_factory(event_type=event_type)
    result = await forward_bounce(event, mock_listmonk_client)
    assert result.webhook_status == WebhookStatus.IGNORED
    assert result.error_code == WebhookErrorCode.EVENTTYPEIGNORED


# ---------------------------------------- #
#  Tests: "REQUIRE_LISTMONK_TAG" flag      #
# ---------------------------------------- #
@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", True)
async def test_ignore_missing_tag_when_flag_enabled(
    event_factory, mock_listmonk_client
) -> None:
    event = event_factory(tags=[])
    result = await forward_bounce(event, mock_listmonk_client)
    assert result.webhook_status == WebhookStatus.IGNORED
    assert result.error_code == WebhookErrorCode.NOTFROMLISTMONK


@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", True)
async def test_accept_listmonk_tag_when_flag_enabled(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(tags=["listmonk"])
    result = await forward_bounce(event, mock_listmonk_client)
    assert result.webhook_status == WebhookStatus.SUCCESS


@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", False)
async def test_accept_listmonk_tag_when_flag_disabled(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(tags=[])
    result = await forward_bounce(event, mock_listmonk_client)
    assert result.webhook_status == WebhookStatus.SUCCESS


# ---------------------------------------- #
#  Tests: correctly map mailgun severity   #
#  listmonk severity                       #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_maps_temporary_severity_to_soft_bounce(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(severity=EventSeverity.TEMPORARY)
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["type"] == ListmonkSeverity.SOFT


@pytest.mark.asyncio
async def test_maps_default_severity_to_hard_bounce(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(severity=EventSeverity.PERMANENT)
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["type"] == ListmonkSeverity.HARD


# ---------------------------------------- #
#  Tests: "ENABLED_CAMPAIGN_TRACKING"      #
#  flag                                    #
# ---------------------------------------- #
@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", True)
async def test_insert_campaign_uuid_when_flag_enabled(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    test_campaign_uuid = "12345"
    event = event_factory(campaign_uuid=test_campaign_uuid)
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["campaign_uuid"] == test_campaign_uuid


@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", True)
async def test_no_campaign_uuid_when_flag_enabled(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(campaign_uuid=None)
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert "campaign_uuid" not in payload


@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", False)
async def test_insert_campaign_uuid_when_flag_disabled(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    event = event_factory(campaign_uuid="12345")
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert "campaign_uuid" not in payload


# ---------------------------------------- #
#  Tests: Error message                    #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_combines_multiple_reasons(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    message = "550"
    description = "Mailbox unavailable"
    event = event_factory(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == message + " | " + description


@pytest.mark.asyncio
async def test_use_default_reason_when_none_provided(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    message = None
    description = None
    event = event_factory(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == "No reason provided"


@pytest.mark.asyncio
async def test_use_only_one_reason(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    message = "550 User unknown"
    description = None
    event = event_factory(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_listmonk_client)
    payload = mock_listmonk_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == message


# ---------------------------------------- #
#  Tests: Network Exceptions               #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_handle_request_error(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    mock_listmonk_client.post.side_effect = httpx.RequestError("Timeout")

    with pytest.raises(HTTPException) as exc:
        await forward_bounce(event_factory(), mock_listmonk_client)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_handle_http_status_error(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )
    mock_listmonk_client.post.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        await forward_bounce(event_factory(), mock_listmonk_client)
    assert exc.value.status_code == 500


# ---------------------------------------- #
#  Tests: Use correct url and credentials  #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_use_correct_url_and_credentials(
    event_factory: Callable[..., EventData], mock_listmonk_client: AsyncMock
) -> None:
    await forward_bounce(event_factory(), mock_listmonk_client)

    call_args, call_kwargs = mock_listmonk_client.post.call_args

    assert call_args[0] == f"{settings.LISTMONK_URL}/webhooks/bounce"
    assert call_kwargs["auth"] == (
        settings.LISTMONK_API_USER,
        settings.LISTMONK_API_TOKEN,
    )
