#!/usr/bin/env python3
"""Seed test data for development."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.database import async_session_maker
from src.core.security import encrypt_data
from src.models.user import SubscriptionTier, TrustLevel, User


async def seed_test_users() -> None:
    """Seed test users for development."""
    settings = get_settings()

    async with async_session_maker() as session:
        # Create test user 1
        user1 = User(
            phone_number="+15551234567",
            phone_number_encrypted=encrypt_data("+15551234567"),
            first_name_encrypted=encrypt_data("Alice"),
            age_verified=True,
            is_minor=False,
            subscription_tier=SubscriptionTier.FREE,
            trust_level=TrustLevel.LEVEL_0,
            consent_given=True,
        )
        session.add(user1)

        # Create test user 2
        user2 = User(
            phone_number="+15559876543",
            phone_number_encrypted=encrypt_data("+15559876543"),
            first_name_encrypted=encrypt_data("Bob"),
            age_verified=True,
            is_minor=False,
            subscription_tier=SubscriptionTier.MONTHLY,
            trust_level=TrustLevel.LEVEL_1,
            consent_given=True,
        )
        session.add(user2)

        await session.commit()

        print("✅ Test users created successfully!")
        print(f"   User 1: Alice (+15551234567) - Free tier")
        print(f"   User 2: Bob (+15559876543) - Monthly tier")


async def main() -> None:
    """Main function."""
    print("🌱 Seeding test data...")
    await seed_test_users()
    print("✅ Test data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
