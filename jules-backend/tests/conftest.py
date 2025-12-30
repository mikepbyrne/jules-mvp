"""Test fixtures and configuration."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings, get_settings
from src.core.database import Base, get_db
from src.core.redis import RedisClient
from src.main import app

fake = Faker()


# Test settings
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        environment="development",
        debug=True,
        log_level="DEBUG",
        secret_key="test-secret-key-32-characters!!",
        database_url="postgresql+asyncpg://test:test@localhost:5432/jules_test",
        redis_url="redis://localhost:6379/1",
        bandwidth_account_id="test-account",
        bandwidth_username="test-user",
        bandwidth_password="test-pass",
        bandwidth_application_id="test-app",
        bandwidth_phone_number="+15551234567",
        anthropic_api_key="test-anthropic-key",
        openai_api_key="test-openai-key",
        veriff_api_key="test-veriff-key",
        veriff_api_secret="test-veriff-secret",
        stripe_secret_key="sk_test_123",
        stripe_publishable_key="pk_test_123",
        stripe_webhook_secret="whsec_test_123",
        stripe_price_id_monthly="price_test_monthly",
        stripe_price_id_annual="price_test_annual",
        encryption_key="test-encryption-key-32-chars!",
        jwt_secret_key="test-jwt-secret-key-32-chars!",
    )


# Override settings dependency
@pytest.fixture(autouse=True)
def override_settings(test_settings: Settings) -> Generator:
    """Override settings for all tests."""
    from src.config import get_settings

    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.clear()


# Event loop
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database
@pytest_asyncio.fixture(scope="function")
async def db_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(test_settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Redis
@pytest_asyncio.fixture(scope="function")
async def redis_client(test_settings: Settings) -> AsyncGenerator[RedisClient, None]:
    """Create test Redis client."""
    client = RedisClient(test_settings.redis_url)

    # Clear test database
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


# Mock services
@pytest.fixture
def mock_sms_service(mocker):
    """Mock SMS service."""
    from src.services.sms_service import SMSService

    mock = mocker.AsyncMock(spec=SMSService)
    mock.send_message.return_value = {"id": "test-msg-id", "status": "sent"}
    mock.validate_phone_number.return_value = "+15551234567"
    return mock


@pytest.fixture
def mock_llm_service(mocker):
    """Mock LLM service."""
    from src.services.llm_service import LLMService

    mock = mocker.AsyncMock(spec=LLMService)
    mock.generate_response.return_value = {
        "content": "Hello! How can I help you today?",
        "tokens_used": 100,
        "model": "claude-3-5-haiku-20241022",
        "provider": "anthropic",
        "latency_ms": 500,
    }
    return mock


@pytest.fixture
def mock_crisis_service(mocker):
    """Mock crisis detection service."""
    from src.services.crisis_service import CrisisDetectionService

    mock = mocker.Mock(spec=CrisisDetectionService)
    mock.detect_crisis.return_value = {"detected": False}
    mock.get_crisis_response.return_value = "Crisis hotline: 988"
    return mock


@pytest.fixture
def mock_stripe(mocker):
    """Mock Stripe API."""
    mock_customer = mocker.Mock()
    mock_customer.id = "cus_test123"
    mock_customer.email = "test@example.com"

    mocker.patch("stripe.Customer.create_async", return_value=mock_customer)
    mocker.patch("stripe.Customer.retrieve_async", return_value=mock_customer)

    mock_session = mocker.Mock()
    mock_session.id = "cs_test123"
    mock_session.url = "https://checkout.stripe.com/test"

    mocker.patch("stripe.checkout.Session.create_async", return_value=mock_session)

    return mocker


# Test data factories
@pytest.fixture
def user_factory(db_session: AsyncSession):
    """Factory for creating test users."""
    from src.models.user import User
    from src.core.security import encrypt_data

    async def create_user(
        phone_number: str | None = None,
        first_name: str | None = None,
        **kwargs,
    ) -> User:
        phone = phone_number or fake.phone_number()
        user = User(
            phone_number=phone,
            phone_number_encrypted=encrypt_data(phone),
            first_name_encrypted=encrypt_data(first_name) if first_name else None,
            **kwargs,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return create_user


@pytest.fixture
def conversation_factory(db_session: AsyncSession):
    """Factory for creating test conversations."""
    from src.models.conversation import Conversation
    import uuid

    async def create_conversation(user_id: int, **kwargs) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            **kwargs,
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        return conversation

    return create_conversation


@pytest.fixture
def message_factory(db_session: AsyncSession):
    """Factory for creating test messages."""
    from src.models.conversation import Message, MessageRole, MessageDirection
    from src.core.security import encrypt_data

    async def create_message(
        conversation_id: int,
        user_id: int,
        content: str,
        role: MessageRole = MessageRole.USER,
        **kwargs,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            content_encrypted=encrypt_data(content),
            role=role,
            direction=MessageDirection.INBOUND
            if role == MessageRole.USER
            else MessageDirection.OUTBOUND,
            **kwargs,
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)
        return message

    return create_message
