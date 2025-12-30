# Jules Tooling & API Research Summary

**Date**: December 29, 2025
**Research Focus**: Debugging, auto-healing, APIs, SDKs, and MCPs to streamline Jules MVP development

---

## 1. Auto-Healing & Resilience Tools

### Tenacity (Python Retry Library)
- **Purpose**: Automatic retry logic with intelligent backoff
- **Features**: Exponential backoff, custom retry strategies, decorators
- **Use in Jules**: API calls to Claude, Twilio, Spoonacular
- **Install**: `pip install tenacity`

### aiobreaker (Circuit Breaker Pattern)
- **Purpose**: Prevent cascade failures in async Python applications
- **Features**: Configurable failure threshold, automatic recovery testing
- **Use in Jules**: Database connections, external API calls
- **Configuration**: fail_max=5, timeout=60s
- **Install**: `pip install aiobreaker`

### ARQ (Async Task Queue)
- **Purpose**: Resilient background task processing
- **Features**: Automatic job recovery on worker crashes, exponential backoff retries
- **Use in Jules**: Recipe extraction, pantry scanning, batch SMS
- **Advantage over Celery**: Better async support, built-in retry mechanisms
- **Install**: `pip install arq`

---

## 2. Debugging & Monitoring Tools

### Sentry (Error Monitoring + AI Auto-Resolution)
**Why Sentry is Critical for Jules:**

#### AI-Powered Features (2025)
1. **Autofix**: 94% accuracy in root cause identification, generates code fixes automatically
2. **Seer AI Agent**:
   - Automatic issue scanning
   - Root cause analysis
   - PR generation for fixes
3. **AI Code Review**: Pre-production bug detection in pull requests
4. **Session Replay**: Video playback of user sessions leading to errors
5. **Performance Monitoring**: Identifies bottlenecks in FastAPI and React

#### Integration
- **FastAPI**: One-line integration, automatic error capture
- **React**: Session replay, component-level error tracking
- **MCP Server**: Query Sentry data from Claude Code/Cursor

**Pricing**: Free tier available, paid plans for advanced features
**Install**:
- Backend: `pip install sentry-sdk`
- Frontend: `npm install @sentry/react`

### FastAPI Radar
- **Purpose**: Real-time debugging dashboard
- **Features**: HTTP requests, SQL queries, exceptions monitoring
- **UI**: Beautiful React dashboard, zero configuration
- **Access**: http://localhost:8000/radar
- **Install**: `pip install fastapi-radar`
- **GitHub**: https://github.com/doganarif/fastapi-radar

### OpenTelemetry Stack
**Components:**
- **Prometheus**: Metrics collection (latency, error rate, throughput)
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing
- **OpenTelemetry**: Instrumentation

**Use in Jules**: Full observability from request to database
**Install**: `pip install opentelemetry-instrumentation-fastapi`

---

## 3. Model Context Protocol (MCP) Servers

### What is MCP?
- **Created by**: Anthropic (November 2024)
- **Adopted by**: OpenAI (March 2025), donated to Linux Foundation (December 2025)
- **Purpose**: Standardize how AI systems integrate with external tools and data

### MCP Servers for Jules

#### 1. Sentry MCP Server
- **Use**: Query Sentry issues from Claude Code/Cursor
- **Install**: `npx -y @sentry/mcp-server`
- **Example**: "Show me the top 5 critical issues in jules-api"

#### 2. GitHub MCP Server
- **Use**: Automate code reviews, PR management
- **Benefits**: AI-assisted development workflow

#### 3. Postgres MCP Server
- **Use**: Database interactions, query optimization
- **Benefits**: AI can help debug database issues

### Security Note
- MCP servers need proper authentication
- Use environment variables for tokens
- Don't expose to public internet without auth

---

## 4. SMS & Communication APIs

### Primary: Twilio
- **Pros**: Reliable, well-documented, extensive SDK support
- **Cons**: Can be expensive, occasional outages
- **SDK**: `pip install twilio`

### Fallback Options

#### Telnyx
- **Pros**: Cheaper rates, free 24/7 support, strong OTP/SMS APIs
- **Features**: Voice, messaging, user verification
- **Use**: SMS failover provider

#### Plivo
- **Pros**: Developer-friendly, cheaper than Twilio, good SDKs
- **Features**: SMS, voice, WhatsApp APIs
- **Transparent pricing**: Pay-as-you-go

**Recommendation**: Use Twilio as primary, Telnyx as fallback with circuit breaker pattern

---

## 5. Meal Planning & Recipe APIs

### Spoonacular API (Recommended)
- **Database**: 900k+ foods, 2.3M+ recipes, 680k+ UPC codes
- **Features**:
  - Weekly meal planning
  - Automatic nutritional calculations
  - Diet/calorie/nutrient filtering
  - Recipe search and analysis
- **Pricing**: Free tier available, paid plans for production
- **Use in Jules**: Supplement AI recipe extraction, meal suggestions
- **Website**: https://spoonacular.com/food-api

### Edamam API (Backup)
- **Database**: 900k+ foods, 2.3M+ recipes
- **Features**: Nutrition analysis, recipe search, dietary restrictions
- **Pricing**: Free tier, paid plans
- **Use in Jules**: Alternative/backup to Spoonacular
- **Website**: https://www.edamam.com/

### TheMealDB (Free Alternative)
- **Database**: Free recipe database with JSON API
- **Pros**: Completely free, easy to use
- **Cons**: Smaller database, less features
- **Use in Jules**: Development/testing, fallback option
- **Website**: https://www.themealdb.com/

### FatSecret Platform API
- **Database**: 17k+ international recipes with nutrition data
- **Features**: Curated recipes, localized nutrition profiles
- **Use in Jules**: Additional recipe source

**Recommendation**:
- Primary: Claude API for recipe extraction (handwritten recipes)
- Supplement: Spoonacular for meal planning database
- Backup: Edamam or TheMealDB for fallback

---

## 6. AI Services Comparison

### Anthropic Claude (Recommended Primary)
- **Model**: Claude 3.5 Sonnet
- **Strengths**:
  - Multimodal (vision + text)
  - Excellent instruction following
  - Long context window (200k tokens)
  - Strong at structured output (JSON)
- **Use in Jules**: Recipe extraction, pantry scanning, conversation, meal planning
- **API**: Anthropic API
- **SDK**: `pip install anthropic`

### OpenAI GPT-4 Vision (Fallback)
- **Model**: GPT-4 Vision Preview
- **Strengths**: Proven vision capabilities, large ecosystem
- **Use in Jules**: Fallback for recipe extraction if Claude fails
- **SDK**: `pip install openai`

**Recommendation**: Use Claude as primary AI, GPT-4V as fallback

---

## 7. Frontend Template & Component Libraries

### Official FastAPI Full-Stack Template
- **Repository**: https://github.com/fastapi/full-stack-fastapi-template
- **Stack**: FastAPI + React 19 + TypeScript + Tailwind + shadcn/ui + PostgreSQL
- **Features**: JWT auth, Docker setup, production-ready
- **Why**: Perfect match for Jules tech stack

### TailAdmin React
- **Repository**: https://github.com/TailAdmin/free-react-tailwind-admin-dashboard
- **Components**: Dashboard, tables, forms, charts, calendar
- **Use in Jules**: Recipe management UI, member management, meal planning calendar
- **License**: MIT (free and open source)

---

## 8. Implementation Priority

### Phase 1: Foundation
1. ✅ Use Official FastAPI Full-Stack Template
2. ✅ Install Sentry SDK (backend + frontend)
3. ✅ Set up FastAPI Radar for debugging
4. ✅ Configure circuit breakers with aiobreaker

### Phase 2: Resilience
1. ✅ Add Tenacity retry decorators to API calls
2. ✅ Replace Celery with ARQ for task queue
3. ✅ Set up OpenTelemetry instrumentation
4. ✅ Configure Prometheus + Grafana

### Phase 3: AI Integration
1. ✅ Integrate Anthropic Claude SDK
2. ✅ Add OpenAI as fallback
3. ✅ Connect Spoonacular API for meal planning data
4. ✅ Set up Edamam as backup

### Phase 4: SMS & Communication
1. ✅ Integrate Twilio SDK
2. ✅ Add Telnyx as fallback provider
3. ✅ Implement circuit breaker for SMS
4. ✅ Set up retry logic with Tenacity

### Phase 5: MCP Servers
1. ✅ Configure Sentry MCP server
2. ✅ Set up GitHub MCP server
3. ✅ Add Postgres MCP server
4. ✅ Enable in Claude Code/Cursor

---

## 9. Cost Estimates (MVP)

### AI Services
- **Claude API**: $3/million input tokens, $15/million output tokens
  - Estimate: ~$50-100/month for MVP testing
- **OpenAI GPT-4V**: Fallback only, minimal cost

### SMS Services
- **Twilio**: $0.0079/SMS in US
  - Estimate: 10 families × 50 messages/month = 500 messages = $4/month
- **Telnyx**: Cheaper rates for failover

### Monitoring
- **Sentry**: Free tier (5k events/month), then $26/month
- **Prometheus/Grafana**: Self-hosted (free)

### Recipe APIs
- **Spoonacular**: Free tier (150 requests/day), then $149/month
- **Edamam**: Free tier, then $49/month

**Total MVP Cost Estimate**: ~$100-200/month

---

## 10. Dependencies to Install

### Backend (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
redis==5.0.1

# Auto-Healing & Resilience
tenacity==8.2.3
aiobreaker==1.4.0
arq==0.25.0

# Monitoring & Debugging
sentry-sdk==1.39.1
fastapi-radar==0.1.2
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
prometheus-fastapi-instrumentator==6.1.0

# SMS Providers
twilio==8.10.1
telnyx==2.0.0

# AI Services
anthropic==0.18.0
openai==1.6.1

# Meal Planning APIs
requests==2.31.0  # For Spoonacular/Edamam HTTP calls

# Security
cryptography==41.0.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@sentry/react": "^7.91.0",
    "@tanstack/react-query": "^5.14.2",
    "axios": "^1.6.2"
  }
}
```

---

## 11. Key Learnings

### Auto-Healing Strategy
1. **Prevent failures**: Circuit breakers stop cascade failures
2. **Retry transient errors**: Tenacity with exponential backoff
3. **Recover gracefully**: ARQ automatically retries failed tasks
4. **Fix automatically**: Sentry AI suggests and generates fixes

### Monitoring Strategy
1. **Real-time debugging**: FastAPI Radar for live request monitoring
2. **Error tracking**: Sentry for automatic issue detection and resolution
3. **Observability**: OpenTelemetry for distributed tracing
4. **Metrics**: Prometheus + Grafana for system health

### MCP Strategy
1. **Developer experience**: Query Sentry issues from IDE
2. **Code quality**: GitHub MCP for automated reviews
3. **Database debugging**: Postgres MCP for query optimization

### AI Strategy
1. **Primary**: Claude for all AI tasks (best instruction following)
2. **Fallback**: OpenAI GPT-4V if Claude fails
3. **Supplement**: Spoonacular API for meal planning database
4. **Cost optimization**: Cache AI responses, use structured output

---

## 12. Next Steps

1. **Clone FastAPI Full-Stack Template**: Start with production-ready foundation
2. **Install debugging tools**: Sentry, FastAPI Radar, OpenTelemetry
3. **Add auto-healing**: Circuit breakers, retry logic, ARQ
4. **Integrate APIs**: Claude, Twilio, Spoonacular
5. **Configure MCP servers**: Enable AI-assisted development
6. **Test resilience**: Simulate failures, verify auto-healing works

---

## Resources & Links

**Templates**
- FastAPI Full-Stack: https://github.com/fastapi/full-stack-fastapi-template
- TailAdmin React: https://github.com/TailAdmin/free-react-tailwind-admin-dashboard

**Monitoring**
- Sentry: https://sentry.io/for/fastapi/
- FastAPI Radar: https://github.com/doganarif/fastapi-radar
- OpenTelemetry FastAPI: https://github.com/blueswen/fastapi-observability

**Auto-Healing**
- Tenacity Docs: https://tenacity.readthedocs.io/
- aiobreaker: https://github.com/arlyon/aiobreaker
- ARQ: https://arq-docs.helpmanual.io/

**APIs**
- Anthropic Claude: https://docs.anthropic.com/
- Spoonacular: https://spoonacular.com/food-api
- Edamam: https://www.edamam.com/
- Twilio: https://www.twilio.com/docs

**MCP**
- MCP Specification: https://modelcontextprotocol.io/
- Sentry MCP: https://docs.sentry.io/ (search for MCP)
- MCP Registry: ~2000 servers available
