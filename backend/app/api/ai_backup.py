from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.intent import (
    Intent,
    detect_intent,
    is_payment_context_question,
)
from app.ai.reasoning import analyze_recovery_decision
from app.ml.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.repositories.entities import (
    get_ai_conversation_repository,
    get_payment_attempt_repository,
    get_payment_repository,
)
from datetime import datetime, timezone

from app.models.domain import (
    AIConversation,
    AIConversationMessage,
)


router = APIRouter(prefix="/ai", tags=["ai"])


class AIMessageRequest(BaseModel):
    message: str
    history: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: str | None = None
    merchant_id: str = "DEMO_MERCHANT_1"


def format_inr(amount: float) -> str:
    """
    Format an amount as Indian Rupees.
    """
    return f"₹{amount:,.2f}"

async def get_or_create_conversation(
    conversation_id: str | None,
    merchant_id: str,
):
    conversation_repo = get_ai_conversation_repository()

    if conversation_id:
        conversation = await conversation_repo.find_by_id(
            conversation_id
        )

        if conversation:
            return conversation

    conversation = AIConversation(
        merchant_id=merchant_id,
        title="RecoverAI Conversation",
    )

    await conversation_repo.insert(conversation)

    return conversation


async def save_conversation_message(
    conversation: AIConversation,
    role: str,
    content: str,
):
    conversation_repo = get_ai_conversation_repository()

    now = datetime.now(timezone.utc)

    message = AIConversationMessage(
        role=role,
        content=content,
        timestamp=now,
    )

    conversation.messages.append(message)

    conversation.updated_at = now

    await conversation_repo.update_by_id(
        conversation.id,
        {
            "messages": [
                item.model_dump(mode="python")
                for item in conversation.messages
            ],
            "active_payment_id": conversation.active_payment_id,
            "updated_at": conversation.updated_at,
        },
    )


def history_from_conversation(
    conversation: AIConversation,
) -> list[dict[str, Any]]:
    return [
        {
            "role": item.role,
            "content": item.content,
            "timestamp": item.timestamp.isoformat(),
        }
        for item in conversation.messages
    ]

def extract_text_from_history_item(item: dict[str, Any]) -> str:
    """
    Extract conversational text from different possible frontend
    history formats.

    Supports:
        {"content": "..."}
        {"message": "..."}
        {"reply": "..."}
        {"text": "..."}
    """

    for key in (
        "content",
        "message",
        "reply",
        "text",
    ):
        value = item.get(key)

        if value:
            return str(value)

    return ""


def find_payment_id(
    message: str,
    history: list[dict[str, Any]],
    payments,
    active_payment_id: str | None = None,
) -> str | None:
    """
    Find the relevant payment ID.

    Priority:

    1. Explicit payment ID in current message.
    2. Most recent payment mentioned in conversation history,
       but ONLY if the current message is a payment-context
       follow-up.

    Example:

        User:
            Analyze DEMO_FAILED_HIGH

        User:
            Tell me more about it

    Result:

        DEMO_FAILED_HIGH
    """

    text = str(message or "").lower()

    # ---------------------------------------------------------
    # 1. Explicit payment ID in current message
    # ---------------------------------------------------------

    for payment in payments:

        payment_id = str(payment.id)

        if payment_id.lower() in text:
            return payment_id

    # ---------------------------------------------------------
    # 2. Do not use old payment context for unrelated questions
    # ---------------------------------------------------------

    if not is_payment_context_question(message):
        return None

    # ---------------------------------------------------------
    # 3. Search history from newest to oldest
    # ---------------------------------------------------------

    for item in reversed(history):

        content = extract_text_from_history_item(item).lower()

        if not content:
            continue

        for payment in payments:

            payment_id = str(payment.id)

            if payment_id.lower() in content:
                return payment_id

    # ---------------------------------------------------------
    # 4. Use persisted active payment as final fallback
    # ---------------------------------------------------------

    if active_payment_id:

        for payment in payments:

            if str(payment.id) == str(active_payment_id):

                return str(active_payment_id)

    return None


def get_frustration_response(message: str) -> str:
    """
    Provide a short empathetic response while keeping the
    conversation focused on RecoverAI.
    """

    lower = message.lower()

    if "failing" in lower or "fail" in lower:

        return (
            "I understand this is frustrating. "
            "RecoverAI can identify why payments are failing, "
            "estimate recovery probability, and recommend the "
            "safest next recovery action."
        )

    if "angry" in lower or "upset" in lower:

        return (
            "I understand you're upset. "
            "Let's work through the payment recovery issue step "
            "by step. RecoverAI can analyze failed payments, "
            "recovery probability, and recommended recovery actions."
        )

    return (
        "I understand this can be frustrating. "
        "Let's take it step by step. RecoverAI can analyze failed "
        "payments, recovery probability, revenue at risk, and "
        "recommended recovery actions."
    )


async def analyze_payment(payment, attempts):
    """
    Complete RecoverAI decision pipeline:

        MongoDB
            ↓
        Feature engineering
            ↓
        ML prediction
            ↓
        Decision engine
            ↓
        AI reasoning
    """

    payment_attempts = [
        attempt
        for attempt in attempts
        if str(attempt.payment_id) == str(payment.id)
    ]

    previous_attempts = len(payment_attempts)

    failed_attempts = sum(
        1
        for attempt in payment_attempts
        if getattr(attempt.status, "value", attempt.status) == "failed"
    )

    payment_data = payment.model_dump()

    payment_data["previous_attempts"] = previous_attempts
    payment_data["failed_attempts"] = failed_attempts

    # ---------------------------------------------------------
    # ML prediction
    # ---------------------------------------------------------

    probability = predict_recovery_probability(
        payment_data
    )

    # ---------------------------------------------------------
    # Decision engine
    # ---------------------------------------------------------

    action = choose_recovery_action(
        probability=probability,
        failure_reason=payment.failure_reason,
        attempts=previous_attempts,
    )

    # ---------------------------------------------------------
    # AI reasoning
    # ---------------------------------------------------------

    reasoning = analyze_recovery_decision(
        payment=payment_data,
        probability=probability,
        recommended_action=action.value,
    )

    return {
        "payment": payment,
        "probability": probability,
        "action": action,
        "reasoning": reasoning,
        "previous_attempts": previous_attempts,
        "failed_attempts": failed_attempts,
    }


def get_payment_status(payment) -> str:
    """
    Safely get a payment status whether status is an Enum
    or a plain string.
    """

    return str(
        getattr(payment.status, "value", payment.status)
    ).lower()


def get_attempt_status(attempt) -> str:
    """
    Safely get an attempt status whether status is an Enum
    or a plain string.
    """

    return str(
        getattr(attempt.status, "value", attempt.status)
    ).lower()


@router.post("/message")
async def ai_message(request: AIMessageRequest):

    message = request.message.strip()

    if not message:

        return {
            "type": "general",
            "reply": "Please enter a question.",
        }

    lower = message.lower()

    # ---------------------------------------------------------
    # Detect intent
    # ---------------------------------------------------------

    intent = detect_intent(message)

    # ---------------------------------------------------------
    # OUT OF SCOPE
    # ---------------------------------------------------------

    if intent == Intent.OUT_OF_SCOPE:

        return {
            "type": "out_of_scope",
            "reply": (
                "I understand. I'm here specifically to help with "
                "RecoverAI and payment recovery. I can't answer "
                "unrelated questions, but I can help with failed "
                "payments, recovery probability, revenue at risk, "
                "recovery attempts, payment prioritization, and "
                "recommended recovery actions."
            ),
        }

    # ---------------------------------------------------------
    # GENERAL RECOVERAI QUESTIONS
    # ---------------------------------------------------------

    if intent == Intent.GENERAL_RECOVERAI:

        if (
            "what can you help me with" in lower
            or "what can you help with" in lower
        ):

            return {
                "type": "general",
                "reply": (
                    "I can help you analyze failed payments, "
                    "predict recovery probability, decide whether "
                    "a payment should be retried, identify failure "
                    "patterns, prioritize payments for recovery, "
                    "and track recovered revenue, revenue at risk, "
                    "recovery attempts, and recovery rate."
                ),
            }

        if (
            "what does recoverai do" in lower
            or "what is recoverai" in lower
            or "what's recoverai" in lower
        ):

            return {
                "type": "general",
                "reply": (
                    "RecoverAI is an intelligent payment recovery "
                    "system. It analyzes failed payments, uses "
                    "recovery probability predictions to assess "
                    "the likelihood of successful recovery, and "
                    "recommends actions such as SMART_RETRY, "
                    "REMINDER, PAYMENT_METHOD_SUGGESTION, "
                    "SUPPORT_ESCALATION, or STOP."
                ),
            }

        if "how does payment recovery work" in lower:

            return {
                "type": "general",
                "reply": (
                    "RecoverAI analyzes a failed payment using "
                    "factors such as transaction amount, payment "
                    "method, failure reason, and previous recovery "
                    "attempts. The ML model predicts the probability "
                    "of successful recovery. The decision engine "
                    "then recommends the safest next action, such "
                    "as a controlled retry or stopping automated "
                    "recovery."
                ),
            }

        if (
            "how do you decide whether to retry" in lower
            or "how do you decide to retry" in lower
            or "how do you decide whether a payment should be retried"
            in lower
            or "how do you decide whether to retry a payment"
            in lower
        ):

            return {
                "type": "general",
                "reply": (
                    "RecoverAI considers the predicted recovery "
                    "probability, payment failure reason, and "
                    "previous recovery attempts. A high recovery "
                    "probability with few previous attempts can "
                    "result in SMART_RETRY. Repeated failures or "
                    "a very low recovery probability can result "
                    "in STOP or another safer recovery action."
                ),
            }

    # ---------------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------------

    payment_repo = get_payment_repository()
    attempt_repo = get_payment_attempt_repository()

    payments = await payment_repo.find_many(limit=1000)
    attempts = await attempt_repo.find_many(limit=1000)

    # ---------------------------------------------------------
    # FIND PAYMENT CONTEXT
    # ---------------------------------------------------------

    payment_id = find_payment_id(
        message,
        request.history,
        payments,
    )

    selected_payment = None

    if payment_id:

        selected_payment = next(
            (
                payment
                for payment in payments
                if str(payment.id) == str(payment_id)
            ),
            None,
        )

    # ---------------------------------------------------------
    # FRUSTRATION
    # ---------------------------------------------------------
    #
    # Only return the frustration response when the user has
    # NOT simultaneously asked for a specific payment action.
    #
    # Example:
    #
    # "I'm frustrated. Should I retry DEMO_FAILED_HIGH?"
    #
    # should still be handled as retry_decision.
    #

    if (
        intent == Intent.FRUSTRATION
        and selected_payment is None
    ):

        return {
            "type": "support",
            "reply": get_frustration_response(message),
        }

    # =========================================================
    # PAYMENT-SPECIFIC QUESTIONS
    # =========================================================

    if selected_payment:

        # -----------------------------------------------------
        # FAILURE REASON
        # -----------------------------------------------------

        if (
            "failure reason" in lower
            or "why did it fail" in lower
            or "why is it failing" in lower
            or "what caused it to fail" in lower
        ):

            failure_reason = (
                selected_payment.failure_reason
                or "Unknown failure reason"
            )

            return {
                "type": "payment_analysis",
                "payment_id": selected_payment.id,
                "reply": (
                    f"The failure reason for payment "
                    f"{selected_payment.id} is "
                    f"{failure_reason}."
                ),
            }

        # -----------------------------------------------------
        # PAYMENT AMOUNT / VALUE
        # -----------------------------------------------------

        if (
            "how much is it worth" in lower
            or "how much is this worth" in lower
            or "how much is that worth" in lower
            or "what is its value" in lower
            or "what's its value" in lower
            or "what is its amount" in lower
            or "what's its amount" in lower
            or "what is the amount" in lower
            or "what's the amount" in lower
            or "how much was the payment" in lower
            or "how much is the payment" in lower
        ):

            return {
                "type": "payment_analysis",
                "payment_id": selected_payment.id,
                "reply": (
                    f"Payment {selected_payment.id} is worth "
                    f"{format_inr(selected_payment.amount)}."
                ),
            }

        # -----------------------------------------------------
        # "TELL ME MORE" / DETAILS
        # -----------------------------------------------------

        if (
            "tell me more" in lower
            or "more about" in lower
            or "more details" in lower
            or "give me more details" in lower
            or "explain it" in lower
            or "explain this" in lower
            or "explain that" in lower
            or "details about it" in lower
        ):

            result = await analyze_payment(
                selected_payment,
                attempts,
            )

            reasoning = result["reasoning"]

            return {
                "type": "payment_analysis",
                "payment_id": selected_payment.id,
                "reply": reasoning["reasoning"],
                "analysis": {
                    **reasoning,
                    "previous_attempts": result["previous_attempts"],
                    "failed_attempts": result["failed_attempts"],
                },
            }

    # =========================================================
    # 1. PRIORITIZATION
    # =========================================================

    if intent == Intent.PRIORITIZATION:

        candidates = []

        for payment in payments:

            status = get_payment_status(payment)

            if status in (
                "recovered",
                "successful",
                "success",
            ):
                continue

            result = await analyze_payment(
                payment,
                attempts,
            )

            candidates.append(result)

        # -----------------------------------------------------
        # Priority score
        # -----------------------------------------------------

        for item in candidates:

            item["priority_score"] = (
                item["payment"].amount
                * item["probability"]
            )

        candidates.sort(
            key=lambda item: item["priority_score"],
            reverse=True,
        )

        if not candidates:

            return {
                "type": "priority",
                "reply": (
                    "There are currently no unrecovered payments "
                    "that require prioritization."
                ),
                "payments": [],
            }

        top = candidates[:5]

        priority_list = []

        for index, item in enumerate(top, start=1):

            payment = item["payment"]

            priority_list.append(
                {
                    "rank": index,
                    "payment_id": payment.id,
                    "amount": payment.amount,
                    "recovery_probability": item["probability"],
                    "priority_score": round(
                        item["priority_score"],
                        2,
                    ),
                    "recommended_action": item["action"].value,
                }
            )

        first = top[0]
        first_payment = first["payment"]

        reply = (
            f"The highest-priority payment is "
            f"{first_payment.id}. "
            f"It has "
            f"{first['probability'] * 100:.2f}% "
            f"predicted recovery probability and "
            f"{format_inr(first_payment.amount)} "
            f"at stake. "
            f"RecoverAI recommends "
            f"{first['action'].value}."
        )

        return {
            "type": "priority",
            "reply": reply,
            "payments": priority_list,
        }

    # =========================================================
    # 2. RECOVERED REVENUE
    # =========================================================

    if intent == Intent.RECOVERED_REVENUE:

        recovered = sum(
            payment.amount
            for payment in payments
            if get_payment_status(payment)
            in (
                "recovered",
                "successful",
                "success",
            )
        )

        return {
            "type": "analytics",
            "reply": (
                f"RecoverAI has recovered "
                f"{format_inr(recovered)} "
                f"of revenue."
            ),
        }

    # =========================================================
    # 3. REVENUE AT RISK
    # =========================================================

    if intent == Intent.REVENUE_AT_RISK:

        at_risk = sum(
            payment.amount
            for payment in payments
            if get_payment_status(payment)
            in (
                "failed",
                "at_risk",
                "recovering",
            )
        )

        return {
            "type": "analytics",
            "reply": (
                f"Revenue currently at risk is "
                f"{format_inr(at_risk)}."
            ),
        }

    # =========================================================
    # 4. RECOVERY RATE
    # =========================================================

    if intent == Intent.RECOVERY_RATE:

        successful_attempts = sum(
            1
            for attempt in attempts
            if get_attempt_status(attempt) == "success"
        )

        recovery_rate = (
            successful_attempts
            / len(attempts)
            * 100
            if attempts
            else 0
        )

        return {
            "type": "analytics",
            "reply": (
                f"The current recovery rate is "
                f"{recovery_rate:.2f}%."
            ),
        }

    # =========================================================
    # 5. ATTEMPT ANALYSIS
    # =========================================================

    if intent == Intent.ATTEMPT_ANALYSIS:

        successful = sum(
            1
            for attempt in attempts
            if get_attempt_status(attempt) == "success"
        )

        failed = sum(
            1
            for attempt in attempts
            if get_attempt_status(attempt) == "failed"
        )

        return {
            "type": "analytics",
            "reply": (
                f"There have been {len(attempts)} "
                f"recovery attempts. "
                f"{successful} succeeded and "
                f"{failed} failed."
            ),
        }

    # =========================================================
    # 6. FAILURE ANALYSIS
    # =========================================================

    if intent == Intent.FAILURE_ANALYSIS:

        failed_payments = [
            payment
            for payment in payments
            if get_payment_status(payment) == "failed"
        ]

        if not failed_payments:

            return {
                "type": "failure_analysis",
                "reply": (
                    "There are currently no failed payments "
                    "to analyze."
                ),
            }

        failure_reasons = {}

        for payment in failed_payments:

            reason = (
                payment.failure_reason
                or "Unknown failure reason"
            )

            failure_reasons[reason] = (
                failure_reasons.get(reason, 0) + 1
            )

        sorted_reasons = sorted(
            failure_reasons.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        reason_text = ", ".join(
            f"{reason} ({count})"
            for reason, count in sorted_reasons
        )

        return {
            "type": "failure_analysis",
            "reply": (
                f"There are currently "
                f"{len(failed_payments)} failed payments. "
                f"The recorded failure reasons are: "
                f"{reason_text}."
            ),
            "failure_reasons": [
                {
                    "reason": reason,
                    "count": count,
                }
                for reason, count in sorted_reasons
            ],
        }

    # =========================================================
    # 7. TOTAL PAYMENTS
    # =========================================================

    if (
        "total payments" in lower
        or "how many payments" in lower
        or "number of payments" in lower
        or "total transactions" in lower
    ):

        return {
            "type": "analytics",
            "reply": (
                f"RecoverAI currently has "
                f"{len(payments)} payments."
            ),
        }

    # =========================================================
    # 8. RECOVERY PROBABILITY
    # =========================================================

    if intent == Intent.RECOVERY_PROBABILITY:

        if not selected_payment:

            return {
                "type": "recovery_probability",
                "reply": (
                    "I can calculate the predicted recovery "
                    "probability. Please provide the payment ID "
                    "you'd like me to analyze."
                ),
            }

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        probability = result["probability"]

        return {
            "type": "recovery_probability",
            "payment_id": selected_payment.id,
            "reply": (
                f"RecoverAI predicts a "
                f"{probability * 100:.2f}% chance of recovering "
                f"payment {selected_payment.id}."
            ),
            "analysis": {
                "probability": probability,
                "recommended_action": result["action"].value,
                "previous_attempts": result["previous_attempts"],
                "failed_attempts": result["failed_attempts"],
            },
        }

    # =========================================================
    # 9. RETRY DECISION
    # =========================================================

    if intent == Intent.RETRY_DECISION:

        if not selected_payment:

            return {
                "type": "retry_decision",
                "reply": (
                    "I can determine whether a retry is "
                    "recommended. Please provide the payment "
                    "ID you'd like me to analyze."
                ),
            }

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        action = result["action"]

        return {
            "type": "retry_decision",
            "payment_id": selected_payment.id,
            "reply": (
                f"For payment {selected_payment.id}, "
                f"RecoverAI recommends: {action.value}."
            ),
            "analysis": {
                "probability": result["probability"],
                "recommended_action": action.value,
                "previous_attempts": result["previous_attempts"],
                "failed_attempts": result["failed_attempts"],
                "reasoning": result["reasoning"],
            },
        }

    # =========================================================
    # 10. PAYMENT ANALYSIS
    # =========================================================

    if (
        selected_payment
        and intent == Intent.PAYMENT_ANALYSIS
    ):

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        reasoning = result["reasoning"]

        return {
            "type": "payment_analysis",
            "payment_id": selected_payment.id,
            "reply": reasoning["reasoning"],
            "analysis": {
                **reasoning,
                "previous_attempts": result["previous_attempts"],
                "failed_attempts": result["failed_attempts"],
            },
        }

    # =========================================================
    # 11. PAYMENT-SPECIFIC FALLBACK
    # =========================================================

    if selected_payment:

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        reasoning = result["reasoning"]

        return {
            "type": "payment_analysis",
            "payment_id": selected_payment.id,
            "reply": reasoning["reasoning"],
            "analysis": {
                **reasoning,
                "previous_attempts": result["previous_attempts"],
                "failed_attempts": result["failed_attempts"],
            },
        }

    # =========================================================
    # 12. GENERAL FALLBACK
    # =========================================================

    return {
        "type": "general",
        "reply": (
            f"I analyzed {len(payments)} payments and "
            f"{len(attempts)} recovery attempts. "
            "You can ask me about a specific payment, "
            "why payments are failing, recovery probability, "
            "recommended actions, payment prioritization, "
            "high-value payments at risk, recovered revenue, "
            "revenue at risk, recovery attempts, or recovery rate."
        ),
    }