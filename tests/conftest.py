from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    UserVariables,
)


@pytest.fixture
def event_factory():
    def _create(
        event_type: EventType = EventType.FAILED,
        severity: EventSeverity = EventSeverity.PERMANENT,
        delivery_status: DeliveryStatus = DeliveryStatus(
            message="Failed", description=None
        ),
        tags: list[str] = ["listmonk"],
        campaign_uuid: str = "123-abc",
    ) -> EventData:
        return EventData(
            event=event_type,
            recipient="test@tamuhack.org",
            severity=severity,
            delivery_status=delivery_status,
            tags=tags,
            user_variables=UserVariables(campaign_uuid=campaign_uuid),
        )

    return _create


@pytest.fixture
def mock_listmonk_client():
    mock_client = AsyncMock()
    mock_client.post.return_value = MagicMock()

    return mock_client


@pytest_asyncio.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
