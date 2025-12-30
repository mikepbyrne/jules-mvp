# Jules - Single-User MVP Testing Plan

**Purpose**: Build and test with you + wife as only users
**Timeline**: 2-4 weeks to working prototype
**Goal**: Validate SMS workflow, recipe features, meal planning basics

---

## 🎯 Ultra-Minimal MVP Scope

### What We're Building

**Core Flow**:
1. You and wife text a phone number
2. Jules responds with meal planning prompts
3. You can add recipes via manual text entry (no AI initially)
4. Jules suggests meals from your recipes
5. You pick meals for the week via SMS
6. Jules sends shopping list

**Cut Everything Else**:
- ❌ No web dashboard (CLI admin only)
- ❌ No AI recipe extraction (manual text entry)
- ❌ No pantry scanning
- ❌ No image uploads
- ❌ No group voting (just direct responses)
- ❌ No multiple households
- ❌ No advanced monitoring (basic logs only)
- ❌ No invitation system (hardcoded phone numbers)

---

## 📱 SMS Conversation Examples

### Initial Setup (You)
```
You: "START"
Jules: "Hi! I'm Jules, your meal planning assistant. Let me get you set up.

What's your name?"

You: "John"
Jules: "Great! And your partner's name?"

You: "Sarah"
Jules: "Perfect! John & Sarah, I'll help you plan meals.

Text RECIPE to add a recipe
Text PLAN to start weekly planning
Text HELP anytime"
```

### Adding a Recipe (Manual Entry)
```
You: "RECIPE"
Jules: "What's the recipe name?"

You: "Chicken Stir Fry"
Jules: "Nice! What are the main ingredients? (comma separated)"

You: "chicken breast, broccoli, soy sauce, rice"
Jules: "How long to cook?"

You: "30 minutes"
Jules: "✓ Saved! Chicken Stir Fry added to your recipes.

Text LIST to see all recipes"
```

### Weekly Planning
```
You: "PLAN"
Jules: "Let's plan this week! You have 3 recipes:
1. Chicken Stir Fry
2. Spaghetti
3. Tacos

Pick 4 meals (numbers, like: 1,2,1,3)"

You: "1,2,3,1"
Jules: "This week:
Mon: Chicken Stir Fry
Tue: Spaghetti
Wed: Tacos
Thu: Chicken Stir Fry

Looks good?"

You: "YES"
Jules: "✓ Week planned! I'll send the shopping list tomorrow."
```

### Shopping List
```
Jules: "🛒 Shopping List:
- Chicken breast (2x)
- Broccoli
- Soy sauce
- Rice
- Pasta
- Ground beef
- Taco shells
- Cheese

Reply DONE when you've shopped!"
```

---

## 🏗️ Ultra-Simple Architecture

### No Database (For Now)
- Store everything in JSON files
- `data/household.json` - Your household data
- `data/recipes.json` - Recipe list
- `data/meal_plan.json` - Current week's plan
- `data/messages.json` - Conversation history

**Why**: Skip PostgreSQL setup, iterate fast

### No Redis (For Now)
- Conversation state in JSON file
- Read/write on every message
- Good enough for 2 users

**Why**: One less service to run

### Minimal Stack
```
FastAPI app (single file)
├── Twilio webhook handler
├── SMS sender
├── Simple state machine (if/else logic)
└── JSON file storage

Ngrok (expose local to Twilio)
```

---

## 📂 Project Structure (Minimal)

```
jules-mvp/
├── app.py                    # Single FastAPI app (500 lines)
├── requirements.txt          # Minimal deps
├── .env                      # Secrets
├── data/                     # JSON storage
│   ├── household.json
│   ├── recipes.json
│   ├── meal_plan.json
│   └── conversation.json
├── README_SETUP.md          # Quick start guide
└── tests/
    └── test_sms_flow.py     # Basic tests
```

---

## 🚀 Development Setup

### Step 1: Install Dependencies (5 min)
```bash
cd jules-mvp
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn twilio python-dotenv
```

### Step 2: Configure Twilio (10 min)
1. Sign up at twilio.com (free trial)
2. Get phone number ($1-2/month or free trial)
3. Copy Account SID, Auth Token
4. Set webhook URL (we'll use ngrok)

### Step 3: Environment Variables (2 min)
```bash
# .env
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
YOUR_PHONE=+1555123456
WIFE_PHONE=+1555789012
```

### Step 4: Run Locally (3 min)
```bash
# Terminal 1: Start FastAPI
uvicorn app:app --reload --port 8000

# Terminal 2: Expose to internet
ngrok http 8000

# Copy ngrok URL (https://abc123.ngrok.io)
# Paste into Twilio webhook settings
```

### Step 5: Test (1 min)
```
Text your Twilio number: "START"
```

**Total setup time**: 20 minutes

---

## 📝 Implementation Phases

### Week 1: Basic SMS Flow (12-16 hours)

**Day 1-2: Core Setup** (4 hours)
- [ ] Create `app.py` with FastAPI
- [ ] Twilio webhook handler
- [ ] SMS send function
- [ ] JSON file storage helpers
- [ ] Test: Send/receive SMS

**Day 3-4: Recipe Management** (4 hours)
- [ ] RECIPE command flow
- [ ] Store recipes in JSON
- [ ] LIST command (show recipes)
- [ ] DELETE command
- [ ] Test: Add 5 test recipes

**Day 5-6: Meal Planning** (4 hours)
- [ ] PLAN command flow
- [ ] Week selection logic
- [ ] Shopping list generation
- [ ] Test: Plan a full week

**Day 7: Polish** (2 hours)
- [ ] HELP command
- [ ] Error handling
- [ ] Basic logging
- [ ] Test with wife

---

### Week 2: Real Usage Testing (8-12 hours)

**Daily Testing** (1 hour/day × 7 days)
- [ ] Monday: Add 3 real recipes
- [ ] Tuesday: Plan actual week
- [ ] Wednesday: Get shopping list
- [ ] Thursday: Add 2 more recipes
- [ ] Friday: Replan weekend
- [ ] Saturday: Test edge cases
- [ ] Sunday: Bug fixes

**Iteration** (2-4 hours)
- Fix what's annoying
- Add missing commands
- Improve responses

---

### Week 3-4: Essential Features (16-20 hours)

**Add Only What You Actually Need**:
- Recipe modification (EDIT command)
- Meal substitution (SWAP command)
- Recipe details (VIEW command)
- Favorites (STAR command)
- Quick add common meals (TONIGHT command)

**Skip If Not Needed**:
- Anything that doesn't solve real problems you encounter

---

## 🧪 Testing Strategy

### Manual Testing Checklist
```
[ ] Send SMS → Receive response
[ ] Add recipe → Appears in LIST
[ ] PLAN → Select meals → Confirm
[ ] Shopping list → Correct ingredients
[ ] Edit recipe → Changes saved
[ ] Delete recipe → Removed from plan
[ ] HELP → Shows commands
[ ] Invalid command → Helpful error
[ ] Wife can use all features
[ ] Works during dinner time (prime usage)
```

### Acceptance Criteria
✅ You and wife use it for 1 full week
✅ Plan at least 5 meals successfully
✅ Generate shopping list actually used
✅ Less than 2 minutes to plan week
✅ SMS responses feel natural

---

## 💰 Costs (Testing Phase)

**Twilio**:
- Phone number: $1/month (or free trial)
- SMS: $0.0079/message × ~200 messages = $1.58/month
- **Total: ~$2.50/month**

**Infrastructure**:
- Local machine: $0
- Ngrok: $0 (free tier)
- **Total: $0**

**Grand Total**: **$2.50/month** 🎉

---

## 📊 Success Metrics

### Week 1 Goal
- [ ] App runs locally
- [ ] Both phones can text Jules
- [ ] Add 3 recipes successfully
- [ ] Plan 1 week of meals

### Week 2 Goal
- [ ] Use for actual meal planning
- [ ] Shopping list used for groceries
- [ ] Zero crashes during use
- [ ] Response time < 3 seconds

### Week 3-4 Goal
- [ ] 90% of interactions successful
- [ ] Wife says "this is useful"
- [ ] You want to keep using it
- [ ] Identified 3 features to add

---

## 🔄 Iteration Plan

### After Each Week
1. Review conversation logs
2. Find annoying parts
3. Add 1-2 small features
4. Remove friction points

### When It Works Well
**Then and only then**:
- Add AI recipe extraction
- Add pantry tracking
- Build web dashboard
- Add more users
- Deploy to cloud

---

## 🚫 What NOT to Build Yet

**Resist the urge** to build:
- User authentication (hardcode your phones)
- Database (JSON files work)
- Web UI (SMS only for now)
- AI anything (manual is fine)
- Multiple households
- Advanced features

**Why**: Validate the core first

---

## 📋 Quick Start Checklist

### Prerequisites
- [ ] Python 3.11+ installed
- [ ] Text editor (VS Code)
- [ ] Credit card for Twilio ($2)
- [ ] 30 minutes of time

### Setup Steps
1. [ ] Create Twilio account
2. [ ] Get phone number
3. [ ] Clone/create jules-mvp folder
4. [ ] Install dependencies
5. [ ] Create .env file
6. [ ] Run app locally
7. [ ] Start ngrok
8. [ ] Configure Twilio webhook
9. [ ] Send first text: "START"
10. [ ] Receive response from Jules

### First Session Goals
- [ ] Add 1 recipe via SMS
- [ ] View recipe list
- [ ] Delete and re-add recipe
- [ ] Get wife to add a recipe
- [ ] Plan 2 meals for tomorrow

---

## 🎯 Minimum Viable Commands

```
START    - Initial setup
HELP     - Show commands
RECIPE   - Add new recipe
LIST     - Show all recipes
VIEW #   - Show recipe details
DELETE # - Remove recipe
PLAN     - Start weekly planning
TONIGHT  - Quick dinner suggestion
SHOP     - Resend shopping list
DONE     - Mark shopping complete
```

**That's it. 11 commands.**

---

## 📞 Sample Conversation State Machine

```
State: IDLE
  "RECIPE" → RECIPE_NAME
  "PLAN" → PLAN_SELECT
  "LIST" → Show recipes, stay IDLE
  "HELP" → Show help, stay IDLE

State: RECIPE_NAME
  <text> → RECIPE_INGREDIENTS (save name)

State: RECIPE_INGREDIENTS
  <text> → RECIPE_TIME (save ingredients)

State: RECIPE_TIME
  <number> minutes → IDLE (save recipe, confirm)

State: PLAN_SELECT
  <numbers> → PLAN_CONFIRM (save selections)

State: PLAN_CONFIRM
  "YES" → IDLE (finalize plan)
  "NO" → PLAN_SELECT (restart)
```

Simple if/else, no fancy framework needed.

---

## 🐛 Expected Issues & Solutions

### Issue: Ngrok URL changes
**Solution**: Restart ngrok, update Twilio webhook (2 min)

### Issue: Forgot conversation state
**Solution**: Add state to JSON, read on each message

### Issue: SMS out of order
**Solution**: Add timestamp, ignore old messages

### Issue: Twilio rate limit
**Solution**: Not a problem with 2 users

### Issue: Want to reset data
**Solution**: Delete JSON files, start fresh

---

## 📈 Growth Path

### If testing goes well:

**Month 2**: Polish MVP
- Improve responses
- Add 2-3 killer features
- Test with 1-2 friends

**Month 3**: Add persistence
- Move to PostgreSQL
- Add proper user accounts
- Deploy to cloud ($10/month)

**Month 4**: AI features
- Recipe extraction from photos
- Meal suggestions

**Month 5**: Scale
- Support 10 households
- Add monitoring
- Improve reliability

---

## ✅ Decision Points

### After Week 1
**If it works**: Keep going
**If it's broken**: Fix core issues
**If it's tedious**: Simplify further

### After Week 2
**If you use it daily**: Add features
**If wife uses it**: You're onto something
**If collecting dust**: Rethink approach

### After Week 4
**If still using**: Consider adding users
**If abandoned**: Learned what doesn't work
**If frustrated**: Identify pain points

---

## 🎉 Week 1 Deliverable

**Working prototype** where:
- You text "RECIPE"
- Jules asks questions
- Recipe is saved
- You text "PLAN"
- Jules shows recipes
- You pick meals
- Jules sends shopping list

**That's the entire MVP.**

Everything else is optional.

---

## 💡 Key Insights

1. **Start stupidly simple**: JSON files beat databases for testing
2. **No web UI needed**: SMS is the UI
3. **Manual beats AI**: Text entry validates workflow first
4. **Two users enough**: You learn more than with 100 strangers
5. **Ship in days, not months**: Working beat perfect

---

## 📞 Support During Testing

**When stuck**:
- Check logs: `tail -f logs/app.log`
- Test manually: Send SMS, check JSON files
- Restart app: `ctrl+C`, `uvicorn app:app --reload`
- Reset data: Delete JSON files

**When confused**:
- Review this doc
- Check Twilio logs
- Test with simple commands first

---

## 🚀 Let's Build

**Next Steps**:
1. Create `jules-mvp/` folder
2. Write `app.py` (minimal version)
3. Test locally
4. Iterate based on real use

**Time to first text**: 30 minutes
**Time to useful**: 1 week
**Time to validated**: 4 weeks

Let's start small and learn fast. 🏃‍♂️
