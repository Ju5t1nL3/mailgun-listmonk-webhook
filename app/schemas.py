from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


class EventSeverity(StrEnum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class DeliveryStatus(BaseModel):
    message: str | None = None
    description: str | None = None


class EventData(BaseModel):
    event: EventType
    recipient: str
    severity: EventSeverity | None = EventSeverity.PERMANENT
    delivery_status: DeliveryStatus = Field(
        default_factory=DeliveryStatus, alias="delivery-status"
    )


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: EventData = Field(alias="event-data")
