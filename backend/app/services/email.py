from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


def send_password_reset_email(
    recipient_email: str,
    customer_name: str,
    reset_url: str,
) -> None:
    """Send a secure password-reset link."""

    settings = get_settings()

    if not settings.EMAIL_USERNAME:
        raise RuntimeError(
            "EMAIL_USERNAME is not configured."
        )

    if not settings.EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_PASSWORD is not configured."
        )

    sender = settings.EMAIL_FROM or settings.EMAIL_USERNAME

    message = EmailMessage()
    message["Subject"] = "Reset your RecoverAI password"
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(
        f"""Hi {customer_name},


We received a request to reset your RecoverAI password.

Use the secure link below to choose a new password:
{reset_url}

This link expires in 30 minutes. If you did not request a password reset,
you can safely ignore this email.

Best regards,
RecoverAI Team
"""
    )

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        server.send_message(message)


def send_demo_confirmation_email(
    recipient_email: str,
    customer_name: str,
    business_name: str,
) -> None:
    """
    Send a confirmation email to a user who requested a demo.
    """

    settings = get_settings()

    if not settings.EMAIL_USERNAME:
        raise RuntimeError(
            "EMAIL_USERNAME is not configured."
        )

    if not settings.EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_PASSWORD is not configured."
        )

    sender = (
        settings.EMAIL_FROM
        or settings.EMAIL_USERNAME
    )

    message = EmailMessage()

    message["Subject"] = (
        "Your RecoverAI Demo Request"
    )

    message["From"] = sender
    message["To"] = recipient_email

    message.set_content(
        f"""Hi {customer_name},

Thank you for requesting a RecoverAI demo.

We have received your request for {business_name}.

Our team will contact you shortly.

Best regards,
RecoverAI Team
"""
    )

    with smtplib.SMTP(
        settings.EMAIL_HOST,
        settings.EMAIL_PORT,
    ) as server:

        server.starttls()

        server.login(
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD,
        )

        server.send_message(message)