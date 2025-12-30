# Jules MVP - Quick Start

## Environment Setup Status

✅ Virtual environment created
✅ Dependencies installed
✅ Data and logs directories created
⚠️ .env file needs completion

## Next Steps

### 1. Complete .env Configuration

Edit `/Users/crucial/Documents/dev/Jules/jules-mvp/.env`:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=OR0e16f7d40cb2280988c79b8f57b41f60  # ✅ Already set
TWILIO_AUTH_TOKEN=your_auth_token_here                  # ⚠️ NEEDS UPDATE
TWILIO_PHONE_NUMBER=+1234567890                         # ⚠️ NEEDS UPDATE

# Your Phone Numbers (E.164 format)
YOUR_PHONE=+14157979915                                  # ✅ Already set
WIFE_PHONE=+1                                           # ⚠️ NEEDS UPDATE
```

**Where to find these values:**

1. **TWILIO_AUTH_TOKEN**:
   - Go to https://console.twilio.com
   - Find "Auth Token" on dashboard
   - Click "Show" and copy

2. **TWILIO_PHONE_NUMBER**:
   - Go to Phone Numbers → Manage → Active numbers
   - Copy your Twilio number in E.164 format (e.g., +15551234567)

3. **WIFE_PHONE**:
   - Wife's phone number in E.164 format
   - Must include +1 for US numbers (e.g., +15559876543)

### 2. Start the App

```bash
cd /Users/crucial/Documents/dev/Jules/jules-mvp
source venv/bin/activate
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Expose with Ngrok (New Terminal)

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 4. Configure Twilio Webhook

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/active
2. Click your phone number
3. Scroll to "Messaging Configuration"
4. Under "A MESSAGE COMES IN":
   - Set to: Webhook
   - URL: `https://your-ngrok-url.ngrok.io/sms/webhook`
   - HTTP: POST
5. Click "Save"

### 5. Test!

Text your Twilio number: **START**

You should receive:
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

## Troubleshooting

**No response from Jules?**
- Check that `python app.py` is still running
- Check that ngrok is still running
- Verify Twilio webhook URL matches your current ngrok URL
- Check logs: `tail -f logs/app.log`

**"Invalid credentials" error?**
- Verify TWILIO_AUTH_TOKEN is correct
- Verify TWILIO_ACCOUNT_SID is correct

**"Invalid phone number" error?**
- Ensure all phone numbers use E.164 format (+1XXXXXXXXXX)
- No spaces, dashes, or parentheses

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

## What's Working

- ✅ JSON file storage (data/)
- ✅ Conversation state machine
- ✅ Manual recipe entry flow
- ✅ Meal planning workflow
- ✅ Shopping list generation
- ✅ 2-person household support

## Costs

- Twilio trial: $15 credit (free)
- After trial: ~$2.50/month for 2 users
- No other costs during local testing

## Next Session Goals

1. [ ] Complete .env configuration
2. [ ] Start app locally
3. [ ] Set up ngrok tunnel
4. [ ] Configure Twilio webhook
5. [ ] Send first "START" message
6. [ ] Add your first recipe
7. [ ] Have wife test adding a recipe
8. [ ] Plan a test week

---

**Ready to start?** Complete the .env file above, then run `python app.py`
