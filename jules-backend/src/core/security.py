"""Security utilities for encryption and authentication."""

import base64
from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption
_encryption_key = settings.encryption_key.encode()
if len(_encryption_key) == 32:
    # If it's 32 bytes, encode it to base64 for Fernet
    _encryption_key = base64.urlsafe_b64encode(_encryption_key)
fernet = Fernet(_encryption_key)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_data(data: str) -> str:
    """Encrypt data using Fernet."""
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using Fernet."""
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def generate_security_phrase() -> str:
    """Generate a random security phrase for user verification."""
    import secrets
    import string

    # Generate 4 random words from a simple word list
    words = ["alpha", "beta", "gamma", "delta", "echo", "foxtrot", "golf", "hotel"]
    phrase = " ".join(secrets.choice(words) for _ in range(3))
    return phrase.upper()


def redact_phone_number(phone: str) -> str:
    """
    Redact phone number for logging (show last 4 digits only).

    Args:
        phone: Phone number to redact (e.g., "+15551234567")

    Returns:
        str: Redacted phone (e.g., "*******4567")
    """
    if not phone or len(phone) < 4:
        return "****"

    # Show last 4 digits, mask the rest
    return "*" * (len(phone) - 4) + phone[-4:]


def redact_email(email: str) -> str:
    """
    Redact email for logging (show first char and domain).

    Args:
        email: Email to redact (e.g., "user@example.com")

    Returns:
        str: Redacted email (e.g., "u***@example.com")
    """
    if not email or "@" not in email:
        return "***@***.***"

    local, domain = email.split("@", 1)
    if len(local) > 1:
        return f"{local[0]}***@{domain}"
    return f"***@{domain}"
