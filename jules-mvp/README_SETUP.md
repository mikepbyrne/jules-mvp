# Jules MVP - Quick Setup Guide

Get Jules running in 20 minutes for 2-person testing.

---

## Prerequisites

- Python 3.11+
- Credit card for Twilio ($2)
- 20 minutes

---

## Step 1: Twilio Setup (10 min)

### 1.1: Create Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up (free trial gives $15 credit)
3. Verify your phone number

### 1.2: Get Phone Number
1. In Twilio Console, click "Get a trial number"
2. Accept the number (or search for specific area code)
3. **Copy this number** - you'll text it

### 1.3: Get Credentials
1. Go to Console Dashboard
2. Copy **Account SID**
3. Copy **Auth Token** (click to reveal)

**Save these** - you'll need them next.

---

## Step 2: Local Setup (5 min)

### 2.1: Install Dependencies
```bash
cd jules-mvp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2.2: Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
nano .env  # or use any editor
```

**Add your values**:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx  # From Twilio Console
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1234567890    # Number from Twilio
YOUR_PHONE=+15551234567            # Your actual phone
WIFE_PHONE=+15559876543            # Wife's phone
```

**Important**: Use E.164 format (+1 for US, then 10 digits, no spaces/dashes)

---

## Step 3: Run Locally (3 min)

### 3.1: Start the Server
```bash
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open**

### 3.2: Expose to Internet (Ngrok)

**New terminal**:
```bash
# Install ngrok (if not installed)
# Mac: brew install ngrok
# Windows: Download from ngrok.com

# Start tunnel
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the https URL** (the abc123.ngrok.io part)

---

## Step 4: Configure Twilio Webhook (2 min)

1. Go to Twilio Console → Phone Numbers → Manage → Active numbers
2. Click your phone number
3. Scroll to "Messaging Configuration"
4. Under "A MESSAGE COMES IN":
   - Set to: Webhook
   - URL: `https://your-ngrok-url.ngrok.io/sms/webhook`
   - HTTP: POST
5. Click "Save"

**Example**:
```
https://abc123.ngrok.io/sms/webhook
```

---

## Step 5: Test! (1 min)

### Send First Message

From your phone, text the Twilio number:
```
START
```

You should receive:
```
Welcome to Jules! 👋

I'll help you plan meals via text.

Commands:
RECIPE - Add a recipe
LIST - Show recipes
PLAN - Plan the week
...
```

**If you got this, it works!** 🎉

---

## Usage Examples

### Add Your First Recipe
```
You: RECIPE
Jules: What's the recipe name?

You: Chicken Stir Fry
Jules: Nice! What are the main ingredients...

You: chicken, broccoli, soy sauce, rice
Jules: How many minutes to cook?

You: 30
Jules: ✓ Saved! Chicken Stir Fry
```

### View Recipes
```
You: LIST
Jules: Your recipes:
1. Chicken Stir Fry (30 min)
2. Spaghetti (25 min)
```

### Plan a Week
```
You: PLAN
Jules: Let's plan this week!
Your recipes:
1. Chicken Stir Fry
2. Spaghetti
3. Tacos

Pick 4-7 meals (numbers like: 1,2,1,3)

You: 1,2,3,1
Jules: This week:
Mon: Chicken Stir Fry
Tue: Spaghetti
Wed: Tacos
Thu: Chicken Stir Fry

Looks good?

You: YES
Jules: ✓ Week planned!

🛒 Shopping List:
- chicken
- broccoli
- soy sauce
...
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| START | Initial setup |
| HELP | Show commands |
| RECIPE | Add new recipe |
| LIST | Show all recipes |
| VIEW # | Show recipe details |
| DELETE # | Remove recipe |
| PLAN | Plan the week |
| TONIGHT | Quick suggestion |
| SHOP | Resend shopping list |

---

## Troubleshooting

### "No response from Jules"

**Check**:
1. Is `python app.py` still running?
2. Is ngrok still running?
3. Did ngrok URL change? (Update Twilio webhook)
4. Check logs: `tail -f logs/app.log`

**Fix**: Restart both, update webhook URL

---

### "Invalid phone number"

**Check**: Phone numbers in .env are E.164 format
- ✅ Good: `+15551234567`
- ❌ Bad: `555-123-4567` or `15551234567`

---

### "Twilio error"

**Check**:
1. Credentials in .env are correct
2. Trial account has credit
3. Your phone is verified in Twilio

**Fix**:
- Go to Twilio Console
- Verify phone numbers
- Check account balance

---

### "Message out of order"

**This is normal** - SMS can arrive out of sequence.

**Fix**: Type HELP to reset conversation state.

---

### Reset Everything

```bash
# Stop app (Ctrl+C)
rm -rf data/*
python app.py
# Text START again
```

---

## Daily Development Workflow

### Morning
```bash
cd jules-mvp
source venv/bin/activate
python app.py              # Terminal 1
ngrok http 8000            # Terminal 2 (if ngrok URL expired)
# Update Twilio webhook if ngrok URL changed
```

### During Day
- Text Jules normally
- Check logs if issues: `tail -f logs/app.log`
- View data: http://localhost:8000/data/recipes

### Evening
- Review what worked/didn't
- Note features to add
- Ctrl+C to stop servers

---

## Viewing Data (Admin)

**While app is running**, visit in browser:

- http://localhost:8000/data/household - Household info
- http://localhost:8000/data/recipes - All recipes
- http://localhost:8000/data/plan - Current meal plan
- http://localhost:8000/data/conversation - Conversation states

---

## Next Steps

Once basic flow works:

### Week 1 Goals
- [ ] Add 5 real recipes
- [ ] Plan 1 full week
- [ ] Generate shopping list
- [ ] Wife adds a recipe
- [ ] Both use for 3 days

### Week 2 Goals
- [ ] Identify annoyances
- [ ] Add 1-2 quality-of-life features
- [ ] Use for actual shopping
- [ ] Decide if valuable

### Week 3-4 Goals
- [ ] Polish top pain points
- [ ] Test edge cases
- [ ] Decide: continue or pivot

---

## Cost Tracking

**Free Trial**: $15 credit
**Phone**: $1/month after trial
**SMS**: $0.0079 per message

**Expected usage** (2 people, 1 month):
- ~200 messages = $1.58
- Phone = $1
- **Total: ~$2.50/month**

---

## Support

### Check Logs
```bash
tail -f logs/app.log
```

### View Raw Data
```bash
cat data/recipes.json
cat data/meal_plan.json
cat data/conversation.json
```

### Reset Conversation State
```bash
rm data/conversation.json
# Text HELP to Jules
```

### Completely Start Over
```bash
rm -rf data/*
rm -rf logs/*
# Text START to Jules
```

---

## Success Checklist

- [ ] Python app running
- [ ] Ngrok exposing to internet
- [ ] Twilio webhook configured
- [ ] Received "Welcome" message
- [ ] Added first recipe
- [ ] Viewed recipe list
- [ ] Wife can also text Jules
- [ ] Both phones work

**If all checked, you're ready to use it daily!**

---

## What's Next?

After 1 week of real usage:

**If it's useful**: Add features you actually need
**If it's clunky**: Simplify the annoying parts
**If you're not using it**: Figure out why

The goal is to **learn what works** before building more.

---

Ready to start? Run:
```bash
python app.py
```

Then text your Twilio number: **START**

Good luck! 🚀
