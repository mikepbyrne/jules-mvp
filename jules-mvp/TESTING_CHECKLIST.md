# Jules MVP Testing Checklist

Use this checklist to systematically test all MVP features.

## Pre-Testing Setup

### Environment Configuration
- [ ] `.env` file has valid `TWILIO_AUTH_TOKEN`
- [ ] `.env` file has valid `TWILIO_PHONE_NUMBER`
- [ ] `.env` file has valid `YOUR_PHONE`
- [ ] `.env` file has valid `WIFE_PHONE`
- [ ] All phone numbers in E.164 format (+1XXXXXXXXXX)

### Application Startup
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] Application started: `python app.py`
- [ ] Server running on http://0.0.0.0:8000
- [ ] No startup errors in terminal

### Ngrok Setup
- [ ] Ngrok installed (or use alternative tunnel)
- [ ] Ngrok running: `ngrok http 8000`
- [ ] HTTPS URL obtained (e.g., https://abc123.ngrok.io)

### Twilio Configuration
- [ ] Logged into Twilio console
- [ ] Navigated to Phone Numbers → Manage → Active numbers
- [ ] Clicked on your Twilio number
- [ ] Set webhook URL: `https://your-ngrok-url.ngrok.io/sms/webhook`
- [ ] Set method to POST
- [ ] Saved configuration

---

## Phase 1: Basic Connectivity (5 minutes)

### Initial Contact
- [ ] Text "START" to Twilio number
- [ ] Received welcome message within 5 seconds
- [ ] Welcome message includes command list
- [ ] No errors in `logs/app.log`

### Help System
- [ ] Text "HELP"
- [ ] Received command list
- [ ] All 9+ commands listed

### Invalid Commands
- [ ] Text random gibberish (e.g., "asdfasdf")
- [ ] Received helpful error message
- [ ] Error suggests texting HELP

---

## Phase 2: Recipe Management (15 minutes)

### Add First Recipe
- [ ] Text "RECIPE"
- [ ] Prompted for recipe name
- [ ] Respond with name (e.g., "Chicken Stir Fry")
- [ ] Prompted for ingredients
- [ ] Respond with ingredients (e.g., "chicken, broccoli, soy sauce, rice")
- [ ] Prompted for cook time
- [ ] Respond with time (e.g., "30")
- [ ] Received confirmation with recipe summary
- [ ] Check `data/recipes.json` exists and contains recipe

### List Recipes
- [ ] Text "LIST"
- [ ] Received list with recipe #1
- [ ] Recipe shows name and cook time
- [ ] Format is readable

### View Recipe Details
- [ ] Text "VIEW 1"
- [ ] Received full recipe details
- [ ] Shows name, cook time, ingredients
- [ ] Format is clear and readable

### Add More Recipes
- [ ] Text "RECIPE"
- [ ] Add second recipe (different ingredients)
- [ ] Text "RECIPE"
- [ ] Add third recipe
- [ ] Text "LIST"
- [ ] Verify all 3 recipes shown

### Delete Recipe
- [ ] Text "DELETE 2"
- [ ] Received confirmation of deletion
- [ ] Text "LIST"
- [ ] Verify recipe #2 is gone
- [ ] Recipe numbering adjusted (now 1, 2 instead of 1, 3)

---

## Phase 3: Meal Planning (15 minutes)

### Plan Week (Happy Path)
- [ ] Text "PLAN"
- [ ] Received recipe list for selection
- [ ] Prompted to pick 4-7 meals
- [ ] Respond with selection (e.g., "1,2,1,2")
- [ ] Received week preview
- [ ] Shows Mon-Thu assignments
- [ ] Prompted for confirmation
- [ ] Text "YES"
- [ ] Received shopping list
- [ ] Shopping list shows all unique ingredients
- [ ] Check `data/meal_plan.json` contains plan

### Resend Shopping List
- [ ] Text "SHOP"
- [ ] Received same shopping list again
- [ ] All ingredients included

### Plan Week (Cancel)
- [ ] Text "PLAN"
- [ ] Receive recipe list
- [ ] Respond with selection (e.g., "1,1,1,1")
- [ ] Text "NO" when asked for confirmation
- [ ] Plan canceled gracefully
- [ ] Can start new plan immediately

### Invalid Plan Selection
- [ ] Text "PLAN"
- [ ] Respond with invalid format (e.g., "abc")
- [ ] Received helpful error message
- [ ] Can retry with correct format

---

## Phase 4: Quick Features (5 minutes)

### Tonight Suggestion
- [ ] Text "TONIGHT"
- [ ] Received random recipe suggestion
- [ ] Shows full recipe details
- [ ] Text "TONIGHT" again
- [ ] May receive different recipe (random)

---

## Phase 5: Wife Testing (15 minutes)

### Wife's Phone Setup
- [ ] Wife's phone number in `WIFE_PHONE` in .env
- [ ] Restart app if .env was changed
- [ ] Wife texts "START" to Twilio number
- [ ] Wife receives welcome message

### Wife Add Recipe
- [ ] Wife texts "RECIPE"
- [ ] Wife completes full recipe flow
- [ ] You text "LIST" from your phone
- [ ] Wife's recipe appears in your list
- [ ] Wife texts "LIST"
- [ ] Wife sees all recipes including yours

### Both Plan Together
- [ ] Either person texts "PLAN"
- [ ] Selects meals from combined recipe list
- [ ] Both receive shopping list (separately, via individual messages)

---

## Phase 6: Edge Cases & Error Handling (10 minutes)

### State Interruption
- [ ] Text "RECIPE"
- [ ] When prompted for name, text "LIST" instead
- [ ] Verify LIST command works
- [ ] Previous recipe flow abandoned
- [ ] Can start new RECIPE flow

### Empty States
- [ ] Delete `data/recipes.json`
- [ ] Text "LIST"
- [ ] Received message about no recipes
- [ ] Suggested to add recipe

### Message Ordering
- [ ] Send two messages rapidly (e.g., "RECIPE" then "Pasta")
- [ ] Both messages processed
- [ ] Responses arrive in correct order (or note if not)

### Long Ingredient List
- [ ] Text "RECIPE"
- [ ] Add recipe with 15+ ingredients
- [ ] Verify all ingredients saved
- [ ] Check response isn't cut off

### Special Characters
- [ ] Add recipe with special chars (e.g., "Mom's Spaghetti")
- [ ] Add ingredients with accents (e.g., "jalapeño")
- [ ] Verify saved correctly

---

## Phase 7: Data Persistence (5 minutes)

### Restart App
- [ ] Stop app (Ctrl+C)
- [ ] Restart: `python app.py`
- [ ] Text "LIST"
- [ ] All recipes still present
- [ ] Previous meal plan still accessible ("SHOP")

### Data Files
- [ ] Check `data/household.json` exists and has both members
- [ ] Check `data/recipes.json` has all recipes
- [ ] Check `data/meal_plan.json` has current plan
- [ ] Check `data/conversation.json` has state for both phones

---

## Phase 8: Logs & Debugging (5 minutes)

### Log File
- [ ] Check `logs/app.log` exists
- [ ] Open log file: `tail -f logs/app.log`
- [ ] Send a message
- [ ] Verify log shows message received
- [ ] Verify log shows message sent
- [ ] Logs are readable JSON format

---

## Phase 9: Real-World Scenario (30 minutes)

### Actual Meal Planning
- [ ] Add 5+ recipes you actually cook
- [ ] Include real ingredients
- [ ] Use real cook times
- [ ] Plan actual week of meals
- [ ] Use shopping list for real grocery trip
- [ ] Note any missing ingredients
- [ ] Note any duplicates not caught

### Use for 3 Days
- [ ] Day 1: Check "what's for dinner" (VIEW command)
- [ ] Day 2: Cook planned meal, note if ingredients were right
- [ ] Day 3: Decide if you'd use this regularly

---

## Issues Tracker

Document any issues encountered:

### Bugs Found
1.
2.
3.

### Missing Features
1.
2.
3.

### UX Annoyances
1.
2.
3.

### Nice-to-Haves
1.
2.
3.

---

## Success Criteria

**MVP is successful if:**
- [ ] Both phones can add recipes
- [ ] Both can view full recipe list
- [ ] Can plan a week of meals
- [ ] Shopping list is actually useful
- [ ] Fewer than 3 critical bugs
- [ ] You want to keep using it

**MVP needs work if:**
- [ ] More than 3 critical bugs
- [ ] Workflow is frustrating
- [ ] Takes too long to add recipes
- [ ] Shopping list is inaccurate
- [ ] You wouldn't use it again

---

## Post-Testing Review

After 1 week of testing, answer:

1. **What worked well?**
   -
   -

2. **What was frustrating?**
   -
   -

3. **What features are missing?**
   -
   -

4. **Would you use this daily?** Yes / No / Maybe
   - Why:

5. **Top 3 improvements needed:**
   -
   -
   -

6. **Should we continue?** Yes / No / Pivot
   - Reasoning:

---

## Next Steps Based on Results

### If Successful (Keep Using It)
- Add top 2-3 requested features
- Polish annoying workflows
- Consider AI recipe extraction
- Plan database migration

### If Mixed Results (Some Issues)
- Fix critical bugs first
- Simplify frustrating flows
- Test for another week
- Re-evaluate

### If Unsuccessful (Not Using It)
- Review why not
- Fundamental workflow problem?
- Feature missing?
- Different approach needed?

---

**Ready to test?** Start with Phase 1 and work through systematically.

**Found bugs?** Document in Issues Tracker section above.

**Questions?** Check README_SETUP.md or QUICKSTART.md.
