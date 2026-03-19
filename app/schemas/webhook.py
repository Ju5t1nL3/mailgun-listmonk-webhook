from enum import StrEnum

from pydantic import BaseModel


class WebhookStatus(StrEnum):
    IGNORED = "ignored"
    SUCCESS = "success"


class WebhookErrorCode(StrEnum):
    EVENTTYPEIGNORED = "event_type_ignored"
    NOTFROMLISTMONK = "not_from_listmonk"


class WebhookResponse(BaseModel):
    webhook_status: WebhookStatus
    error_code: WebhookErrorCode | None = None
    message: str
