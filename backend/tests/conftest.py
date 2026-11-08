import pytest
from httpx import ASGITransport, AsyncClient
from app.api.main import app
from app.services.queue import queue


@pytest.fixture(autouse=True)
async def cleanup_queue():
    yield
    await queue.close()


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
