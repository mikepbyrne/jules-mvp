# Jules AI Meal Planning Assistant - Ready to Test! 🎉

**Status:** ✅ Running on port 8000
**Ngrok:** Active (webhook configured)
**AI:** Enabled (Claude Sonnet 4.5)
**Date:** December 29, 2025

---

## What's New

### Conversational Onboarding
Jules now has a natural, friendly onboarding flow that:
- Explains the knowledge base concept
- Collects household member information
- Gathers dietary restrictions (DEI-compliant)
- Sets clear expectations about MVP vs future features

### Natural Conversation Style
- No more "Reply YES to proceed" - now "Want to get started?"
- Feels like texting a friend, not filling out a form
- Flexible response handling (accepts yes/yeah/sure/ok etc.)
- Conversational tone throughout

### DEI-Compliant Member Collection
- Uses "household" not "family"
- Collects "people" not roles (mom/dad/etc.)
- Names first, no assumptions
- All dietary restrictions treated equally (cultural, religious, medical, ethical)
- Flexible age input (accepts numbers or "toddler", "baby", etc.)

---

## Current Capabilities

### NOW (MVP)
✅ Store family recipes
✅ Learn about household members
✅ Collect dietary restrictions
✅ Suggest meals from recipe collection
✅ Natural conversation with Claude AI

### COMING SOON (Explained during onboarding)
⏳ Learn pantry inventory over time
⏳ Smart grocery suggestions
⏳ Track household supplies (toilet paper, etc.)

---

## Test the Onboarding Flow

Text your Twilio number: **+18664978083**

### Complete Onboarding Conversation Example

```
You: Hi

Jules: Hi! I'm Jules, your AI meal planning assistant 👋

I help with recipes, meal planning, and eventually I'll learn what's in
your pantry to make smart suggestions.

Reply HI to get started, or STOP to opt out.

---

You: Hi

Jules: Awesome! Let me explain how this works.

I'm an AI that builds a knowledge base about YOUR household - your recipes,
who lives with you, dietary needs, and over time I'll learn what's in your pantry.

Your data stays private and you're in complete control.

Sound good so far?

---

You: Yeah sounds good

Jules: Great! Here's what I can do:

RIGHT NOW:
• Store your family recipes
• Learn about everyone in your household
• Suggest meals from your recipe collection

COMING SOON:
• Learn what's in your pantry over time
• Smart grocery suggestions
• Track household supplies

Want to get started?

---

You: Yes!

Jules: Perfect! Let's start by learning about your household.

How many people live with you?

(Just send me a number like 3 or 4)

---

You: 3

Jules: Nice - 3 people! Let's learn about everyone so I can suggest
meals that work for the whole household.

First person - what's their name?

---

You: Sarah

Jules: Nice to meet Sarah! How old are they?

(Helps me suggest age-appropriate meals)

---

You: 42

Jules: Got it! Any dietary restrictions for Sarah?

Like: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher...

Or just say 'none' if they eat everything!

---

You: Gluten-free, dairy-free

Jules: Perfect! Next person - what's their name?

---

You: Mike

Jules: Nice to meet Mike! How old are they?

(Helps me suggest age-appropriate meals)

---

You: 45

Jules: Got it! Any dietary restrictions for Mike?

Like: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher...

Or just say 'none' if they eat everything!

---

You: None

Jules: Perfect! Next person - what's their name?

---

You: Emma

Jules: Nice to meet Emma! How old are they?

(Helps me suggest age-appropriate meals)

---

You: 8

Jules: Got it! Any dietary restrictions for Emma?

Like: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher...

Or just say 'none' if they eat everything!

---

You: Peanut allergy

Jules: Perfect! Here's everyone:

• Sarah, 42 (gluten-free, dairy-free)
• Mike, 45
• Emma, 8 (peanut allergy)

Now I can suggest meals that work for your whole household!

Want to add your first recipe? Just tell me about a meal you all love.
```

---

## Key Features to Test

### 1. Natural Responses
Try responding naturally:
- "yeah that's cool" (should work)
- "sure!" (should work)
- "ok I guess" (should work)
- Not just "YES"

### 2. Flexible Input
- Ages: Try "8", "toddler", "baby", "42"
- Dietary: Try "none", "vegetarian", "gluten-free, dairy-free"
- Numbers: Try "1", "2", "5", etc.

### 3. DEI Compliance
- Notice no assumptions about relationships
- "Person" not "mom/dad"
- All dietary restrictions equal weight
- Cultural, religious, medical all supported

### 4. Commands at Any Time
Try these at any point:
- HELP - Get help
- PAUSE - Pause setup
- STOP - Opt out
- Back to previous step

### 5. Conversation Feel
- Should feel like texting a friend
- Not like filling out a form
- Friendly, warm, patient
- Concise (SMS-friendly)

---

## What Data Gets Stored

### Household Profile
```json
{
  "phone": "+14157979915",
  "household_size": 3,
  "members": [
    {
      "name": "Sarah",
      "age": 42,
      "dietary_restrictions": ["gluten-free", "dairy-free"]
    },
    {
      "name": "Mike",
      "age": 45,
      "dietary_restrictions": []
    },
    {
      "name": "Emma",
      "age": 8,
      "dietary_restrictions": ["peanut allergy"]
    }
  ]
}
```

### User State
```json
{
  "phone": "+14157979915",
  "onboarding_state": "onboarded",
  "onboarded": true,
  "messages_exchanged": 15,
  "created_at": "2025-12-29T17:00:00",
  "last_activity": "2025-12-29T17:05:00"
}
```

---

## Monitoring & Debugging

### View Logs
```bash
tail -f logs/housekeeper.log
```

### Check User State
```bash
curl http://localhost:8000/admin/user/+14157979915 | python3 -m json.tool
```

### View All Users
```bash
curl http://localhost:8000/admin/users | python3 -m json.tool
```

### Check AI Usage
```bash
curl http://localhost:8000/admin/ai-usage | python3 -m json.tool
```

---

## Files Created/Modified

### New Files
- `app_housekeeper.py` - Main application with conversational onboarding
- `ONBOARDING_FLOW.md` - Complete onboarding documentation
- `READY_TO_TEST_JULES.md` - This file

### Data Files (created on first use)
- `data/user_states.json` - User onboarding states
- `data/household_profiles.json` - Household member information
- `data/conversation_history.json` - Message history
- `data/ai_usage.json` - Cost tracking
- `data/tasks.json` - Future: recipes and tasks

---

## AI Cost Tracking

Jules tracks every AI call:
- **Intent classification:** ~$0.0002 per call
- **Task extraction:** ~$0.0004 per call
- **Conversation:** ~$0.002-0.005 per message

**Expected onboarding cost:** ~$0.01-0.03 per user
**Monthly budget alert:** $10.00 (configurable)

View costs at: http://localhost:8000/admin/ai-usage

---

## Next Steps After Onboarding

Once a user completes onboarding, they can:
1. Add recipes (conversational or structured)
2. Ask for meal suggestions
3. View their profile
4. Get recipe ideas based on dietary needs

---

## Testing Checklist

- [ ] Complete full onboarding flow
- [ ] Try natural language responses
- [ ] Test PAUSE command
- [ ] Test HELP command
- [ ] Try different household sizes (1, 2, 4+)
- [ ] Test various dietary restrictions
- [ ] Check data storage in admin endpoints
- [ ] Verify AI cost tracking
- [ ] Test error recovery (unclear input)
- [ ] Verify conversation feels natural

---

## Technical Details

**Server:** http://0.0.0.0:8000
**Ngrok:** https://juryless-eugena-nonsyntactically.ngrok-free.dev
**Webhook:** /sms/webhook
**Model:** claude-sonnet-4-5-20250929
**Max Tokens:** 1024 (cost control)
**Temperature:** 0.7

**Process ID:** 27885
**Status:** ✅ Running
**Logs:** logs/housekeeper.log

---

## What Makes This Different

### vs. Traditional Meal Planning Apps
❌ No app download required
❌ No forms to fill out
❌ No complicated UI
✅ Just text messages
✅ Natural conversation
✅ Learns over time

### vs. Generic AI Chatbots
❌ Not general purpose
❌ Not trying to do everything
✅ Focused on meal planning
✅ Builds household knowledge base
✅ Respects dietary needs
✅ Privacy-first

---

## Privacy & Control

**What Jules stores:**
- Household member info (names, ages, dietary restrictions)
- Your recipes
- Conversation history (last 30 messages)
- AI usage stats

**What Jules NEVER does:**
- Share your data
- Track your location
- Call you (SMS only)
- Make assumptions about your family

**User control:**
- PAUSE - Pause at any time
- STOP - Opt out instantly (data deleted in 30 days)
- START - Rejoin anytime

---

## Ready to Test!

Text **HI** to **+18664978083** and start your onboarding journey!

The conversation should feel natural, friendly, and respectful - like texting a helpful friend who's genuinely interested in making your meal planning easier.

Enjoy testing Jules! 🎉
