# Jules - AI Household Companion Development Guide

## Project Overview

Jules is an SMS-first AI household companion for family meal planning via text messages. Simple web dashboard for one-time setup.

### MVP Features
1. **SMS-First Interface** - Communication through text messaging
2. **Dual Channel Architecture** - Group + individual threads with shared context
3. **AI Recipe Extraction** - Digitize handwritten recipes with GPT-4 Vision or Claude
4. **Conversational Meal Planning** - Natural language meal suggestions
5. **SMS Compliance** - TCPA/CTIA compliant opt-in/opt-out flows

## Tech Stack

**Backend**: FastAPI + Python 3.11, PostgreSQL 15+, Redis 6+, Celery
**Frontend**: React 18 + TypeScript, Vite, Tailwind CSS + shadcn/ui
**AI**: Anthropic Claude API (primary), OpenAI GPT-4 Vision (fallback)
**SMS**: Twilio (primary), Telnyx/Plivo (fallback providers)
**Infrastructure**: Docker, AWS ECS, RDS, S3, CloudFront
**Monitoring**: Sentry (errors + AI auto-resolution), FastAPI Radar (debugging), OpenTelemetry
**Auto-Healing**: Tenacity (retries), aiobreaker (circuit breakers), ARQ (task resilience)

## Recommended Templates & SDKs for MVP

**Full-Stack Template**
- **Official FastAPI Full-Stack Template**: https://github.com/fastapi/full-stack-fastapi-template
- FastAPI + React 19 + TypeScript + Tailwind + shadcn/ui + PostgreSQL
- JWT auth, Docker setup, production-ready

**Dashboard UI Components**
- **TailAdmin React**: https://github.com/TailAdmin/free-react-tailwind-admin-dashboard
- React + TypeScript + Tailwind components
- Use for recipe management, member management, meal planning interfaces

**Essential APIs & SDKs**
- **Anthropic Claude SDK**: Multimodal AI for recipe extraction, pantry scanning, conversation
- **Twilio Python SDK**: SMS messaging with webhook handling
- **Spoonacular API**: Meal planning database (900k+ foods, 2.3M recipes, nutrition data)
- **Edamam API**: Recipe and nutrition API (backup/supplement to AI extraction)
- **Sentry Python SDK**: Error monitoring with AI-powered auto-resolution
- **OpenTelemetry**: Distributed tracing and observability

**MCP (Model Context Protocol) Servers**
- **Sentry MCP Server**: Access Sentry data from Claude Code/Cursor for debugging
- **GitHub MCP Server**: Automate engineering processes and code reviews
- **Postgres MCP Server**: Database interactions and query optimization

## Core Services

**SMS Service**: Message routing, Twilio integration, compliance
**AI Service**: Recipe extraction (GPT-4V/Claude), NLP, pantry scanning
**Conversation Service**: State machines, flow control, context management
**Notification Service**: Rate limiting, delivery, queuing

## Database Models (Core Tables)

**households**: name, budget_tier, timezone, shopping_day
**members**: household_id, name, phone, email, role, opt_in_status, password_hash
**family_recipes**: household_id, title, ingredients (JSON), instructions (JSON), prep/cook times, original_file_url
**pantry_items**: household_id, item_name, quantity_status, category, confidence_level
**conversation_states**: household_id, member_id, channel, current_flow, flow_data (JSON)
**messages**: household_id, member_id, channel, direction, content, message_type

**Key Relationships**
- households (1) → (*) members, family_recipes, pantry_items, conversation_states
- members → opt_in_status: pending, active, declined, opted_out
- conversation_states → channel: group, individual

## Conversation Flows

**Recipe Submission Flow**
1. User sends image → AI extracts recipe
2. System confirms extraction → User validates/corrects
3. Save to family_recipes with original image preserved

**Weekly Planning Flow**
1. Sunday trigger → Group SMS with meal options
2. Family votes via number responses → Tally votes
3. Generate shopping list → Send before shopping day

**Pantry Scan Flow**
1. User sends pantry photo → AI identifies items
2. Update pantry_items table → Confirm with user
3. Use for meal suggestions

**Message Router Logic**
- Group intents: weekly_planning, meal_voting, shopping_list_delivery
- Individual intents: recipe_submission, pantry_scan, whats_for_dinner
- Check opt_in_status before processing
- Map intent to appropriate flow

## AI Integration

**Recipe Extraction Prompt**
- Extract from handwritten/printed recipes
- Return JSON: title, ingredients[], instructions[], prep_time, cook_time, servings, difficulty
- Handle common abbreviations, estimate missing values
- Preserve personal notes and attribution

**Pantry Scanning Prompt**
- Identify food items in photos
- Return: item name, quantity_estimate, quantity_status, confidence level
- Conservative estimates, normalized names

**Meal Suggestion Prompt**
- Input: pantry items, dietary preferences, family recipes, recent meals
- Output: 3-4 diverse meal options with explanations
- Prioritize using available ingredients and family favorites

**Use Claude API for:**
- All AI tasks (recipe extraction, pantry scanning, meal planning, conversation)
- Multimodal capabilities for image analysis
- Natural language processing for SMS conversations

## SMS Compliance

**Opt-In Flow**
1. Account holder adds member via web dashboard
2. System sends invitation SMS with clear opt-in language
3. Member responds YES → opt_in_status = active
4. Member responds STOP → opt_in_status = declined

**Opt-Out Processing**
- Keywords: STOP, UNSUBSCRIBE, CANCEL, END, QUIT
- Immediately set opt_in_status = opted_out
- Send confirmation SMS
- Stop all messages to that member
- Allow rejoin with START keyword

**Rate Limiting**
- Individual: max 10 messages/day
- Group: max 5 messages/day
- Track in Redis with daily expiration

**Compliance Requirements**
- Prior express consent before first message
- Clear opt-out instructions
- Audit trail of all consent actions
- Immediate processing of STOP requests

## Key Implementation Patterns

**SMS Provider Abstraction**
```python
class SMSProvider(ABC):
    async def send_message(self, to: str, body: str) -> str: pass
    async def send_media_message(self, to: str, body: str, media_url: str) -> str: pass
```

**AI Service Pattern**
```python
class AIService:
    async def extract_recipe(self, image_url: str) -> RecipeExtraction
    async def identify_pantry_items(self, image_url: str) -> List[PantryItem]
    async def generate_meal_suggestions(self, context: Dict) -> List[Recipe]
```

**Conversation State Machine**
```python
class ConversationFlow:
    state: ConversationState
    async def process_message(self, message: InboundMessage) -> FlowResponse
    async def transition_to(self, new_state: ConversationState)
```

## API Endpoints (Key Routes)

**Authentication**
- POST /api/auth/register - Create household account
- POST /api/auth/login - Login with email/password
- POST /api/auth/refresh - Refresh JWT token

**Households**
- GET /api/households/me - Get current household
- POST /api/households/members - Add family member (triggers invitation)
- PUT /api/households/members/{id} - Update member

**Recipes**
- GET /api/recipes/family - List family recipes
- POST /api/recipes/upload - Upload recipe image for extraction
- POST /api/recipes/family - Save confirmed recipe
- GET /api/recipes/family/{id} - Get recipe details

**SMS Webhooks**
- POST /api/sms/webhook - Twilio inbound message handler
- POST /api/sms/status - Delivery status callback

**Meal Planning**
- GET /api/meals/planned - Get weekly plan
- POST /api/meals/plan - Create meal plan
- GET /api/shopping-list - Get current shopping list

## Security

**Authentication**
- JWT tokens with refresh mechanism
- Password hashing with bcrypt
- Role-based access control (account_holder, adult, teen, child)

**Data Protection**
- Phone numbers encrypted at rest
- Sensitive data in environment variables
- Input validation on all endpoints
- Rate limiting on API routes

**SMS Security**
- Twilio webhook signature verification
- Validate phone numbers (E.164 format)
- Sanitize message content

## Development Workflow

**Setup**
```bash
# Use official FastAPI template
git clone https://github.com/fastapi/full-stack-fastapi-template
cd full-stack-fastapi-template

# Configure environment
cp .env.example .env
# Edit .env with Twilio, OpenAI, AWS credentials

# Start with Docker
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

**Testing**
```bash
# Backend tests
pytest

# Frontend tests
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

**Code Quality**
```bash
# Python
black backend/
isort backend/
flake8 backend/
mypy backend/

# TypeScript
npm run lint
npm run type-check
```

## Deployment

**Docker Containers**
- API service (FastAPI)
- Worker service (Celery)
- Scheduler service (Celery Beat)

**AWS Services**
- ECS Fargate: Container orchestration
- RDS PostgreSQL: Database with automated backups
- ElastiCache Redis: Task queue and caching
- S3 + CloudFront: Recipe images and assets
- ALB: Load balancing with SSL/TLS

**CI/CD**
- GitHub Actions for automated testing
- Build Docker images on push to main
- Deploy to ECS with zero-downtime rolling updates

## Performance & Scaling

**Caching Strategy**
- Redis cache for: household context (5 min), member permissions (1 hr), pantry items (30 min)
- CDN for static assets and recipe images

**Background Processing**
- Celery tasks for: AI recipe extraction, pantry scanning, batch SMS sending
- Scheduled tasks for: weekly planning triggers, invitation reminders

**Database Optimization**
- Indexes on: phone_number, household_id, conversation_state
- Read replicas for analytics queries
- Connection pooling with SQLAlchemy

## Error Handling & Auto-Healing

**Auto-Healing Mechanisms**
- **Tenacity**: Automatic retry logic with exponential backoff for API calls
- **aiobreaker**: Circuit breaker pattern for database connections (failure threshold: 5, recovery: 60s)
- **ARQ**: Resilient task queue with automatic job recovery after worker interruptions
- **FastAPI Exception Handlers**: Centralized error handling with retry-after headers

**Graceful Degradation**
- AI failures → fallback to manual entry or alternative AI provider
- SMS failures → retry with exponential backoff, failover to Telnyx/Plivo
- Database connection → circuit breaker prevents cascade failures
- Recipe extraction fails → offer manual form entry option

**Error Monitoring & Resolution**
- **Sentry AI Features** (2025):
  - **Autofix**: AI generates code fixes with 94% root cause accuracy
  - **Seer AI Agent**: Automatic issue scanning, root cause analysis, PR generation
  - **AI Code Review**: Pre-production bug detection in pull requests
  - **Session Replay**: Video playback of user sessions leading to errors
  - **Performance Monitoring**: Identifies bottlenecks in FastAPI and React
- **FastAPI Radar**: Real-time debugging dashboard for HTTP requests, SQL queries, exceptions
- **OpenTelemetry**: Distributed tracing across services (Tempo + Grafana)
- **Structured Logging**: Concise JSON logs with correlation IDs
  ```python
  # Good: logger.info("db_query", table="recipes", duration_ms=45, rows=12)
  # Bad: logger.info("Database query to recipes table took 45ms and returned 12 rows")
  ```

**Monitoring Stack**
- Prometheus: Metrics collection (latency, error rate, throughput)
- Grafana: Visualization dashboards
- Loki: Log aggregation
- Sentry: Error tracking + AI-powered resolution
- Twilio Insights: SMS delivery analytics

## Development Phases (MVP Roadmap Reference)

**Phase 1**: Foundation (Database, API, Redis, Celery)
**Phase 2**: SMS Infrastructure (Twilio integration, routing, compliance)
**Phase 3**: Authentication (Member management, invitations, opt-in)
**Phase 4**: Conversation Framework (State machines, intent detection)
**Phase 5**: AI Recipe Extraction (GPT-4V/Claude integration, image processing)
**Phase 6**: Meal Planning (Suggestions, voting, shopping lists)
**Phase 7**: Dual Channels (Group/individual routing, context sharing)
**Phase 8**: Web Dashboard (React UI, recipe management, settings)

See MICRO-ROADMAP.md for detailed task breakdown (8 phases, 40+ micro-tasks, 1-4 hours each).

## Quick Reference

**Environment Variables**
```bash
# Database & Cache
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0

# SMS Providers
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
TELNYX_API_KEY=...  # Fallback SMS provider
TELNYX_PHONE_NUMBER=...

# AI Services
ANTHROPIC_API_KEY=sk-ant-...  # Primary AI
OPENAI_API_KEY=sk-...  # Fallback AI
SPOONACULAR_API_KEY=...  # Meal planning data
EDAMAM_APP_ID=...  # Recipe/nutrition data
EDAMAM_APP_KEY=...

# Monitoring & Debugging
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENABLE_AI=true  # Enable Autofix and Seer
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% in dev, 0.1 in prod

# AWS
AWS_S3_BUCKET=jules-files
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Security
SECRET_KEY=...
ENCRYPTION_KEY=...
```

**Common Commands**
```bash
# Start dev environment with monitoring
docker-compose up -d

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Run tests with coverage
pytest --cov=app --cov-report=html
npm test

# View logs with correlation IDs
docker-compose logs -f backend | jq '.correlation_id, .message'

# Check Sentry issues
sentry-cli issues list --project=jules-api

# Monitor with FastAPI Radar
# Access: http://localhost:8000/radar

# Test circuit breaker
python -m scripts.test_circuit_breaker

# Check retry mechanisms
python -m scripts.test_retries
```

**Testing SMS Locally**
```bash
# Use ngrok for Twilio webhooks
ngrok http 8000
# Set TWILIO_WEBHOOK_BASE_URL to ngrok URL
```

## Best Practices

**Logging (Concise Format)**
```python
# Use structured JSON logs with essential fields only
logger.info("recipe_extracted", recipe_id=id, confidence=0.95, duration_ms=234)
# NOT: "Successfully extracted recipe ID abc-123 with confidence 0.95 in 234ms"

# Correlation IDs for tracing
logger.info("sms_sent", correlation_id=req_id, member_id=mid, status="ok")

# Errors with context
logger.error("ai_failed", correlation_id=req_id, provider="claude", retry=2, error_code="rate_limit")
```

**SMS Messages**
- Max 160 chars, conversational, opt-out in first message

**AI Prompts**
- Specify JSON structure, validate responses, cache results

**Database**
- Transactions for multi-table updates, index foreign keys, JSON for flexible fields

**Security**
- Never log PII (phone numbers, messages), rotate keys, rate limit all endpoints

**Auto-Healing**
- Circuit breakers on external APIs, Tenacity retries (max 3), ARQ task recovery

**Changelog**
- All changes documented in CHANGELOG.md
- Follow Keep a Changelog format
- Update on every significant change

## Implementation Examples

**Sentry Integration**
```python
# backend/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[
        FastApiIntegration(auto_enabling_integrations=False),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=1.0,
    enable_tracing=True,
)
```

**Circuit Breaker for Database**
```python
# backend/core/database.py
from aiobreaker import CircuitBreaker

db_breaker = CircuitBreaker(
    fail_max=5,  # Open circuit after 5 failures
    timeout=60,  # Try recovery after 60 seconds
)

@db_breaker
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
```

**Retry Logic with Tenacity**
```python
# backend/services/ai_service.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def extract_recipe_with_retry(image_url: str):
    return await anthropic_client.messages.create(...)
```

**FastAPI Radar Setup**
```python
# backend/main.py
from fastapi_radar import RadarMiddleware

app = FastAPI()
app.add_middleware(RadarMiddleware)
# Access dashboard at http://localhost:8000/radar
```

**ARQ Task with Auto-Recovery**
```python
# backend/workers/tasks.py
from arq import cron

async def extract_recipe_task(ctx, recipe_id: str, image_url: str):
    """ARQ automatically retries this if worker crashes"""
    try:
        result = await ai_service.extract_recipe(image_url)
        await save_recipe(recipe_id, result)
    except Exception as e:
        # ARQ will retry with exponential backoff
        raise

class WorkerSettings:
    max_tries = 3
    retry_jobs = True
    job_timeout = 300
```

**React Sentry Integration**
```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

**MCP Server Usage (Sentry)**
```bash
# Add to your MCP client config (Claude Code, Cursor, etc.)
{
  "mcpServers": {
    "sentry": {
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "your_token",
        "SENTRY_ORG": "your_org"
      }
    }
  }
}

# Then ask Claude: "Show me the top 5 critical issues in jules-api project"
```

## Support & Resources

**Documentation**
- FastAPI Docs: http://localhost:8000/docs (when running)
- See README.md for project overview
- See ARCHITECTURE.md for detailed system design
- See PROJECT_SETUP.md for setup instructions

**Debugging**
- Check logs: `docker-compose logs -f`
- Database: `docker-compose exec db psql -U jules`
- Redis: `docker-compose exec redis redis-cli`
- Test Twilio: Twilio Console → Phone Numbers → Configure

**Common Issues**
- SMS not sending → Check Twilio credentials and webhook URL; Check circuit breaker state
- AI extraction failing → Verify API key and rate limits; Check Sentry for auto-suggested fixes
- Database connection errors → Check DATABASE_URL and pg_isready; Circuit breaker may be open
- Redis connection errors → Verify Redis is running; Check ARQ worker status
- High error rate → Review Sentry dashboard; Enable Autofix for automatic resolution
- Task failures → Check ARQ worker logs; Verify retry configuration

**Debugging with Tools**
- **FastAPI Radar**: http://localhost:8000/radar - Real-time request/SQL monitoring
- **Sentry Dashboard**: View session replays, AI-suggested fixes, performance bottlenecks
- **Grafana**: http://localhost:3000 - Metrics, logs, traces visualization
- **MCP Sentry Server**: Query issues from Claude Code/Cursor directly
