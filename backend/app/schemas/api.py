"""Public API DTOs for the RecoverAI frontend.

These schemas are deliberately separate from the MongoDB/domain models. The
frontend consumes camelCase JSON while the domain layer keeps Python/Mongo
snake_case field names.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import (
    PaymentAttemptStatus,
    PaymentStatus,
    RecommendedAction,
    RecoveryCaseStatus,
)


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class TimelineEventDTO(APIModel):
    id: str
    type: str
    title: str
    description: str
    timestamp: str | None = None
    status: Literal["completed", "current", "pending"]


class PaymentAttemptDTO(APIModel):
    id: str
    payment_id: str = Field(alias="paymentId")
    attempt_number: int = Field(alias="attemptNumber")
    method: str | None = None
    amount: float | None = None
    status: PaymentAttemptStatus
    failure_reason: str | None = Field(default=None, alias="failureReason")
    timestamp: str | None = None


class CustomerDTO(APIModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    total_payments: int = Field(alias="totalPayments")
    successful_payments: int = Field(alias="successfulPayments")
    failed_payments: int = Field(alias="failedPayments")
    total_amount: float = Field(alias="totalAmount")
    recovery_probability: float = Field(alias="recoveryProbability", ge=0, le=100)
    risk_profile: str = Field(alias="riskProfile")
    avatar_color: str | None = Field(default=None, alias="avatarColor")
    joined_at: str | None = Field(default=None, alias="joinedAt")


class AIAnalysisDTO(APIModel):
    probability: float = Field(ge=0, le=1)
    probability_percent: float = Field(alias="probabilityPercent", ge=0, le=100)
    risk_level: str = Field(alias="riskLevel")
    recommended_action: RecommendedAction = Field(alias="recommendedAction")
    summary: str
    reasoning: str
    next_step: str = Field(alias="nextStep")
    payment_amount: float = Field(alias="paymentAmount")
    payment_method: str = Field(alias="paymentMethod")
    failure_reason: str = Field(alias="failureReason")
    previous_attempts: int = Field(alias="previousAttempts", ge=0)
    failed_attempts: int = Field(alias="failedAttempts", ge=0)


class PaymentDTO(APIModel):
    id: str
    customer_id: str = Field(alias="customerId")
    customer_name: str = Field(alias="customerName")
    customer_email: str = Field(alias="customerEmail")
    amount: float
    currency: str
    payment_method: str = Field(alias="paymentMethod")
    status: PaymentStatus
    failure_reason: str | None = Field(default=None, alias="failureReason")
    recovery_probability: float = Field(alias="recoveryProbability", ge=0, le=100)
    last_attempt: str | None = Field(default=None, alias="lastAttempt")
    recommended_action: RecommendedAction = Field(alias="recommendedAction")
    created_at: str | None = Field(default=None, alias="createdAt")
    attempts: list[PaymentAttemptDTO] = Field(default_factory=list)
    timeline: list[TimelineEventDTO] = Field(default_factory=list)
    ai_explanation: AIAnalysisDTO | None = Field(default=None, alias="aiExplanation")


class RecoveryCaseDTO(APIModel):
    id: str
    payment_id: str = Field(alias="paymentId")
    customer_id: str = Field(alias="customerId")
    customer_name: str = Field(alias="customerName")
    amount_at_risk: float = Field(alias="amountAtRisk")
    failure_reason: str = Field(alias="failureReason")
    recovery_probability: float = Field(alias="recoveryProbability", ge=0, le=100)
    recommended_action: RecommendedAction = Field(alias="recommendedAction")
    status: RecoveryCaseStatus
    attempts: int = Field(ge=0)
    created_at: str | None = Field(default=None, alias="createdAt")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    ai_explanation: AIAnalysisDTO | None = Field(default=None, alias="aiExplanation")


class DashboardStatsDTO(APIModel):
    total_transactions: int = Field(alias="totalTransactions")
    successful_payments: int = Field(alias="successfulPayments")
    failed_payments: int = Field(alias="failedPayments")
    revenue_at_risk: float = Field(alias="revenueAtRisk")
    revenue_recovered: float = Field(alias="revenueRecovered")
    recovery_rate: float = Field(alias="recoveryRate")


class RevenuePointDTO(APIModel):
    label: str
    recovered: float
    at_risk: float = Field(alias="atRisk")


class PaymentStatusPointDTO(APIModel):
    label: str
    successful: int
    failed: int


class FailureReasonStatDTO(APIModel):
    reason: str
    count: int
    amount: float


class AIRecommendationDTO(APIModel):
    id: str
    payment_id: str = Field(alias="paymentId")
    customer_name: str = Field(alias="customerName")
    amount: float
    reason: str
    probability: float = Field(ge=0, le=100)
    action: RecommendedAction
    rationale: str


class RecentRecoveryAttemptDTO(APIModel):
    id: str
    customer_name: str = Field(alias="customerName")
    amount: float
    action: RecommendedAction
    status: str
    timestamp: str | None = None


class DashboardDTO(APIModel):
    stats: DashboardStatsDTO
    revenue_chart: list[RevenuePointDTO] = Field(alias="revenueChart")
    status_chart: list[PaymentStatusPointDTO] = Field(alias="statusChart")
    recent_attempts: list[RecentRecoveryAttemptDTO] = Field(alias="recentAttempts")
    top_failure_reasons: list[FailureReasonStatDTO] = Field(alias="topFailureReasons")
    recommendations: list[AIRecommendationDTO]


class RecoveryMethodStatDTO(APIModel):
    method: str
    recovered: float
    attempted: float


class RecoveryReasonStatDTO(APIModel):
    reason: str
    recovered: float
    attempted: float


class AnalyticsDTO(APIModel):
    revenue_at_risk: float = Field(alias="revenueAtRisk")
    revenue_recovered: float = Field(alias="revenueRecovered")
    recovery_rate: float = Field(alias="recoveryRate")
    recovery_attempts: int = Field(alias="recoveryAttempts")
    successful_recoveries: int = Field(alias="successfulRecoveries")
    recovery_by_method: list[RecoveryMethodStatDTO] = Field(alias="recoveryByMethod")
    recovery_by_reason: list[RecoveryReasonStatDTO] = Field(alias="recoveryByReason")
    performance_over_time: list[RevenuePointDTO] = Field(alias="performanceOverTime")


class RecoveryWorkflowResultDTO(APIModel):
    payment: dict[str, Any] | None = None
    recovery_case: dict[str, Any] | None = Field(default=None, alias="recoveryCase")
    payment_attempt: dict[str, Any] | None = Field(default=None, alias="paymentAttempt")
    audit_log: dict[str, Any] | None = Field(default=None, alias="auditLog")
    probability: float | None = None
    action: RecommendedAction | None = None
    recommended_action: RecommendedAction | None = Field(default=None, alias="recommendedAction")
    success: bool
    ai_explanation: AIAnalysisDTO | None = Field(default=None, alias="aiExplanation")
    message: str | None = None


class RecoveryActionResponseDTO(APIModel):
    success: bool
    payment_id: str = Field(alias="paymentId")
    requested_action: RecommendedAction | None = Field(default=None, alias="requestedAction")
    recommended_action: RecommendedAction | None = Field(default=None, alias="recommendedAction")
    selected_action: RecommendedAction | None = Field(default=None, alias="selectedAction")
    action_overridden: bool = Field(alias="actionOverridden")
    result: RecoveryWorkflowResultDTO | None = None


class AIResponseDTO(APIModel):
    type: str
    reply: str
    conversation_id: str | None = Field(default=None, alias="conversationId")
    payment_id: str | None = Field(default=None, alias="paymentId")
    analysis: dict[str, Any] | None = None
    payments: list[dict[str, Any]] | None = None
    failure_reasons: list[dict[str, Any]] | None = Field(default=None, alias="failureReasons")
