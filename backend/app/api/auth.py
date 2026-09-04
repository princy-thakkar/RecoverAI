"""
Authentication API for RecoverAI.

Provides:
    POST /api/auth/login
    POST /api/auth/register
    GET  /api/auth/me
    POST /api/auth/request-demo
    POST /api/auth/request-password-reset
    POST /api/auth/reset-password

Authentication uses:
    - MongoDB Merchant repository
    - Argon2 password hashing through pwdlib
    - JWT bearer access tokens
    - short-lived signed password-reset tokens

Request Demo:
    The demo-request flow also creates a merchant account so that
    a new evaluator/customer can immediately log in and use RecoverAI.
"""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.demo_request import DemoRequest as DemoRequestModel
from app.models.domain import Merchant
from app.repositories.entities import (
    get_demo_request_repository,
    get_merchant_repository,
)
from app.services.email import (
    send_demo_confirmation_email,
    send_password_reset_email,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# SECURITY
# ============================================================

bearer_scheme = HTTPBearer(auto_error=False)
PASSWORD_RESET_TOKEN_TYPE = "password_reset"
PASSWORD_RESET_EXPIRE_MINUTES = 30


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str
    user: UserResponse


class LoginResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str
    user: UserResponse


class DemoRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    business_name: str = Field(min_length=1)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class DemoRequestResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    token_type: str
    user: UserResponse


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8)


class PasswordResetResponse(BaseModel):
    success: bool
    message: str


# ============================================================
# HELPERS
# ============================================================

def _public_user(merchant: Merchant) -> UserResponse:
    return UserResponse(
        id=merchant.id,
        name=merchant.name,
        email=merchant.email,
    )


async def _find_merchant_by_email(email: str) -> Merchant | None:
    repository = get_merchant_repository()
    return await repository.find_one(
        {"email": email.lower().strip()}
    )


def _create_password_reset_token(merchant_id: str) -> str:
    return create_access_token(
        subject=merchant_id,
        expires_minutes=PASSWORD_RESET_EXPIRE_MINUTES,
        extra_claims={"type": PASSWORD_RESET_TOKEN_TYPE},
    )


def _decode_password_reset_token(token: str) -> str:
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link has expired. Please request a new one.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid. Please request a new one.",
        ) from exc

    if payload.get("type") != PASSWORD_RESET_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid. Please request a new one.",
        )

    merchant_id = payload.get("sub")
    if not isinstance(merchant_id, str) or not merchant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid. Please request a new one.",
        )

    return merchant_id


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(request: RegisterRequest) -> RegisterResponse:
    repository = get_merchant_repository()

    email = request.email.lower().strip()
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty.",
        )

    existing_merchant = await repository.find_one({"email": email})
    if existing_merchant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    merchant = Merchant(
        name=name,
        email=email,
        password_hash=hash_password(request.password),
    )

    await repository.insert(merchant)

    access_token = create_access_token(subject=merchant.id)

    return RegisterResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        user=_public_user(merchant),
    )


# ============================================================
# CURRENT USER DEPENDENCY
# ============================================================

async def get_current_merchant(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> Merchant:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc

    merchant_id = payload.get("sub")
    if not isinstance(merchant_id, str) or not merchant_id:
        raise unauthorized

    merchant = await get_merchant_repository().find_by_id(merchant_id)
    if merchant is None:
        raise unauthorized

    return merchant


CurrentMerchant = Annotated[
    Merchant,
    Depends(get_current_merchant),
]


# ============================================================
# LOGIN
# ============================================================

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest) -> LoginResponse:
    merchant = await _find_merchant_by_email(credentials.email)

    if (
        merchant is None
        or not merchant.password_hash
        or not verify_password(credentials.password, merchant.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=merchant.id)

    return LoginResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        user=_public_user(merchant),
    )


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/me", response_model=UserResponse)
async def get_me(merchant: CurrentMerchant) -> UserResponse:
    return _public_user(merchant)


# ============================================================
# PASSWORD RESET
# ============================================================

@router.post(
    "/request-password-reset",
    response_model=PasswordResetResponse,
)
async def request_password_reset(
    request: PasswordResetRequest,
) -> PasswordResetResponse:
    """
    Start a password reset.

    The response intentionally does not reveal whether an account exists.
    When the account exists, a short-lived signed reset link is emailed.
    """

    email = request.email.lower().strip()
    merchant = await _find_merchant_by_email(email)

    if merchant is not None:
        settings = get_settings()
        token = _create_password_reset_token(merchant.id)
        reset_url = (
            f"{settings.FRONTEND_URL.rstrip('/')}/"
            f"?reset_token={token}"
        )

        try:
            send_password_reset_email(
                recipient_email=merchant.email,
                customer_name=merchant.name,
                reset_url=reset_url,
            )
        except Exception as exc:
            print(f"Failed to send password reset email: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to send the password reset email right now. Please try again later.",
            ) from exc

    return PasswordResetResponse(
        success=True,
        message=(
            "If an account exists for this email, a password reset link has been sent."
        ),
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
)
async def reset_password(
    request: PasswordResetConfirmRequest,
) -> PasswordResetResponse:
    """Validate a reset token and replace the merchant password."""

    merchant_id = _decode_password_reset_token(request.token)
    repository = get_merchant_repository()
    merchant = await repository.find_by_id(merchant_id)

    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid. Please request a new one.",
        )

    await repository.update_by_id(
        merchant.id,
        {"password_hash": hash_password(request.password)},
    )

    return PasswordResetResponse(
        success=True,
        message="Your password has been updated successfully. You can now sign in with your new password.",
    )


# ============================================================
# REQUEST DEMO
# ============================================================

@router.post(
    "/request-demo",
    response_model=DemoRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_demo(request: DemoRequest) -> DemoRequestResponse:
    merchant_repository = get_merchant_repository()
    demo_repository = get_demo_request_repository()

    name = request.name.strip()
    email = request.email.lower().strip()
    business_name = request.business_name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty.",
        )

    if not business_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Business name cannot be empty.",
        )

    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passwords do not match.",
        )

    existing_merchant = await merchant_repository.find_one({"email": email})
    if existing_merchant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please log in instead.",
        )

    merchant = Merchant(
        name=name,
        email=email,
        password_hash=hash_password(request.password),
    )

    await merchant_repository.insert(merchant)

    demo_request = DemoRequestModel(
        name=name,
        email=email,
        business_name=business_name,
    )

    try:
        await demo_repository.insert(demo_request)
    except Exception as exc:
        print(f"Failed to persist demo request: {exc}")

    try:
        send_demo_confirmation_email(
            recipient_email=str(demo_request.email),
            customer_name=demo_request.name,
            business_name=demo_request.business_name,
        )
    except Exception as exc:
        print(f"Failed to send demo confirmation email: {exc}")

    access_token = create_access_token(subject=merchant.id)

    return DemoRequestResponse(
        success=True,
        message=(
            "Your RecoverAI account has been created successfully. "
            "You are now signed in."
        ),
        access_token=access_token,
        token_type="bearer",
        user=_public_user(merchant),
    )
