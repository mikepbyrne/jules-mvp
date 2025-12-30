#!/usr/bin/env python3
"""Generate secure keys for Jules backend."""

import base64
import secrets


def generate_secret_key(length: int = 32) -> str:
    """Generate a random secret key."""
    return secrets.token_hex(length)


def generate_encryption_key() -> str:
    """Generate a base64-encoded encryption key for Fernet."""
    key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key).decode()


def main() -> None:
    """Generate and print all required keys."""
    print("🔐 Jules Backend - Secret Key Generator")
    print("=" * 50)
    print()
    print("Copy these values to your .env file:")
    print()
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print(f"JWT_SECRET_KEY={generate_secret_key()}")
    print()
    print("⚠️  Keep these keys secret and never commit them to version control!")
    print()


if __name__ == "__main__":
    main()
