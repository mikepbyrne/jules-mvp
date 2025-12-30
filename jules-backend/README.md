# Jules Backend API

Production-ready SMS-based AI life companion backend service built with FastAPI, PostgreSQL, Redis, and Anthropic Claude.

## Features

- **SMS Communication**: Receive and send SMS messages via Bandwidth API
- **AI Conversations**: Claude-powered contextual conversations with fallback to OpenAI
- **Crisis Detection**: Automatic detection of suicide, self-harm, violence, and abuse indicators
- **Age Verification**: Veriff integration for COPPA compliance
- **Payment Processing**: Stripe subscriptions and payment management
- **Memory Management**: Redis-backed conversation context and user preferences
- **Compliance**: AI disclosure tracking, opt-out handling, data encryption
- **Monitoring**: Sentry error tracking, Langfuse LLM observability
- **Production-Ready**: Docker support, comprehensive tests, async architecture

## Architecture

```
src/
├── api/              # API routes and webhooks
├── core/             # Core utilities (database, Redis, logging, security)
├── models/           # SQLAlchemy models
├── services/         # Business logic services
│   ├── sms_service.py
│   ├── llm_service.py
│   ├── crisis_service.py
│   ├── conversation_service.py
│   ├── user_service.py
│   ├── compliance_service.py
│   ├── veriff_service.py
│   ├── stripe_service.py
│   └── memory_service.py
├── config.py         # Configuration management
└── main.py           # FastAPI application
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 16+
- Redis 7+
- Poetry (for dependency management)

## Quick Start (Docker)

### 1. Clone and Setup

```bash
cd jules-backend
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```env
# Required API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
BANDWIDTH_ACCOUNT_ID=your-bandwidth-account-id
BANDWIDTH_USERNAME=your-bandwidth-username
BANDWIDTH_PASSWORD=your-bandwidth-password
BANDWIDTH_APPLICATION_ID=your-bandwidth-app-id
BANDWIDTH_PHONE_NUMBER=+15551234567

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Veriff (for age verification)
VERIFF_API_KEY=your-veriff-key
VERIFF_API_SECRET=your-veriff-secret

# Security (generate strong random keys)
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps
```

### 4. Run Database Migrations

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Check current version
docker-compose exec api alembic current
```

### 5. Access Services

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Adminer (DB UI): http://localhost:8080
- Redis Commander: http://localhost:8081

## Local Development (Without Docker)

### 1. Install Dependencies

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Start PostgreSQL and Redis

```bash
# Using Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Run Migrations

```bash
poetry run alembic upgrade head
```

### 4. Start Development Server

```bash
poetry run uvicorn src.main:app --reload --port 8000
```

## Testing

### Run All Tests

```bash
# With Docker
docker-compose run --rm api pytest -v

# Local
poetry run pytest -v
```

### Run Specific Tests

```bash
# Test a specific file
poetry run pytest tests/test_sms_service.py -v

# Test with coverage
poetry run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Coverage

The project maintains 80%+ test coverage across all services:

- `test_sms_service.py` - SMS sending and validation
- `test_llm_service.py` - AI response generation
- `test_crisis_service.py` - Crisis detection
- `test_conversation_service.py` - Message orchestration
- `test_api_webhooks.py` - API endpoints

## Database Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Add new field to user"

# Create empty migration
poetry run alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
poetry run alembic upgrade head

# Upgrade to specific revision
poetry run alembic upgrade abc123

# Downgrade one revision
poetry run alembic downgrade -1
```

### Migration History

```bash
# Show current version
poetry run alembic current

# Show migration history
poetry run alembic history
```

## API Endpoints

### Webhooks

**POST /webhooks/sms** - Receive inbound SMS messages

```bash
curl -X POST http://localhost:8000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '[{
    "type": "message-received",
    "message": {
      "id": "msg-123",
      "from": "+15551234567",
      "text": "Hello Jules!"
    }
  }]'
```

**POST /webhooks/stripe** - Handle Stripe webhook events

```bash
curl -X POST http://localhost:8000/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: signature" \
  -d '{
    "type": "checkout.session.completed",
    "data": {...}
  }'
```

### Health Checks

**GET /health** - Detailed health check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "jules-backend",
  "version": "0.1.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

## Configuration

All configuration is managed through environment variables defined in `src/config.py`:

### Core Settings
- `ENVIRONMENT`: development/staging/production
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### Database
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Connection pool size (default: 20)

### Redis
- `REDIS_URL`: Redis connection string
- `REDIS_SESSION_TTL`: Session TTL in seconds (default: 14400)

### External Services
- Bandwidth (SMS)
- Anthropic & OpenAI (LLM)
- Veriff (Age Verification)
- Stripe (Payments)
- Sentry (Error Tracking)
- Langfuse (LLM Observability)

See `.env.example` for complete list.

## Service Architecture

### Conversation Flow

1. **Inbound SMS** → Bandwidth webhook → `/webhooks/sms`
2. **User Lookup** → Get or create user
3. **Crisis Detection** → Scan for crisis keywords
4. **Context Building** → Load conversation history from Redis/DB
5. **LLM Generation** → Generate response with Claude/OpenAI
6. **Compliance** → Add AI disclosure if needed
7. **Outbound SMS** → Send response via Bandwidth
8. **Logging** → Save message, update metrics

### Service Dependencies

```
ConversationService (orchestrator)
├── SMSService (Bandwidth)
├── LLMService (Anthropic/OpenAI)
├── CrisisService (keyword detection)
├── ComplianceService (disclosures, consent)
├── UserService (user management)
└── MemoryService (Redis cache)
```

## Security Features

### Data Encryption
- PII encrypted at rest using Fernet (AES-128)
- Encrypted fields: phone numbers, names, emails, preferences
- Message content encrypted in database

### Authentication
- JWT tokens for API access
- Webhook signature verification (Stripe)
- IP whitelisting for webhooks (optional)

### Compliance
- COPPA: Age verification via Veriff
- TCPA: Opt-out handling (STOP command)
- AI Disclosure: Periodic reminders every 3 hours
- Crisis Resources: Automatic hotline provision

## Monitoring & Observability

### Sentry
- Error tracking and performance monitoring
- Automatic error capture and alerting
- Configure via `SENTRY_DSN`

### Langfuse
- LLM prompt and response tracking
- Token usage and cost monitoring
- Performance analytics
- Configure via `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`

### Logging
- Structured JSON logging
- Request/response logging
- Database query logging (debug mode)
- Service-level metrics

## Production Deployment

### Build Production Image

```bash
docker build --target production -t jules-backend:latest .
```

### Run Production Container

```bash
docker run -d \
  --name jules-api \
  -p 8000:8000 \
  --env-file .env.production \
  jules-backend:latest
```

### Environment Checklist

Before deploying to production:

- [ ] Set strong `SECRET_KEY`, `ENCRYPTION_KEY`, `JWT_SECRET_KEY`
- [ ] Configure production `DATABASE_URL` (managed PostgreSQL)
- [ ] Configure production `REDIS_URL` (managed Redis)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `SENTRY_DSN` for error tracking
- [ ] Set `ALLOWED_ORIGINS` for CORS
- [ ] Configure all API keys (Bandwidth, Anthropic, Stripe, Veriff)
- [ ] Run database migrations
- [ ] Set up SSL/TLS termination
- [ ] Configure webhook URLs in Bandwidth and Stripe dashboards
- [ ] Enable monitoring and alerting

### Scaling

The application is designed to scale horizontally:

- Stateless API servers (store session in Redis)
- Database connection pooling
- Async I/O throughout
- Multiple Uvicorn workers
- Redis for distributed caching

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U jules -d jules_dev -c "SELECT 1"

# View logs
docker-compose logs postgres
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli -a jules_redis_password ping

# View logs
docker-compose logs redis
```

### API Issues

```bash
# View API logs
docker-compose logs -f api

# Check health
curl http://localhost:8000/health

# Restart API
docker-compose restart api
```

### Migration Issues

```bash
# Check current migration
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Rollback one migration
docker-compose exec api alembic downgrade -1
```

## Development Workflow

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## Contributing

1. Create a feature branch
2. Make changes
3. Add tests (maintain 80%+ coverage)
4. Run tests and linting
5. Submit pull request

## License

Proprietary - Jules Team

## Support

For issues or questions, contact the development team.
