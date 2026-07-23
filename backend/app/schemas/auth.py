from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    role: Optional[str] = None
    user_id: Optional[int] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    first_login: Optional[bool] = None
    require_otp: Optional[bool] = False
    email_sent: Optional[bool] = None  # True if OTP email was delivered, False if it failed
    preferred_language: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


class ChangePasswordRequest(BaseModel):
    new_password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str


class RequestOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Disable2FARequest(BaseModel):
    user_id: int


class UpdateLanguageRequest(BaseModel):
    preferred_language: str


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_language: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str
