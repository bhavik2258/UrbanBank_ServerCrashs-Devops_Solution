from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv

load_dotenv()

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be configured")

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _configured_users() -> dict[str, dict[str, str]]:
    raw_users = os.getenv("AUTH_USERS_JSON")
    if raw_users:
        users = json.loads(raw_users)
        if not isinstance(users, dict):
            raise RuntimeError("AUTH_USERS_JSON must be a JSON object")
        return users

    configured_users = {
        "admin@urbanbank.com": {
            "name": "UrbanBank Platform Admin",
            "role": "platform_admin",
            "password": os.getenv("ADMIN_PASSWORD", ""),
        },
        "ops@urbanbank.com": {
            "name": "UrbanBank Operations Analyst",
            "role": "operations_analyst",
            "password": os.getenv("OPS_PASSWORD", ""),
        },
        "auditor@urbanbank.com": {
            "name": "UrbanBank Compliance Auditor",
            "role": "auditor",
            "password": os.getenv("AUDITOR_PASSWORD", ""),
        },
    }
    for user in configured_users.values():
        if user["password"]:
            user["password"] = hash_password(user["password"])
    return configured_users


def verify_password(password: str, stored_password: str) -> bool:
    if stored_password.startswith("scrypt$"):
        _, salt_text, digest_text = stored_password.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
        return hmac.compare_digest(actual, expected)

    return bool(stored_password) and hmac.compare_digest(password, stored_password)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode('ascii')}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def authenticate_user(email: str, password: str) -> dict[str, str] | None:
    user = _configured_users().get(email.strip().lower())
    if user is None or not verify_password(password, user.get("password", "")):
        return None
    return {
        "email": email.strip().lower(),
        "name": user["name"],
        "role": user["role"],
    }


def create_access_token(user: dict[str, str]) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": user["email"],
        "name": user["name"],
        "role": user["role"],
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from error
    if not payload.get("sub") or not payload.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    return payload


async def require_platform_admin(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    if user.get("role") != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform Admin role required")
    return user


async def require_operator(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    if user.get("role") not in {"platform_admin", "operations_analyst"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operations role required")
    return user
