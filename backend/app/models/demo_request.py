"""
Demo request domain model for RecoverAI.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DemoRequest(BaseModel):
    """
    A prospective merchant requesting a RecoverAI demo.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    name: str = Field(
        min_length=1
    )

    email: EmailStr

    business_name: str = Field(
        min_length=1
    )

    status: str = Field(
        default="new"
    )

    created_at: datetime = Field(
        default_factory=utcnow
    )