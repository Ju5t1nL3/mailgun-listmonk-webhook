from pydantic import BaseModel, Field
from typing import Any

class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str

class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: dict[str, Any] = Field(alias="event-data")
