import time
import jwt
import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_auth_missing_header(async_client: AsyncClient):
    response = await async_client.get("/api/v1/domains")
    assert response.status_code == 401
    assert "Missing Authorization header" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_test_token(async_client: AsyncClient):
    headers = {"Authorization": "Bearer test-token-user123-test@example.com"}
    response = await async_client.get("/api/v1/domains", headers=headers)
    assert response.status_code == 200
    assert response.json()["domains"] == []


@pytest.mark.asyncio
async def test_auth_dev_token_uuid_extraction():
    """Verifies that full hyphenated UUIDs in dev tokens are correctly extracted without truncation."""
    from fastapi.security import HTTPAuthorizationCredentials
    from app.api.deps import get_current_user

    test_uuid = "5efa673e-c78b-4dca-86c6-70908906758d"
    token = f"test-token-{test_uuid}-owner@example.com"
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    auth_user = await get_current_user(creds)
    assert auth_user.id == test_uuid
    assert auth_user.email == "owner@example.com"

    # Also test UUID without email suffix (fresh UUID)
    test_uuid_2 = "11111111-2222-3333-4444-555555555555"
    token_no_email = f"test-token-{test_uuid_2}"
    creds_no_email = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_no_email)
    auth_user_no_email = await get_current_user(creds_no_email)
    assert auth_user_no_email.id == test_uuid_2
    assert auth_user_no_email.email == f"user_{test_uuid_2[:8]}@example.com"



@pytest.mark.asyncio
async def test_auth_valid_jwt(async_client: AsyncClient):
    payload = {
        "sub": "b2c3d4e5-1111-2222-3333-444455556666",
        "email": "realuser@company.com",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/domains", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_expired_jwt(async_client: AsyncClient):
    payload = {
        "sub": "b2c3d4e5-1111-2222-3333-444455556666",
        "email": "realuser@company.com",
        "role": "authenticated",
        "exp": int(time.time()) - 3600,  # Expired in past
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/domains", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_dev_token_rejected_when_bypass_disabled(async_client: AsyncClient, monkeypatch):
    """Verifies test tokens are rejected when ENABLE_DEV_TOKEN_BYPASS is False."""
    monkeypatch.setattr(settings, "ENABLE_DEV_TOKEN_BYPASS", False)
    headers = {"Authorization": "Bearer test-token-user123-test@example.com"}
    response = await async_client.get("/api/v1/domains", headers=headers)
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_settings_refuses_dev_bypass_in_production():
    """Verifies Settings refuses initialization when dev bypass is True in production."""
    from app.core.config import Settings
    with pytest.raises(ValueError, match="Dev-token bypass is strictly forbidden"):
        Settings(
            ENVIRONMENT="production",
            ENABLE_DEV_TOKEN_BYPASS=True,
            _env_file=None,
        )


def test_settings_refuses_dev_bypass_in_staging():
    """Verifies Settings refuses initialization when dev bypass is True in staging."""
    from app.core.config import Settings
    with pytest.raises(ValueError, match="Dev-token bypass is strictly forbidden"):
        Settings(
            ENVIRONMENT="staging",
            ENABLE_DEV_TOKEN_BYPASS=True,
            _env_file=None,
        )


@pytest.mark.asyncio
async def test_lifespan_refuses_startup_in_production(monkeypatch):
    """Verifies FastAPI startup lifespan refuses to start if dev bypass is active in production."""
    from app.api.main import app, lifespan
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ENABLE_DEV_TOKEN_BYPASS", True)

    with pytest.raises(RuntimeError, match="dev-token bypass is strictly forbidden"):
        async with lifespan(app):
            pass
