import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import EventData, EventType, MailgunPayload, MailgunSignature


@pytest.fixture
def valid_payload() -> MailgunPayload:
    return MailgunPayload(
        signature=MailgunSignature(timestamp="123", token="123", signature="123"),
        event_data=EventData(event=EventType.FAILED, recipient="hi"),
    )


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
