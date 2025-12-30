"""
Phone number encryption for PII protection.

Uses Fernet symmetric encryption for database fields.
"""
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from ENCRYPTION_KEY env var.
        """
        key = encryption_key or os.getenv("ENCRYPTION_KEY")

        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable must be set")

        self.fernet = Fernet(key.encode())

    def encrypt(self, value: str) -> str:
        """Encrypt string value."""
        if not value:
            return value

        encrypted = self.fernet.encrypt(value.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt encrypted value."""
        if not encrypted_value:
            return encrypted_value

        decrypted = self.fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance."""
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy custom type for encrypted string fields.

    Usage:
        class Member(Base):
            phone_number = Column(EncryptedString(255), nullable=False)
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        if value is None:
            return value

        try:
            service = get_encryption_service()
            encrypted = service.encrypt(value)

            logger.debug("field_encrypted", field_length=len(value))

            return encrypted

        except Exception as e:
            logger.error("encryption_failed", error=str(e))
            raise

    def process_result_value(self, value, dialect):
        """Decrypt value when reading from database."""
        if value is None:
            return value

        try:
            service = get_encryption_service()
            decrypted = service.decrypt(value)

            logger.debug("field_decrypted")

            return decrypted

        except Exception as e:
            logger.error("decryption_failed", error=str(e))
            raise


def generate_encryption_key() -> str:
    """
    Generate new Fernet encryption key.

    Use once to generate key, then store in environment variable.

    Returns:
        Base64-encoded encryption key
    """
    key = Fernet.generate_key()
    return key.decode()


# Example usage for generating key (run once):
# if __name__ == "__main__":
#     key = generate_encryption_key()
#     print(f"ENCRYPTION_KEY={key}")
#     print("Store this in your .env file and keep it secure!")
