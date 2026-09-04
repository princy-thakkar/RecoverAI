"""
Merchant settings API for RecoverAI.

Settings are scoped to the authenticated merchant.

The merchant's identity fields come from the authenticated
Merchant record rather than hardcoded demo data.

Recovery preferences are kept per merchant in memory for now.
They should be moved to a dedicated MongoDB settings collection
when persistent merchant configuration is introduced.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter

from app.api.auth import CurrentMerchant


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS: dict[str, Any] = {
    "merchantPhone": "",
    "businessName": "",
    "gstin": "",
    "maxRetryAttempts": 3,
    "retryIntervalHours": 24,
    "minRecoveryProbability": 50,
    "emailNotifications": True,
    "smsNotifications": True,
    "weeklyReport": True,
    "recoveryAlerts": True,
}


# ============================================================
# MERCHANT-SCOPED SETTINGS STORE
# ============================================================
#
# This prevents one merchant from overwriting another merchant's
# settings during the current demo/runtime.
#
# It is intentionally isolated so it can later be replaced with
# a MongoDB-backed settings repository without changing the API.
#

_settings_by_merchant: dict[str, dict[str, Any]] = {}


def _get_merchant_settings(
    merchant_id: str,
) -> dict[str, Any]:
    """
    Return a copy of the stored settings for one merchant.

    A copy is returned so callers cannot accidentally mutate the
    stored configuration without going through the PUT endpoint.
    """

    if merchant_id not in _settings_by_merchant:
        _settings_by_merchant[merchant_id] = deepcopy(
            DEFAULT_SETTINGS,
        )

    return deepcopy(
        _settings_by_merchant[merchant_id],
    )


def _build_response(
    merchant,
) -> dict[str, Any]:
    """
    Combine authenticated merchant identity with merchant settings.
    """

    settings = _get_merchant_settings(
        merchant.id,
    )

    return {
        "merchantName": merchant.name,
        "merchantEmail": str(merchant.email),
        **settings,
    }


# ============================================================
# GET SETTINGS
# ============================================================

@router.get("")
async def get_settings(
    merchant: CurrentMerchant,
) -> dict[str, Any]:
    """
    Return settings for the authenticated merchant.

    Identity information always comes from the authenticated
    Merchant record.
    """

    return _build_response(
        merchant,
    )


# ============================================================
# UPDATE SETTINGS
# ============================================================

@router.put("")
async def update_settings(
    data: dict[str, Any],
    merchant: CurrentMerchant,
) -> dict[str, Any]:
    """
    Update configurable settings for the authenticated merchant.

    merchantName and merchantEmail are intentionally ignored here.
    They are authentication/profile fields and must not be changed
    through this generic settings endpoint.
    """

    allowed_fields = set(
        DEFAULT_SETTINGS.keys(),
    )

    updates = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    settings = _get_merchant_settings(
        merchant.id,
    )

    settings.update(
        updates,
    )

    _settings_by_merchant[
        merchant.id
    ] = settings

    return {
        "success": True,
        "settings": _build_response(
            merchant,
        ),
    }