from pydantic import BaseModel, Field

from app.schemas.event import EventData


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: EventData = Field(validation_alias="event-data")
