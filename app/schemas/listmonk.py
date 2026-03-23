from enum import StrEnum

from pydantic import BaseModel


class ListmonkSeverity(StrEnum):
    SOFT = "soft"
    HARD = "hard"


class ListmonkMeta(BaseModel):
    reason: str


class ListmonkPayload(BaseModel):
    """
    The strict JSON structure required by Listmonk's
    bounce webhook endpoint.
    """

    email: str
    source: str = "mailgun_webhook"
    type: ListmonkSeverity
    meta: ListmonkMeta
    campaign_uuid: str | None = None
