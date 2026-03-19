from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    UserVariables,
)
from app.services import forward_bounce


@pytest.fixture
def mock_event():
    def _create(
        event_type: EventType = EventType.FAILED,
        severity: EventSeverity = EventSeverity.PERMANENT,
        delivery_status: DeliveryStatus = DeliveryStatus(
            message="Failed", description=None
        ),
        tags: list[str] = [],
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


@pytest.mark.asyncio
async def test_ignore_irrelevant_events(mock_event, mock_http_client):
    event_type = EventType.ACCEPTED
    event = mock_event(event_type=event_type)
    result = await forward_bounce(event, mock_http_client)
    assert result["status"] == "ignored"
    assert result["reason"] == f"Event '{event_type}' ignored"


@pytest.mark.asyncio
@patch("app.services.settings.REQUIRE_LISTMONK_TAG", True)
async def test_ignore_missing_tag_when_flag_enabled(mock_event, mock_http_client):
    event = mock_event(tags=[])
    result = await forward_bounce(event, mock_http_client)
    assert result["status"] == "ignored"
    assert result["reason"] == "Not a Listmonk email"
