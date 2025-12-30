# Jules Testing Quick Reference Card

**Quick commands and checklists for daily testing work**

---

## 🚀 Quick Start Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/ -m unit                    # Unit tests only
pytest tests/ -m integration             # Integration tests
pytest tests/ -m compliance              # Compliance tests
pytest tests/ -m red_team                # Red team tests
pytest tests/ -m crisis                  # Crisis detection tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Run specific file
pytest tests/test_compliance_service.py -v
pytest tests/red_team/test_security.py -v
pytest tests/integration/test_crisis_flow.py -v

# Run single test
pytest tests/test_compliance_service.py::TestAIDisclosure::test_ai_disclosure_on_session_start -vv

# Watch mode (auto-run on file changes)
pytest-watch tests/

# Parallel execution (faster)
pytest tests/ -n 4
```

---

## 📋 Test Categories

| Category | Command | Description |
|----------|---------|-------------|
| **Unit** | `pytest -m unit` | Fast, isolated tests (80%+ coverage) |
| **Integration** | `pytest -m integration` | Multi-service workflows |
| **E2E** | `pytest -m e2e` | Complete user journeys |
| **Red Team** | `pytest -m red_team` | Adversarial security/safety tests |
| **Compliance** | `pytest -m compliance` | Regulatory requirement tests |
| **Crisis** | `pytest -m crisis` | Crisis detection (CRITICAL) |
| **Safety** | `pytest -m safety` | Safety and content moderation |

---

## ✅ Critical Tests (Must Pass Before Launch)

```bash
# Crisis detection (ZERO false negatives allowed)
pytest tests/integration/test_crisis_flow.py::TestCrisisDetectionFlow::test_suicide_keyword_detection_988_response -v

# AI disclosure compliance (NY law)
pytest tests/integration/test_compliance_flows.py::TestAIDisclosureFlow -v

# Opt-out compliance (TCPA)
pytest tests/integration/test_compliance_flows.py::TestOptOutFlow::test_stop_keyword_immediate_opt_out -v

# Age verification (CA SB 243)
pytest tests/integration/test_compliance_flows.py::TestAgeVerificationFlow::test_minor_age_verification_required -v

# Security red team (all attacks blocked)
pytest tests/red_team/test_security.py -v

# Safety red team (boundaries maintained)
pytest tests/red_team/test_safety.py -v
```

---

## 🎯 Coverage Commands

```bash
# Check current coverage
pytest tests/ --cov=src --cov-report=term

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Show missing lines
pytest tests/ --cov=src --cov-report=term-missing

# Fail if coverage < 80%
pytest tests/ --cov=src --cov-fail-under=80

# Coverage for specific module
pytest tests/test_compliance_service.py --cov=src.services.compliance_service
```

---

## 🔧 Development Commands

```bash
# Run tests with verbose output
pytest tests/ -vv

# Run tests with print statements
pytest tests/ -s

# Run tests with debugging
pytest tests/ --pdb

# Run only failed tests from last run
pytest tests/ --lf

# Run failed tests first, then rest
pytest tests/ --ff

# Stop on first failure
pytest tests/ -x

# Run tests matching keyword
pytest tests/ -k "crisis"
pytest tests/ -k "compliance and ai_disclosure"
```

---

## 🏥 Health Checks

```bash
# Check test environment
pytest tests/ --collect-only

# Verify test databases
docker-compose ps postgres-test redis

# Test database connection
docker-compose exec postgres-test psql -U test -d jules_test -c "SELECT 1"

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check API health
curl http://localhost:8000/health
```

---

## 📊 Compliance Checklist (Pre-Launch)

### Safety & Compliance
- [ ] Crisis detection: 100% accuracy ✅ `pytest -m crisis`
- [ ] 988 hotline: Always provided
- [ ] AI disclosure: Session start + 3-hour ✅ `pytest -m compliance`
- [ ] STOP keyword: Immediate processing
- [ ] Age verification: Required before SMS
- [ ] Minor content: Blocked
- [ ] Crisis logging: Anonymous (SB 243)

### Red Team
- [ ] SQL injection: Blocked ✅ `pytest tests/red_team/test_security.py::TestSQLInjectionProtection`
- [ ] Prompt injection: Boundaries hold
- [ ] PII extraction: Failed
- [ ] API keys: Cannot extract
- [ ] Crisis evasion: Still detects ✅ `pytest tests/red_team/test_safety.py::TestCrisisDetectionEvasion`
- [ ] Therapy boundaries: Maintained

### Quality
- [ ] Conversation quality: ≥ 8.0/10
- [ ] Critical failures: < 3%
- [ ] Response brevity: 85%+ (140-250 chars)
- [ ] Response latency: p95 < 8s
- [ ] Dietary violations: 0%

---

## 🎨 Test File Locations

```
jules-backend/tests/
├── test_compliance_service.py          # 50+ compliance tests
├── test_sms_service.py                 # SMS tests
├── test_llm_service.py                 # LLM tests
├── test_crisis_service.py              # Crisis detection
├── test_conversation_service.py        # Conversation orchestration
├── test_api_webhooks.py                # API endpoints
│
├── integration/
│   ├── test_crisis_flow.py             # Crisis E2E (CRITICAL)
│   ├── test_compliance_flows.py        # Compliance E2E
│   ├── test_sms_integration.py         # SMS E2E (to create)
│   └── test_llm_quality.py             # LLM quality (to create)
│
├── e2e/
│   ├── test_onboarding.py              # User onboarding (to create)
│   └── test_conversations.py           # Core conversations (to create)
│
├── red_team/
│   ├── test_security.py                # 50+ security attacks
│   └── test_safety.py                  # 40+ safety scenarios
│
└── quality/
    └── test_conversation_quality.py    # 1,360+ scenarios (to adapt)
```

---

## 💡 Common Test Patterns

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_something(db_session):
    result = await async_function()
    assert result is not None
```

### Testing with Fixtures
```python
async def test_with_user(db_session, user_service):
    user = await user_service.create_user(...)
    assert user.id is not None
```

### Testing Exceptions
```python
async def test_raises_exception(db_session):
    with pytest.raises(ValueError):
        await function_that_raises()
```

### Mocking External APIs
```python
@patch('src.services.llm_service.Anthropic')
async def test_with_mock(mock_anthropic):
    mock_anthropic.return_value.messages.create.return_value = ...
    result = await llm_service.generate_response(...)
```

---

## 🐛 Debugging Tests

```bash
# Run with verbose output
pytest tests/test_file.py -vv

# Run with print statements visible
pytest tests/test_file.py -s

# Run with debugger (drops into pdb on failure)
pytest tests/test_file.py --pdb

# Run with debugger on errors only
pytest tests/test_file.py --pdbcls=IPython.terminal.debugger:Pdb

# Show local variables on failure
pytest tests/test_file.py -l

# Show full diff on assertion errors
pytest tests/test_file.py -vv
```

---

## 📈 CI/CD Integration

### GitHub Actions (Automated)
```yaml
# .github/workflows/test.yml runs automatically:
- Unit tests on every push
- Integration tests on PRs
- Coverage checks (≥80%)
- Red team tests before merge to main
```

### Manual CI Commands
```bash
# Run full CI test suite locally
pytest tests/ -v --cov=src --cov-fail-under=80

# Run security tests (red team)
pytest tests/red_team/ -v -m red_team

# Run compliance tests
pytest tests/ -v -m compliance
```

---

## 🎯 Phase-Specific Commands

### Phase 1: Foundation (Week 1-2)
```bash
# Run unit tests
pytest tests/ -m unit --cov=src --cov-fail-under=80

# Specific services
pytest tests/test_compliance_service.py -v
pytest tests/test_memory_service.py -v
pytest tests/test_moderation.py -v
```

### Phase 2: Integration (Week 3-4)
```bash
# Run integration tests
pytest tests/integration/ -v

# Critical crisis flow
pytest tests/integration/test_crisis_flow.py -v -m crisis

# Compliance workflows
pytest tests/integration/test_compliance_flows.py -v -m compliance
```

### Phase 4: Red Team (Week 9-12)
```bash
# Run all red team tests
pytest tests/red_team/ -v -m red_team

# Security only
pytest tests/red_team/test_security.py -v

# Safety only
pytest tests/red_team/test_safety.py -v
```

---

## 📝 Quick Notes

### Test Markers
- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.unit` - Unit test
- `@pytest.mark.integration` - Integration test
- `@pytest.mark.red_team` - Red team test
- `@pytest.mark.compliance` - Compliance test
- `@pytest.mark.crisis` - Crisis detection test

### Coverage Goals
- **Unit tests:** 80%+ required
- **Integration tests:** 100% of critical flows
- **E2E tests:** 100% of user journeys
- **Red team:** 100% before launch

### Success Criteria
- Crisis detection: 100% accuracy (zero false negatives)
- Dietary safety: 0% violations
- Response latency: p95 < 8 seconds
- Conversation quality: ≥ 8.0/10 average
- Critical failures: < 3%

---

## 🆘 Help

```bash
# Get help on pytest
pytest --help

# Get help on markers
pytest --markers

# List all tests
pytest --collect-only

# List tests matching keyword
pytest --collect-only -k "crisis"

# Show pytest version
pytest --version

# Show installed plugins
pytest --version --version
```

---

**For detailed information, see:**
- `TESTING_STRATEGY.md` - Complete testing plan
- `TESTING_IMPLEMENTATION_GUIDE.md` - Implementation guide
- `TESTING_SYSTEM_COMPLETE.md` - System summary

**Status:** ✅ Ready for Implementation
