# Jules AI Housekeeper - Onboarding Flow

## Conversational Onboarding Design

### Key Principles
- Explain the knowledge base concept upfront
- Gather household member information (DEI-compliant)
- Focus on meal planning, recipes, and pantry learning
- Set clear expectations about MVP vs future capabilities

---

## Complete Onboarding Conversation

### Step 1: Welcome
**Jules:** Hi! I'm Jules, your AI meal planning assistant 👋

I help with recipes, meal planning, and eventually I'll learn what's in your pantry to make smart suggestions.

Reply HI to get started, or STOP to opt out.

**User:** Hi

---

### Step 2: Explain Knowledge Base
**Jules:** Great! Let me explain how I work:

I'm an AI powered by Claude. I build a knowledge base about YOUR household - your recipes, who lives with you, dietary needs, and gradually what's in your pantry.

Your data stays private. You're in control.

Ready to continue? Reply YES

**User:** Yes

---

### Step 3: Set Expectations (MVP vs Future)
**Jules:** Perfect! Here's what I do:

**NOW (MVP):**
- Store your family recipes
- Learn about your household
- Suggest meals from your recipes

**SOON:**
- Learn pantry inventory
- Smart grocery suggestions
- Track household supplies

Let's start! Ready?

**User:** Yes

---

### Step 4: Household Size
**Jules:** Great! First, tell me about your household.

How many people live in your home?

Just reply with a number (like 3 or 4)

**User:** 4

---

### Step 5-N: Member Information (Loop for each person)

**Jules:** Got it - 4 people in your household.

Let's learn about each person so I can suggest meals everyone will enjoy.

Person 1: What's their name?

**User:** Sarah

---

**Jules:** Great! How old is Sarah?

(This helps with age-appropriate meal suggestions)

**User:** 42

---

**Jules:** Thanks! Does Sarah have any dietary restrictions?

Reply with restrictions separated by commas, or NONE:
Examples: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher, none

**User:** None

---

**Jules:** Perfect! Person 2: What's their name?

**User:** Mike

---

**Jules:** Great! How old is Mike?

(This helps with age-appropriate meal suggestions)

**User:** 45

---

**Jules:** Thanks! Does Mike have any dietary restrictions?

Reply with restrictions separated by commas, or NONE:
Examples: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher, none

**User:** Gluten-free, dairy-free

---

**Jules:** Perfect! Person 3: What's their name?

**User:** Emma

---

**Jules:** Great! How old is Emma?

(This helps with age-appropriate meal suggestions)

**User:** 12

---

**Jules:** Thanks! Does Emma have any dietary restrictions?

Reply with restrictions separated by commas, or NONE:
Examples: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher, none

**User:** Vegetarian

---

**Jules:** Perfect! Person 4: What's their name?

**User:** Lucas

---

**Jules:** Great! How old is Lucas?

(This helps with age-appropriate meal suggestions)

**User:** 8

---

**Jules:** Thanks! Does Lucas have any dietary restrictions?

Reply with restrictions separated by commas, or NONE:
Examples: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher, none

**User:** Peanut allergy

---

### Step 6: Onboarding Complete + First Recipe Prompt

**Jules:** Awesome! Here's your household:

- Sarah, 42
- Mike, 45 (gluten-free, dairy-free)
- Emma, 12 (vegetarian)
- Lucas, 8 (peanut allergy)

I'll use this to suggest meals everyone can enjoy!

Ready to add your first recipe? Tell me about a meal your household loves.

---

## DEI Compliance Features

### Inclusive Language
- ✅ "Household" instead of "family" (inclusive of all living arrangements)
- ✅ "Person" instead of assuming relationships (mom, dad, etc.)
- ✅ Names first, no assumptions about roles
- ✅ Age-neutral approach (works for multi-generational households)

### Dietary Respect
- ✅ All dietary restrictions treated equally
- ✅ Cultural (halal, kosher) alongside medical (allergies)
- ✅ Ethical choices (vegetarian, vegan) alongside health needs
- ✅ No judgment language - neutral framing

### Flexible Data Collection
- ✅ Accept numeric ages or descriptions ("toddler", "baby")
- ✅ Allow multiple dietary restrictions per person
- ✅ Support households of any size (1-10+)
- ✅ No required fields beyond name

---

## Knowledge Base Explained

During onboarding, users learn that Jules:

1. **Builds a Knowledge Base** - Stores information specific to their household
2. **Learns Gradually** - Pantry inventory will be learned over time (future feature)
3. **Respects Privacy** - Data stays with the household, not shared
4. **User Control** - Can pause, stop, or modify anytime

### What Gets Stored
- Household member profiles (names, ages, dietary needs)
- Family recipes (ingredients, instructions)
- Meal preferences (over time)
- Pantry inventory (future)
- Shopping patterns (future)

---

## Message Count
**Target: 8-12 messages for single-person household**
**Actual: ~15-20 messages for 4-person household** (reasonable given data collected)

Each additional household member adds ~3 messages (name, age, dietary restrictions).

---

## Future Enhancements

### Pantry Learning
- "Over the next few weeks, I'll learn what's typically in your pantry"
- "When you add recipes, I'll track common ingredients"
- "Eventually, I'll suggest when to restock essentials"

### Smart Suggestions
- "I'll learn which meals your household enjoys most"
- "I'll suggest recipes that use what you already have"
- "I'll help reduce food waste by using up ingredients"

### Household Supplies
- "Beyond food, I'll learn your household supply patterns"
- "I'll suggest when to buy toilet paper, cleaning supplies"
- "You'll never run out of essentials unexpectedly"

---

## Example Alternative Flows

### Single Person Household

**Jules:** How many people live in your home?

**User:** 1

**Jules:** Got it - just you!

What's your name?

**User:** Alex

**Jules:** Great! How old are you Alex?

**User:** 28

**Jules:** Thanks! Do you have any dietary restrictions?

**User:** Vegan

**Jules:** Awesome! Here's your household:

- Alex, 28 (vegan)

Ready to add your first recipe? Tell me about a meal you love.

---

### Large Multi-Generational Household

**Jules:** How many people live in your home?

**User:** 7

**Jules:** Got it - 7 people in your household.

Let's learn about each person so I can suggest meals everyone will enjoy.

Person 1: What's their name?

[... continues for all 7 people ...]

---

## Error Handling

### Unclear Dietary Restriction

**User:** I don't eat red meat

**Jules:** Got it - I'll note that as a dietary preference. Any specific allergies or other restrictions?

### Age Format Variations

**User:** She's a toddler

**Jules:** [Accepts "toddler" as age value, works fine]

### Multiple Names

**User:** Sarah and Mike

**Jules:** Let's go one at a time! Person 1: What's their name?

[Guides back to one-by-one flow]

---

## Success Metrics

**Onboarding Completion:**
- User reaches "ONBOARDED" state
- Household profile fully populated
- At least 1 member added
- Ready to add recipes

**Quality Indicators:**
- Complete dietary information for each member
- Age information for meal suggestions
- All members have names

**User Satisfaction:**
- Clear understanding of Jules' capabilities
- Excitement to add first recipe
- Privacy concerns addressed
