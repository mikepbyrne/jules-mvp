# Contributing to Jules Backend

Thank you for your interest in contributing to Jules!

## Development Setup

1. **Prerequisites**
   - Python 3.11+
   - Docker & Docker Compose
   - Poetry (for dependency management)

2. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd jules-backend

   # Install dependencies
   poetry install

   # Generate secure keys
   poetry run python scripts/generate_keys.py

   # Copy environment template
   cp .env.local .env
   # Edit .env with your API keys

   # Start services
   docker-compose up -d

   # Run migrations
   docker-compose exec api alembic upgrade head

   # Seed test data (optional)
   docker-compose exec api python scripts/seed_test_data.py
   ```

3. **Install Pre-commit Hooks**
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:
```bash
# Format code
make format

# Check code quality
make lint

# Run type checker
make check
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Watch mode (auto-run on changes)
make test-watch
```

### Database Migrations

```bash
# Create a new migration
make migrate-create name=your_migration_name

# Run migrations
make migrate

# Rollback one migration
alembic downgrade -1
```

## Project Structure

```
jules-backend/
├── src/
│   ├── api/          # API routes and webhooks
│   ├── core/         # Core infrastructure (db, redis, security)
│   ├── models/       # SQLAlchemy models
│   └── services/     # Business logic services
├── tests/            # Test suite
├── alembic/          # Database migrations
├── scripts/          # Utility scripts
└── docs/             # Documentation
```

## Service Architecture

All business logic is organized into services:

- **ConversationService**: Main orchestrator
- **SMSService**: Bandwidth integration
- **LLMService**: AI (Anthropic/OpenAI)
- **CrisisService**: Crisis detection
- **ComplianceService**: Regulatory compliance
- **UserService**: User management
- **VeriffService**: Age verification
- **StripeService**: Payments
- **MemoryService**: Context & caching

## Testing Guidelines

1. **Write tests for all new features**
   - Unit tests for services
   - Integration tests for API endpoints
   - Use mocks for external services

2. **Test Structure**
   ```python
   async def test_feature_name(db_session, mock_service):
       # Arrange
       ...

       # Act
       result = await service.method()

       # Assert
       assert result.field == expected_value
   ```

3. **Coverage Target**: 80%+

## API Development

### Adding a New Endpoint

1. Create route in `src/api/`
2. Add service method if needed
3. Write tests in `tests/test_api_*.py`
4. Update API documentation

### Webhook Handlers

All webhooks must:
- Verify signatures (Bandwidth HMAC, Stripe signatures)
- Handle idempotency
- Return quickly (< 3s)
- Use background tasks for long operations

## Database Changes

1. **Never edit migration files directly**
2. Create new migration: `make migrate-create name=description`
3. Review auto-generated migration
4. Test both upgrade and downgrade
5. Update models if needed

## Security

- **Never commit secrets** (use .env)
- **Always encrypt PII** (use `encrypt_data()`)
- **Validate all inputs** (use Pydantic models)
- **Verify webhook signatures**
- **Use type hints** for all functions

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Write tests
   - Update documentation

3. **Run checks**
   ```bash
   make format
   make lint
   make test
   ```

4. **Commit with descriptive messages**
   ```bash
   git commit -m "feat: add user preference management"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

Examples:
```
feat: add crisis detection service
fix: resolve encryption key generation bug
docs: update API endpoint documentation
test: add integration tests for SMS webhooks
```

## Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests pass and coverage is adequate
- [ ] Documentation is updated
- [ ] No secrets in code
- [ ] PII is encrypted
- [ ] Error handling is robust
- [ ] Type hints are present
- [ ] PR description is clear

## Getting Help

- **Documentation**: See README.md, DEPLOYMENT.md, QUICKSTART.md
- **Issues**: Open a GitHub issue
- **Questions**: Tag maintainers in PR

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
