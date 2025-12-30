"""
Jules MVP - Single file FastAPI app for 2-user testing.

Ultra-minimal implementation for validating SMS workflow.
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.request_validator import RequestValidator
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
app = FastAPI(title="Jules MVP")

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE = os.getenv("YOUR_PHONE")
WIFE_PHONE = os.getenv("WIFE_PHONE")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
validator = RequestValidator(TWILIO_AUTH_TOKEN)

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


def get_conversation_state(phone: str) -> dict:
    """Get conversation state for phone number."""
    states = load_json("conversation.json")
    return states.get(phone, {"state": "IDLE", "data": {}})


def save_conversation_state(phone: str, state: str, data: dict = None):
    """Save conversation state."""
    states = load_json("conversation.json")
    states[phone] = {
        "state": state,
        "data": data or {},
        "updated_at": datetime.now().isoformat()
    }
    save_json("conversation.json", states)


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


def verify_twilio_signature(request: Request) -> bool:
    """Verify Twilio webhook signature."""
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    # Form data will be added by caller
    return True  # TODO: Implement actual verification


# ============================================================================
# Command Handlers
# ============================================================================

def handle_start(phone: str, household: dict) -> str:
    """Handle START command."""
    if not household:
        # First time setup
        save_household({
            "members": {
                YOUR_PHONE: {"name": "You", "phone": YOUR_PHONE},
                WIFE_PHONE: {"name": "Wife", "phone": WIFE_PHONE}
            },
            "created_at": datetime.now().isoformat()
        })
        save_conversation_state(phone, "IDLE")
        return """Welcome to Jules! 👋

I'll help you plan meals via text.

Commands:
RECIPE - Add a recipe
LIST - Show recipes
PLAN - Plan the week
SHOP - Get shopping list
HELP - Show commands

Try: RECIPE"""

    return "You're already set up! Text HELP for commands."


def handle_help(phone: str) -> str:
    """Handle HELP command."""
    return """Jules Commands:

RECIPE - Add new recipe
LIST - Show all recipes
VIEW # - Show recipe details
DELETE # - Remove recipe
PLAN - Start weekly planning
TONIGHT - Quick suggestion
SHOP - Get shopping list
HELP - This message

Example: "RECIPE" """


def handle_list(phone: str) -> str:
    """Handle LIST command."""
    recipes = get_recipes()

    if not recipes:
        return "No recipes yet! Text RECIPE to add one."

    lines = ["Your recipes:"]
    for i, recipe in enumerate(recipes, 1):
        cook_time = recipe.get("cook_time", "?")
        lines.append(f"{i}. {recipe['name']} ({cook_time} min)")

    lines.append("\nText VIEW # to see details")
    return "\n".join(lines)


def handle_recipe_start(phone: str) -> str:
    """Start recipe addition flow."""
    save_conversation_state(phone, "RECIPE_NAME")
    return "What's the recipe name?"


def handle_recipe_name(phone: str, message: str, state_data: dict) -> str:
    """Handle recipe name input."""
    state_data["name"] = message
    save_conversation_state(phone, "RECIPE_INGREDIENTS", state_data)
    return f"Nice! What are the main ingredients for {message}?\n(Comma separated)"


def handle_recipe_ingredients(phone: str, message: str, state_data: dict) -> str:
    """Handle ingredients input."""
    state_data["ingredients"] = [i.strip() for i in message.split(",")]
    save_conversation_state(phone, "RECIPE_TIME", state_data)
    return "How many minutes to cook?"


def handle_recipe_time(phone: str, message: str, state_data: dict) -> str:
    """Handle cook time and save recipe."""
    try:
        cook_time = int(message.strip().split()[0])  # Extract first number
    except:
        return "Please enter a number (e.g., '30 minutes' or just '30')"

    # Save recipe
    recipes = get_recipes()
    recipe = {
        "name": state_data["name"],
        "ingredients": state_data["ingredients"],
        "cook_time": cook_time,
        "added_at": datetime.now().isoformat()
    }
    recipes.append(recipe)
    save_recipes(recipes)

    save_conversation_state(phone, "IDLE")

    return f"""✓ Saved! {recipe['name']}

Ingredients: {', '.join(recipe['ingredients'])}
Cook time: {cook_time} min

Text LIST to see all recipes."""


def handle_plan_start(phone: str) -> str:
    """Start meal planning flow."""
    recipes = get_recipes()

    if len(recipes) < 2:
        return "You need at least 2 recipes to plan. Text RECIPE to add more!"

    lines = ["Let's plan this week! 🍽️\n"]
    lines.append("Your recipes:")

    for i, recipe in enumerate(recipes, 1):
        lines.append(f"{i}. {recipe['name']}")

    lines.append("\nPick 4-7 meals (numbers like: 1,2,1,3)")

    save_conversation_state(phone, "PLAN_SELECT")
    return "\n".join(lines)


def handle_plan_select(phone: str, message: str) -> str:
    """Handle meal selection."""
    recipes = get_recipes()

    try:
        # Parse selections
        selections = [int(n.strip()) - 1 for n in message.split(",")]

        # Validate
        if not all(0 <= s < len(recipes) for s in selections):
            return f"Invalid selection! Use numbers 1-{len(recipes)}"

        # Build plan
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        plan_items = []

        for i, sel in enumerate(selections[:7]):  # Max 7 days
            meal = recipes[sel]
            plan_items.append(f"{days[i]}: {meal['name']}")

        plan_text = "\n".join(plan_items)

        # Save temp plan
        save_conversation_state(phone, "PLAN_CONFIRM", {
            "selections": selections,
            "plan_text": plan_text
        })

        return f"""This week:
{plan_text}

Looks good? Reply YES or NO"""

    except:
        return "Format: 1,2,3 (numbers separated by commas)"


def handle_plan_confirm(phone: str, message: str, state_data: dict) -> str:
    """Confirm meal plan."""
    if message.upper().startswith("Y"):
        # Save plan
        recipes = get_recipes()
        selections = state_data["selections"]

        plan = {
            "meals": [recipes[s] for s in selections],
            "created_at": datetime.now().isoformat()
        }
        save_meal_plan(plan)

        save_conversation_state(phone, "IDLE")

        # Generate shopping list
        all_ingredients = []
        for meal in plan["meals"]:
            all_ingredients.extend(meal.get("ingredients", []))

        # Deduplicate
        unique_ingredients = list(set(all_ingredients))

        shopping_list = "\n".join(f"- {ing}" for ing in unique_ingredients)

        return f"""✓ Week planned!

🛒 Shopping List:
{shopping_list}

Reply DONE when you've shopped!"""

    else:
        save_conversation_state(phone, "IDLE")
        return "No problem! Text PLAN when ready."


def handle_shop(phone: str) -> str:
    """Resend shopping list."""
    plan = get_meal_plan()

    if not plan.get("meals"):
        return "No meal plan yet! Text PLAN to create one."

    all_ingredients = []
    for meal in plan["meals"]:
        all_ingredients.extend(meal.get("ingredients", []))

    unique_ingredients = list(set(all_ingredients))
    shopping_list = "\n".join(f"- {ing}" for ing in unique_ingredients)

    return f"""🛒 Shopping List:
{shopping_list}

Reply DONE when done!"""


def handle_view(phone: str, message: str) -> str:
    """View recipe details."""
    try:
        num = int(message.split()[1])  # "VIEW 3"
        recipes = get_recipes()

        if num < 1 or num > len(recipes):
            return f"Recipe {num} not found. Text LIST to see all."

        recipe = recipes[num - 1]

        return f"""📖 {recipe['name']}

⏱️ Cook time: {recipe['cook_time']} min

🥘 Ingredients:
{chr(10).join(f'- {ing}' for ing in recipe['ingredients'])}"""

    except:
        return "Format: VIEW 3 (to view recipe #3)"


def handle_delete(phone: str, message: str) -> str:
    """Delete a recipe."""
    try:
        num = int(message.split()[1])
        recipes = get_recipes()

        if num < 1 or num > len(recipes):
            return f"Recipe {num} not found."

        deleted = recipes.pop(num - 1)
        save_recipes(recipes)

        return f"✓ Deleted: {deleted['name']}"

    except:
        return "Format: DELETE 3 (to delete recipe #3)"


def handle_tonight(phone: str) -> str:
    """Quick dinner suggestion."""
    recipes = get_recipes()

    if not recipes:
        return "No recipes yet! Text RECIPE to add one."

    import random
    recipe = random.choice(recipes)

    return f"""Tonight: {recipe['name']} 🍽️

Cook time: {recipe['cook_time']} min

Ingredients:
{chr(10).join(f'- {ing}' for ing in recipe['ingredients'])}"""


# ============================================================================
# Main Message Router
# ============================================================================

def process_message(phone: str, message: str) -> str:
    """Process incoming message and return response."""
    logger.info(f"msg_received phone={phone} msg={message[:50]}")

    household = get_household()
    state_info = get_conversation_state(phone)
    state = state_info["state"]
    state_data = state_info["data"]

    message_upper = message.strip().upper()

    # Handle commands in IDLE state
    if state == "IDLE":
        if message_upper == "START":
            return handle_start(phone, household)
        elif message_upper == "HELP":
            return handle_help(phone)
        elif message_upper == "LIST":
            return handle_list(phone)
        elif message_upper == "RECIPE":
            return handle_recipe_start(phone)
        elif message_upper == "PLAN":
            return handle_plan_start(phone)
        elif message_upper == "SHOP":
            return handle_shop(phone)
        elif message_upper.startswith("VIEW"):
            return handle_view(phone, message_upper)
        elif message_upper.startswith("DELETE"):
            return handle_delete(phone, message_upper)
        elif message_upper == "TONIGHT":
            return handle_tonight(phone)
        else:
            return "Not sure what you mean. Text HELP for commands."

    # Handle conversation flows
    elif state == "RECIPE_NAME":
        return handle_recipe_name(phone, message, state_data)
    elif state == "RECIPE_INGREDIENTS":
        return handle_recipe_ingredients(phone, message, state_data)
    elif state == "RECIPE_TIME":
        return handle_recipe_time(phone, message, state_data)
    elif state == "PLAN_SELECT":
        return handle_plan_select(phone, message)
    elif state == "PLAN_CONFIRM":
        return handle_plan_confirm(phone, message, state_data)

    return "Something went wrong! Text HELP to reset."


# ============================================================================
# FastAPI Routes
# ============================================================================

@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "app": "Jules MVP"}


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


@app.get("/data/household")
async def get_household_data():
    """View household data (admin)."""
    return get_household()


@app.get("/data/recipes")
async def get_recipes_data():
    """View recipes (admin)."""
    return {"recipes": get_recipes()}


@app.get("/data/plan")
async def get_plan_data():
    """View meal plan (admin)."""
    return get_meal_plan()


@app.get("/data/conversation")
async def get_conversation_data():
    """View conversation states (admin)."""
    return load_json("conversation.json")


if __name__ == "__main__":
    import uvicorn

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
