from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    UserVariables,
    WebhookErrorCode,
    WebhookStatus,
)
from app.schemas.listmonk import ListmonkSeverity
from app.services import forward_bounce
from app.utils.config import settings


@pytest.fixture
def mock_event():
    def _create(
        event_type: EventType = EventType.FAILED,
        severity: EventSeverity = EventSeverity.PERMANENT,
        delivery_status: DeliveryStatus = DeliveryStatus(
            message="Failed", description=None
        ),
        tags: list[str] = ["listmonk"],
        campaign_uuid: str = "123-abc",
    ) -> EventData:
        return EventData(
            event=event_type,
            recipient="test@tamuhack.org",
            severity=severity,
            delivery_status=delivery_status,
            tags=tags,
            user_variables=UserVariables(campaign_uuid=campaign_uuid),
        )

    return _create


@pytest.fixture
def mock_http_client():
    mock_client = AsyncMock()
    mock_client.post.return_value = MagicMock()

    return mock_client


# ---------------------------------------- #
#  Tests: ignore irrelevant events         #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_ignore_irrelevant_events(mock_event, mock_http_client):
    event_type = EventType.ACCEPTED
    event = mock_event(event_type=event_type)
    result = await forward_bounce(event, mock_http_client)
    assert result.webhook_status == WebhookStatus.IGNORED
    assert result.error_code == WebhookErrorCode.EVENTTYPEIGNORED


# ---------------------------------------- #
#  Tests: "REQUIRE_LISTMONK_TAG" flag      #
# ---------------------------------------- #
@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", True)
async def test_ignore_missing_tag_when_flag_enabled(mock_event, mock_http_client):
    event = mock_event(tags=[])
    result = await forward_bounce(event, mock_http_client)
    assert result.webhook_status == WebhookStatus.IGNORED
    assert result.error_code == WebhookErrorCode.NOTFROMLISTMONK


@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", True)
async def test_accept_listmonk_tag_when_flag_enabeld(mock_event, mock_http_client):
    event = mock_event(tags=["listmonk"])
    result = await forward_bounce(event, mock_http_client)
    assert result.webhook_status == WebhookStatus.SUCCESS


@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", False)
async def test_accept_listmonk_tag_when_flag_disabled(mock_event, mock_http_client):
    event = mock_event(tags=[])
    result = await forward_bounce(event, mock_http_client)
    assert result.webhook_status == WebhookStatus.SUCCESS


# ---------------------------------------- #
#  Tests: correctly map mailgun severity   #
#  listmonk severity                       #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_maps_temporary_severity_to_soft_bounce(mock_event, mock_http_client):
    event = mock_event(severity=EventSeverity.TEMPORARY)
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["type"] == ListmonkSeverity.SOFT


@pytest.mark.asyncio
async def test_maps_default_severity_to_hard_bounce(mock_event, mock_http_client):
    event = mock_event(severity=EventSeverity.PERMANENT)
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["type"] == ListmonkSeverity.HARD


# ---------------------------------------- #
#  Tests: "ENABLED_CAMPAIGN_TRACKING"      #
#  flag                                    #
# ---------------------------------------- #
@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", True)
async def test_insert_campaign_uuid_when_flag_enabled(mock_event, mock_http_client):
    test_campaign_uuid = "12345"
    event = mock_event(campaign_uuid=test_campaign_uuid)
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["campaign_uuid"] == test_campaign_uuid


@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", True)
async def test_no_campaign_uuid_when_flag_enabeld(mock_event, mock_http_client):
    event = mock_event(campaign_uuid=None)
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert "campaign_uuid" not in payload


@pytest.mark.asyncio
@patch("app.services.settings.ENABLE_CAMPAIGN_TRACKING", False)
async def test_insert_campaign_uuid_when_flag_disabled(mock_event, mock_http_client):
    event = mock_event(campaign_uuid="12345")
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert "campaign_uuid" not in payload


# ---------------------------------------- #
#  Tests: Error message                    #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_combines_multiple_reasons(mock_event, mock_http_client):
    message = "550"
    description = "Mailbox unavailable"
    event = mock_event(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == message + " | " + description


@pytest.mark.asyncio
async def test_use_default_reason_when_none_provided(mock_event, mock_http_client):
    message = None
    description = None
    event = mock_event(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == "No reason provided"


@pytest.mark.asyncio
async def test_use_only_one_reason(mock_event, mock_http_client):
    message = "550 User unknown"
    description = None
    event = mock_event(
        delivery_status=DeliveryStatus(message=message, description=description)
    )
    await forward_bounce(event, mock_http_client)
    payload = mock_http_client.post.call_args.kwargs["json"]
    assert payload["meta"]["reason"] == message


# ---------------------------------------- #
#  Tests: Network Exceptions               #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_handle_request_error(mock_event, mock_http_client):
    mock_http_client.post.side_effect = httpx.RequestError("Timeout")

    with pytest.raises(HTTPException) as exc:
        await forward_bounce(mock_event(), mock_http_client)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_handle_http_status_error(mock_event, mock_http_client):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )
    mock_http_client.post.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        await forward_bounce(mock_event(), mock_http_client)
    assert exc.value.status_code == 500


# ---------------------------------------- #
#  Tests: Use correct url and credentials  #
# ---------------------------------------- #
@pytest.mark.asyncio
async def test_use_correct_url_and_credentials(mock_event, mock_http_client):
    await forward_bounce(mock_event(), mock_http_client)

    args, kwargs = mock_http_client.post.call_args

    call_args, call_kwargs = mock_http_client.post.call_args
    assert call_args[0] == f"{settings.LISTMONK_URL}/webhooks/bounce"
    assert call_kwargs["auth"] == (
        settings.LISTMONK_API_USER,
        settings.LISTMONK_API_TOKEN,
    )
