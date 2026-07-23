import datetime
import secrets
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now() + (
        expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Include a unique JWT ID (jti) so individual tokens can be blacklisted on logout
    to_encode.update({
        "exp": expire,
        "jti": secrets.token_hex(16),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> Optional[str]:
    """
    Validates password strength. Returns an error message string if invalid,
    or None if the password is acceptable.
    Rules: ≥8 chars, at least one uppercase, one lowercase, one digit.
    """
    if len(password) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères."
    if not any(c.isupper() for c in password):
        return "Le mot de passe doit contenir au moins une lettre majuscule."
    if not any(c.islower() for c in password):
        return "Le mot de passe doit contenir au moins une lettre minuscule."
    if not any(c.isdigit() for c in password):
        return "Le mot de passe doit contenir au moins un chiffre."
    return None
