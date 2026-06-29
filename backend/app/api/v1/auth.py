# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import cast
import datetime
import random
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    VerifyOTPRequest,
    RequestOTPRequest,
    Disable2FARequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token, get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Look up user by email
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect."
        )

    if user.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est verrouillé. Veuillez contacter l'administrateur."
        )

    if user.status == "DISABLED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est désactivé."
        )

    user_email: str = user.email  # type: ignore[assignment]
    user_password_hash: str = user.password_hash  # type: ignore[assignment]

    if not verify_password(payload.password, user_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect."
        )

    # Extract typed locals to avoid InstrumentedAttribute issues
    user_id: int = user.id  # type: ignore[assignment]
    user_first_login: bool = user.first_login  # type: ignore[assignment]
    user_two_factor_enabled: bool = user.two_factor_enabled  # type: ignore[assignment]
    user_password_only_until: datetime.datetime | None = user.password_only_until  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]

    # Check super-admin override/bypass duration
    is_bypassed = False
    if user_password_only_until:
        now_compare = datetime.datetime.now(datetime.timezone.utc)
        if user_password_only_until > now_compare:
            is_bypassed = True

    # Check if 2FA/OTP is required
    if user_two_factor_enabled and not is_bypassed:
        from app.core.redis import is_account_locked, set_otp
        if is_account_locked(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte est verrouillé pour 24 heures en raison d'un grand nombre de tentatives OTP infructueuses."
            )

        # Generate 6-digit OTP code
        otp_code = f"{random.randint(100000, 999999)}"
        set_otp(user_id, otp_code)

        # Send email synchronously (no Celery worker needed)
        from app.tasks.email_tasks import send_otp_email
        result = send_otp_email(user_email, otp_code, user_preferred_language)
        email_sent = result.get("email_sent", False)

        return TokenResponse(
            require_otp=True,
            email=user_email,
            email_sent=email_sent
        )

    # Get role code
    role_code: str = user.role.code if user.role else "UNKNOWN"  # type: ignore[assignment]

    # Create JWT token
    access_token = create_access_token(data={
        "sub": str(user_id),
        "email": user_email,
        "role": role_code
    })

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_code,
        user_id=user_id,
        email=user_email,
        first_login=user_first_login,
        require_otp=False
    )


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )

    # Extract typed locals
    user_id: int = user.id  # type: ignore[assignment]
    user_email: str = user.email  # type: ignore[assignment]
    user_first_login: bool = user.first_login  # type: ignore[assignment]

    from app.core.redis import is_account_locked, get_otp, increment_otp_attempts, set_account_lock, delete_otp, clear_account_lock

    if is_account_locked(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est verrouillé pour 24 heures en raison d'un grand nombre de tentatives OTP infructueuses."
        )

    otp_info = get_otp(user_id)
    if not otp_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le code OTP a expiré ou est invalide. Veuillez en demander un nouveau."
        )

    if payload.code != otp_info["code"]:
        attempts = increment_otp_attempts(user_id)
        if attempts >= 3:
            set_account_lock(user_id)
            delete_otp(user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte a été verrouillé pour 24 heures suite à 3 tentatives incorrectes."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code incorrect. Tentatives restantes : {3 - attempts}."
            )

    # Success! Delete OTP and clear lockout
    delete_otp(user_id)
    clear_account_lock(user_id)

    role_code: str = user.role.code if user.role else "UNKNOWN"  # type: ignore[assignment]
    access_token = create_access_token(data={
        "sub": str(user_id),
        "email": user_email,
        "role": role_code
    })

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_code,
        user_id=user_id,
        email=user_email,
        first_login=user_first_login,
        require_otp=False
    )


@router.post("/request-otp")
def request_otp(payload: RequestOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )

    # Extract typed locals
    user_id: int = user.id  # type: ignore[assignment]
    user_email: str = user.email  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]

    from app.core.redis import is_account_locked, get_otp_resends, increment_otp_resends, set_otp

    if is_account_locked(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte est verrouillé pour 24 heures."
        )

    resend_count = get_otp_resends(user_id)
    if resend_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Vous avez dépassé la limite de 3 renvois de code par 24 heures."
        )

    otp_code = f"{random.randint(100000, 999999)}"
    set_otp(user_id, otp_code)
    increment_otp_resends(user_id)

    from app.tasks.email_tasks import send_otp_email
    result = send_otp_email(user_email, otp_code, user_preferred_language)
    email_sent = result.get("email_sent", False)

    if not email_sent:
        return {"detail": "OTP generated but email delivery failed. Check the server logs for the code.", "email_sent": False}

    return {"detail": "OTP sent successfully.", "email_sent": True}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Avoid leaking user existence, just return success
        return {"detail": "If the email exists, a reset link has been sent.", "email_sent": False}
        
    user_email: str = user.email  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]
    user_id: int = user.id  # type: ignore[assignment]
    
    import secrets
    reset_token = secrets.token_urlsafe(32)
    
    from app.core.redis import set_reset_token
    set_reset_token(reset_token, user_id)
    
    from app.core.config import settings
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    from app.tasks.email_tasks import send_password_reset_email
    result = send_password_reset_email(user_email, reset_link, user_preferred_language)
    
    return {"detail": "If the email exists, a reset link has been sent.", "email_sent": True}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    from app.core.redis import get_reset_token, delete_reset_token
    
    user_id = get_reset_token(payload.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien de réinitialisation est invalide ou a expiré."
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )
        
    user.password_hash = get_password_hash(payload.new_password)
    user.first_login = False
    db.commit()
    
    delete_reset_token(payload.token)
    return {"message": "Votre mot de passe a été réinitialisé avec succès."}


@router.post("/admin/disable-2fa")
def disable_2fa(
    payload: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_code: str = current_user.role.code if current_user.role else "UNKNOWN"  # type: ignore[assignment]
    if role_code != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs système peuvent effectuer cette action."
        )

    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur cible non trouvé."
        )

    # Bypass 2FA for 1 hour
    target_user.password_only_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    db.commit()

    target_email: str = target_user.email  # type: ignore[assignment]
    return {"message": f"2FA désactivée pour {target_email} pendant 1 heure."}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    role_code: str = current_user.role.code if current_user.role else "UNKNOWN"  # type: ignore[assignment]
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": role_code,
        "first_login": current_user.first_login
    }


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_first_login: bool = current_user.first_login  # type: ignore[assignment]
    if not user_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already completed first login password change."
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.first_login = False
    db.commit()

    return {"message": "Password updated successfully."}
