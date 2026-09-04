from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import CurrentMerchant
from app.ai.intent import (
    Intent,
    detect_intent,
    is_payment_context_question,
)
from app.ai.reasoning import analyze_recovery_decision
from app.ml.decision import choose_recovery_action
from app.ml.predict import predict_recovery_probability
from app.schemas.api import AIResponseDTO
from app.repositories.entities import (
    get_ai_conversation_repository,
    get_payment_attempt_repository,
    get_payment_repository,
)
from app.models.domain import (
    AIConversation,
    AIConversationMessage,
)


router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class AIMessageRequest(BaseModel):
    """
    Request received from the frontend AI assistant.

    The merchant is determined from the authenticated JWT
    rather than being accepted from the request body.
    """

    message: str = Field(min_length=1)
    history: list[dict[str, Any]] = Field(default_factory=list)
    conversation_id: str | None = None


# =========================================================
# HELPERS
# =========================================================

def get_enum_value(value: Any) -> str:
    """
    Return the underlying value when the object is an Enum,
    otherwise return the value itself as a string.
    """

    return str(
        getattr(
            value,
            "value",
            value,
        )
    )

# =========================================================
# BASIC CONVERSATION
# =========================================================

def get_basic_conversation_response(
    message: str,
) -> str | None:
    """
    Handle simple conversational questions that should not be
    classified as payment-domain questions.
    """

    lower = (
        message
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # GREETINGS
    # -----------------------------------------------------

    greetings = {
        "hi",
        "hello",
        "hey",
        "hiya",
        "howdy",
        "good morning",
        "good afternoon",
        "good evening",
    }

    if lower in greetings:
        if lower == "good morning":
            return (
                "Good morning! 👋 I'm your RecoverAI assistant. "
                "I can help you analyze recovered revenue, "
                "failed payments, revenue at risk, and recovery priorities. "
                "What would you like to check?"
            )

        if lower == "good afternoon":
            return (
                "Good afternoon! 👋 I'm your RecoverAI assistant. "
                "I can help you analyze recovered revenue, "
                "failed payments, revenue at risk, and recovery priorities. "
                "What would you like to check?"
            )

        if lower == "good evening":
            return (
                "Good evening! 👋 I'm your RecoverAI assistant. "
                "I can help you analyze recovered revenue, "
                "failed payments, revenue at risk, and recovery priorities. "
                "What would you like to check?"
            )

        return (
            "Hello! 👋 I'm your RecoverAI assistant. "
            "I can help you analyze recovered revenue, "
            "failed payments, revenue at risk, and recovery priorities. "
            "What would you like to check?"
        )

    # -----------------------------------------------------
    # IDENTITY
    # -----------------------------------------------------

    if lower in {
        "what is your name",
        "what's your name",
        "who are you",
        "what are you",
        "tell me your name",
    }:
        return (
            "I'm RecoverAI, your AI payment-recovery assistant. "
            "I help you understand failed payments, recovery probability, "
            "revenue at risk, recovery opportunities, and recommended "
            "recovery actions."
        )

    # -----------------------------------------------------
    # CAPABILITIES
    # -----------------------------------------------------

    if lower in {
        "what can you do",
        "what can you help me with",
        "what can you help with",
        "how can you help me",
    }:
        return (
            "I can help you analyze failed payments, predict recovery "
            "probability, identify failure patterns, prioritize payments "
            "for recovery, explain retry decisions, and track recovered "
            "revenue, revenue at risk, recovery attempts, and recovery rate."
        )

    # -----------------------------------------------------
    # THANKS
    # -----------------------------------------------------

    if lower in {
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you so much",
    }:
        return (
            "You're welcome! 👋 I'm here whenever you want to analyze "
            "your payment recovery performance."
        )

    return None


# =========================================================
# RECOVERY STRATEGY / POLICY QUESTIONS
# =========================================================

def get_strategy_policy_response(
    message: str,
) -> str | None:
    """
    Answer RecoverAI strategy and policy questions directly.

    These questions are about how the RecoverAI recovery system works,
    rather than about a specific payment or merchant metric. Handling them
    explicitly prevents them from falling through to the generic analytics
    response when the intent classifier does not have a dedicated intent.
    """

    lower = (
        str(message or "")
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # INDEFINITE / UNLIMITED RETRIES
    # -----------------------------------------------------

    indefinite_retry_phrases = (
        "retry indefinitely",
        "retry forever",
        "retry forever?",
        "retry without limit",
        "retry with no limit",
        "retry unlimited",
        "unlimited retries",
        "unlimited recovery attempts",
        "can you retry a payment indefinitely",
        "can we retry a payment indefinitely",
        "can i retry a payment indefinitely",
        "can you retry indefinitely",
        "can we retry indefinitely",
        "can i retry indefinitely",
        "retry a payment forever",
        "retry payments forever",
        "retry a payment without limit",
        "retry payments without limit",
        "retry a payment with no limit",
        "retry payments with no limit",
    )

    if any(
        phrase in lower
        for phrase in indefinite_retry_phrases
    ):
        return (
            "No. RecoverAI does not retry payments indefinitely. "
            "Recovery is bounded by policy, including a maximum of "
            "3 recovery attempts. If the payment reaches that limit, "
            "or the failure is non-retryable, the policy can select STOP. "
            "AI recommends the recovery action; policy authorizes whether "
            "that action is allowed."
        )

    # -----------------------------------------------------
    # MAXIMUM ATTEMPTS / STOP POLICY
    # -----------------------------------------------------

    maximum_attempt_phrases = (
        "maximum recovery attempts",
        "maximum number of recovery attempts",
        "maximum attempts",
        "max attempts",
        "how many times can we retry",
        "how many times can i retry",
        "how many retries are allowed",
        "how many recovery attempts are allowed",
        "what happens after 3 attempts",
        "what happens after three attempts",
        "what happens after 3 retries",
        "what happens after three retries",
        "after 3 failed recovery attempts",
        "after three failed recovery attempts",
    )

    if any(
        phrase in lower
        for phrase in maximum_attempt_phrases
    ):
        return (
            "RecoverAI allows a maximum of 3 recovery attempts. "
            "The decision engine considers the payment context and "
            "recovery probability, while the policy engine enforces the "
            "attempt limit. Once the limit is reached, RecoverAI should "
            "stop automated recovery rather than retry indefinitely."
        )

    # -----------------------------------------------------
    # SMART RETRY
    # -----------------------------------------------------

    smart_retry_phrases = (
        "when should recoverai use a smart retry",
        "when should recoverai use smart retry",
        "when should we use a smart retry",
        "when should we use smart retry",
        "when should i use a smart retry",
        "when should i use smart retry",
        "when do we use a smart retry",
        "when do we use smart retry",
        "when is smart retry appropriate",
        "when should smart retry be used",
        "when should recoverai retry",
        "when should recoverai retry a payment",
        "when should recoverai perform a smart retry",
    )

    if any(
        phrase in lower
        for phrase in smart_retry_phrases
    ):
        return (
            "RecoverAI uses SMART_RETRY when the payment appears "
            "recoverable and the failure context supports another retry. "
            "The system considers the predicted recovery probability, "
            "failure reason, and previous recovery attempts. Transient "
            "failures such as network or timing-related problems are more "
            "appropriate retry candidates, while non-retryable failures "
            "should not be blindly retried. The policy engine must still "
            "authorize the action and enforce safety limits."
        )

    # -----------------------------------------------------
    # REMINDER
    # -----------------------------------------------------

    reminder_phrases = (
        "when should recoverai send a reminder",
        "when should we send a reminder",
        "when should recoverai use a reminder",
        "when is a reminder appropriate",
        "when should i send a payment reminder",
    )

    if any(
        phrase in lower
        for phrase in reminder_phrases
    ):
        return (
            "RecoverAI uses REMINDER when asking the customer to complete "
            "or retry the payment is more appropriate than automatically "
            "attempting another charge. This is especially useful when "
            "customer action is needed or another automated retry would add "
            "little value."
        )

    # -----------------------------------------------------
    # PAYMENT METHOD SUGGESTION
    # -----------------------------------------------------

    method_suggestion_phrases = (
        "when should recoverai suggest another payment method",
        "when should we suggest another payment method",
        "when should recoverai suggest a different payment method",
        "when is payment method suggestion appropriate",
        "when should i suggest another payment method",
    )

    if any(
        phrase in lower
        for phrase in method_suggestion_phrases
    ):
        return (
            "RecoverAI can use PAYMENT_METHOD_SUGGESTION when the current "
            "payment method is unlikely to recover the transaction, such as "
            "an expired or invalid card. Instead of repeatedly retrying the "
            "same failed method, the system can guide the customer toward "
            "an alternative payment method."
        )

    # -----------------------------------------------------
    # SUPPORT ESCALATION
    # -----------------------------------------------------

    support_phrases = (
        "when should recoverai escalate to support",
        "when should we escalate to support",
        "when is support escalation appropriate",
        "when should recoverai use support escalation",
        "when should i escalate a payment to support",
    )

    if any(
        phrase in lower
        for phrase in support_phrases
    ):
        return (
            "RecoverAI uses SUPPORT_ESCALATION when automated recovery is "
            "not appropriate or when the payment needs human intervention. "
            "The goal is to avoid repeated automated actions when a support "
            "team is better positioned to resolve the issue."
        )

    # -----------------------------------------------------
    # STOP / POLICY
    # -----------------------------------------------------

    stop_phrases = (
        "when should recoverai stop",
        "when should recoverai stop recovery",
        "when should we stop recovery",
        "when should recoverai choose stop",
        "why would recoverai choose stop",
        "why does recoverai choose stop",
        "why is stop recommended",
        "why would the system choose stop",
        "when should the system stop",
    )

    if any(
        phrase in lower
        for phrase in stop_phrases
    ):
        return (
            "RecoverAI chooses STOP when automated recovery is no longer "
            "appropriate or safe. Examples include reaching the maximum of "
            "3 recovery attempts, encountering a non-retryable failure, or "
            "a policy rule blocking further automation. STOP protects the "
            "customer and merchant from unnecessary repeated actions."
        )

    # -----------------------------------------------------
    # POLICY OVERRIDE / UNSAFE ACTIONS
    # -----------------------------------------------------

    override_phrases = (
        "can you override the recovery policy",
        "can recoverai override the recovery policy",
        "can we override the recovery policy",
        "can i override the recovery policy",
        "can you bypass the recovery policy",
        "can recoverai bypass policy",
        "can we bypass policy",
        "can you perform an unsafe recovery action",
        "can recoverai perform an unsafe recovery action",
        "can you ignore the recovery policy",
        "can we ignore the recovery policy",
    )

    if any(
        phrase in lower
        for phrase in override_phrases
    ):
        return (
            "No. RecoverAI's AI layer recommends an action, but it does not "
            "override the recovery policy. The policy engine independently "
            "authorizes or blocks the requested action based on safety rules, "
            "including retry limits and non-retryable failure conditions. "
            "In RecoverAI: AI recommends. Policy authorizes."
        )

    # -----------------------------------------------------
    # GENERAL RETRY SAFETY
    # -----------------------------------------------------

    retry_safety_phrases = (
        "should we retry every failed payment",
        "should we retry all failed payments",
        "why shouldn't we retry every failed payment",
        "why shouldnt we retry every failed payment",
        "why not retry every failed payment",
        "should recoverai retry every failed payment",
    )

    if any(
        phrase in lower
        for phrase in retry_safety_phrases
    ):
        return (
            "No. RecoverAI is designed to recover the right revenue, not "
            "retry every failed payment. The system evaluates recovery "
            "probability, failure reason, and previous attempts before "
            "recommending an action. Policy controls whether automation is "
            "allowed, including retry limits and non-retryable failure rules."
        )

    return None


# =========================================================
# SIMPLE CALCULATIONS
# =========================================================

def _parse_number(value: str) -> Decimal:
    """
    Parse a user-entered number such as:
    10000
    10,000
    ₹10,000
    10k
    """

    cleaned = (
        value
        .strip()
        .lower()
        .replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .strip()
    )

    multiplier = Decimal("1")

    if cleaned.endswith("k"):
        multiplier = Decimal("1000")
        cleaned = cleaned[:-1]

    elif cleaned.endswith("l"):
        multiplier = Decimal("100000")
        cleaned = cleaned[:-1]

    elif cleaned.endswith("m"):
        multiplier = Decimal("1000000")
        cleaned = cleaned[:-1]

    return Decimal(cleaned) * multiplier


def get_calculation_response(
    message: str,
) -> str | None:
    """
    Handle simple arithmetic questions without interfering
    with RecoverAI's payment-domain intelligence.

    This intentionally supports only clear financial percentage
    questions rather than attempting to become a general-purpose
    calculator.
    """

    lower = (
        message
        .strip()
        .lower()
    )

    # -----------------------------------------------------
    # PROFIT AS A PERCENTAGE OF LOSS
    #
    # Example:
    # "my profit is 10000 and my loss is 9000
    #  find the percentage of a profit"
    #
    # Result:
    # 10000 / 9000 * 100 = 111.11%
    # -----------------------------------------------------

    profit_loss_patterns = [
        r"profit\s*(?:is|=)\s*([\d,₹$€£.]+[kKmMlL]?)"
        r".*?"
        r"loss\s*(?:is|=)\s*([\d,₹$€£.]+[kKmMlL]?)",

        r"profit\s*([\d,₹$€£.]+[kKmMlL]?)"
        r".*?"
        r"loss\s*([\d,₹$€£.]+[kKmMlL]?)",
    ]

    for pattern in profit_loss_patterns:
        match = re.search(
            pattern,
            lower,
        )

        if not match:
            continue

        try:
            profit = _parse_number(
                match.group(1)
            )

            loss = _parse_number(
                match.group(2)
            )

        except (InvalidOperation, ValueError):
            return None

        if loss == 0:
            return (
                "The loss is ₹0, so the profit cannot be expressed "
                "as a percentage of the loss."
            )

        percentage = (
            profit / loss
        ) * Decimal("100")

        return (
            f"Your profit is {profit:,.2f} and your loss is "
            f"{loss:,.2f}. The profit is "
            f"{percentage:.2f}% of the loss."
        )

    return None

def format_amount(
    amount: float,
    currency: str | None = None,
) -> str:
    """
    Format a monetary amount using the currency stored on the payment.

    No currency is invented here.
    """

    currency_code = (
        str(currency).upper()
        if currency
        else ""
    )

    if currency_code == "INR":
        return f"₹{amount:,.2f}"

    if currency_code == "USD":
        return f"${amount:,.2f}"

    if currency_code == "EUR":
        return f"€{amount:,.2f}"

    if currency_code == "GBP":
        return f"£{amount:,.2f}"

    if currency_code:
        return f"{amount:,.2f} {currency_code}"

    return f"{amount:,.2f}"


def get_payment_currency(payment: Any) -> str | None:
    """
    Safely obtain the payment currency.

    This keeps the AI layer compatible with payment models that
    may or may not contain a currency field.
    """

    currency = getattr(
        payment,
        "currency",
        None,
    )

    if currency is None:
        return None

    return str(currency)


def get_greeting_response(
    message: str,
) -> str | None:
    """
    Return a natural conversational response for simple greetings.

    Greetings are handled before intent detection so that messages
    such as "hi", "hello", and "hey" are not incorrectly classified
    as OUT_OF_SCOPE.
    """

    lower = (
        str(message or "")
        .strip()
        .lower()
    )

    greetings = {
        "hi",
        "hello",
        "hey",
        "hiya",
        "howdy",
        "good morning",
        "good afternoon",
        "good evening",
    }

    if lower not in greetings:
        return None

    if lower == "good morning":
        return (
            "Good morning! 👋 I'm your RecoverAI assistant. "
            "I can help you analyze recovered revenue, "
            "failed payments, revenue at risk, and recovery priorities. "
            "What would you like to check?"
        )

    if lower == "good afternoon":
        return (
            "Good afternoon! 👋 I'm your RecoverAI assistant. "
            "I can help you analyze recovered revenue, "
            "failed payments, revenue at risk, and recovery priorities. "
            "What would you like to check?"
        )

    if lower == "good evening":
        return (
            "Good evening! 👋 I'm your RecoverAI assistant. "
            "I can help you analyze recovered revenue, "
            "failed payments, revenue at risk, and recovery priorities. "
            "What would you like to check?"
        )

    return (
        "Hello! 👋 I'm your RecoverAI assistant. "
        "I can help you analyze recovered revenue, "
        "failed payments, revenue at risk, and recovery priorities. "
        "What would you like to check?"
    )


# =========================================================
# CONVERSATION MANAGEMENT
# =========================================================

async def get_or_create_conversation(
    conversation_id: str | None,
    merchant_id: str,
) -> AIConversation:
    """
    Get an existing conversation belonging to the merchant,
    or create a new one.

    A conversation ID belonging to another merchant is rejected
    instead of exposing another merchant's conversation.
    """

    conversation_repo = get_ai_conversation_repository()

    if conversation_id:

        conversation = await conversation_repo.find_one(
            {
                "id": conversation_id,
                "merchant_id": merchant_id,
            }
        )

        if conversation:
            return conversation

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    conversation = AIConversation(
        merchant_id=merchant_id,
    )

    await conversation_repo.insert(
        conversation
    )

    return conversation


async def save_conversation_message(
    conversation: AIConversation,
    role: str,
    content: str,
) -> AIConversation:
    """
    Persist one message in the conversation.
    """

    conversation_repo = (
        get_ai_conversation_repository()
    )

    now = datetime.now(timezone.utc)

    message = AIConversationMessage(
        role=role,
        content=content,
        timestamp=now,
    )

    conversation.messages.append(
        message
    )

    conversation.updated_at = now

    await conversation_repo.update_by_id(
        conversation.id,
        {
            "messages": [
                item.model_dump(
                    mode="python"
                )
                for item in conversation.messages
            ],
            "active_payment_id": (
                conversation.active_payment_id
            ),
            "updated_at": conversation.updated_at,
        },
    )

    return conversation


async def set_active_payment(
    conversation: AIConversation,
    payment_id: str,
) -> AIConversation:
    """
    Persist the payment currently being discussed.
    """

    conversation_repo = (
        get_ai_conversation_repository()
    )

    conversation.active_payment_id = payment_id

    conversation.updated_at = (
        datetime.now(timezone.utc)
    )

    await conversation_repo.update_by_id(
        conversation.id,
        {
            "active_payment_id": (
                conversation.active_payment_id
            ),
            "updated_at": conversation.updated_at,
        },
    )

    return conversation


async def conversation_response(
    conversation: AIConversation,
    response: dict[str, Any],
) -> dict[str, Any]:
    """
    Save assistant response and return conversation metadata.
    """

    reply = str(
        response.get(
            "reply",
            "",
        )
    )

    if reply:
        await save_conversation_message(
            conversation=conversation,
            role="assistant",
            content=reply,
        )

        response["conversation_id"] = conversation.id

    return _camelize(response)


# =========================================================
# CONVERSATION HISTORY
# =========================================================

def history_from_conversation(
    conversation: AIConversation,
) -> list[dict[str, Any]]:
    """
    Convert stored messages to a simple history structure.
    """

    return [
        {
            "role": item.role,
            "content": item.content,
            "timestamp": item.timestamp.isoformat(),
        }
        for item in conversation.messages
    ]


def extract_text_from_history_item(
    item: dict[str, Any],
) -> str:
    """
    Extract message text from different frontend history formats.
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


# =========================================================
# PAYMENT FOLLOW-UP DETECTION
# =========================================================

def is_payment_followup(
    message: str,
) -> bool:
    """
    Determine whether a message refers to the currently
    selected payment.
    """

    lower = (
        str(message or "")
        .strip()
        .lower()
    )

    followup_phrases = (
        "tell me more",
        "more about it",
        "more about this",
        "more details",
        "give me more details",
        "explain it",
        "explain this",
        "explain that",
        "details about it",
        "details about this",
        "what is its amount",
        "what's its amount",
        "what is its value",
        "what's its value",
        "how much is it worth",
        "how much is this worth",
        "how much is that worth",
        "how much was the payment",
        "how much is the payment",
        "what caused it to fail",
        "why did it fail",
        "why is it failing",
        "should i retry it",
        "should i retry this",
        "should we retry it",
        "should we retry this",
        "can i retry it",
        "can i retry this",
        "can we retry it",
        "can we retry this",
        "do i retry it",
        "do we retry it",
        "what is the recovery probability",
        "what's the recovery probability",
        "recovery probability",
    )

    return (
        any(
            phrase in lower
            for phrase in followup_phrases
        )
        or is_payment_context_question(
            message
        )
    )


# =========================================================
# PAYMENT CONTEXT
# =========================================================

def find_payment_id(
    message: str,
    history: list[dict[str, Any]],
    payments: list[Any],
    active_payment_id: str | None = None,
) -> str | None:
    """
    Find the relevant payment.

    Priority:

    1. Payment ID explicitly mentioned in current message.
    2. Active payment in current conversation.
    3. Payment mentioned earlier in conversation history.
    """

    text = (
        str(message or "")
        .lower()
    )

    # -----------------------------------------------------
    # 1. CURRENT MESSAGE
    # -----------------------------------------------------

    for payment in payments:

        payment_id = str(
            payment.id
        )

        if (
            payment_id.lower()
            in text
        ):
            return payment_id

    # -----------------------------------------------------
    # 2. ACTIVE CONVERSATION PAYMENT
    # -----------------------------------------------------

    if (
        active_payment_id
        and is_payment_followup(message)
    ):

        for payment in payments:

            if (
                str(payment.id)
                == str(active_payment_id)
            ):
                return str(
                    active_payment_id
                )

    # -----------------------------------------------------
    # 3. PREVIOUS CONVERSATION HISTORY
    # -----------------------------------------------------

    if is_payment_followup(message):

        for item in reversed(history):

            content = (
                extract_text_from_history_item(
                    item
                )
                .lower()
            )

            if not content:
                continue

            for payment in payments:

                payment_id = str(
                    payment.id
                )

                if (
                    payment_id.lower()
                    in content
                ):
                    return payment_id

    return None


# =========================================================
# FRUSTRATION RESPONSE
# =========================================================

def get_frustration_response(
    message: str,
) -> str:

    lower = (
        message
        .strip()
        .lower()
    )

    if (
        "failing" in lower
        or "fail" in lower
    ):
        return (
            "I understand this is frustrating. "
            "RecoverAI can identify why payments are failing, "
            "estimate recovery probability, and recommend "
            "the next recovery action."
        )

    if (
        "angry" in lower
        or "upset" in lower
    ):
        return (
            "I understand you're upset. "
            "Let's work through the payment recovery issue "
            "step by step. RecoverAI can analyze failed "
            "payments, recovery probability, and recommended "
            "recovery actions."
        )

    return (
        "I understand this can be frustrating. "
        "Let's take it step by step. RecoverAI can analyze "
        "failed payments, recovery probability, revenue at "
        "risk, and recommended recovery actions."
    )


# =========================================================
# PAYMENT ANALYSIS
# =========================================================

async def analyze_payment(
    payment: Any,
    attempts: list[Any],
) -> dict[str, Any]:
    """
    Run the complete recovery analysis pipeline.
    """

    payment_attempts = [
        attempt
        for attempt in attempts
        if str(
            attempt.payment_id
        )
        == str(
            payment.id
        )
    ]

    previous_attempts = len(
        payment_attempts
    )

    failed_attempts = sum(
        1
        for attempt in payment_attempts
        if get_enum_value(
            attempt.status
        ).lower()
        == "failed"
    )

    payment_data = payment.model_dump(
        mode="python"
    )

    payment_data[
        "previous_attempts"
    ] = previous_attempts

    payment_data[
        "failed_attempts"
    ] = failed_attempts

    # -----------------------------------------------------
    # ML
    # -----------------------------------------------------

    probability = (
        predict_recovery_probability(
            payment_data
        )
    )

    # -----------------------------------------------------
    # DECISION ENGINE
    # -----------------------------------------------------

    action = choose_recovery_action(
        probability=probability,
        failure_reason=(
            payment.failure_reason
        ),
        attempts=previous_attempts,
    )

    # -----------------------------------------------------
    # AI REASONING
    # -----------------------------------------------------

    reasoning = (
        analyze_recovery_decision(
            payment=payment_data,
            probability=probability,
            recommended_action=(
                get_enum_value(action)
            ),
        )
    )

    return {
        "payment": payment,
        "probability": probability,
        "action": action,
        "reasoning": reasoning,
        "previous_attempts": (
            previous_attempts
        ),
        "failed_attempts": (
            failed_attempts
        ),
    }


# =========================================================
# STATUS HELPERS
# =========================================================

def get_payment_status(
    payment: Any,
) -> str:

    return get_enum_value(
        payment.status
    ).lower()


def get_attempt_status(
    attempt: Any,
) -> str:

    return get_enum_value(
        attempt.status
    ).lower()


# =========================================================
# RESPONSE CAMELIZATION
# =========================================================

def _camelize_key(key: str) -> str:
    parts = key.split("_")

    return parts[0] + "".join(
        part[:1].upper() + part[1:]
        for part in parts[1:]
    )


def _camelize(value):
    if isinstance(value, dict):
        return {
            _camelize_key(str(key)): _camelize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _camelize(item)
            for item in value
        ]

    return value


# =========================================================
# MAIN AI ENDPOINT
# =========================================================

@router.post(
    "/message",
    response_model=AIResponseDTO,
    response_model_by_alias=True,
)
async def ai_message(
    request: AIMessageRequest,
    current_merchant: CurrentMerchant,
):
    """
    Main RecoverAI assistant endpoint.

    The merchant is taken from the authenticated JWT.

    All payment/analytics values are calculated from
    MongoDB data rather than hardcoded.
    """

    merchant_id = str(
        current_merchant.id
    )

    message = (
        request.message
        .strip()
    )

    # =====================================================
    # EMPTY MESSAGE
    # =====================================================

    if not message:

        return {
            "type": "general",
            "reply": "Please enter a question.",
        }

    # =====================================================
    # CONVERSATION
    # =====================================================

    conversation = (
        await get_or_create_conversation(
            conversation_id=(
                request.conversation_id
            ),
            merchant_id=merchant_id,
        )
    )

    # =====================================================
    # SAVE USER MESSAGE
    # =====================================================

    await save_conversation_message(
        conversation=conversation,
        role="user",
        content=message,
    )

    # =====================================================
    # HISTORY
    # =====================================================

    conversation_history = (
        history_from_conversation(
            conversation
        )
    )

    lower = message.lower()

    # =====================================================
    # NATURAL GREETINGS
    # =====================================================

    greeting_response = get_greeting_response(
        message
    )

    if greeting_response:

        return await conversation_response(
            conversation,
            {
                "type": "general",
                "reply": greeting_response,
            },
        )
    # =====================================================
    # BASIC CONVERSATION
    # =====================================================

    basic_response = get_basic_conversation_response(
        message
    )

    if basic_response:
        return await conversation_response(
            conversation,
            {
                "type": "general",
                "reply": basic_response,
            },
        )


    # =====================================================
    # RECOVERY STRATEGY / POLICY QUESTIONS
    # =====================================================

    strategy_policy_response = get_strategy_policy_response(
        message
    )

    if strategy_policy_response:
        return await conversation_response(
            conversation,
            {
                "type": "general",
                "reply": strategy_policy_response,
            },
        )

    # =====================================================
    # SIMPLE CALCULATIONS
    # =====================================================

    calculation_response = get_calculation_response(
        message
    )

    if calculation_response:
        return await conversation_response(
            conversation,
            {
                "type": "calculation",
                "reply": calculation_response,
            },
        )


    # =====================================================
    # INTENT
    # =====================================================

    intent = detect_intent(
        message
    )

    # =====================================================
    # OUT OF SCOPE
    # =====================================================

    if intent == Intent.OUT_OF_SCOPE:

        return await conversation_response(
            conversation,
            {
                "type": "out_of_scope",
                "reply": (
                    "I understand. I'm here specifically "
                    "to help with RecoverAI and payment recovery. "
                    "I can help with failed payments, recovery "
                    "probability, revenue at risk, recovery "
                    "attempts, payment prioritization, and "
                    "recommended recovery actions."
                ),
            },
        )

    # =====================================================
    # GENERAL RECOVERAI QUESTIONS
    # =====================================================

    if intent == Intent.GENERAL_RECOVERAI:

        if (
            "what can you help me with"
            in lower
            or "what can you help with"
            in lower
        ):

            return await conversation_response(
                conversation,
                {
                    "type": "general",
                    "reply": (
                        "I can help you analyze failed payments, "
                        "predict recovery probability, decide "
                        "whether a payment should be retried, "
                        "identify failure patterns, prioritize "
                        "payments for recovery, and track "
                        "recovered revenue, revenue at risk, "
                        "recovery attempts, and recovery rate."
                    ),
                },
            )

        if (
            "what does recoverai do"
            in lower
            or "what is recoverai"
            in lower
            or "what's recoverai"
            in lower
        ):

            return await conversation_response(
                conversation,
                {
                    "type": "general",
                    "reply": (
                        "RecoverAI is an intelligent payment "
                        "recovery system. It analyzes failed "
                        "payments, predicts recovery probability, "
                        "and recommends recovery actions such as "
                        "SMART_RETRY, PAYMENT_METHOD_SUGGESTION, "
                        "REMINDER, SUPPORT_ESCALATION, or STOP."
                    ),
                },
            )

        if (
            "how does payment recovery work"
            in lower
        ):

            return await conversation_response(
                conversation,
                {
                    "type": "general",
                    "reply": (
                        "RecoverAI analyzes payment information "
                        "such as the transaction amount, payment "
                        "method, failure reason, and previous "
                        "recovery attempts. The ML model predicts "
                        "the probability of successful recovery. "
                        "The decision engine then recommends an "
                        "appropriate recovery action."
                    ),
                },
            )

        if (
            "how do you decide whether to retry"
            in lower
            or "how do you decide to retry"
            in lower
            or "how do you decide whether a payment should be retried"
            in lower
            or "how do you decide whether to retry a payment"
            in lower
        ):

            return await conversation_response(
                conversation,
                {
                    "type": "general",
                    "reply": (
                        "RecoverAI considers the predicted "
                        "recovery probability, payment failure "
                        "reason, and previous recovery attempts. "
                        "The decision engine uses these factors "
                        "to select the appropriate recovery action."
                    ),
                },
            )

    # =====================================================
    # LOAD MERCHANT PAYMENT DATA
    # =====================================================

    payment_repo = (
        get_payment_repository()
    )

    attempt_repo = (
        get_payment_attempt_repository()
    )

    payments = await payment_repo.find_many(
        filter_query={
            "merchant_id": merchant_id,
        },
        limit=1000,
    )

    # Payment attempts are linked to payments rather than
    # directly to merchants, so retrieve the attempts for
    # the merchant's payments only.

    merchant_payment_ids = {
        str(payment.id)
        for payment in payments
    }

    all_attempts = (
        await attempt_repo.find_many(
            limit=1000
        )
    )

    attempts = [
        attempt
        for attempt in all_attempts
        if str(
            attempt.payment_id
        )
        in merchant_payment_ids
    ]

    # =====================================================
    # FIND PAYMENT CONTEXT
    # =====================================================

    payment_id = find_payment_id(
        message=message,
        history=conversation_history,
        payments=payments,
        active_payment_id=(
            conversation.active_payment_id
        ),
    )

    selected_payment = None

    if payment_id:

        selected_payment = next(
            (
                payment
                for payment in payments
                if str(payment.id)
                == str(payment_id)
            ),
            None,
        )

    # =====================================================
    # SAVE ACTIVE PAYMENT
    # =====================================================

    if selected_payment:

        await set_active_payment(
            conversation=conversation,
            payment_id=str(
                selected_payment.id
            ),
        )

    # =====================================================
    # FRUSTRATION
    # =====================================================

    if (
        intent == Intent.FRUSTRATION
        and selected_payment is None
    ):

        return await conversation_response(
            conversation,
            {
                "type": "support",
                "reply": (
                    get_frustration_response(
                        message
                    )
                ),
            },
        )

    # =====================================================
    # PAYMENT-SPECIFIC QUESTIONS
    # =====================================================

    if selected_payment:

        # -------------------------------------------------
        # FAILURE REASON
        # -------------------------------------------------

        if (
            "failure reason" in lower
            or "why did it fail" in lower
            or "why is it failing" in lower
            or "what caused it to fail" in lower
        ):

            failure_reason = (
                selected_payment.failure_reason
                or "No failure reason was recorded."
            )

            return await conversation_response(
                conversation,
                {
                    "type": "payment_analysis",
                    "payment_id": (
                        selected_payment.id
                    ),
                    "reply": (
                        f"The failure reason for payment "
                        f"{selected_payment.id} is "
                        f"{failure_reason}."
                    ),
                },
            )

        # -------------------------------------------------
        # PAYMENT AMOUNT
        # -------------------------------------------------

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
            or "what is it worth" in lower
            or "what's it worth" in lower
        ):

            currency = (
                get_payment_currency(
                    selected_payment
                )
            )

            amount = format_amount(
                selected_payment.amount,
                currency,
            )

            return await conversation_response(
                conversation,
                {
                    "type": "payment_analysis",
                    "payment_id": (
                        selected_payment.id
                    ),
                    "reply": (
                        f"Payment "
                        f"{selected_payment.id} "
                        f"is worth {amount}."
                    ),
                    "amount": (
                        selected_payment.amount
                    ),
                    "currency": currency,
                },
            )

        # -------------------------------------------------
        # TELL ME MORE
        # -------------------------------------------------

        if (
            "tell me more" in lower
            or "more about" in lower
            or "more details" in lower
            or "give me more details" in lower
            or "explain it" in lower
            or "explain this" in lower
            or "explain that" in lower
            or "details about it" in lower
            or "details about this" in lower
        ):

            result = await analyze_payment(
                selected_payment,
                attempts,
            )

            reasoning = result[
                "reasoning"
            ]

            return await conversation_response(
                conversation,
                {
                    "type": "payment_analysis",
                    "payment_id": (
                        selected_payment.id
                    ),
                    "reply": reasoning[
                        "reasoning"
                    ],
                    "analysis": {
                        **reasoning,
                        "previous_attempts": (
                            result[
                                "previous_attempts"
                            ]
                        ),
                        "failed_attempts": (
                            result[
                                "failed_attempts"
                            ]
                        ),
                    },
                },
            )

    # =====================================================
    # 1. PRIORITIZATION
    # =====================================================

    if intent == Intent.PRIORITIZATION:

        candidates = []

        for payment in payments:

            status = get_payment_status(
                payment
            )

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

            result["priority_score"] = (
                payment.amount
                * result["probability"]
            )

            candidates.append(
                result
            )

        candidates.sort(
            key=lambda item: item[
                "priority_score"
            ],
            reverse=True,
        )

        if not candidates:

            return await conversation_response(
                conversation,
                {
                    "type": "priority",
                    "reply": (
                        "There are currently no "
                        "unrecovered payments that "
                        "require prioritization."
                    ),
                    "payments": [],
                },
            )

        top = candidates[:5]

        priority_list = []

        for index, item in enumerate(
            top,
            start=1,
        ):

            payment = item[
                "payment"
            ]

            priority_list.append(
                {
                    "rank": index,
                    "payment_id": (
                        payment.id
                    ),
                    "amount": (
                        payment.amount
                    ),
                    "currency": (
                        get_payment_currency(
                            payment
                        )
                    ),
                    "recovery_probability": (
                        item["probability"]
                    ),
                    "priority_score": round(
                        item[
                            "priority_score"
                        ],
                        2,
                    ),
                    "recommended_action": (
                        get_enum_value(
                            item["action"]
                        )
                    ),
                }
            )

        first = top[0]

        first_payment = first[
            "payment"
        ]

        amount = format_amount(
            first_payment.amount,
            get_payment_currency(
                first_payment
            ),
        )

        action = get_enum_value(
            first["action"]
        )

        reply = (
            f"The highest-priority payment is "
            f"{first_payment.id}. It has "
            f"{first['probability'] * 100:.2f}% "
            f"predicted recovery probability and "
            f"{amount} at stake. RecoverAI "
            f"recommends {action}."
        )

        return await conversation_response(
            conversation,
            {
                "type": "priority",
                "reply": reply,
                "payments": priority_list,
            },
        )

    # =====================================================
    # 2. RECOVERED REVENUE
    # =====================================================

    if intent == Intent.RECOVERED_REVENUE:

        recovered_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            )
            in (
                "recovered",
                "successful",
                "success",
            )
        ]

        recovered = sum(
            payment.amount
            for payment in recovered_payments
        )

        currency = (
            get_payment_currency(
                recovered_payments[0]
            )
            if recovered_payments
            else None
        )

        return await conversation_response(
            conversation,
            {
                "type": "analytics",
                "reply": (
                    f"RecoverAI has recovered "
                    f"{format_amount(recovered, currency)} "
                    f"of revenue."
                ),
                "revenue_recovered": recovered,
                "currency": currency,
            },
        )

    # =====================================================
    # 3. REVENUE AT RISK
    # =====================================================

    if intent == Intent.REVENUE_AT_RISK:

        at_risk_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            )
            in (
                "failed",
                "at_risk",
                "recovering",
            )
        ]

        at_risk = sum(
            payment.amount
            for payment in at_risk_payments
        )

        currency = (
            get_payment_currency(
                at_risk_payments[0]
            )
            if at_risk_payments
            else None
        )

        return await conversation_response(
            conversation,
            {
                "type": "analytics",
                "reply": (
                    f"Revenue currently at risk is "
                    f"{format_amount(at_risk, currency)}."
                ),
                "revenue_at_risk": at_risk,
                "currency": currency,
            },
        )

    # =====================================================
    # 4. RECOVERY RATE
    # =====================================================

    if intent == Intent.RECOVERY_RATE:

        successful_attempts = sum(
            1
            for attempt in attempts
            if get_attempt_status(
                attempt
            ) == "success"
        )

        recovery_rate = (
            successful_attempts
            / len(attempts)
            * 100
            if attempts
            else 0
        )

        return await conversation_response(
            conversation,
            {
                "type": "analytics",
                "reply": (
                    f"The current recovery rate is "
                    f"{recovery_rate:.2f}%."
                ),
                "recovery_rate": (
                    recovery_rate
                ),
                "successful_attempts": (
                    successful_attempts
                ),
                "total_attempts": (
                    len(attempts)
                ),
            },
        )

    # =====================================================
    # 5. ATTEMPT ANALYSIS
    # =====================================================

    if intent == Intent.ATTEMPT_ANALYSIS:

        successful = sum(
            1
            for attempt in attempts
            if get_attempt_status(
                attempt
            ) == "success"
        )

        failed = sum(
            1
            for attempt in attempts
            if get_attempt_status(
                attempt
            ) == "failed"
        )

        return await conversation_response(
            conversation,
            {
                "type": "analytics",
                "reply": (
                    f"There have been "
                    f"{len(attempts)} recovery attempts. "
                    f"{successful} succeeded and "
                    f"{failed} failed."
                ),
                "total_attempts": (
                    len(attempts)
                ),
                "successful_attempts": (
                    successful
                ),
                "failed_attempts": failed,
            },
        )

    # =====================================================
    # 6. FAILURE ANALYSIS
    # =====================================================

    failure_analysis_question = (
        intent == Intent.FAILURE_ANALYSIS
        or "most common failure reason" in lower
        or "most common failure" in lower
        or "which failure reason happens most often" in lower
        or "which failure happens most often" in lower
        or "what causes the most payment failures" in lower
        or "what are our top failure reasons" in lower
        or "which failure reason is most frequent" in lower
        or "which failure reason should we focus on" in lower
        or "which failure is happening most often" in lower
        or "biggest causes of payment failures" in lower
        or "which failure reason affects the most payments" in lower
        or "which failure reason is costing us the most revenue" in lower
        or "which failure is costing us the most revenue" in lower
    )

    if failure_analysis_question:

        failed_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            ) == "failed"
        ]

        if not failed_payments:

            return await conversation_response(
                conversation,
                {
                    "type": "failure_analysis",
                    "reply": (
                        "There are currently no failed "
                        "payments to analyze."
                    ),
                    "failure_reasons": [],
                },
            )

        failure_reasons: dict[
            str,
            int,
        ] = {}

        for payment in failed_payments:

            reason = (
                payment.failure_reason
                or "Unknown failure reason"
            )

            failure_reasons[
                reason
            ] = (
                failure_reasons.get(
                    reason,
                    0,
                )
                + 1
            )

        sorted_reasons = sorted(
            failure_reasons.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        reason_text = ", ".join(
            f"{reason} ({count})"
            for reason, count
            in sorted_reasons
        )

        asks_most_common = (
            "most common" in lower
            or "happens most often" in lower
            or "most frequent" in lower
            or "happening most often" in lower
            or "most payments" in lower
        )

        if asks_most_common and sorted_reasons:
            top_reason, top_count = sorted_reasons[0]
            reply = (
                f"{top_reason} is currently the most common failure reason, "
                f"with {top_count} failed payment"
                f"{"s" if top_count != 1 else ""}. "
                f"Across all failed payments, the recorded failure reasons are: "
                f"{reason_text}."
            )
        else:
            reply = (
                f"There are currently {len(failed_payments)} "
                f"failed payments. The recorded failure reasons are: "
                f"{reason_text}."
            )

        return await conversation_response(
            conversation,
            {
                "type": "failure_analysis",
                "reply": reply,
                "failure_reasons": [
                    {
                        "reason": reason,
                        "count": count,
                    }
                    for reason, count
                    in sorted_reasons
                ],
            },
        )

    # =====================================================
    # 7. TOTAL PAYMENTS
    # =====================================================

    if (
        "total payments" in lower
        or "how many payments" in lower
        or "number of payments" in lower
        or "total transactions" in lower
    ):

        return await conversation_response(
            conversation,
            {
                "type": "analytics",
                "reply": (
                    f"RecoverAI currently has "
                    f"{len(payments)} payments."
                ),
                "total_payments": len(
                    payments
                ),
            },
        )

    # =====================================================
    # 8. RECOVERY PROBABILITY
    # =====================================================

    if intent == Intent.RECOVERY_PROBABILITY:

        if not selected_payment:

            return await conversation_response(
                conversation,
                {
                    "type": "recovery_probability",
                    "reply": (
                        "I can calculate the predicted "
                        "recovery probability. Please provide "
                        "the payment ID you'd like me to analyze."
                    ),
                },
            )

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        probability = result[
            "probability"
        ]

        return await conversation_response(
            conversation,
            {
                "type": "recovery_probability",
                "payment_id": (
                    selected_payment.id
                ),
                "reply": (
                    f"RecoverAI predicts a "
                    f"{probability * 100:.2f}% chance "
                    f"of recovering payment "
                    f"{selected_payment.id}."
                ),
                "analysis": {
                    "probability": probability,
                    "recommended_action": (
                        get_enum_value(
                            result["action"]
                        )
                    ),
                    "previous_attempts": (
                        result[
                            "previous_attempts"
                        ]
                    ),
                    "failed_attempts": (
                        result[
                            "failed_attempts"
                        ]
                    ),
                },
            },
        )

    # =====================================================
    # 9. RETRY DECISION
    # =====================================================

    if intent == Intent.RETRY_DECISION:

        if not selected_payment:

            return await conversation_response(
                conversation,
                {
                    "type": "retry_decision",
                    "reply": (
                        "I can determine whether a retry "
                        "is recommended. Please provide the "
                        "payment ID you'd like me to analyze."
                    ),
                },
            )

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        action = result[
            "action"
        ]

        return await conversation_response(
            conversation,
            {
                "type": "retry_decision",
                "payment_id": (
                    selected_payment.id
                ),
                "reply": (
                    f"For payment "
                    f"{selected_payment.id}, "
                    f"RecoverAI recommends: "
                    f"{get_enum_value(action)}."
                ),
                "analysis": {
                    "probability": (
                        result["probability"]
                    ),
                    "recommended_action": (
                        get_enum_value(action)
                    ),
                    "previous_attempts": (
                        result[
                            "previous_attempts"
                        ]
                    ),
                    "failed_attempts": (
                        result[
                            "failed_attempts"
                        ]
                    ),
                    "reasoning": (
                        result["reasoning"]
                    ),
                },
            },
        )

    # =====================================================
    # 10. PAYMENT ANALYSIS
    # =====================================================

    if (
        selected_payment
        and intent
        == Intent.PAYMENT_ANALYSIS
    ):

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        reasoning = result[
            "reasoning"
        ]

        return await conversation_response(
            conversation,
            {
                "type": "payment_analysis",
                "payment_id": (
                    selected_payment.id
                ),
                "reply": reasoning[
                    "reasoning"
                ],
                "analysis": {
                    **reasoning,
                    "previous_attempts": (
                        result[
                            "previous_attempts"
                        ]
                    ),
                    "failed_attempts": (
                        result[
                            "failed_attempts"
                        ]
                    ),
                },
            },
        )

    # =====================================================
    # 11. PAYMENT-SPECIFIC FALLBACK
    # =====================================================

    if selected_payment:

        result = await analyze_payment(
            selected_payment,
            attempts,
        )

        reasoning = result[
            "reasoning"
        ]

        return await conversation_response(
            conversation,
            {
                "type": "payment_analysis",
                "payment_id": (
                    selected_payment.id
                ),
                "reply": reasoning[
                    "reasoning"
                ],
                "analysis": {
                    **reasoning,
                    "previous_attempts": (
                        result[
                            "previous_attempts"
                        ]
                    ),
                    "failed_attempts": (
                        result[
                            "failed_attempts"
                        ]
                    ),
                },
            },
        )

    # =====================================================
    # 12. GENERAL FALLBACK
    # =====================================================

    return await conversation_response(
        conversation,
        {
            "type": "general",
            "reply": (
                f"I analyzed {len(payments)} "
                f"payments and {len(attempts)} "
                "recovery attempts. You can ask me "
                "about a specific payment, why payments "
                "are failing, recovery probability, "
                "recommended actions, payment "
                "prioritization, high-value payments "
                "at risk, recovered revenue, revenue "
                "at risk, recovery attempts, or "
                "recovery rate."
            ),
        },
    )