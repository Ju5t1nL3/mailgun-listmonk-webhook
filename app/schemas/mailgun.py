from pydantic import BaseModel, ConfigDict, Field

from app.schemas.event import EventData


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class MailgunPayload(BaseModel):
    """
    The top level JSON structure sent by mailgun.
    """

    signature: MailgunSignature
    event_data: EventData = Field(validation_alias="event-data")

    model_config = ConfigDict(populate_by_name=True)
