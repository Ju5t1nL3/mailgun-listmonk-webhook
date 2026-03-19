import pytest
from unittest.mock import AsyncMock, patch

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

@pytest.fixture
def mock_http_client():
    mock_client = AsyncMock()
    with patch("app.services.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_ignore_irrelevant_events(mock_event):
    event = mock_event(event_type=EventType.ACCEPTED)
    result = await forward_bounce(event)
    assert result["status"] == "ignored"
