import re
from typing import Optional
import uuid
import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.user import AuthUser

security_scheme = HTTPBearer(auto_error=False)

_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Retrieves or initializes the PyJWKClient for Supabase asymmetric JWTs (ES256/RS256)."""
    global _jwks_client
    if _jwks_client is None:
        supabase_url = settings.SUPABASE_URL.rstrip("/")
        if supabase_url and not supabase_url.startswith("https://mock"):
            jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
            try:
                _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
            except Exception as e:
                logger.warning(f"Could not initialize PyJWKClient for {jwks_url}: {e}")
    return _jwks_client


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> AuthUser:
    """
    Validates Supabase JWT token and retrieves the authenticated user context.
    Supports test/development tokens for automated testing.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Test / Dev token hook - strictly gated behind explicit setting and development/test environment
    if (
        settings.ENABLE_DEV_TOKEN_BYPASS
        and settings.ENVIRONMENT in ("development", "test")
        and token.startswith("test-token-")
    ):
        prefix = "test-token-"
        payload = token[len(prefix):]

        # Extract full UUID portion via fixed prefix strip + regex validation
        uuid_match = re.match(
            r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?:-(.+))?$",
            payload,
        )
        if uuid_match:
            raw_uuid = uuid_match.group(1)
            user_id = str(uuid.UUID(raw_uuid))
            email = uuid_match.group(2) or f"user_{user_id[:8]}@example.com"
        else:
            # Fallback for non-UUID tokens used in test suites (e.g. test-token-billuser-billing@example.com)
            parts = payload.split("-")
            if len(parts) >= 2 and "@" in parts[-1]:
                raw_user_id = "-".join(parts[:-1])
                email = parts[-1]
            elif parts and parts[0]:
                raw_user_id = parts[0]
                email = f"user_{raw_user_id}@example.com"
            else:
                raw_user_id = "00000000-0000-0000-0000-000000000001"
                email = "demo@example.com"

            try:
                user_id = str(uuid.UUID(raw_user_id))
            except (ValueError, AttributeError):
                user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_user_id))

        user = await repo.get_or_create_user(user_id=user_id, email=email)
        return AuthUser(id=user.id, email=user.email, plan=user.plan)

    # Decode and verify Supabase JWT
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg in ("ES256", "RS256"):
            jwks = get_jwks_client()
            if jwks:
                signing_key = jwks.get_signing_key_from_jwt(token)
                key = signing_key.key
            else:
                key = settings.SUPABASE_JWT_SECRET

            payload = jwt.decode(
                token,
                key,
                algorithms=["ES256", "RS256"],
                options={"verify_aud": False},
            )
        else:
            # Symmetric HMAC verification (HS256)
            jwt_secret = settings.SUPABASE_JWT_SECRET
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )

        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier",
            )

        user = await repo.get_or_create_user(user_id=user_id, email=email)
        return AuthUser(id=user.id, email=user.email, plan=user.plan)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token presented: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
