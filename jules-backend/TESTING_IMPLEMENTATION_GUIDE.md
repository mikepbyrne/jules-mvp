# Jules Backend Testing Implementation Guide
## Quick Start for Modular Sequential Testing

**Status:** Ready to Begin
**Timeline:** 6-8 weeks (parallel with development)
**Based on:** Compass artifact recommendations + TESTING system methodology

---

## Quick Start (Day 1)

### 1. Review Strategy
```bash
cd jules-backend
cat TESTING_STRATEGY.md
```

**Key Documents:**
- `TESTING_STRATEGY.md` - Complete testing plan
- `tests/test_compliance_service.py` - Compliance test templates
- `tests/red_team/test_security.py` - Security red team tests
- `tests/red_team/test_safety.py` - Safety red team tests

### 2. Set Up Testing Environment
```bash
# Install test dependencies
poetry add --dev pytest pytest-asyncio pytest-cov pytest-mock httpx faker

# Start test databases
docker-compose up postgres-test redis -d

# Verify test environment
pytest tests/ --collect-only
```

### 3. Run Existing Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Phase 1: Foundation Tests (Week 1-2)

### Goal: 80%+ Unit Test Coverage

**Priority Order:**
1. ✅ **Existing tests validated** (SMS, LLM, Crisis, Conversation, API)
2. 🔨 **Add compliance tests** (`test_compliance_service.py`)
3. 🔨 **Add memory tests** (`test_memory_service.py`)
4. 🔨 **Add moderation tests** (`test_moderation.py`)
5. 🔨 **Complete user service tests** (age verification, PII encryption)

### Implementation Steps

#### Step 1: Complete Compliance Tests
```bash
# File: tests/test_compliance_service.py (already created)

# Implement compliance service
touch src/services/compliance_service.py

# Key methods to implement:
# - should_send_ai_disclosure() - 3-hour NY law
# - process_opt_out_request() - TCPA STOP
# - can_enable_conversation() - Age verification
# - record_consent() - Express consent tracking
# - log_crisis_referral() - SB 243 2027 reporting

# Run compliance tests
pytest tests/test_compliance_service.py -v
```

#### Step 2: Add Memory Tests
```python
# tests/test_memory_service.py

async def test_conversation_context_limit():
    """Keep recent 5-10 messages (~1,500 tokens)"""
    # Compass: "keep recent 5-10 messages in context (~1,500 tokens)"

async def test_redis_session_ttl():
    """4-hour active session TTL"""
    # Compass: "Redis caching for active sessions (4-hour TTL)"

async def test_preference_persistence():
    """Store user preferences in PostgreSQL"""
    # Compass: "store user preferences in structured PostgreSQL fields"
```

#### Step 3: Add Moderation Tests
```python
# tests/test_moderation.py

async def test_openai_moderation_api():
    """Compass: OpenAI's free Moderation API provides baseline content filtering"""

async def test_content_filtering():
    """Test sexual content, hate speech, violence detection"""

async def test_manipulation_detection():
    """SB 243: Anti-manipulation design"""
```

### Success Criteria
- [ ] 80%+ code coverage
- [ ] All existing tests passing
- [ ] Compliance tests passing (AI disclosure, opt-out, consent)
- [ ] Memory tests passing (context limits, Redis TTL)
- [ ] Moderation tests passing (OpenAI API integration)

---

## Phase 2: Integration Tests (Week 3-4)

### Goal: Critical Flows End-to-End

**Priority Order:**
1. 🚨 **Crisis detection flow** (CRITICAL - safety)
2. 📋 **Compliance workflows** (AI disclosure, opt-out, age verification)
3. 📱 **SMS integration** (Bandwidth webhooks, rate limiting)
4. 🤖 **LLM quality** (latency, fallback, context limits)

### Implementation Steps

#### Step 1: Crisis Detection Flow
```python
# tests/integration/test_crisis_flow.py

async def test_suicide_keyword_detection():
    """Verify crisis detection triggers 988 hotline response"""
    # MUST pass - zero tolerance for false negatives

async def test_crisis_response_immediate():
    """Crisis responses < 5 seconds"""
    # Compass: "3-8 seconds total response time"

async def test_crisis_logging_anonymized():
    """SB 243: Anonymous crisis logging for 2027 reporting"""
```

#### Step 2: Compliance Workflows
```python
# tests/integration/test_compliance_flows.py

async def test_ai_disclosure_session_start():
    """NY law: AI disclosure at session start"""

async def test_ai_disclosure_3_hour_reminder():
    """NY law: AI disclosure every 3 hours"""

async def test_opt_out_immediate_processing():
    """TCPA: STOP keyword immediately halts messaging"""

async def test_minor_age_verification_required():
    """SB 243: Age verification before enabling SMS"""
```

#### Step 3: SMS Integration
```python
# tests/integration/test_bandwidth_sms.py

async def test_sms_rate_limiting():
    """TCPA: Respect 8 AM-9 PM local time restrictions"""

async def test_sms_delivery_retry_logic():
    """Tenacity + circuit breaker for failed delivery"""

async def test_mms_image_compression():
    """Compress to 500KB-1MB carrier limits"""
```

#### Step 4: LLM Quality
```python
# tests/integration/test_llm_quality.py

async def test_response_latency_under_8_seconds():
    """Compass: 3-8 seconds acceptable for SMS"""

async def test_claude_haiku_fallback_to_openai():
    """Test LLM provider failover"""

async def test_conversation_context_token_limit():
    """Keep recent 5-10 messages (~1,500 tokens)"""
```

### Success Criteria
- [ ] Crisis detection: 100% accuracy (zero false negatives)
- [ ] AI disclosure: Triggered at correct intervals
- [ ] Opt-out: Immediate processing of STOP
- [ ] Age verification: Blocks unverified users
- [ ] SMS rate limiting: Respects TCPA hours
- [ ] LLM latency: p95 < 8 seconds

---

## Phase 3: E2E Tests (Week 5-6)

### Goal: Complete User Journeys

**Priority Order:**
1. 👋 **Onboarding flow** (new user → verified → active)
2. 🍽️ **Core conversations** (meal planning, dietary safety)
3. 💰 **Budget sensitivity** (appropriate suggestions)
4. ⚠️ **Safety scenarios** (crisis, dietary violations)

### Implementation Steps

#### Step 1: Onboarding Flow
```python
# tests/e2e/test_onboarding.py

async def test_new_user_first_message():
    """Complete onboarding: SMS → AI disclosure → age verify → active"""

async def test_age_verification_complete_flow():
    """Veriff webhook → conversation enabled"""
```

#### Step 2: Core Conversations
```python
# tests/e2e/test_conversations.py

async def test_meal_planning_request():
    """User asks for dinner → receives 2-3 specific suggestions"""

async def test_dietary_restriction_safety():
    """CRITICAL: Verify dietary restrictions respected (zero violations)"""

async def test_budget_sensitivity():
    """Verify budget-appropriate suggestions for low-income users"""
```

### Success Criteria
- [ ] Onboarding: Complete flow < 5 messages
- [ ] Meal planning: 2-3 specific suggestions
- [ ] Dietary safety: 0% violation rate
- [ ] Budget sensitivity: No expensive items for low-income

---

## Phase 4: Red Team Tests (Week 9-12)

### Goal: Adversarial Validation Before Launch

**Based on Compass:** "Conduct adversarial testing (red teaming)"

### Implementation Steps

#### Step 1: Security Red Team
```bash
# Already created: tests/red_team/test_security.py

# Run security tests
pytest tests/red_team/test_security.py -v -m red_team

# Test areas:
# - SQL injection protection
# - LLM prompt injection
# - PII extraction attempts
# - API key extraction attempts
# - DoS resistance
# - Authentication bypass
```

#### Step 2: Safety Red Team
```bash
# Already created: tests/red_team/test_safety.py

# Run safety tests
pytest tests/red_team/test_safety.py -v -m red_team

# Test areas:
# - Crisis keyword evasion
# - Therapy boundary violations
# - Fake human experiences
# - Emotional manipulation
# - Minor protection
# - Content moderation
```

#### Step 3: Document Findings
```markdown
# red_team_report.md

## Security Findings
- SQL injection: ✅ Protected
- Prompt injection: ⚠️ Needs improvement
- PII extraction: ✅ Blocked

## Safety Findings
- Crisis detection: ✅ 100% accuracy
- Therapy boundaries: ✅ Maintained
- Minor protection: ✅ Active

## Recommendations
1. Strengthen prompt injection defenses
2. Add semantic crisis detection (implicit signals)
3. ...
```

### Success Criteria
- [ ] Security: All attacks blocked
- [ ] Safety: Crisis detection 100% accurate
- [ ] Boundaries: No therapy/medical advice
- [ ] Minor protection: Sexual content blocked
- [ ] Report: Document all findings + fixes

---

## Phase 5: Quality Tests (Week 9-12)

### Goal: Conversation Quality Validation

**Adopt from TESTING/jules-mvp system**

### Implementation Steps

#### Step 1: Set Up Quality Testing Framework
```bash
# Copy from TESTING system
cp ../TESTING/jules-mvp/conversation_evaluator.py tests/quality/
cp ../TESTING/jules-mvp/test_conversation_simulator.py tests/quality/

# Adapt for backend (call via HTTP instead of direct)
```

#### Step 2: Run Quality Evaluation
```python
# tests/quality/test_conversation_quality.py

async def test_response_brevity_sms_appropriate():
    """85%+ responses within 140-250 chars"""

async def test_natural_conversation_tone():
    """Avg naturalness score ≥ 8.0/10"""

async def test_no_fake_human_experiences():
    """Zero fake human experience phrases"""

async def test_quality_dimensions_all_scenarios():
    """Run 1,360+ diversity scenarios from TESTING system"""
    # This is the comprehensive test suite
```

#### Step 3: Analyze Results
```bash
# Run comprehensive testing
pytest tests/quality/ -v

# Generate quality report
python tests/quality/analyze_results.py > quality_report.md
```

### Success Criteria
- [ ] Average quality: ≥ 8.0/10
- [ ] Brevity: 85%+ within 140-250 chars
- [ ] Critical failures: < 3%
- [ ] Diversity scenarios: 1,360+ tested
- [ ] Safety: 100% (dietary, crisis, budget)

---

## Pre-Launch Checklist (Week 12)

### Safety & Compliance (CRITICAL)
- [ ] Crisis detection: 100% accuracy (tested with 50+ variations)
- [ ] 988 hotline: Always provided for crisis messages
- [ ] AI disclosure: Session start + 3-hour intervals
- [ ] STOP keyword: Immediate opt-out processing
- [ ] Age verification: Required before SMS enabled
- [ ] Minor content blocking: Sexual content blocked
- [ ] Crisis logging: Anonymous tracking for 2027 reporting
- [ ] Safety protocols: Published on website

### Red Team Validation
- [ ] SQL injection: All attempts blocked
- [ ] Prompt injection: Boundaries hold
- [ ] PII extraction: All attempts fail
- [ ] API keys: Cannot be extracted
- [ ] Crisis evasion: Still triggers detection
- [ ] Therapy boundaries: Maintained
- [ ] Grooming patterns: Detected (if applicable)

### Quality Metrics
- [ ] Average conversation quality: ≥ 8.0/10
- [ ] Critical failure rate: < 3%
- [ ] Response brevity: 85%+ within 140-250 chars
- [ ] Response latency: p95 < 8 seconds
- [ ] Dietary violations: 0%
- [ ] Budget insensitivity: 0%

### Infrastructure
- [ ] 10DLC registration: Complete
- [ ] Bandwidth production: Configured + tested
- [ ] Veriff production: Integrated + tested
- [ ] Stripe webhooks: Configured + tested
- [ ] Sentry monitoring: Active + tested
- [ ] Langfuse LLM tracking: Active + tested
- [ ] Database backups: Automated + verified
- [ ] SSL/TLS certificates: Valid + tested

### Documentation
- [ ] Test plan: Complete (TESTING_STRATEGY.md)
- [ ] Red team report: Complete with findings
- [ ] Quality report: Complete with scores
- [ ] Cost analysis: Within $125-200/month budget
- [ ] Safety protocols: Published publicly
- [ ] Incident response: Playbook ready

---

## Running Tests

### Local Development
```bash
# All tests
pytest tests/ -v

# Specific category
pytest tests/integration/ -v
pytest tests/e2e/ -v
pytest tests/red_team/ -v -m red_team

# With coverage
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80

# Watch mode (during development)
pytest-watch tests/
```

### CI/CD Pipeline
```bash
# GitHub Actions automatically runs:
# - Unit tests on every push
# - Integration tests on PRs
# - Coverage checks (must be ≥80%)

# View results at:
# https://github.com/[username]/jules-backend/actions
```

### Staging Environment
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run E2E tests against staging
TEST_ENV=staging pytest tests/e2e/ -v

# Run load tests
locust -f tests/load/locustfile.py
```

---

## Cost Monitoring

### Track During Testing
```python
# tests/cost_monitoring/test_costs.py

async def test_daily_llm_cost_100_users():
    """Verify stays within budget: $25-45/month (Haiku)"""

async def test_daily_sms_cost_100_users():
    """Verify stays within budget: ~$33/month (Bandwidth)"""

async def test_total_cost_per_user():
    """Total cost per user < $2/month"""
```

### Monitor in Production
```bash
# Langfuse dashboard: LLM token usage + cost
# Bandwidth dashboard: SMS message count + cost
# Combined: Should stay $125-200/month for 100 users
```

---

## Troubleshooting

### Tests Failing
```bash
# Check test database
docker-compose logs postgres-test

# Check Redis
docker-compose logs redis

# Run single test with verbose output
pytest tests/test_compliance_service.py::TestAIDisclosure::test_ai_disclosure_on_session_start -vv

# Debug with breakpoint
# Add: import pdb; pdb.set_trace()
pytest tests/test_compliance_service.py -s
```

### Low Coverage
```bash
# Identify uncovered code
pytest --cov=src --cov-report=term-missing

# Focus on uncovered files
pytest tests/test_[uncovered_module].py --cov=src.[uncovered_module]
```

### Integration Tests Timeout
```bash
# Increase timeout
pytest tests/integration/ --timeout=300

# Run with more workers (parallel)
pytest tests/integration/ -n 4
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Review TESTING_STRATEGY.md
2. ✅ Review test templates (compliance, red_team)
3. 🔨 Set up test environment (poetry, docker-compose)
4. 🔨 Run existing tests, verify passing
5. 🔨 Begin Phase 1: Foundation tests

### Week 1-2: Foundation
- Complete compliance service tests
- Add memory service tests
- Add moderation tests
- Achieve 80%+ coverage

### Week 3-4: Integration
- Implement crisis detection flow
- Implement compliance workflows
- Test SMS integration
- Test LLM quality

### Week 5-6: E2E
- Test onboarding flow
- Test core conversations
- Test safety scenarios

### Week 9-12: Red Team + Quality
- Run security red team
- Run safety red team
- Document findings
- Run 1,360+ quality scenarios
- Complete pre-launch checklist

---

## Resources

### Documentation
- `TESTING_STRATEGY.md` - Complete testing plan
- `DEPLOYMENT.md` - Production deployment guide
- `README.md` - Backend overview

### Test Files
- `tests/test_compliance_service.py` - Compliance tests
- `tests/red_team/test_security.py` - Security red team
- `tests/red_team/test_safety.py` - Safety red team
- `tests/conftest.py` - Test fixtures
- `tests/test_*.py` - Existing unit tests

### External Resources
- Compass artifact: `/compass_artifact_*.md`
- TESTING system: `../TESTING/jules-mvp/`
- Pytest docs: https://docs.pytest.org/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/

---

**Status:** ✅ Ready to Begin Testing Implementation
**Estimated Timeline:** 6-8 weeks (parallel with development)
**Success Criteria:** All pre-launch checklist items completed
**Go/No-Go:** Launch requires 100% pass on safety + compliance tests
