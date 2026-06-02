"""Local JWT-style authentication for the runtime API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

from video_factory_runtime.domain import ActorContext

DEFAULT_SECRET = "dev-video-factory-secret-change-me"


@dataclass(frozen=True)
class User:
    """Seeded local user."""

    user_id: str
    tenant_id: str
    email: str
    role: str
    password_hash: str
    salt: str

    def to_api(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "role": self.role,
        }


class AuthError(ValueError):
    """Authentication or token validation failure."""


def hash_password(password: str, *, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with stdlib PBKDF2."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return base64.urlsafe_b64encode(digest).decode(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, password_hash)


def create_access_token(user: User, *, secret: str | None = None, ttl_seconds: int = 86400) -> str:
    """Create an HS256 JWT-compatible bearer token."""
    secret = secret or os.environ.get("VIDEO_FACTORY_JWT_SECRET", DEFAULT_SECRET)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "role": user.role,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    signing_input = f"{_b64_json(header)}.{_b64_json(payload)}"
    signature = _b64(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def create_artifact_access_token(
    *,
    tenant_id: str,
    artifact_id: str,
    secret: str | None = None,
    ttl_seconds: int = 600,
) -> str:
    """Create a short-lived signed token for browser media playback."""
    secret = secret or os.environ.get("VIDEO_FACTORY_JWT_SECRET", DEFAULT_SECRET)
    header = {"alg": "HS256", "typ": "VF_ARTIFACT"}
    payload = {
        "tenant_id": tenant_id,
        "artifact_id": artifact_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    signing_input = f"{_b64_json(header)}.{_b64_json(payload)}"
    signature = _b64(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def verify_access_token(token: str, *, secret: str | None = None) -> ActorContext:
    """Verify a bearer token and return the actor context."""
    secret = secret or os.environ.get("VIDEO_FACTORY_JWT_SECRET", DEFAULT_SECRET)
    try:
        header_b64, payload_b64, signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("malformed bearer token") from exc
    signing_input = f"{header_b64}.{payload_b64}"
    expected = _b64(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise AuthError("invalid bearer token signature")
    payload = _unb64_json(payload_b64)
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("bearer token expired")
    return ActorContext(
        tenant_id=str(payload["tenant_id"]),
        user_id=str(payload["sub"]),
        role=str(payload["role"]),
    )


def verify_artifact_access_token(token: str, *, secret: str | None = None) -> dict[str, str]:
    """Verify a short-lived artifact media token."""
    payload = _verify_signed_payload(token, secret=secret)
    return {
        "tenant_id": str(payload["tenant_id"]),
        "artifact_id": str(payload["artifact_id"]),
    }


def _verify_signed_payload(token: str, *, secret: str | None = None) -> dict[str, Any]:
    secret = secret or os.environ.get("VIDEO_FACTORY_JWT_SECRET", DEFAULT_SECRET)
    try:
        header_b64, payload_b64, signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("malformed token") from exc
    signing_input = f"{header_b64}.{payload_b64}"
    expected = _b64(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise AuthError("invalid token signature")
    payload = _unb64_json(payload_b64)
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("token expired")
    return payload


def _b64_json(value: dict[str, Any]) -> str:
    return _b64(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _unb64_json(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode((value + padding).encode()).decode())
