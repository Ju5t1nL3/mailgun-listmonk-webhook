import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_production_hides_docs(
    prod_client: AsyncClient,
) -> None:
    response = await prod_client.get("/docs")
    assert response.status_code == 404
    response = await prod_client.get("/redoc")
    assert response.status_code == 404
    response = await prod_client.get("/openapi.json")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_development_shows_docs(
    dev_client: AsyncClient,
) -> None:
    response = await dev_client.get("/docs")
    assert response.status_code == 200
    response = await dev_client.get("/redoc")
    assert response.status_code == 200
    response = await dev_client.get("/openapi.json")
    assert response.status_code == 200
