# Jules MVP - Cost Monitoring Dashboard

**Purpose:** Track and control costs for Twilio SMS + Claude AI

---

## Current Configuration ✅

### API Keys Configured
- ✅ **Twilio:** AC[your_account_sid]
- ✅ **Anthropic (Claude):** ysk-ant-api03-... (configured)

### AI Status
- **Enabled:** Currently `false` (AI features disabled for MVP)
- **Model:** Claude 3.5 Sonnet
- **Safety Limits:** $10/month threshold, 100 requests/day

---

## Monitoring Dashboards

### 1. Twilio Console
**URL:** https://console.twilio.com

**What to Monitor:**
- SMS sent/received count
- Current balance
- Usage by day/week/month

**Location:**
1. Dashboard → Usage
2. Billing → Current Period Usage

**Current Number:** +18664978083

### 2. Anthropic Console
**URL:** https://console.anthropic.com/settings/usage

**What to Monitor:**
- API calls count
- Tokens consumed (input/output)
- Estimated cost
- Daily/monthly usage graphs

**To Set Up Billing Alerts:**
1. Go to Settings → Billing
2. Set monthly spending limit: **$10**
3. Enable alerts at:
   - 50% ($5)
   - 75% ($7.50)
   - 90% ($9)

### 3. Jules Local Tracking
**File:** `data/ai_usage.json`

**What's Tracked:**
```json
{
  "2025-12": {
    "total_requests": 0,
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "estimated_cost": 0.00,
    "by_feature": {}
  }
}
```

**To View:**
```bash
cat data/ai_usage.json | python3 -m json.tool
```

---

## Cost Breakdown

### Monthly Budget: $6-8

| Service | Feature | Estimated Cost |
|---------|---------|----------------|
| **Twilio** | Phone number | $1.00/month |
| | SMS (200 msgs) | $1.58/month |
| | **Twilio Total** | **$2.58/month** |
| **Claude AI** | Recipe extraction (10/week) | $1.20/month |
| | Meal suggestions (30/month) | $0.15/month |
| | **AI Total (if enabled)** | **$1.35/month** |
| **Infrastructure** | Ngrok free tier | $0/month |
| | Local hosting | $0/month |
| | **Total Infrastructure** | **$0/month** |
| | | |
| **TOTAL (AI disabled)** | | **$2.58/month** |
| **TOTAL (AI enabled)** | | **$3.93/month** |

### Cost per User
- 2 users: **$2/month per person** (AI enabled)
- 4 users: **$1/month per person** (if scaled)

---

## Real-Time Monitoring

### Check Current Costs (Twilio)

```bash
# Using Twilio CLI (if installed)
twilio api:core:usage:records:all-time:list

# Or visit web console
open https://console.twilio.com/us1/billing/usage
```

### Check Current Costs (Claude)

**Web Console:**
```bash
open https://console.anthropic.com/settings/usage
```

**Expected to see:**
- Current month: $0.00 (AI features disabled)
- After enabling: ~$0.03 per recipe extraction

### Check Jules Local Tracking

```bash
# View AI usage
cat data/ai_usage.json | python3 -m json.tool

# Count recipes processed
ls -l data/recipes.json

# Check conversation state (how active)
cat data/conversation.json | python3 -m json.tool
```

---

## Cost Alerts & Safeguards

### Automatic Limits (Jules App)

**Daily Request Limit:**
```bash
# .env setting
AI_REQUEST_LIMIT_PER_DAY=100
```
- Jules will stop processing AI requests after 100/day
- Prevents runaway costs from bugs/loops
- Resets at midnight UTC

**Monthly Cost Alert:**
```bash
# .env setting
AI_COST_ALERT_THRESHOLD=10.00
```
- Jules logs warning when estimated monthly cost exceeds $10
- Check logs: `tail -f logs/app.log | grep "AI cost alert"`

### Anthropic Console Limits

**Set Hard Cap:**
1. Go to https://console.anthropic.com/settings/limits
2. Set "Monthly spend limit": **$10**
3. Requests will be rejected once limit hit
4. **Recommended:** Set to $10 for testing

**Email Alerts:**
- Enable in Settings → Notifications
- Get emails at 50%, 75%, 90% of limit

### Twilio Console Limits

**Set Hard Cap:**
1. Go to https://console.twilio.com/us1/billing/manage-billing/billing-settings
2. Set "Account spending limit": **$20**
3. Account suspended when hit (prevents bill shock)

---

## Usage Scenarios & Costs

### Scenario 1: MVP Testing (Current)
**AI Disabled, Manual Entry Only**
- Twilio: $2.58/month
- Claude: $0/month
- **Total: $2.58/month**

**Good for:**
- Initial 2-4 weeks testing
- Validating SMS workflow
- Learning the interface

### Scenario 2: AI Recipe Extraction Enabled
**10 recipe photos/week**
- Twilio: $2.58/month
- Claude: $1.20/month
- **Total: $3.78/month**

**Good for:**
- After manual entry validated
- High volume of new recipes
- Convenience worth $1.20/month

### Scenario 3: Full AI Features
**10 recipes/week + daily meal suggestions**
- Twilio: $2.58/month
- Claude: $1.35/month
- **Total: $3.93/month**

**Good for:**
- Regular active use
- Want intelligent suggestions
- Value time savings

### Scenario 4: Heavy Usage (2 Households)
**20 recipes/week + 60 suggestions/month**
- Twilio: $5/month
- Claude: $2.70/month
- **Total: $7.70/month**

**Still well under $10 safety limit**

---

## How to Monitor Effectively

### Daily (Quick Check)
```bash
# Check if app is running without errors
tail -20 logs/app.log

# Quick cost check (if AI enabled)
cat data/ai_usage.json | grep estimated_cost
```

### Weekly (Detailed Review)
1. **Twilio Console:**
   - Check SMS count vs. expected
   - Verify no unusual spikes
   - Current spend vs. budget

2. **Anthropic Console (if AI enabled):**
   - Review API call count
   - Check cost trend
   - Verify no errors/retries

3. **Jules Data:**
   - Count recipes added
   - Review conversation logs
   - Check for error patterns

### Monthly (Budget Review)
1. Compare actual to estimated:
   - Twilio bill
   - Anthropic bill
   - Total vs. $6-8 budget

2. Analyze usage patterns:
   - Are you using it regularly?
   - Is AI worth the cost?
   - Should you adjust limits?

3. Optimize if needed:
   - Disable AI if not using
   - Reduce request limits
   - Review which features are valuable

---

## Cost Optimization Tips

### 1. Start Without AI (Current State)
- **Savings:** $1.35/month
- Test manual entry for 2-4 weeks
- Only enable AI if manual is too tedious

### 2. Use AI Selectively
- Manual entry for simple recipes
- AI for complex handwritten recipes
- **Savings:** ~50% of AI costs

### 3. Batch Recipe Entry
- Take photos of multiple recipes
- Process once per week vs. daily
- **Savings:** Reduces overhead

### 4. Monitor and Adjust
```bash
# If costs too high, disable AI
ENABLE_AI_FEATURES=false

# Or reduce limits
AI_REQUEST_LIMIT_PER_DAY=20  # Down from 100
```

### 5. Use Correct Model
- Current: Claude 3.5 Sonnet (good balance)
- Cheaper: Claude 3.5 Haiku (for simple tasks)
- **Don't use:** Claude 3 Opus (3x more expensive)

---

## Warning Signs

### 🚨 Check Immediately If:
- Monthly cost exceeds $10
- More than 100 AI requests in one day
- Twilio bill exceeds $5/month
- Getting error emails from Anthropic or Twilio
- App logs show repeated failures/retries

### ⚠️ Review Soon If:
- Cost trending higher than expected
- Not using Jules regularly (wasting money)
- AI accuracy below 80% (paying for bad results)
- Finding manual entry faster than AI

---

## Getting Help

### Twilio Support
- **Console:** https://console.twilio.com/us1/support
- **Docs:** https://www.twilio.com/docs
- **Billing:** support@twilio.com

### Anthropic Support
- **Console:** https://console.anthropic.com
- **Docs:** https://docs.anthropic.com
- **Email:** support@anthropic.com

### Jules App Issues
- **Logs:** `tail -f logs/app.log`
- **Data:** Check `data/*.json` files
- **Reset:** Delete data files to start fresh

---

## Quick Reference Commands

```bash
# Check Twilio balance
curl -u YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN \
  https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Balance.json

# View Jules AI usage
cat data/ai_usage.json | python3 -m json.tool

# Count total recipes
cat data/recipes.json | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('recipes', [])))"

# Check if over daily limit (when AI enabled)
cat logs/app.log | grep "AI request limit"

# View today's costs
cat logs/app.log | grep "$(date +%Y-%m-%d)" | grep "AI usage"
```

---

## Current Status Summary

### Configured ✅
- Twilio API credentials
- Anthropic API key
- Cost tracking variables
- Safety limits set

### Monitoring Tools Ready ✅
- Twilio console access
- Anthropic console access
- Local JSON tracking
- Log monitoring

### Current Costs 💰
- **This month:** ~$0.50 (minimal testing)
- **Projected:** $2.58/month (AI disabled)
- **With AI:** $3.93/month (estimated)

### Recommendation 📊
**Keep AI disabled** for initial 2-4 week testing period. Enable only when:
- Manual workflow validated
- Using Jules regularly
- Typing recipes is annoying
- Ready to spend extra $1.35/month

---

**Last Updated:** December 29, 2025
**Monitoring Status:** Active
**Budget Status:** Well under limits ✅
