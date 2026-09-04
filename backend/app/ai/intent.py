import re
from enum import Enum


class Intent(str, Enum):
    PAYMENT_ANALYSIS = "payment_analysis"
    RECOVERY_PROBABILITY = "recovery_probability"
    RETRY_DECISION = "retry_decision"
    PRIORITIZATION = "prioritization"
    FAILURE_ANALYSIS = "failure_analysis"
    RECOVERED_REVENUE = "recovered_revenue"
    REVENUE_AT_RISK = "revenue_at_risk"
    RECOVERY_RATE = "recovery_rate"
    ATTEMPT_ANALYSIS = "attempt_analysis"
    GENERAL_RECOVERAI = "general_recoverai"
    FRUSTRATION = "frustration"
    OUT_OF_SCOPE = "out_of_scope"


def normalize_text(message: str) -> str:
    """
    Normalize user input so intent detection is more reliable.
    """
    text = str(message or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def detect_frustration(message: str) -> bool:
    """
    Detect emotional or frustrated language.
    """

    text = normalize_text(message)

    frustration_phrases = [
        "frustrated",
        "frustrating",
        "angry",
        "upset",
        "stressed",
        "stress",
        "worried",
        "annoyed",
        "annoying",
        "fed up",
        "nothing works",
        "everything is failing",
        "not working",
        "this isn't working",
        "this is not working",
        "terrible",
        "hopeless",
    ]

    return any(phrase in text for phrase in frustration_phrases)


def contains_payment_id(message: str) -> bool:
    """
    Detect common RecoverAI payment IDs.

    Examples:
        DEMO_FAILED_HIGH
        DEMO_FAILED_LOW
        DEMO_PAYMENT_1
        PAY_123
        PAYMENT_001
    """

    text = str(message or "").upper()

    patterns = [
        r"\bDEMO_[A-Z0-9_-]+\b",
        r"\bPAY_[A-Z0-9_-]+\b",
        r"\bPAYMENT_[A-Z0-9_-]+\b",
        r"\bPAYMENT[0-9]+\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def is_payment_context_question(message: str) -> bool:
    """
    Detect questions that can refer to the payment discussed previously.

    These questions intentionally do NOT require the user to repeat
    the payment ID.
    """

    text = normalize_text(message)

    context_phrases = [
        # Pronoun/context references
        "tell me more",
        "tell me more about it",
        "tell me more about this",
        "tell me more about that",
        "more about it",
        "more about this",
        "more about that",
        "explain it",
        "explain this",
        "explain that",
        "give me more details",
        "more details",
        "details about it",
        "details about this",
        "details about that",

        # Direct references
        "this payment",
        "that payment",
        "this transaction",
        "that transaction",

        # Retry
        "should i retry it",
        "should we retry it",
        "should i retry this",
        "should we retry this",
        "should i retry that",
        "should we retry that",
        "can i retry it",
        "can we retry it",
        "can i retry this",
        "can we retry this",
        "is it safe to retry",
        "is this safe to retry",
        "is that safe to retry",
        "is it safe",
        "should it be retried",
        "should this be retried",

        # Failure reason
        "what is its failure reason",
        "what's its failure reason",
        "what is the failure reason",
        "what's the failure reason",
        "what caused it to fail",
        "why did it fail",
        "why is it failing",
        "why has it failed",

        # Amount / value
        "how much is it worth",
        "how much is this worth",
        "how much is that worth",
        "what is its value",
        "what's its value",
        "what is its amount",
        "what's its amount",
        "what is the amount",
        "what's the amount",
        "how much was the payment",
        "how much is the payment",
        "what was the payment amount",

        # Probability
        "what is its recovery probability",
        "what's its recovery probability",
        "what is the recovery probability",
        "what's the recovery probability",
        "how likely is it",
        "what are its chances",
        "what is its recovery chance",
        "what's its recovery chance",

        # Recommended action
        "what should i do",
        "what should we do",
        "what should i do now",
        "what should we do now",
        "what do i do",
        "what do we do",
        "what do i do now",
        "what do we do now",
        "what next",
        "what should happen next",
        "next step",
        "what should i do with it",
        "what should we do with it",

        # Analyze
        "analyze it",
        "analyse it",
        "analyze this",
        "analyse this",
        "analyze that",
        "analyse that",
    ]

    return any(phrase in text for phrase in context_phrases)


def is_general_recoverai_question(message: str) -> bool:
    """
    Questions about RecoverAI itself rather than a specific payment.
    """

    text = normalize_text(message)

    phrases = [
        "what can you help me with",
        "what can you help with",
        "what does recoverai do",
        "what is recoverai",
        "what's recoverai",
        "how does recoverai work",
        "how does payment recovery work",
        "how do you decide whether to retry",
        "how do you decide to retry",
        "how do you decide whether a payment should be retried",
        "how do you decide whether to retry a payment",
    ]

    return any(phrase in text for phrase in phrases)


def is_failure_analysis_question(message: str) -> bool:
    """
    Detect GLOBAL failure-analysis questions.

    Important:
    Payment-specific questions such as
    'What is its failure reason?'
    are handled separately by detect_intent().
    """

    text = normalize_text(message)

    phrases = [
        "why are payments failing",
        "why do payments fail",
        "why are my payments failing",
        "why did payments fail",
        "why are payment failures happening",
        "failure reasons",
        "main failure reasons",
        "payment failures",
        "payments keep failing",
        "failure pattern",
        "failure patterns",
        "failure analysis",
        "what are the failure reasons",
        "what are the main failure reasons",
        "why are so many payments failing",
        "why do my payments keep failing",
    ]

    return any(phrase in text for phrase in phrases)


def is_retry_question(message: str) -> bool:
    """
    Detect retry/recovery-action questions.
    """

    text = normalize_text(message)

    phrases = [
        "should i retry",
        "should we retry",
        "should i try again",
        "should we try again",
        "retry it",
        "retry this",
        "retry that",
        "can i retry",
        "can we retry",
        "try again",
        "is it safe to retry",
        "is this safe to retry",
        "is that safe to retry",
        "should it be retried",
    ]

    return any(phrase in text for phrase in phrases)


def is_probability_question(message: str) -> bool:
    """
    Detect recovery-probability questions.
    """

    text = normalize_text(message)

    phrases = [
        "recovery probability",
        "probability of recovery",
        "chance of recovery",
        "likelihood of recovery",
        "likely to recover",
        "recovery chance",
        "how likely",
        "chance of recovering",
        "what are the chances",
    ]

    return any(phrase in text for phrase in phrases)


def is_prioritization_question(message: str) -> bool:
    """
    Detect payment prioritization questions.
    """

    text = normalize_text(message)

    phrases = [
        "prioritize",
        "priority",
        "which payment",
        "which payments",
        "recover first",
        "what should we recover first",
        "which payment should we recover",
        "which payments should we recover",
        "high-value payments",
        "high value payments",
        "highest priority",
        "highest-priority",
    ]

    return any(phrase in text for phrase in phrases)


def is_recovered_revenue_question(message: str) -> bool:
    """
    Detect recovered-revenue questions.
    """

    text = normalize_text(message)

    phrases = [
        "recovered revenue",
        "revenue recovered",
        "how much did we recover",
        "how much revenue did we recover",
        "how much have we recovered",
        "how much money did we recover",
        "total recovered",
        "revenue we recovered",
    ]

    return any(phrase in text for phrase in phrases)


def is_revenue_at_risk_question(message: str) -> bool:
    """
    Detect revenue-at-risk questions.
    """

    text = normalize_text(message)

    phrases = [
        "revenue at risk",
        "how much revenue is at risk",
        "how much money is at risk",
        "how much is at risk",
        "payments at risk",
        "payment at risk",
        "at risk",
        "high-value payments at risk",
        "high value payments at risk",
        "money at risk",
        "what money is currently at risk",
        "what money is at risk",
    ]

    return any(phrase in text for phrase in phrases)


def is_recovery_rate_question(message: str) -> bool:
    """
    Detect recovery-rate questions.
    """

    text = normalize_text(message)

    phrases = [
        "recovery rate",
        "recoveryrate",
        "what percentage recovered",
        "percentage recovered",
        "what percentage did we recover",
        "what is our recovery percentage",
    ]

    return any(phrase in text for phrase in phrases)


def is_attempt_analysis_question(message: str) -> bool:
    """
    Detect recovery-attempt questions.
    """

    text = normalize_text(message)

    phrases = [
        "attempt",
        "attempts",
        "retry history",
        "how many retries",
        "retry attempts",
        "recovery history",
        "how many recovery attempts",
        "number of recovery attempts",
    ]

    return any(phrase in text for phrase in phrases)


def is_total_payments_question(message: str) -> bool:
    """
    Detect total-payment count questions.
    """

    text = normalize_text(message)

    phrases = [
        "total payments",
        "how many payments",
        "number of payments",
        "how many transactions",
        "total transactions",
    ]

    return any(phrase in text for phrase in phrases)


def detect_intent(message: str) -> Intent:
    """
    Detect the user's RecoverAI intent.

    Priority is important.

    Specific conversational/payment questions are checked before
    global analytics questions so that:

        "What is its failure reason?"

    is NOT interpreted as:

        "Why are all payments failing?"

    and:

        "Tell me more about it"

    can be handled as a payment-specific follow-up when history
    contains a payment ID.
    """

    text = normalize_text(message)

    if not text:
        return Intent.OUT_OF_SCOPE

    # ---------------------------------------------------------
    # GENERAL RECOVERAI QUESTIONS
    # ---------------------------------------------------------

    if is_general_recoverai_question(text):
        return Intent.GENERAL_RECOVERAI

    # ---------------------------------------------------------
    # SPECIFIC PAYMENT-CONTEXT QUESTIONS
    # ---------------------------------------------------------
    #
    # These are deliberately checked before global failure analysis.
    #

    if is_payment_context_question(text):

        # Specific failure reason
        if (
            "failure reason" in text
            or "why did it fail" in text
            or "why is it failing" in text
            or "what caused it to fail" in text
        ):
            return Intent.PAYMENT_ANALYSIS

        # Specific amount
        if (
            "how much is it worth" in text
            or "how much is this worth" in text
            or "how much is that worth" in text
            or "what is its value" in text
            or "what's its value" in text
            or "what is its amount" in text
            or "what's its amount" in text
            or "what is the amount" in text
            or "what's the amount" in text
            or "how much was the payment" in text
            or "how much is the payment" in text
        ):
            return Intent.PAYMENT_ANALYSIS

        # Specific probability
        if is_probability_question(text):
            return Intent.RECOVERY_PROBABILITY

        # Specific retry decision
        if is_retry_question(text):
            return Intent.RETRY_DECISION

        # Generic follow-up / tell me more
        return Intent.PAYMENT_ANALYSIS

    # ---------------------------------------------------------
    # OUT OF SCOPE
    # ---------------------------------------------------------

    recoverai_related = (
        contains_payment_id(text)
        or any(
            keyword in text
            for keyword in [
                "payment",
                "payments",
                "recovery",
                "recoverai",
                "retry",
                "transaction",
                "revenue",
                "failure",
                "failed",
                "attempt",
            ]
        )
    )

    if not recoverai_related:
        return Intent.OUT_OF_SCOPE

    # ---------------------------------------------------------
    # FRUSTRATION
    # ---------------------------------------------------------

    if detect_frustration(text):
        return Intent.FRUSTRATION

    # ---------------------------------------------------------
    # GLOBAL FAILURE ANALYSIS
    # ---------------------------------------------------------

    if is_failure_analysis_question(text):
        return Intent.FAILURE_ANALYSIS

    # ---------------------------------------------------------
    # RETRY DECISION
    # ---------------------------------------------------------

    if is_retry_question(text):
        return Intent.RETRY_DECISION

    # ---------------------------------------------------------
    # RECOVERY PROBABILITY
    # ---------------------------------------------------------

    if is_probability_question(text):
        return Intent.RECOVERY_PROBABILITY

    # ---------------------------------------------------------
    # PRIORITIZATION
    # ---------------------------------------------------------

    if is_prioritization_question(text):
        return Intent.PRIORITIZATION

    # ---------------------------------------------------------
    # RECOVERED REVENUE
    # ---------------------------------------------------------

    if is_recovered_revenue_question(text):
        return Intent.RECOVERED_REVENUE

    # ---------------------------------------------------------
    # REVENUE AT RISK
    # ---------------------------------------------------------

    if is_revenue_at_risk_question(text):
        return Intent.REVENUE_AT_RISK

    # ---------------------------------------------------------
    # RECOVERY RATE
    # ---------------------------------------------------------

    if is_recovery_rate_question(text):
        return Intent.RECOVERY_RATE

    # ---------------------------------------------------------
    # ATTEMPT ANALYSIS
    # ---------------------------------------------------------

    if is_attempt_analysis_question(text):
        return Intent.ATTEMPT_ANALYSIS

    # ---------------------------------------------------------
    # TOTAL PAYMENTS
    # ---------------------------------------------------------

    if is_total_payments_question(text):
        return Intent.GENERAL_RECOVERAI

    # ---------------------------------------------------------
    # PAYMENT ANALYSIS
    # ---------------------------------------------------------

    if (
        "analyze" in text
        or "analyse" in text
        or "analysis" in text
        or "details" in text
        or "what happened" in text
        or "explain this payment" in text
        or "explain the payment" in text
        or "tell me about this payment" in text
        or "show payment details" in text
        or "payment details" in text
    ):
        return Intent.PAYMENT_ANALYSIS

    # ---------------------------------------------------------
    # GENERAL RECOVERAI
    # ---------------------------------------------------------

    return Intent.GENERAL_RECOVERAI