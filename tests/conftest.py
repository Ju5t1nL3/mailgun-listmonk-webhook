from typing import AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app, lifespan
from app.schemas import (
    DeliveryStatus,
    EventData,
    EventSeverity,
    EventType,
    UserVariables,
)
from app.utils.config import Environment


@pytest.fixture
def event_factory() -> Callable[..., EventData]:
    """
    Provides a factory function to generate mock Mailgun EventData.

    Allows individual tests to override specific fields (like tags
    or severity) while being structurally valid for defaults
    """

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
def mock_listmonk_client() -> AsyncMock:
    """
    Provides an AsyncMock of the internal HTTP client

    Injected into the service layer to fake network
    requests to Listmonk
    """
    mock_client = AsyncMock()
    mock_client.post.return_value = MagicMock()

    return mock_client


@pytest_asyncio.fixture
async def dev_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Simulates incoming Mailgun requests by bypassing
    the ASGI web server

    Uses the default DEVELOPMENT environment
    """
    app = create_app()
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest_asyncio.fixture
async def prod_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Yields a test client where the app was
    built under PRODUCTION environment settings
    """
    with patch("app.main.settings.ENVIRONMENT", Environment.PRODUCTION):
        app = create_app()
        async with lifespan(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                yield client
