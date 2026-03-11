from pydantic import BaseModel, Field
from typing import Dict, Any

class MailgunSignature(BaseModel):
    timestamp: str
    token: str
    signature: str

class MailgunPayload(BaseModel):
    signature: MailgunSignature
    event_data: Dict[str, Any] = Field(alias="event-data")
