"""
Jules MVP - AI-Powered Meal Planning Companion

Claude-powered conversational assistant for meal planning via SMS.
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from anthropic import Anthropic
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Jules AI MVP")

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE = os.getenv("YOUR_PHONE")
WIFE_PHONE = os.getenv("WIFE_PHONE")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
validator = RequestValidator(TWILIO_AUTH_TOKEN)

# Claude AI setup
AI_ENABLED = os.getenv("ENABLE_AI_FEATURES", "false").lower() == "true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-5-20250929")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", 4096))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", 0.7))

if AI_ENABLED:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info(f"AI features enabled with model: {AI_MODEL}")
else:
    anthropic_client = None
    logger.info("AI features disabled - using rule-based responses")

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# JSON Storage Helpers
# ============================================================================

def load_json(filename: str) -> dict:
    """Load data from JSON file."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}


def save_json(filename: str, data: dict):
    """Save data to JSON file."""
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"saved_json file={filename}")


# ============================================================================
# Data Access
# ============================================================================

def get_household() -> dict:
    """Get household data."""
    return load_json("household.json")


def save_household(data: dict):
    """Save household data."""
    save_json("household.json", data)


def get_recipes() -> List[dict]:
    """Get all recipes."""
    data = load_json("recipes.json")
    return data.get("recipes", [])


def save_recipes(recipes: List[dict]):
    """Save recipes."""
    save_json("recipes.json", {"recipes": recipes})


def get_meal_plan() -> dict:
    """Get current meal plan."""
    return load_json("meal_plan.json")


def save_meal_plan(plan: dict):
    """Save meal plan."""
    save_json("meal_plan.json", plan)


def get_conversation_history(phone: str) -> List[dict]:
    """Get conversation history for phone number."""
    histories = load_json("conversation_history.json")
    return histories.get(phone, [])


def save_conversation_history(phone: str, history: List[dict]):
    """Save conversation history."""
    histories = load_json("conversation_history.json")
    histories[phone] = history[-20:]  # Keep last 20 messages
    save_json("conversation_history.json", histories)


def log_ai_usage(feature: str, input_tokens: int, output_tokens: int, cost: float):
    """Track AI usage and costs."""
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

    # Update totals
    usage[month]["total_requests"] += 1
    usage[month]["total_input_tokens"] += input_tokens
    usage[month]["total_output_tokens"] += output_tokens
    usage[month]["estimated_cost"] += cost

    # Update feature breakdown
    if feature not in usage[month]["by_feature"]:
        usage[month]["by_feature"][feature] = {"requests": 0, "cost": 0.0}
    usage[month]["by_feature"][feature]["requests"] += 1
    usage[month]["by_feature"][feature]["cost"] += cost

    # Save
    with open(usage_file, 'w') as f:
        json.dump(usage, f, indent=2)

    # Check alert threshold
    threshold = float(os.getenv("AI_COST_ALERT_THRESHOLD", 10.00))
    if usage[month]["estimated_cost"] > threshold:
        logger.warning(f"AI cost alert: ${usage[month]['estimated_cost']:.2f} exceeds ${threshold:.2f}")

    logger.info(f"AI usage: {feature} - {input_tokens}in + {output_tokens}out = ${cost:.4f}")


# ============================================================================
# SMS Helpers
# ============================================================================

def send_sms(to: str, body: str):
    """Send SMS via Twilio."""
    try:
        message = twilio_client.messages.create(
            to=to,
            from_=TWILIO_PHONE,
            body=body
        )
        logger.info(f"sms_sent to={to} sid={message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"sms_failed to={to} error={str(e)}")
        raise


# ============================================================================
# AI Conversation System
# ============================================================================

JULES_SYSTEM_PROMPT = """You are Jules, a friendly and helpful AI meal planning companion. You communicate via SMS text messages.

Your purpose is to help families:
- Store and organize their favorite recipes
- Plan weekly meals
- Generate shopping lists
- Answer questions about what to cook

Key personality traits:
- Warm and conversational, like texting a helpful friend
- Concise responses (SMS-friendly, usually 1-2 sentences)
- Enthusiastic about food and cooking
- Remember context from the conversation
- Proactive in helping users achieve their goals

Current capabilities:
- Add recipes (name, ingredients, cook time)
- List all recipes
- View recipe details
- Plan weekly meals
- Generate shopping lists
- Suggest tonight's dinner

Important SMS constraints:
- Keep responses under 300 characters when possible
- Use emojis sparingly (1-2 per message max)
- Be conversational but concise
- If you need structured data (like ingredients), ask clearly

Data format expectations:
- Ingredients: comma-separated list
- Cook times: just the number in minutes
- Meal selections: numbers like "1,2,3,4"

When users want to:
- Add a recipe: Get name, ingredients (comma-separated), and cook time (minutes)
- List recipes: Show numbered list with names and cook times
- Plan meals: Show recipes, ask them to pick by numbers, confirm, then generate shopping list
- Tonight's suggestion: Pick a random recipe and share it

Remember: You're a helpful companion, not just a data entry system. Be friendly, encouraging, and helpful!"""


def get_context_for_claude(phone: str) -> str:
    """Build context string with recipes and household data."""
    household = get_household()
    recipes = get_recipes()
    meal_plan = get_meal_plan()

    context_parts = []

    # Household info
    if household:
        context_parts.append(f"Household members: {', '.join([m['name'] for m in household.get('members', {}).values()])}")

    # Recipes
    if recipes:
        recipe_list = "\n".join([
            f"{i+1}. {r['name']} ({r.get('cook_time', '?')} min) - {', '.join(r.get('ingredients', [])[:3])}..."
            for i, r in enumerate(recipes[:10])  # Limit to 10 most recent
        ])
        context_parts.append(f"\nRecipes in collection ({len(recipes)} total):\n{recipe_list}")

    # Current meal plan
    if meal_plan.get("meals"):
        context_parts.append(f"\nCurrent meal plan: {len(meal_plan['meals'])} meals planned")

    context = "\n\n".join(context_parts) if context_parts else "No data yet - fresh start!"

    return f"Current household data:\n{context}"


def chat_with_claude(phone: str, user_message: str) -> str:
    """Send message to Claude and get response."""
    if not AI_ENABLED or not anthropic_client:
        return "AI features are not enabled. Please check your configuration."

    # Get conversation history
    history = get_conversation_history(phone)

    # Build messages for Claude
    messages = []

    # Add conversation history (last 10 exchanges)
    for msg in history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Get household context
    context = get_context_for_claude(phone)

    # Create full system prompt with context
    system_prompt = f"{JULES_SYSTEM_PROMPT}\n\n{context}"

    try:
        # Call Claude API
        response = anthropic_client.messages.create(
            model=AI_MODEL,
            max_tokens=AI_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
            system=system_prompt,
            messages=messages
        )

        assistant_message = response.content[0].text

        # Log usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        # Sonnet 4.5 pricing: $3/M input, $15/M output
        cost = (input_tokens / 1_000_000) * 3.0 + (output_tokens / 1_000_000) * 15.0
        log_ai_usage("conversation", input_tokens, output_tokens, cost)

        # Update conversation history
        history.append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
        history.append({"role": "assistant", "content": assistant_message, "timestamp": datetime.now().isoformat()})
        save_conversation_history(phone, history)

        return assistant_message

    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        return "Sorry, I'm having trouble thinking right now. Can you try again?"


def extract_recipe_from_conversation(phone: str) -> Optional[dict]:
    """Parse conversation history to extract recipe data."""
    history = get_conversation_history(phone)

    # Look at recent messages for recipe data
    recent_messages = ' '.join([msg['content'] for msg in history[-10:] if msg['role'] == 'user'])

    # Try to use Claude to extract structured data
    if not AI_ENABLED:
        return None

    extraction_prompt = f"""Based on this conversation, extract recipe information if available.

Conversation: {recent_messages}

If you can identify a recipe with name, ingredients, and cook time, respond with ONLY valid JSON in this format:
{{"name": "Recipe Name", "ingredients": ["ingredient1", "ingredient2"], "cook_time": 30}}

If you cannot extract a complete recipe, respond with: {{"error": "incomplete"}}"""

    try:
        response = anthropic_client.messages.create(
            model=AI_MODEL,
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": extraction_prompt}]
        )

        result = json.loads(response.content[0].text)
        if "error" not in result:
            return result
    except:
        pass

    return None


# ============================================================================
# Main Message Router
# ============================================================================

def process_message(phone: str, message: str) -> str:
    """Process incoming message with Claude AI."""
    logger.info(f"msg_received phone={phone} msg={message[:50]}")

    # Initialize household if needed
    household = get_household()
    if not household:
        save_household({
            "members": {
                YOUR_PHONE: {"name": "You", "phone": YOUR_PHONE},
                WIFE_PHONE: {"name": "Wife", "phone": WIFE_PHONE}
            },
            "created_at": datetime.now().isoformat()
        })

    # Check for special commands that trigger actions
    message_upper = message.strip().upper()

    # SAVE command - try to extract and save recipe from conversation
    if message_upper == "SAVE":
        recipe = extract_recipe_from_conversation(phone)
        if recipe:
            recipes = get_recipes()
            recipe["added_at"] = datetime.now().isoformat()
            recipes.append(recipe)
            save_recipes(recipes)
            return f"✓ Saved {recipe['name']}! You now have {len(recipes)} recipes. Text LIST to see them all."
        else:
            return "I couldn't find enough recipe details in our conversation. Can you tell me the recipe name, ingredients (comma-separated), and cook time?"

    # Use Claude for conversational response
    response = chat_with_claude(phone, message)

    # Check if Claude's response indicates a recipe was completed
    # (This is a simple heuristic - Claude will naturally guide the conversation)
    if any(word in message.lower() for word in ["that's all", "that's it", "done", "finished"]):
        recipe = extract_recipe_from_conversation(phone)
        if recipe:
            recipes = get_recipes()
            recipe["added_at"] = datetime.now().isoformat()
            recipes.append(recipe)
            save_recipes(recipes)
            response += f"\n\n✓ Saved {recipe['name']}! Text LIST to see all {len(recipes)} recipes."

    return response


# ============================================================================
# FastAPI Routes
# ============================================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "app": "Jules AI MVP",
        "ai_enabled": AI_ENABLED,
        "model": AI_MODEL if AI_ENABLED else "none"
    }


@app.post("/sms/webhook", response_class=PlainTextResponse)
async def sms_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """Handle inbound SMS from Twilio."""

    # Process message
    response_text = process_message(From, Body)

    # Send response
    send_sms(From, response_text)

    # Twilio expects TwiML response
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


@app.get("/data/recipes")
async def get_recipes_data():
    """View recipes (admin)."""
    return {"recipes": get_recipes()}


@app.get("/data/conversation/{phone}")
async def get_conversation_data(phone: str):
    """View conversation history (admin)."""
    return {"history": get_conversation_history(phone)}


@app.get("/data/ai-usage")
async def get_ai_usage():
    """View AI usage and costs (admin)."""
    usage_file = DATA_DIR / "ai_usage.json"
    if usage_file.exists():
        with open(usage_file) as f:
            return json.load(f)
    return {"message": "No AI usage data yet"}


if __name__ == "__main__":
    import uvicorn

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
