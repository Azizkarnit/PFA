# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.utils import get_client_ip
from typing import cast
import datetime
import random
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, validate_password_strength
from app.models import User
from app.schemas.auth import (
    LoginRequest, TokenResponse, ErrorResponse, ChangePasswordRequest,
    VerifyOTPRequest, RequestOTPRequest, ForgotPasswordRequest,
    ResetPasswordRequest, Disable2FARequest, UpdateLanguageRequest,
    UpdateProfileRequest, UpdatePasswordRequest
)
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token, get_password_hash

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if this token has been blacklisted (i.e., user already logged out)
    from app.core.redis import is_blacklisted
    jti = payload.get("jti")
    if jti and is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
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
    # ── Rate limiting (per IP) ────────────────────────────────────────────────
    from app.core.redis import increment_rate_limit
    from app.core.config import settings as cfg
    client_ip = get_client_ip(request)
    attempt_count = increment_rate_limit(client_ip, cfg.RATE_LIMIT_WINDOW_MINUTES)
    if attempt_count > cfg.MAX_LOGIN_ATTEMPTS_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de tentatives de connexion. Réessayez dans {cfg.RATE_LIMIT_WINDOW_MINUTES} minutes."
        )

    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

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
        now_compare = datetime.datetime.now()
        if user_password_only_until.tzinfo is not None:
            user_password_only_until = user_password_only_until.replace(tzinfo=None)
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

        import secrets
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        from app.api.v1.system_settings import get_setting
        expiration = int(get_setting(db, "code_expiration"))
        set_otp(user_id, otp_code, expiration)

        from app.tasks.email_tasks import send_otp_email
        result = send_otp_email(user_email, otp_code, user_preferred_language, expiration_minutes=expiration)
        email_sent = result.get("email_sent", False)

        return TokenResponse(
            require_otp=True,
            email=user_email,
            email_sent=email_sent,
            preferred_language=user_preferred_language
        )

    # Get role code
    role_code: str = user.role.code if user.role else "UNKNOWN"  # type: ignore[assignment]

    # Create JWT token
    access_token = create_access_token(data={
        "sub": str(user_id),
        "email": user_email,
        "role": role_code
    })

    from app.models import AuditLog
    audit_entry = AuditLog(
        user_id=user_id,
        action="User Logged In",
        entity_type="User",
        entity_id=user_id,
        ip_address=client_ip
    )
    db.add(audit_entry)
    user.last_login_at = datetime.datetime.now()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_code,
        user_id=user_id,
        email=user_email,
        first_name=user.first_name,
        last_name=user.last_name,
        first_login=user_first_login,
        require_otp=False,
        preferred_language=user_preferred_language
    )


@router.post("/logout")
def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user)
):
    """
    Invalidates the current JWT by adding its jti to the Redis blacklist.
    The token will be rejected by get_current_user on subsequent requests.
    """
    from app.core.redis import blacklist_token
    from app.core.config import settings as cfg
    payload = decode_access_token(token)
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            remaining_ttl = int(exp - datetime.datetime.now().timestamp())
            if remaining_ttl > 0:
                blacklist_token(jti, remaining_ttl)
    return {"message": "Déconnexion réussie."}


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )

    user_id: int = user.id  # type: ignore[assignment]
    user_email: str = user.email  # type: ignore[assignment]
    user_first_login: bool = user.first_login  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]

    from app.core.redis import is_account_locked, get_otp, increment_otp_attempts, set_account_lock, delete_otp, clear_account_lock
    from app.api.v1.system_settings import get_setting

    lock_hours = int(get_setting(db, "lock_duration"))
    max_attempts = int(get_setting(db, "max_signin_attempts"))

    if is_account_locked(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Votre compte est verrouillé pour {lock_hours} heures en raison d'un grand nombre de tentatives OTP infructueuses."
        )

    otp_info = get_otp(user_id)
    if not otp_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le code OTP a expiré ou est invalide. Veuillez en demander un nouveau."
        )

    if payload.code != otp_info["code"]:
        attempts = increment_otp_attempts(user_id)
        if attempts >= max_attempts:
            set_account_lock(user_id, lock_hours)
            
            # Notify System Admins and Account Managers
            from app.core.notification_service import notify_system_admins, notify_account_managers
            lock_msg = f"User {user.email} has been locked out after multiple failed login attempts."
            notify_system_admins(db, "Account Locked", lock_msg, type="WARNING", action_url="/admin/locked-accounts")
            notify_account_managers(db, "Account Locked", lock_msg, type="WARNING", action_url="/admin/locked-accounts")
            delete_otp(user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Votre compte a été verrouillé pour {lock_hours} heures suite à {max_attempts} tentatives incorrectes."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code incorrect. Tentatives restantes : {max_attempts - attempts}."
            )

    delete_otp(user_id)
    clear_account_lock(user_id)

    role_code: str = user.role.code if user.role else "UNKNOWN"  # type: ignore[assignment]
    access_token = create_access_token(data={
        "sub": str(user_id),
        "email": user_email,
        "role": role_code
    })

    from app.models import AuditLog
    audit_entry = AuditLog(
        user_id=user_id,
        action="User Logged In",
        entity_type="User",
        entity_id=user_id,
        ip_address=get_client_ip(request)
    )
    db.add(audit_entry)
    user.last_login_at = datetime.datetime.now()
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role_code,
        user_id=user_id,
        email=user_email,
        first_name=user.first_name,
        last_name=user.last_name,
        first_login=user_first_login,
        require_otp=False,
        preferred_language=user_preferred_language
    )


@router.post("/request-otp")
def request_otp(payload: RequestOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé."
        )

    user_id: int = user.id  # type: ignore[assignment]
    user_email: str = user.email  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]

    from app.core.redis import is_account_locked, get_otp_resends, increment_otp_resends, set_otp

    if is_account_locked(user_id):
        from app.api.v1.system_settings import get_setting
        lock_hours = int(get_setting(db, "lock_duration"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Votre compte est verrouillé pour {lock_hours} heures."
        )

    resend_count = get_otp_resends(user_id)
    if resend_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Vous avez dépassé la limite de 3 renvois de code par 24 heures."
        )

    import secrets
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    from app.api.v1.system_settings import get_setting
    expiration = int(get_setting(db, "code_expiration"))
    set_otp(user_id, otp_code, expiration)
    increment_otp_resends(user_id)

    from app.tasks.email_tasks import send_otp_email
    result = send_otp_email(user_email, otp_code, user_preferred_language, expiration_minutes=expiration)
    email_sent = result.get("email_sent", False)

    if not email_sent:
        return {"detail": "OTP generated but email delivery failed. Check the server logs for the code.", "email_sent": False}

    return {"detail": "OTP sent successfully.", "email_sent": True}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        # Avoid leaking user existence
        return {"detail": "If the email exists, a reset link has been sent.", "email_sent": False}

    user_email: str = user.email  # type: ignore[assignment]
    user_preferred_language: str = user.preferred_language  # type: ignore[assignment]
    user_id: int = user.id  # type: ignore[assignment]

    import secrets as _secrets
    reset_token = _secrets.token_urlsafe(32)

    from app.core.redis import set_reset_token
    set_reset_token(reset_token, user_id)

    from app.core.config import settings
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    from app.tasks.email_tasks import send_password_reset_email
    send_password_reset_email(user_email, reset_link, user_preferred_language)

    return {"detail": "If the email exists, a reset link has been sent.", "email_sent": True}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Validate password strength before anything else
    pw_error = validate_password_strength(payload.new_password)
    if pw_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pw_error)

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

    target_user.password_only_until = datetime.datetime.now() + datetime.timedelta(hours=1)
    db.commit()

    target_email: str = target_user.email  # type: ignore[assignment]
    return {"message": f"2FA désactivée pour {target_email} pendant 1 heure."}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    role_code: str = current_user.role.code if current_user.role else "UNKNOWN"  # type: ignore[assignment]
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone_number": current_user.phone_number,
        "preferred_language": current_user.preferred_language,
        "role": role_code,
        "first_login": current_user.first_login,
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at
    }


@router.put("/me")
def update_current_user_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number
    if payload.preferred_language is not None:
        current_user.preferred_language = payload.preferred_language

    db.commit()
    return {"message": "Profile updated successfully."}


@router.put("/me/password")
def update_current_user_password(
    payload: UpdatePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, str(current_user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel est incorrect."
        )

    # Validate new password strength
    pw_error = validate_password_strength(payload.new_password)
    if pw_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pw_error)

    current_user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully."}


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_first_login: bool = current_user.first_login  # type: ignore[assignment]
    if not user_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already completed first login password change."
        )

    # Validate new password strength
    pw_error = validate_password_strength(payload.new_password)
    if pw_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pw_error)

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.first_login = False
    db.commit()

    return {"message": "Password updated successfully."}


@router.put("/me/language")
def update_preferred_language(payload: UpdateLanguageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.preferred_language = payload.preferred_language
    db.commit()
    return {"message": "Language updated successfully.", "preferred_language": payload.preferred_language}
