"""
Authentication and JWT security utilities for RecoverAI.

This module contains:
- password hashing
- password verification
- JWT access-token creation
- JWT access-token validation
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash


# ============================================================
# JWT CONFIGURATION
# ============================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "recoverai-development-secret-change-me",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Securely hash a plaintext password.

    The plaintext password must never be stored in MongoDB.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(password)


def verify_password(
    password: str,
    stored_password_hash: str,
) -> bool:
    """
    Verify a plaintext password against its stored hash.
    """

    if not password or not stored_password_hash:
        return False

    try:
        return password_hash.verify(
            password,
            stored_password_hash,
        )
    except Exception:
        return False


# ============================================================
# JWT CREATION
# ============================================================

def create_access_token(
    subject: str,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    The `sub` claim contains the merchant ID.
    """

    if not subject:
        raise ValueError(
            "JWT subject cannot be empty."
        )

    expiration_minutes = (
        expires_minutes
        if expires_minutes is not None
        else JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    now = datetime.now(timezone.utc)

    expires_at = (
        now
        + timedelta(
            minutes=expiration_minutes
        )
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# JWT VALIDATION
# ============================================================

def decode_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        jwt.InvalidTokenError:
            If the token is invalid or expired.
    """

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )