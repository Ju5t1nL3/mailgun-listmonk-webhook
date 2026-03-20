from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


class EventSeverity(StrEnum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class DeliveryStatus(BaseModel):
    message: str | None = None
    description: str | None = None


class UserVariables(BaseModel):
    campaign_uuid: str | None = None


class EventData(BaseModel):
    event: EventType
    recipient: str
    severity: EventSeverity | None = EventSeverity.PERMANENT
    delivery_status: DeliveryStatus = Field(
        default_factory=DeliveryStatus, validation_alias="delivery-status"
    )

    tags: list[str] = Field(default_factory=list)
    user_variables: UserVariables = Field(
        default_factory=UserVariables, validation_alias="user-variables"
    )

    model_config = ConfigDict(populate_by_name=True)
