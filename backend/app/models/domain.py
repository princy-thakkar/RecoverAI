"""
Domain models for RecoverAI.

These models define the data contract between:
    MongoDB <-> repositories <-> services <-> API routes <-> frontend

No demo IDs, merchant IDs, customer IDs, payment IDs, or other
application-specific values are hardcoded here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# COMMON HELPERS
# ============================================================

def utcnow() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


# ============================================================
# ENUMS
# ============================================================

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    AT_RISK = "at_risk"
    RECOVERING = "recovering"
    RECOVERED = "recovered"


class PaymentAttemptStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class RecoveryCaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER = "awaiting_customer"
    RETRY_SCHEDULED = "retry_scheduled"
    RECOVERED = "recovered"
    FAILED = "failed"


class RecommendedAction(str, Enum):
    """
    Actions that the recovery decision engine can recommend.
    """

    SMART_RETRY = "SMART_RETRY"
    PAYMENT_METHOD_SUGGESTION = "PAYMENT_METHOD_SUGGESTION"
    REMINDER = "REMINDER"
    SUPPORT_ESCALATION = "SUPPORT_ESCALATION"
    STOP = "STOP"


# ============================================================
# MERCHANT
# ============================================================

class Merchant(BaseModel):
    """
    A business using RecoverAI.

    password_hash contains only the securely hashed password.
    Plaintext passwords must never be stored.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    name: str

    email: EmailStr

    password_hash: str | None = Field(
        default=None,
        min_length=1,
    )

    created_at: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# CUSTOMER
# ============================================================

class Customer(BaseModel):
    """
    A customer belonging to a merchant.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    merchant_id: str = Field(
        min_length=1
    )

    name: str = Field(
        min_length=1
    )

    email: EmailStr

    phone: str = Field(
        min_length=1
    )

    risk_score: float = Field(
        ge=0,
        le=1,
        description=(
            "0 = low risk of payment failure, "
            "1 = high risk of payment failure."
        ),
    )

    created_at: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# PAYMENT
# ============================================================

class Payment(BaseModel):
    """
    A payment transaction belonging to a merchant and customer.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    merchant_id: str = Field(
        min_length=1
    )

    customer_id: str = Field(
        min_length=1
    )

    amount: float = Field(
        gt=0
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    status: PaymentStatus

    payment_method: str = Field(
        min_length=1
    )

    failure_reason: str | None = None

    created_at: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# PAYMENT ATTEMPT
# ============================================================

class PaymentAttempt(BaseModel):
    """
    A recovery/retry attempt made against a payment.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    payment_id: str = Field(
        min_length=1
    )

    attempt_number: int = Field(
        ge=1
    )

    status: PaymentAttemptStatus

    attempted_at: datetime = Field(
        default_factory=utcnow
    )

    failure_reason: str | None = None


# ============================================================
# RECOVERY CASE
# ============================================================

class RecoveryCase(BaseModel):
    """
    Recovery workflow state for a failed or at-risk payment.

    Recovery probability and recommended action are values produced
    by the ML/decision pipeline and stored with the recovery case.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    payment_id: str = Field(
        min_length=1
    )

    customer_id: str = Field(
        min_length=1
    )

    recovery_probability: float = Field(
        ge=0,
        le=1
    )

    status: RecoveryCaseStatus

    recommended_action: RecommendedAction

    created_at: datetime = Field(
        default_factory=utcnow
    )

    updated_at: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(BaseModel):
    """
    Immutable record of an automated decision or action.

    Every automated recovery decision can be logged here together
    with the reason and confidence.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    payment_id: str = Field(
        min_length=1
    )

    action: str = Field(
        min_length=1
    )

    reason: str = Field(
        min_length=1
    )

    confidence: float = Field(
        ge=0,
        le=1
    )

    created_at: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# AI CONVERSATION MESSAGE
# ============================================================

class AIConversationMessage(BaseModel):
    """
    One message stored inside an AI conversation.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    role: str = Field(
        min_length=1
    )

    content: str = Field(
        min_length=1
    )

    timestamp: datetime = Field(
        default_factory=utcnow
    )


# ============================================================
# AI CONVERSATION
# ============================================================

class AIConversation(BaseModel):
    """
    Persistent conversation memory for the RecoverAI assistant.

    merchant_id is required and is never hardcoded.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    merchant_id: str = Field(
        min_length=1
    )

    title: str = Field(
        default="RecoverAI Conversation",
        min_length=1,
    )

    active_payment_id: str | None = None

    messages: list[AIConversationMessage] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=utcnow
    )

    updated_at: datetime = Field(
        default_factory=utcnow
    )
    
# ============================================================
# DEMO REQUEST
# ============================================================

class DemoRequest(BaseModel):
    """
    A prospective customer requesting a RecoverAI demo.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )

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