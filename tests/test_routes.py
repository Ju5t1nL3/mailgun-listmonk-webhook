import pytest
from app.schemas import EventData, EventType, MailgunPayload, MailgunSignature
@pytest.fixture
def valid_payload() -> MailgunPayload:
    return MailgunPayload(
        signature=MailgunSignature(timestamp="123", token="123", signature="123"),
        event_data=EventData(event=EventType.FAILED, recipient="hi"),
    )
