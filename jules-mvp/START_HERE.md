# 🚀 START HERE - Jules MVP

**Welcome!** This is your ultra-minimal SMS meal planning assistant, ready for 2-person testing.

---

## ⚡ Quick Start (20 Minutes)

### 1. Complete Configuration (5 min)

Edit `.env` file - only 3 values needed:

```bash
TWILIO_AUTH_TOKEN=your_auth_token_here    # ⚠️ Get from https://console.twilio.com
TWILIO_PHONE_NUMBER=+1234567890            # ⚠️ Your Twilio number
WIFE_PHONE=+1                             # ⚠️ Wife's phone in E.164 format
```

**Already set:**
- ✅ `TWILIO_ACCOUNT_SID` - Already configured
- ✅ `YOUR_PHONE` - Already configured

### 2. Start the App (1 min)

```bash
cd /Users/crucial/Documents/dev/Jules/jules-mvp
source venv/bin/activate
python app.py
```

**Should see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Leave this terminal running.**

### 3. Expose to Internet (2 min)

**New terminal:**
```bash
ngrok http 8000
```

**Copy the HTTPS URL** (looks like: `https://abc123.ngrok.io`)

### 4. Configure Twilio (2 min)

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/active
2. Click your phone number
3. Scroll to "Messaging Configuration"
4. Under "A MESSAGE COMES IN":
   - URL: `https://abc123.ngrok.io/sms/webhook` (use your ngrok URL)
   - HTTP: POST
5. Click "Save"

### 5. Test! (1 min)

Text your Twilio number: **START**

**You should receive:**
```
Welcome to Jules! 👋

I'll help you plan meals via text.

Commands:
RECIPE - Add a recipe
LIST - Show recipes
PLAN - Plan the week
SHOP - Get shopping list
HELP - Show commands

Try: RECIPE
```

---

## ✅ If Everything Works

Try this sequence:

1. Text: **RECIPE**
2. Follow prompts to add a recipe
3. Text: **LIST** (see your recipe)
4. Add 2 more recipes
5. Text: **PLAN** (plan a week)
6. Text: **SHOP** (get shopping list)

**Then:** Have your wife text START and add a recipe.

---

## ⚠️ If Something Doesn't Work

### No response from Jules?

**Check:**
1. Is `python app.py` still running? (Terminal 1)
2. Is `ngrok` still running? (Terminal 2)
3. Any errors in the app terminal?

**Fix:**
- Restart app: Ctrl+C, then `python app.py`
- Check logs: `tail -f logs/app.log`

### "Invalid credentials" error?

**Problem:** Wrong Twilio credentials

**Fix:**
1. Go to https://console.twilio.com
2. Copy "Auth Token" (click "Show")
3. Update `.env` with correct token
4. Restart app

### "Invalid phone number" error?

**Problem:** Phone format wrong

**Fix:** Ensure E.164 format
- ✅ Correct: `+15551234567`
- ❌ Wrong: `555-123-4567` or `(555) 123-4567`

### Ngrok URL changed?

**Problem:** Free ngrok gives new URL each time

**Fix:**
1. Copy new ngrok URL
2. Update Twilio webhook with new URL
3. Save in Twilio console

---

## 📚 Documentation

**Choose your path:**

- **Just want to start?** → You're reading it! Complete steps 1-5 above.
- **Want detailed setup?** → Read `README_SETUP.md` (20-min guide)
- **Want to test systematically?** → Use `TESTING_CHECKLIST.md`
- **Want full context?** → Read `STATUS.md` (complete project status)
- **Quick reference?** → Check `QUICKSTART.md`

---

## 🎯 What You Can Do

### Commands

| Text This | Jules Does This |
|-----------|-----------------|
| START | Initial setup |
| HELP | Show all commands |
| RECIPE | Add recipe (step-by-step) |
| LIST | Show all recipes |
| VIEW 1 | Show recipe #1 details |
| DELETE 2 | Delete recipe #2 |
| PLAN | Plan the week (select meals) |
| TONIGHT | Random dinner suggestion |
| SHOP | Resend shopping list |

### Example Conversation

```
You: RECIPE
Jules: What's the recipe name?

You: Chicken Stir Fry
Jules: Nice! What are the main ingredients?

You: chicken, broccoli, soy sauce, rice
Jules: How many minutes to cook?

You: 30
Jules: ✓ Saved! Chicken Stir Fry
       Ingredients: chicken, broccoli, soy sauce, rice
       Cook time: 30 min

       Text LIST to see all recipes.
```

---

## 💡 Tips

**For Best Results:**
- Add 5+ recipes before planning
- Use simple ingredient names
- Keep recipes you actually cook
- Test with your wife early
- Use for real meal planning

**If You Get Stuck:**
- Text HELP to reset conversation
- Check `logs/app.log` for errors
- Restart the app
- Check documentation

**Reset Everything:**
```bash
rm -rf data/*
# Text START again
```

---

## 📊 After 1 Week of Testing

**Fill out:** `TESTING_CHECKLIST.md` (bottom section)

**Answer:**
1. What worked well?
2. What was frustrating?
3. Top 3 improvements needed?
4. Should we continue developing this?

---

## 🎉 Success Criteria

**MVP is working if:**
- ✅ Both phones can add recipes
- ✅ You can plan a week
- ✅ Shopping list is useful
- ✅ You want to keep using it

**Then we add:**
- AI recipe extraction (from photos)
- Better meal suggestions
- Pantry tracking
- Web dashboard

---

## 🚨 Need Help?

**Check in order:**
1. This file (you're reading it)
2. `QUICKSTART.md` - Next steps reference
3. `README_SETUP.md` - Detailed guide
4. `logs/app.log` - Error logs

---

## ⏱️ Time Budget

**Setup:** 20 minutes (if you have Twilio already)
**First test:** 5 minutes (add a recipe)
**Full test:** 30 minutes (add recipes, plan week)
**Real usage:** 1-2 weeks

**Cost:** ~$2.50/month

---

## 🎯 Your Next 3 Steps

1. **Edit `.env`** - Add 3 missing values
2. **Run `python app.py`** - Start the server
3. **Text START** - Test it works

**That's it!** You'll figure out the rest by texting Jules.

---

**Questions?** Read the docs above.

**Ready?** Edit `.env` and run `python app.py`

**Good luck! 🚀**
