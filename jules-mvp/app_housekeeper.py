"""
AI Housekeeper - SMS-Based Household Management Assistant

Conversational AI companion for household task management via SMS.
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from anthropic import Anthropic
import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    handlers=[
        logging.FileHandler("logs/housekeeper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="AI Housekeeper")

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE = os.getenv("YOUR_PHONE")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
validator = RequestValidator(TWILIO_AUTH_TOKEN)

# Claude AI setup
AI_ENABLED = os.getenv("ENABLE_AI_FEATURES", "false").lower() == "true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-5-20250929")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", 1024))  # Lower for cost control
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", 0.7))

if AI_ENABLED:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info(f"AI features enabled with model: {AI_MODEL}")
else:
    anthropic_client = None
    logger.info("AI features disabled - using rule-based responses only")

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# Onboarding State Machine
# ============================================================================

class OnboardingState(Enum):
    """Onboarding conversation states"""
    NEW_USER = "new_user"
    WELCOME_SENT = "welcome_sent"
    AWAITING_ACK = "awaiting_acknowledgment"
    TRUST_BUILDING = "trust_building"
    CAPABILITY_INTRO = "capability_intro"
    QUICK_WIN_SETUP = "quick_win_setup"
    PREFERENCE_GATHERING = "preference_gathering"
    FIRST_TASK_CONFIG = "first_task_configured"
    ONBOARDED = "onboarded"
    PAUSED = "paused"
    OPTED_OUT = "opted_out"

    # Error states
    CLARIFICATION_REQUEST = "clarification_request"
    TRUST_RECOVERY = "trust_recovery"

class QuickWinType(Enum):
    """Types of quick wins during onboarding"""
    CHORE_REMINDER = "chore_reminder"
    TODO_TRACKING = "todo_tracking"
    CLEANING_ROUTINE = "cleaning_routine"
    HOUSEHOLD_PROFILE = "household_profile"

# ============================================================================
# System Prompts
# ============================================================================

HOUSEKEEPER_SYSTEM_PROMPT = """You are Jules, a friendly AI household assistant communicating via SMS.

Your purpose is to help households with meal planning, pantry management, and recipe suggestions:
- Learn what's in their pantry over time
- Suggest recipes based on available ingredients
- Track their family recipes
- Help with meal planning and grocery lists
- Remember household members and dietary preferences

Key personality traits:
- Warm and conversational, like a helpful friend
- Concise responses (SMS-friendly, 140-250 characters ideal)
- Patient teacher (explaining how you learn and improve)
- Proactive but not pushy
- Inclusive and respectful of all family structures
- Organized and reliable

Current MVP capabilities:
- Store family recipes
- Learn household member preferences (dietary restrictions, ages)
- Basic meal suggestions based on stored recipes
- Generate shopping lists from recipes
- Plan weekly meals
- Respect dietary needs (vegetarian, vegan, allergies, religious, cultural)

Future capabilities (explain during onboarding):
- Automatically learn pantry inventory over time
- Suggest when to buy toilet paper, cleaning supplies
- Recipe recommendations based on what's in stock
- Smart pantry-based shopping lists (only buy what you need)

SMS constraints:
- Keep responses under 300 characters when possible
- Use emojis sparingly (0-1 per message)
- Be conversational but concise
- Ask clear, simple questions
- Provide numbered options when helpful

Conversation style:
- Use "I" statements (I'll learn, I can help)
- Confirm actions clearly
- Give users control (they can pause, stop, modify anytime)
- Be encouraging and positive
- Never assume family structure (use inclusive language)
- Respect all dietary choices without judgment

DEI principles:
- Use gender-neutral terms unless user specifies
- Never assume relationships (ask, don't assume)
- Respect all dietary restrictions equally (cultural, religious, health, ethical)
- Use "household members" not "family" until user's term is known
- Support diverse household structures

Remember: You're learning about this household. Be curious, respectful, and patient."""

TASK_EXTRACTION_PROMPT = """Extract household task information from this message.

Message: {message}

Return ONLY valid JSON with this structure:
{{
  "task": "brief task description",
  "frequency": "once|daily|weekly|monthly|custom",
  "day": "monday|tuesday|etc or null",
  "time": "morning|afternoon|evening|specific time or null",
  "confidence": "high|medium|low"
}}

If you cannot extract a clear task, return: {{"error": "unclear"}}"""

INTENT_CLASSIFICATION_PROMPT = """Classify this message intent for household management.

Message: {message}

Return ONLY one word:
- chore_reminder (user wants reminder for recurring task)
- todo_item (user wants to track a one-time task)
- cleaning_routine (user wants cleaning schedule)
- household_info (user sharing household details)
- question (user asking a question)
- unclear (cannot determine intent)

Classification:"""

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
# User State Management
# ============================================================================

def get_user_state(phone: str) -> Dict:
    """Get user's onboarding and conversation state."""
    states = load_json("user_states.json")
    if phone not in states:
        states[phone] = {
            "phone": phone,
            "onboarding_state": OnboardingState.NEW_USER.value,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "messages_exchanged": 0,
            "onboarded": False,
            "quick_win_type": None,
            "temp_data": {},  # Temporary data during flows
            "previous_state": None  # For back/undo
        }
        save_json("user_states.json", states)
    return states[phone]

def update_user_state(phone: str, updates: Dict):
    """Update user's state."""
    states = load_json("user_states.json")
    if phone in states:
        states[phone].update(updates)
        states[phone]["last_activity"] = datetime.now().isoformat()
        save_json("user_states.json", states)

def set_onboarding_state(phone: str, new_state: OnboardingState, temp_data: Dict = None):
    """Change user's onboarding state."""
    user_state = get_user_state(phone)
    updates = {
        "previous_state": user_state["onboarding_state"],
        "onboarding_state": new_state.value
    }
    if temp_data:
        updates["temp_data"] = {**user_state.get("temp_data", {}), **temp_data}
    update_user_state(phone, updates)

def get_household_profile(phone: str) -> Dict:
    """Get household profile for user."""
    profiles = load_json("household_profiles.json")
    return profiles.get(phone, {
        "phone": phone,
        "household_size": None,
        "members": [],  # List of {"name": "X", "age": Y, "dietary_restrictions": [...]}
        "members_added": 0,
        "created_at": datetime.now().isoformat()
    })

def update_household_profile(phone: str, updates: Dict):
    """Update household profile."""
    profiles = load_json("household_profiles.json")
    if phone not in profiles:
        profiles[phone] = get_household_profile(phone)
    profiles[phone].update(updates)
    save_json("household_profiles.json", profiles)

def add_household_member(phone: str, member: Dict):
    """Add a household member."""
    profile = get_household_profile(phone)
    profile["members"].append(member)
    profile["members_added"] = len(profile["members"])
    update_household_profile(phone, profile)

def get_tasks(phone: str) -> List[Dict]:
    """Get user's tasks and reminders."""
    all_tasks = load_json("tasks.json")
    return all_tasks.get(phone, [])

def add_task(phone: str, task: Dict):
    """Add a task for user."""
    all_tasks = load_json("tasks.json")
    if phone not in all_tasks:
        all_tasks[phone] = []

    task["id"] = len(all_tasks[phone]) + 1
    task["created_at"] = datetime.now().isoformat()
    task["status"] = "active"

    all_tasks[phone].append(task)
    save_json("tasks.json", all_tasks)
    return task

def get_conversation_history(phone: str) -> List[Dict]:
    """Get conversation history."""
    histories = load_json("conversation_history.json")
    return histories.get(phone, [])

def save_conversation_history(phone: str, history: List[Dict]):
    """Save conversation history."""
    histories = load_json("conversation_history.json")
    histories[phone] = history[-30:]  # Keep last 30 messages
    save_json("conversation_history.json", histories)

def log_ai_usage(feature: str, input_tokens: int, output_tokens: int, cost: float):
    """Track AI usage and costs."""
    usage_file = DATA_DIR / "ai_usage.json"
    if usage_file.exists():
        with open(usage_file) as f:
            usage = json.load(f)
    else:
        usage = {}

    month = datetime.now().strftime("%Y-%m")
    if month not in usage:
        usage[month] = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost": 0.0,
            "by_feature": {}
        }

    usage[month]["total_requests"] += 1
    usage[month]["total_input_tokens"] += input_tokens
    usage[month]["total_output_tokens"] += output_tokens
    usage[month]["estimated_cost"] += cost

    if feature not in usage[month]["by_feature"]:
        usage[month]["by_feature"][feature] = {"requests": 0, "cost": 0.0}
    usage[month]["by_feature"][feature]["requests"] += 1
    usage[month]["by_feature"][feature]["cost"] += cost

    with open(usage_file, 'w') as f:
        json.dump(usage, f, indent=2)

    threshold = float(os.getenv("AI_COST_ALERT_THRESHOLD", 10.00))
    if usage[month]["estimated_cost"] > threshold:
        logger.warning(f"AI cost alert: ${usage[month]['estimated_cost']:.2f} exceeds ${threshold:.2f}")

    logger.info(f"AI usage: {feature} - {input_tokens}in + {output_tokens}out = ${cost:.4f}")

# ============================================================================
# Pattern Matching for Rule-Based Responses
# ============================================================================

def matches_simple_pattern(message: str) -> Optional[str]:
    """Check if message matches simple patterns for rule-based routing."""
    msg_lower = message.lower().strip()

    # Affirmative
    if re.match(r'\b(yes|yeah|yep|sure|ok|okay|fine|good|yup)\b', msg_lower):
        return 'AFFIRMATIVE'

    # Negative
    if re.match(r'\b(no|nope|nah|not really)\b', msg_lower):
        return 'NEGATIVE'

    # Opt-out keywords
    if re.match(r'\b(stop|end|quit|cancel|unsubscribe)\b', msg_lower):
        return 'OPT_OUT'

    # Pause
    if re.match(r'\b(pause|wait|later|hold)\b', msg_lower):
        return 'PAUSE_REQUEST'

    # Help
    if re.match(r'\b(help|what|how|commands|options)\b', msg_lower):
        return 'HELP_REQUEST'

    # Numeric choice
    if re.match(r'^\d+$', msg_lower):
        return 'NUMERIC_CHOICE'

    # Day mention
    if re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b', msg_lower):
        return 'DAY_MENTION'

    # Greeting
    if re.match(r'\b(hi|hello|hey|start)\b', msg_lower):
        return 'GREETING'

    return None

# ============================================================================
# AI Helpers
# ============================================================================

def should_use_ai(message: str, state: OnboardingState) -> bool:
    """Determine if AI should be used for this message."""
    if not AI_ENABLED or not anthropic_client:
        return False

    # Always rule-based for these states
    if state in [OnboardingState.WELCOME_SENT, OnboardingState.TRUST_BUILDING,
                 OnboardingState.OPTED_OUT]:
        return False

    # Check for simple patterns first
    if matches_simple_pattern(message):
        return False

    # Use AI for natural language in these states
    if state in [OnboardingState.QUICK_WIN_SETUP, OnboardingState.PREFERENCE_GATHERING,
                 OnboardingState.ONBOARDED]:
        return True

    return False

def classify_intent_with_ai(message: str) -> str:
    """Use AI to classify message intent."""
    if not AI_ENABLED:
        return "unclear"

    try:
        response = anthropic_client.messages.create(
            model=AI_MODEL,
            max_tokens=50,
            temperature=0,
            messages=[{
                "role": "user",
                "content": INTENT_CLASSIFICATION_PROMPT.format(message=message)
            }]
        )

        intent = response.content[0].text.strip().lower()

        # Log minimal usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000) * 3.0 + (output_tokens / 1_000_000) * 15.0
        log_ai_usage("intent_classification", input_tokens, output_tokens, cost)

        return intent
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return "unclear"

def extract_task_with_ai(message: str) -> Optional[Dict]:
    """Use AI to extract task details from natural language."""
    if not AI_ENABLED:
        return None

    try:
        response = anthropic_client.messages.create(
            model=AI_MODEL,
            max_tokens=200,
            temperature=0,
            messages=[{
                "role": "user",
                "content": TASK_EXTRACTION_PROMPT.format(message=message)
            }]
        )

        result = json.loads(response.content[0].text.strip())

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000) * 3.0 + (output_tokens / 1_000_000) * 15.0
        log_ai_usage("task_extraction", input_tokens, output_tokens, cost)

        if "error" in result:
            return None
        return result
    except Exception as e:
        logger.error(f"Task extraction error: {e}")
        return None

def generate_ai_response(phone: str, message: str, context: str = "") -> str:
    """Generate conversational AI response."""
    if not AI_ENABLED:
        return "I'm having trouble right now. Please try a simple command like HELP."

    history = get_conversation_history(phone)
    profile = get_household_profile(phone)

    # Build context
    context_parts = []
    if profile.get("household_size"):
        context_parts.append(f"Household: {profile['household_size']} people")
    if profile.get("has_children"):
        context_parts.append("Has children")
    if profile.get("has_pets"):
        context_parts.append("Has pets")

    if context:
        context_parts.append(context)

    full_context = "\n".join(context_parts) if context_parts else "New user"
    system_prompt = f"{HOUSEKEEPER_SYSTEM_PROMPT}\n\nUser Context:\n{full_context}"

    # Build messages with limited history
    messages = []
    for msg in history[-6:]:  # Only last 6 messages for context
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": message})

    try:
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
        cost = (input_tokens / 1_000_000) * 3.0 + (output_tokens / 1_000_000) * 15.0
        log_ai_usage("conversation", input_tokens, output_tokens, cost)

        # Save history
        history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
        history.append({"role": "assistant", "content": assistant_message, "timestamp": datetime.now().isoformat()})
        save_conversation_history(phone, history)

        return assistant_message
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return "I'm having trouble thinking right now. Can you try rephrasing that?"

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
# Onboarding Message Flows (Rule-Based)
# ============================================================================

def handle_new_user(phone: str) -> str:
    """Handle first contact with new user."""
    set_onboarding_state(phone, OnboardingState.WELCOME_SENT)
    return ("Hi! I'm Jules, your AI meal planning assistant 👋\n\n"
            "I help with recipes, meal planning, and eventually I'll learn what's "
            "in your pantry to make smart suggestions.\n\n"
            "Reply HI to get started, or STOP to opt out.")

def handle_welcome_sent(phone: str, message: str) -> str:
    """Handle response to welcome message."""
    pattern = matches_simple_pattern(message)

    if pattern == 'GREETING' or pattern == 'AFFIRMATIVE':
        set_onboarding_state(phone, OnboardingState.TRUST_BUILDING)
        return ("Awesome! Let me explain how this works.\n\n"
                "I'm an AI that builds a knowledge base about YOUR household - "
                "your recipes, who lives with you, dietary needs, and over time "
                "I'll learn what's in your pantry.\n\n"
                "Your data stays private and you're in complete control.\n\n"
                "Sound good so far?")
    elif pattern == 'OPT_OUT':
        return handle_opt_out(phone)
    else:
        return ("Just say hi to get started! Or reply STOP if you'd rather not.")

def handle_trust_building(phone: str, message: str) -> str:
    """Handle trust building confirmation."""
    pattern = matches_simple_pattern(message)

    if pattern == 'AFFIRMATIVE' or 'good' in message.lower() or 'ok' in message.lower():
        set_onboarding_state(phone, OnboardingState.CAPABILITY_INTRO)
        return ("Great! Here's what I can do:\n\n"
                "RIGHT NOW:\n"
                "• Store your family recipes\n"
                "• Learn about everyone in your household\n"
                "• Suggest meals from your recipe collection\n"
                "• Generate shopping lists\n"
                "• Plan weekly meals\n\n"
                "COMING SOON:\n"
                "• Learn what's in your pantry over time\n"
                "• Smart grocery suggestions (based on pantry)\n"
                "• Track household supplies\n\n"
                "Want to get started?")
    elif pattern == 'NEGATIVE':
        set_onboarding_state(phone, OnboardingState.TRUST_RECOVERY)
        return ("No problem! What's on your mind? Happy to answer any questions.")
    else:
        return "What do you think? Ready to try it out?"

def handle_capability_intro(phone: str, message: str) -> str:
    """Handle capability selection - start with household profile."""
    pattern = matches_simple_pattern(message)

    if pattern == 'AFFIRMATIVE' or pattern == 'GREETING' or 'yes' in message.lower() or 'sure' in message.lower():
        # Go directly to preference gathering
        set_onboarding_state(phone, OnboardingState.PREFERENCE_GATHERING)
        return ("Perfect! Let's start by learning about your household.\n\n"
                "How many people live with you?\n\n"
                "(Just send me a number like 3 or 4)")
    else:
        return "Ready when you are! Just let me know."

def handle_quick_win_setup(phone: str, message: str) -> str:
    """Handle quick win configuration flow."""
    user_state = get_user_state(phone)
    quick_win_type = user_state.get("temp_data", {}).get("quick_win_type")

    if quick_win_type == QuickWinType.CHORE_REMINDER.value:
        return handle_chore_reminder_flow(phone, message, user_state)
    elif quick_win_type == QuickWinType.TODO_TRACKING.value:
        return handle_todo_tracking_flow(phone, message, user_state)
    elif quick_win_type == QuickWinType.CLEANING_ROUTINE.value:
        return handle_cleaning_routine_flow(phone, message, user_state)
    else:
        return "Something went wrong. Reply HELP for assistance."

def handle_chore_reminder_flow(phone: str, message: str, user_state: Dict) -> str:
    """Handle chore reminder setup flow."""
    temp_data = user_state.get("temp_data", {})

    # Step 1: Get the chore description
    if "chore_task" not in temp_data:
        # Extract task from message
        task_data = extract_task_with_ai(message)
        if task_data and task_data.get("task"):
            chore_task = task_data["task"]
        else:
            chore_task = message.strip()

        set_onboarding_state(phone, OnboardingState.QUICK_WIN_SETUP, {
            "quick_win_type": QuickWinType.CHORE_REMINDER.value,
            "chore_task": chore_task
        })
        return f"When does '{chore_task}' need to happen? Reply with a day like 'Tuesday' or 'Every Wednesday morning'"

    # Step 2: Get the schedule
    elif "chore_schedule" not in temp_data:
        pattern = matches_simple_pattern(message)
        if pattern == 'DAY_MENTION':
            day_match = re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', message.lower())
            if day_match:
                day = day_match.group(1).capitalize()
                set_onboarding_state(phone, OnboardingState.QUICK_WIN_SETUP, {
                    "quick_win_type": QuickWinType.CHORE_REMINDER.value,
                    "chore_task": temp_data["chore_task"],
                    "chore_schedule": day
                })
                return f"Perfect! I'll remind you about '{temp_data['chore_task']}' every {day}. Want the reminder the night before? Reply YES or NO."

        # Fallback
        set_onboarding_state(phone, OnboardingState.QUICK_WIN_SETUP, {
            "quick_win_type": QuickWinType.CHORE_REMINDER.value,
            "chore_task": temp_data["chore_task"],
            "chore_schedule": message.strip()
        })
        return f"Got it - {message.strip()}. I'll remind you about '{temp_data['chore_task']}'. Sound good? Reply YES to confirm."

    # Step 3: Confirmation and save
    else:
        pattern = matches_simple_pattern(message)
        if pattern == 'AFFIRMATIVE' or pattern is None:
            # Save the task
            task = add_task(phone, {
                "type": "chore_reminder",
                "description": temp_data["chore_task"],
                "schedule": temp_data.get("chore_schedule"),
                "reminder_before": pattern == 'AFFIRMATIVE'
            })

            # Mark as onboarded
            update_user_state(phone, {
                "onboarded": True,
                "temp_data": {}
            })
            set_onboarding_state(phone, OnboardingState.ONBOARDED)

            return (f"You're all set! I'll remind you about '{temp_data['chore_task']}'.\n\n"
                    "You're ready to go! Text me anytime to:\n"
                    "- Add reminders (just tell me what)\n"
                    "- See your tasks (reply TODO)\n"
                    "- Get help (reply HELP)\n\n"
                    "Try it now - tell me something you need to remember!")
        else:
            return "Reply YES to save this reminder, or tell me what to change."

def handle_todo_tracking_flow(phone: str, message: str, user_state: Dict) -> str:
    """Handle to-do list setup flow."""
    # Extract multiple tasks from message
    tasks = extract_task_with_ai(message)

    # Simple implementation - parse line by line or comma-separated
    task_list = [t.strip() for t in message.split(',') if t.strip()]
    if not task_list:
        task_list = [t.strip() for t in message.split('\n') if t.strip()]

    if len(task_list) == 0:
        return "Tell me what tasks you need to track. You can list them separated by commas or on separate lines."

    # Save tasks
    for task_desc in task_list:
        add_task(phone, {
            "type": "todo_item",
            "description": task_desc,
            "status": "pending"
        })

    # Build response
    task_list_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(task_list)])

    update_user_state(phone, {"onboarded": True, "temp_data": {}})
    set_onboarding_state(phone, OnboardingState.ONBOARDED)

    return (f"Added to your list:\n{task_list_str}\n\n"
            "You're all set! Text me to:\n"
            "- Add more tasks\n"
            "- Mark tasks done (TODO)\n"
            "- Get help (HELP)")

def handle_cleaning_routine_flow(phone: str, message: str, user_state: Dict) -> str:
    """Handle cleaning routine setup."""
    # Parse time from message
    if "10" in message:
        time = "10min"
    elif "20" in message:
        time = "20min"
    elif "30" in message:
        time = "30min"
    else:
        return "How much time daily? Reply: 10min, 20min, or 30min"

    # Generate simple routine
    routines = {
        "10min": "Mon: Kitchen quick-clean\nTue: Bathroom wipe-down\nWed: Living room tidy\nThu: Bedroom pickup\nFri: Catch-up",
        "20min": "Mon: Kitchen (wipe, sweep)\nTue: Bathrooms (clean)\nWed: Living areas (vacuum)\nThu: Bedrooms (organize)\nFri: Deep clean one area",
        "30min": "Mon: Kitchen deep clean\nTue: All bathrooms\nWed: Living + dining rooms\nThu: All bedrooms\nFri: Laundry + catch-up"
    }

    routine = routines.get(time, routines["20min"])

    update_user_state(phone, {"onboarded": True, "temp_data": {}})
    set_onboarding_state(phone, OnboardingState.ONBOARDED)

    return (f"Here's your {time} daily routine:\n\n{routine}\n\n"
            "Want daily reminders? Reply YES or NO")

def handle_preference_gathering(phone: str, message: str) -> str:
    """Handle household profile building with member collection."""
    profile = get_household_profile(phone)
    user_state = get_user_state(phone)
    temp_data = user_state.get("temp_data", {})

    # Step 1: Get household size
    if profile.get("household_size") is None:
        number_match = re.search(r'\d+', message)
        if number_match:
            size = int(number_match.group())
            update_household_profile(phone, {"household_size": size})
            if size == 1:
                return "Just you? Perfect! What's your name?"
            else:
                return (f"Nice - {size} people! Let's learn about everyone so I can "
                        f"suggest meals that work for the whole household.\n\n"
                        f"First person - what's their name?")
        else:
            return "Just send me the number of people in your household."

    # Step 2-N: Collect member information
    members_added = profile.get("members_added", 0)
    total_members = profile.get("household_size", 0)

    if members_added < total_members:
        # Sub-flow for each member
        current_member = temp_data.get("current_member", {})

        # Get name
        if "name" not in current_member:
            name = message.strip()
            current_member["name"] = name
            set_onboarding_state(phone, OnboardingState.PREFERENCE_GATHERING, {
                "current_member": current_member
            })
            return f"Nice to meet {name}! How old are they?\n\n(Helps me suggest age-appropriate meals)"

        # Get age
        elif "age" not in current_member:
            age_match = re.search(r'\d+', message)
            if age_match:
                current_member["age"] = int(age_match.group())
            else:
                current_member["age"] = message.strip()  # Handle "toddler", "baby", etc.

            set_onboarding_state(phone, OnboardingState.PREFERENCE_GATHERING, {
                "current_member": current_member
            })
            return (f"Got it! Any dietary restrictions for {current_member['name']}?\n\n"
                    f"Like: vegetarian, vegan, gluten-free, dairy-free, nut allergy, halal, kosher...\n\n"
                    f"Or just say 'none' if they eat everything!")

        # Get dietary restrictions
        elif "dietary_restrictions" not in current_member:
            restrictions_text = message.strip().lower()

            if restrictions_text in ["none", "no", "nope", "n/a", "everything", "anything"]:
                current_member["dietary_restrictions"] = []
            else:
                # Parse comma-separated restrictions
                restrictions = [r.strip() for r in restrictions_text.split(',')]
                current_member["dietary_restrictions"] = restrictions

            # Save this member
            add_household_member(phone, current_member)

            # Check if more members to add
            new_count = profile.get("members_added", 0)

            if new_count < total_members:
                # More members to add
                set_onboarding_state(phone, OnboardingState.PREFERENCE_GATHERING, {
                    "current_member": {}
                })
                return f"Perfect! Next person - what's their name?"
            else:
                # All members added - complete onboarding
                update_user_state(phone, {"onboarded": True, "temp_data": {}})
                set_onboarding_state(phone, OnboardingState.ONBOARDED)

                # Build summary
                member_summary = "\n".join([
                    f"• {m['name']}, {m['age']}" +
                    (f" ({', '.join(m['dietary_restrictions'])})" if m['dietary_restrictions'] else "")
                    for m in profile["members"]
                ])

                return (f"Perfect! Here's everyone:\n\n{member_summary}\n\n"
                        f"Now I can suggest meals that work for your whole household!\n\n"
                        f"Want to add your first recipe? Just tell me about a meal you all love.")

    return "Reply HELP if you're stuck!"

# ============================================================================
# Special Handlers
# ============================================================================

def handle_opt_out(phone: str) -> str:
    """Handle user opt-out request."""
    set_onboarding_state(phone, OnboardingState.OPTED_OUT)
    return ("Got it! You're all set - no more messages from Jules. "
            "Your data will be deleted within 30 days.\n\n"
            "If you change your mind, just text START. Take care!")

def handle_pause_request(phone: str) -> str:
    """Handle pause request."""
    user_state = get_user_state(phone)
    set_onboarding_state(phone, OnboardingState.PAUSED)
    return ("No problem! Take your time. Just text me when you're ready to continue.\n\n"
            "(I'll check back in 24 hours too, just in case!)")

def handle_help_request(phone: str) -> str:
    """Handle help request."""
    user_state = get_user_state(phone)
    if user_state.get("onboarded"):
        return ("Here's what I can do:\n\n"
                "• Add recipes (just tell me about them)\n"
                "• RECIPES - see all your recipes\n"
                "• PROFILE - see household info\n"
                "• SUGGEST - get meal ideas\n"
                "• PAUSE - take a break\n"
                "• STOP - unsubscribe\n\n"
                "Or just chat with me naturally!")
    else:
        return ("Hey! I'm Jules, your AI meal planning assistant.\n\n"
                "Just say HI to finish getting set up!\n\n"
                "Or text STOP if you'd rather not.")

def handle_clarification_request(phone: str, message: str) -> str:
    """Handle unclear messages."""
    return ("Hmm, I didn't quite get that.\n\n"
            "Text HELP to see what I can do, or just tell me what you need in your own words!")

# ============================================================================
# Main Message Router
# ============================================================================

def process_message(phone: str, message: str) -> str:
    """Main message processing logic with state machine."""
    logger.info(f"msg_received phone={phone} msg={message[:100]}")

    # Get user state
    user_state = get_user_state(phone)
    current_state = OnboardingState(user_state["onboarding_state"])

    # Update message count
    update_user_state(phone, {
        "messages_exchanged": user_state.get("messages_exchanged", 0) + 1
    })

    # Check for global commands first
    pattern = matches_simple_pattern(message)

    if pattern == 'OPT_OUT':
        return handle_opt_out(phone)
    elif pattern == 'PAUSE_REQUEST':
        return handle_pause_request(phone)
    elif pattern == 'HELP_REQUEST':
        return handle_help_request(phone)

    # Route based on onboarding state
    if current_state == OnboardingState.NEW_USER:
        return handle_new_user(phone)

    elif current_state == OnboardingState.WELCOME_SENT:
        return handle_welcome_sent(phone, message)

    elif current_state == OnboardingState.TRUST_BUILDING:
        return handle_trust_building(phone, message)

    elif current_state == OnboardingState.CAPABILITY_INTRO:
        return handle_capability_intro(phone, message)

    elif current_state == OnboardingState.QUICK_WIN_SETUP:
        return handle_quick_win_setup(phone, message)

    elif current_state == OnboardingState.PREFERENCE_GATHERING:
        return handle_preference_gathering(phone, message)

    elif current_state == OnboardingState.ONBOARDED:
        # Fully onboarded - use AI for natural conversation
        if should_use_ai(message, current_state):
            return generate_ai_response(phone, message)
        else:
            # Handle simple commands
            if pattern == 'HELP_REQUEST':
                return handle_help_request(phone)
            elif message.upper().strip() == 'TODO':
                tasks = get_tasks(phone)
                if tasks:
                    task_list = "\n".join([f"{i+1}. {t['description']}" for i, t in enumerate(tasks) if t.get('status') == 'active'])
                    return f"Your tasks:\n{task_list}\n\nReply with task number to mark done."
                else:
                    return "No tasks yet! Tell me what you need to remember."
            else:
                return generate_ai_response(phone, message)

    elif current_state == OnboardingState.PAUSED:
        if pattern == 'AFFIRMATIVE' or 'continue' in message.lower():
            # Resume from previous state
            previous_state = user_state.get("previous_state", OnboardingState.CAPABILITY_INTRO.value)
            set_onboarding_state(phone, OnboardingState(previous_state))
            return "Welcome back! Let's continue where we left off."
        else:
            return "Reply CONTINUE when you're ready to resume setup."

    elif current_state == OnboardingState.OPTED_OUT:
        if pattern == 'GREETING' or 'start' in message.lower():
            set_onboarding_state(phone, OnboardingState.WELCOME_SENT)
            return "Welcome back! Let's get you set up. Reply HI to continue."
        else:
            return "You're currently opted out. Reply START to rejoin."

    else:
        return handle_clarification_request(phone, message)

# ============================================================================
# FastAPI Routes
# ============================================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "app": "AI Housekeeper",
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

@app.get("/admin/users")
async def get_users():
    """Get all user states (admin)."""
    return load_json("user_states.json")

@app.get("/admin/user/{phone}")
async def get_user_info(phone: str):
    """Get specific user info (admin)."""
    return {
        "state": get_user_state(phone),
        "profile": get_household_profile(phone),
        "tasks": get_tasks(phone),
        "history": get_conversation_history(phone)
    }

@app.get("/admin/ai-usage")
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
