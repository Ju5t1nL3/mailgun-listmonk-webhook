from enum import StrEnum

from pydantic import BaseModel


class ListmonkSeverity(StrEnum):
    SOFT = "soft"
    HARD = "hard"


class ListmonkMeta(BaseModel):
    reason: str


class ListmonkPayload(BaseModel):
    email: str
    source: str = "mailgun_webhook"
    type: ListmonkSeverity
    meta: ListmonkMeta
    campaign_uuid: str | None = None
