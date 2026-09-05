from __future__ import annotations

import json
from urllib import request

from app.core.config import get_settings


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _send_brevo_email(
    recipient_email: str,
    customer_name: str,
    subject: str,
    text_content: str,
) -> None:
    """Send an email through Brevo's HTTPS API."""

    settings = get_settings()

    if not settings.BREVO_API_KEY:
        raise RuntimeError(
            "BREVO_API_KEY is not configured."
        )

    sender = settings.EMAIL_FROM or settings.EMAIL_USERNAME

    if not sender:
        raise RuntimeError(
            "EMAIL_FROM or EMAIL_USERNAME must be configured."
        )

    payload = {
        "sender": {
            "name": "RecoverAI Team",
            "email": sender,
        },
        "to": [
            {
                "email": recipient_email,
                "name": customer_name,
            }
        ],
        "subject": subject,
        "textContent": text_content,
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        BREVO_API_URL,
        data=data,
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            response.read()

    except Exception as exc:
        raise RuntimeError(
            f"Brevo email sending failed: {exc}"
        ) from exc


def send_password_reset_email(
    recipient_email: str,
    customer_name: str,
    reset_url: str,
) -> None:
    """Send a secure password-reset link."""

    _send_brevo_email(
        recipient_email=recipient_email,
        customer_name=customer_name,
        subject="Reset your RecoverAI password",
        text_content=f"""Hi {customer_name},

We received a request to reset your RecoverAI password.

Use the secure link below to choose a new password:

{reset_url}

This link expires in 30 minutes. If you did not request a password reset,
you can safely ignore this email.

Best regards,
RecoverAI Team
""",
    )


def send_demo_confirmation_email(
    recipient_email: str,
    customer_name: str,
    business_name: str,
) -> None:
    """Send a confirmation email to a user who requested a demo."""

    _send_brevo_email(
        recipient_email=recipient_email,
        customer_name=customer_name,
        subject="Your RecoverAI Demo Request",
        text_content=f"""Hi {customer_name},

Thank you for requesting a RecoverAI demo.

We have received your request for {business_name}.

Our team will contact you shortly.

Best regards,
RecoverAI Team
""",
    )