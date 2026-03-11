from typing import Any, Dict

from pydantic import BaseModel, Field


class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str


class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: Dict[str, Any] = Field(alias="event-data")
