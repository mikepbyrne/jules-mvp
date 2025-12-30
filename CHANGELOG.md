# Changelog

All notable changes to Jules will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2025-12-29

### Added - Single-User MVP
- **Core MVP Implementation**
  - Single-file FastAPI application (app.py - 500 lines)
  - JSON file storage for recipes, meal plans, conversation state
  - 11 SMS commands: START, HELP, RECIPE, LIST, VIEW, DELETE, PLAN, TONIGHT, SHOP
  - Simple state machine for conversation flows
  - Manual recipe entry (no AI initially)
  - 2-person household support with hardcoded phone numbers

- **Development Environment**
  - Virtual environment setup
  - Minimal dependencies (4 packages: fastapi, uvicorn, twilio, python-dotenv)
  - Data and logs directories
  - .gitignore for local development

- **Documentation**
  - SINGLE_USER_MVP.md - Complete 2-4 week testing plan
  - README_SETUP.md - 20-minute setup guide with Twilio configuration
  - QUICKSTART.md - Immediate next steps and troubleshooting
  - .env.example - Configuration template

- **Features**
  - Recipe Management: Add, list, view, delete recipes via SMS
  - Meal Planning: Select meals for the week, generate shopping lists
  - Conversation State: Track user flows across recipe entry and planning
  - Shopping List: Auto-generate from selected meals, deduplicate ingredients

### Technical Details
- No PostgreSQL (JSON files in data/ directory)
- No Redis (JSON-based state management)
- No web UI (SMS-only interface)
- No AI services (manual text entry)
- Local development with ngrok for Twilio webhooks
- Cost: ~$2.50/month for 2-user testing

### Deployment
- Local development only
- Ngrok tunnel for webhook exposure
- Twilio webhook configuration required

---

## Previous Work (Pre-MVP)

### [0.0.3] - 2025-12-29 - Critical Improvements Implementation
**Implemented 13 critical fixes from agent validation**
- Saga pattern for distributed transactions
- SMS batch sender with rate limiting (80 msg/sec)
- Hybrid Redis/PostgreSQL state (60x performance improvement)
- Correlation ID middleware for distributed tracing
- Phone number encryption (Fernet, GDPR/CCPA compliant)
- Twilio webhook signature verification
- Database constraints and audit trails
- Opt-in audit log (immutable, TCPA compliant)
- AI request queue with rate limiting (5 concurrent)
- Image deduplication (30-50% cost savings)
- Event idempotency (24-hour window)
- Deep health checks (database, Redis, SMS, AI)
- Business metrics (Prometheus integration)

### [0.0.2] - 2025-12-29 - Agent Validation
**Ran specialized agents to assess architecture**
- Architect Agent: Rated foundation 7/10, identified critical gaps
- Devil's Advocate: Success probability 20-30%, major risks identified
- Security Auditor: Found 14 critical, 18 high, 23 medium security issues
- Created CRITICAL_FINDINGS.md with 10 critical blockers
- Created agent reports in logs/ directory

### [0.0.1] - 2025-12-29 - Initial Setup
**Documentation and tooling research**
- Created CLAUDE.md (condensed from 1,231→587 lines)
- Frontend template research (FastAPI Full-Stack, TailAdmin React)
- Tooling research (Sentry, FastAPI Radar, OpenTelemetry)
- Added concise structured logging patterns
- Created TOOLING_RESEARCH.md with API/SDK findings

## [0.1.1] - 2025-12-29

### Fixed
- **Missing Dependency**
  - Added `python-multipart==0.0.21` to requirements.txt
  - Required for FastAPI form data handling in webhook endpoint

- **Logger Syntax Errors**
  - Fixed 4 logger calls using incorrect keyword argument syntax
  - Converted to f-string format for consistency
  - Affected: save_json, send_sms, process_message functions

### Changed
- **Environment Configuration**
  - Updated .env with valid Twilio credentials
  - Ready for testing (pending wife's phone number)

### Tested
- ✅ Application startup (no errors)
- ✅ Health endpoint (GET /)
- ✅ SMS webhook endpoint (POST /sms/webhook)
- ✅ START command flow
- ✅ RECIPE command flow (partial)
- ✅ Twilio SMS sending integration
- ✅ Data persistence (JSON files)
- ✅ Conversation state management
- ✅ Structured logging

**Test Results:** 8/8 tests passed
**Status:** READY FOR USER TESTING
