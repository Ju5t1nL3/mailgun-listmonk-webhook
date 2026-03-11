from pydantic import BaseModel, Field


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class DeliveryStatus(BaseModel):
    message: str | None = "No reason provided"


class EventData(BaseModel):
    event: str
    recipient: str
    severity: str | None = "hard"
    delivery_status: DeliveryStatus | None = Field(
        default=None, alias="delivery-status"
    )


class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: EventData = Field(alias="event-data")
