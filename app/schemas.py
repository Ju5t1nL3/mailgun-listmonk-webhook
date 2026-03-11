from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class DeliveryStatus(BaseModel):
    message: str | None = "No reason provided"


class EventData(BaseModel):
    event: str
    recipient: str
    severity: Severity | None = Severity.PERMANENT
    delivery_status: DeliveryStatus | None = Field(
        default=None, alias="delivery-status"
    )


class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: EventData = Field(alias="event-data")
