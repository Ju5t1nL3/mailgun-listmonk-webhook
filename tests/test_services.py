import pytest

from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    UserVariables,
)
from app.services import forward_bounce


def create_test_event(
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


@pytest.mark.asyncio
async def test_ignore_irrelevant_events():
    event = create_test_event(event_type=EventType.ACCEPTED)
    result = await forward_bounce(event)
    assert result["status"] == "ignored"
