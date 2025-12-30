# Jules - AI Life Companion Backend

An SMS-based AI companion service built with compliance-first architecture for regulatory environments.

## Overview

Jules is a production-grade backend API for delivering AI-powered conversation experiences via SMS. Built with safety, compliance, and scalability as core design principles.

### Key Features

- **SMS-First Communication** - Native SMS conversation interface
- **Compliance-Ready** - Built-in support for NY AI Companion Law and CA SB 243
- **Safety-First Architecture** - Crisis detection with 988 Suicide & Crisis Lifeline integration
- **Enterprise-Grade** - FastAPI + PostgreSQL + Redis with comprehensive testing
- **Payment & Verification** - Integrated Stripe payments and Veriff age verification

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16+ with SQLAlchemy ORM
- **Cache**: Redis 7+ for session management
- **LLM**: Anthropic Claude (Haiku/Sonnet) with OpenAI fallback
- **SMS**: Bandwidth API
- **Payments**: Stripe
- **Age Verification**: Veriff
- **Testing**: Pytest with 80%+ coverage requirement

## Architecture

```
jules-backend/
├── src/
│   ├── api/          # REST API endpoints
│   ├── core/         # Database, Redis, security
│   ├── models/       # SQLAlchemy models
│   └── services/     # Business logic services
├── tests/
│   ├── unit/         # Fast, isolated tests
│   ├── integration/  # Multi-service workflows
│   ├── red_team/     # Adversarial security tests
│   └── e2e/          # Complete user journeys
├── alembic/          # Database migrations
└── scripts/          # Deployment and utilities
```

## Services

- **SMS Service** - Bandwidth API integration for message delivery
- **LLM Service** - Multi-provider LLM orchestration with fallback
- **Crisis Service** - Real-time crisis detection and 988 referral
- **Conversation Service** - Core conversation orchestration
- **User Service** - User management and authentication
- **Compliance Service** - Regulatory requirement enforcement
- **Veriff Service** - Age verification integration
- **Stripe Service** - Payment processing
- **Memory Service** - Conversation context and memory

## Compliance Features

### NY AI Companion Law
- AI disclosure at session start
- Recurring disclosure every 3 hours
- Clear indication of AI nature

### CA SB 243 (Effective Jan 1, 2026)
- Age verification before SMS access
- Content filtering for minors
- Anonymous crisis reporting for regulatory compliance

### TCPA Compliance
- STOP keyword immediate opt-out processing
- 8 AM - 9 PM message time restrictions
- Express consent tracking
- Opt-in/opt-out documentation

### Crisis Safety
- Immediate detection of crisis keywords
- 988 Suicide & Crisis Lifeline referral
- Sub-5-second response time for crisis messages
- Anonymous logging for safety reporting

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Jules.git
cd Jules/jules-backend

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start services with Docker
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/ -m unit              # Unit tests only
pytest tests/ -m integration       # Integration tests
pytest tests/ -m compliance        # Compliance tests
pytest tests/ -m red_team          # Security/safety tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## API Documentation

Once running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jules

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
ANTHROPIC_API_KEY=your-anthropic-key
DEFAULT_MODEL=claude-3-5-haiku-20241022

# Verification & Payments
VERIFF_API_KEY=your-veriff-key
STRIPE_SECRET_KEY=your-stripe-key

# Compliance
CRISIS_HOTLINE_NUMBER=988
AI_DISCLOSURE_INTERVAL_HOURS=3
```

## Testing Strategy

Comprehensive testing across 5 dimensions:

1. **Unit Tests** - 80%+ coverage requirement, fast isolated tests
2. **Integration Tests** - Multi-service workflows and critical flows
3. **E2E Tests** - Complete user journeys from onboarding to conversation
4. **Red Team Tests** - Adversarial security and safety validation
5. **Quality Tests** - AI-powered conversation quality evaluation

### Critical Test Categories

- **Crisis Detection** (100% accuracy required)
- **Compliance Flows** (NY + CA + TCPA)
- **Security** (SQL injection, prompt injection, PII extraction)
- **Safety** (Crisis evasion, therapy boundaries, minor protection)

## Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Docker

```bash
# Build
docker build -t jules-backend .

# Run
docker run -p 8000:8000 \
  --env-file .env \
  jules-backend
```

## Performance Targets

- **Response Latency**: p95 < 8 seconds (p95 < 5s for crisis)
- **Uptime**: 99.9% availability
- **Conversation Quality**: ≥ 8.0/10 average score
- **Critical Failures**: < 3% of conversations

## Security

- Secrets encrypted at rest with `cryptography.fernet`
- PII redaction in all logs
- Rate limiting on all API endpoints
- SQL injection protection via SQLAlchemy ORM
- Input validation and sanitization
- Redis session management with 4-hour TTL

## Contributing

This is a production codebase with strict quality requirements:

1. All code must have 80%+ test coverage
2. All PRs must pass red team security tests
3. Compliance tests must pass at 100%
4. Crisis detection tests have zero tolerance for false negatives
5. Code must follow project style guide (see `.editorconfig`)

## License

Proprietary - All Rights Reserved

## Support

For issues, questions, or support:
- GitHub Issues: [github.com/yourusername/Jules/issues](https://github.com/yourusername/Jules/issues)
- Email: support@jules-ai.com

## Acknowledgments

Built with compliance guidance from:
- NY AI Companion Law (effective 2024)
- CA SB 243 (effective January 1, 2026)
- TCPA regulations
- 988 Suicide & Crisis Lifeline integration

---

**Status**: Production-ready backend with comprehensive testing infrastructure

**Last Updated**: December 2024
