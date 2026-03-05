import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():  # type: ignore[no-untyped-def]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "redis" in data
    assert "storage" in data


@pytest.mark.asyncio
async def test_readiness_endpoint_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
