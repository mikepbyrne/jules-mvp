# Jules MVP - Claude AI Integration & Cost Monitoring

**Current Status:** AI features disabled (MVP uses manual text entry)
**When to Enable:** After validating core SMS workflow with manual entry

---

## Getting Your Anthropic API Key

### Step 1: Create Anthropic Account
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to **API Keys** section

### Step 2: Generate API Key
1. Click **Create Key**
2. Name it: "Jules MVP - Development"
3. Copy the key (starts with `sk-ant-...`)
4. **Save it securely** - you won't see it again

### Step 3: Add to Jules
Edit `/Users/crucial/Documents/dev/Jules/jules-mvp/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...  # Your actual key
ENABLE_AI_FEATURES=true                    # Enable AI processing
```

---

## Cost Structure

### Claude API Pricing (as of Dec 2025)

**Claude 3.5 Sonnet (Recommended):**
- Input: $3 per million tokens (~750K words)
- Output: $15 per million tokens (~750K words)
- Vision: $4.80 per million tokens (for recipe image analysis)

### Estimated Costs for Jules MVP

#### Scenario 1: Recipe Extraction Only
**Usage:** 10 recipe photos/week
- Average tokens per extraction: 2,000 input + 1,000 output + 3,000 vision
- Cost per recipe: ~$0.03
- **Monthly cost: ~$1.20** (40 recipes)

#### Scenario 2: Recipe + Meal Suggestions
**Usage:** 10 recipes/week + daily meal suggestions
- Recipes: $1.20/month (from above)
- Meal suggestions: 30 requests/month × 1,500 tokens × $0.003 = $0.135
- **Monthly cost: ~$1.35**

#### Scenario 3: Heavy Usage (2 households)
**Usage:** 20 recipes/week + 60 meal suggestions/month
- Recipes: $2.40/month
- Suggestions: $0.27/month
- **Monthly cost: ~$2.70**

### Comparison to Budget

**Total Jules Testing Budget:**
- Twilio SMS: $2.50/month
- Claude API: $1.50/month (estimated)
- **Total: ~$4/month** for 2-person testing

**Much cheaper than alternatives:**
- ChatGPT API (GPT-4 Turbo): ~2x more expensive
- Google Vertex AI: Similar pricing but less capable for recipes
- OpenAI GPT-4V: $10 per million input tokens (3x more)

---

## Cost Monitoring & Alerts

### Built-in Safety Limits

Jules includes automatic cost controls:

```bash
# .env configuration
AI_COST_ALERT_THRESHOLD=10.00      # Alert if monthly cost exceeds $10
AI_REQUEST_LIMIT_PER_DAY=100       # Max 100 AI requests per day
```

### Monitoring via Anthropic Console

1. Go to https://console.anthropic.com/settings/usage
2. View real-time usage:
   - Tokens consumed
   - Cost breakdown by day/week/month
   - API call counts

3. Set billing alerts:
   - Settings → Billing → Usage Limits
   - Set monthly spending cap: $10
   - Email alerts at 50%, 75%, 90%

### Track Costs in Jules Data

Jules will log AI usage to `data/ai_usage.json`:
```json
{
  "2025-12": {
    "total_requests": 45,
    "total_tokens": 135000,
    "estimated_cost": 0.85,
    "by_feature": {
      "recipe_extraction": {
        "requests": 12,
        "cost": 0.36
      },
      "meal_suggestions": {
        "requests": 33,
        "cost": 0.49
      }
    }
  }
}
```

---

## When to Add AI Features

### Phase 1: Manual Entry (NOW)
**Current MVP state:**
- ✅ Manual text entry for recipes
- ✅ SMS commands for meal planning
- ✅ No AI costs
- 🎯 **Goal:** Validate workflow with 2 users

**Duration:** 2-4 weeks of testing

### Phase 2: Add Recipe Extraction (LATER)
**When to enable:**
- ✓ Manual entry workflow is validated
- ✓ You're using Jules regularly
- ✓ Wife is also using it
- ✓ Typing recipes is annoying

**To enable:**
1. Get Anthropic API key
2. Add to `.env`
3. Set `ENABLE_AI_FEATURES=true`
4. Restart Jules app

**New capability:** Text a photo of a recipe card → Jules extracts it automatically

### Phase 3: AI Meal Suggestions (EVEN LATER)
**When to enable:**
- ✓ Recipe extraction is working well
- ✓ You have 20+ recipes in collection
- ✓ Want smarter meal suggestions

**New capability:** "SUGGEST" command → Claude analyzes your recipes and suggests optimal weekly plan

---

## API Integration Code (Future)

When you're ready to enable AI, here's what gets added to `app.py`:

```python
import anthropic
from anthropic import AsyncAnthropic

# Initialize client
if os.getenv("ENABLE_AI_FEATURES") == "true":
    anthropic_client = AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
else:
    anthropic_client = None

async def extract_recipe_from_image(image_url: str) -> dict:
    """Extract recipe from photo using Claude Vision"""
    if not anthropic_client:
        return {"error": "AI features not enabled"}

    try:
        response = await anthropic_client.messages.create(
            model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", 4096)),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": """Extract this recipe. Return JSON with:
                        - title
                        - ingredients (array of {quantity, unit, item})
                        - instructions (array of steps)
                        - prep_time (minutes)
                        - cook_time (minutes)
                        """
                    }
                ]
            }]
        )

        # Log usage for cost tracking
        log_ai_usage(
            feature="recipe_extraction",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )

        return json.loads(response.content[0].text)

    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {"error": str(e)}

def log_ai_usage(feature: str, input_tokens: int, output_tokens: int):
    """Track AI usage and costs"""
    # Load usage data
    usage_file = DATA_DIR / "ai_usage.json"
    if usage_file.exists():
        with open(usage_file) as f:
            usage = json.load(f)
    else:
        usage = {}

    # Current month
    month = datetime.now().strftime("%Y-%m")
    if month not in usage:
        usage[month] = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost": 0.0,
            "by_feature": {}
        }

    # Calculate cost (Claude 3.5 Sonnet pricing)
    input_cost = (input_tokens / 1_000_000) * 3.00
    output_cost = (output_tokens / 1_000_000) * 15.00
    total_cost = input_cost + output_cost

    # Update totals
    usage[month]["total_requests"] += 1
    usage[month]["total_input_tokens"] += input_tokens
    usage[month]["total_output_tokens"] += output_tokens
    usage[month]["estimated_cost"] += total_cost

    # Update feature breakdown
    if feature not in usage[month]["by_feature"]:
        usage[month]["by_feature"][feature] = {
            "requests": 0,
            "cost": 0.0
        }
    usage[month]["by_feature"][feature]["requests"] += 1
    usage[month]["by_feature"][feature]["cost"] += total_cost

    # Save
    with open(usage_file, 'w') as f:
        json.dump(usage, f, indent=2)

    # Check alert threshold
    threshold = float(os.getenv("AI_COST_ALERT_THRESHOLD", 10.00))
    if usage[month]["estimated_cost"] > threshold:
        logger.warning(f"AI cost alert: ${usage[month]['estimated_cost']:.2f} exceeds ${threshold:.2f}")

    logger.info(f"AI usage: {feature} - {input_tokens}in + {output_tokens}out = ${total_cost:.4f}")
```

---

## Cost Optimization Tips

### 1. Use Caching (Future Enhancement)
```python
# Cache identical requests for 24 hours
# If user sends same image twice, use cached result
# Saves ~100% on duplicate requests
```

### 2. Prompt Optimization
- Keep prompts concise
- Use structured output (JSON)
- Avoid unnecessary examples in prompts
- **Savings:** ~30% fewer tokens

### 3. Model Selection
- Use Haiku for simple tasks (20x cheaper)
- Use Sonnet for complex tasks (current choice)
- Use Opus only if needed (3x more expensive)

**Example savings:**
- Recipe name extraction: Use Haiku → $0.001 vs $0.003
- Full recipe with vision: Use Sonnet → $0.03 (good balance)

### 4. Batch Processing
- Process multiple recipes in one request when possible
- **Savings:** Reduces API call overhead

### 5. Rate Limiting
```bash
AI_REQUEST_LIMIT_PER_DAY=100  # Prevents runaway costs
```

---

## Testing AI Integration (When Ready)

### Before Adding API Key
1. Ensure manual entry workflow is solid
2. Have 10+ recipes entered manually
3. Both users comfortable with SMS interface
4. Ready to spend ~$1-2/month on AI

### After Adding API Key
1. Test with 1 recipe photo
2. Verify extraction accuracy
3. Check `data/ai_usage.json` for cost tracking
4. Monitor Anthropic console for usage
5. Gradually increase usage

### Warning Signs to Watch
- ⚠️ Costs exceeding $5/month (MVP should be <$2)
- ⚠️ Extraction accuracy below 80%
- ⚠️ More than 5 retries needed per image
- ⚠️ Users frustrated with AI results

---

## API Key Security

### Best Practices
✅ **DO:**
- Store in `.env` file (gitignored)
- Use environment variables
- Rotate keys periodically
- Set spending limits in Anthropic console
- Use separate keys for dev/prod

❌ **DON'T:**
- Commit API keys to git
- Share keys in messages/emails
- Use same key across multiple projects
- Store in code files
- Leave in logs

### If Key is Compromised
1. Go to https://console.anthropic.com/settings/keys
2. Delete compromised key
3. Generate new key
4. Update `.env` file
5. Check billing for unexpected usage

---

## Current State Summary

### What's Configured
- ✅ `.env` has placeholder for Anthropic API key
- ✅ AI features disabled by default
- ✅ Cost tracking variables set
- ✅ Safety limits defined

### What You Need to Do (Later)
1. Create Anthropic account
2. Generate API key
3. Add to `.env`
4. Enable AI features
5. Test with one recipe photo

### Recommendation
**Wait 2-4 weeks** before enabling AI:
- Validate manual workflow first
- Ensure you'll actually use it
- Avoid paying for AI you might not need
- Start simple, add complexity when proven valuable

---

## Cost Comparison: Manual vs AI

### Manual Entry (Current MVP)
- **Cost:** $0/month for recipe entry
- **Time:** 2-3 minutes per recipe
- **Accuracy:** 100% (you type it correctly)
- **Best for:** Starting out, low volume

### AI Extraction (Future)
- **Cost:** $0.03 per recipe
- **Time:** 30 seconds per recipe
- **Accuracy:** 85-95% (may need minor edits)
- **Best for:** High volume, convenience

### Break-Even Analysis
- Manual time value: $30/hour ÷ 60 min = $0.50/min
- Manual entry: 3 min × $0.50 = $1.50 value
- AI cost: $0.03
- **Savings:** $1.47 per recipe in time value

**Conclusion:** AI becomes cost-effective after ~10 recipes/month

---

## Next Steps

### Immediate (MVP Testing)
- [ ] Keep AI features disabled
- [ ] Test manual entry workflow
- [ ] Use for 2-4 weeks
- [ ] Validate core concept

### Phase 2 (If MVP Succeeds)
- [ ] Create Anthropic account
- [ ] Generate API key
- [ ] Add to `.env`
- [ ] Test with 1 recipe photo
- [ ] Monitor costs
- [ ] Decide if worth continuing

### Phase 3 (If AI Extraction Works)
- [ ] Add meal suggestion features
- [ ] Implement caching
- [ ] Optimize prompts
- [ ] Track ROI

---

## Support Resources

**Anthropic Documentation:**
- API Reference: https://docs.anthropic.com/claude/reference
- Pricing: https://www.anthropic.com/api#pricing
- Best Practices: https://docs.anthropic.com/claude/docs/best-practices

**Jules AI Integration:**
- This file (AI_SETUP.md)
- `data/ai_usage.json` (cost tracking)
- Application logs: `logs/app.log`

**Questions?**
- Check Anthropic console for real-time usage
- Review `data/ai_usage.json` for Jules-specific tracking
- Monitor email for billing alerts

---

**Current Status:** Ready to add API key when you're ready
**Monthly Budget:** ~$1.50 estimated (well under $10 safety limit)
**Recommendation:** Wait until manual workflow is validated
