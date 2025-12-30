# QUICK FIX GUIDE - SMS Delivery Issue

## Problem
SMS messages showing error 30032 (undelivered) - toll-free number requires verification.

## Root Cause
Your toll-free number (+18664978083) needs toll-free verification before it can send SMS messages.

## IMMEDIATE FIX - Choose One:

### Option A: Purchase Local 10DLC Number (Works in 5 minutes)
**Best for:** Testing and development

1. **Buy a local number:**
   ```
   Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/search
   - Select your area code (e.g., 415 for San Francisco)
   - Click "Search"
   - Click "Buy" on any available number
   Cost: ~$1.15/month
   ```

2. **Update your .env file:**
   ```bash
   # Replace the toll-free number with your new local number
   TWILIO_PHONE_NUMBER=+1<your_new_number>
   ```

3. **Restart your application:**
   ```bash
   # Kill the current app (Ctrl+C)
   source venv/bin/activate
   python app_housekeeper.py
   ```

4. **Update webhook (do this every time you restart ngrok):**
   ```bash
   # In a new terminal, start ngrok
   ngrok http 8000

   # Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
   # Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active
   # Click on your NEW phone number
   # Under "Messaging Configuration":
   #   - Set webhook to: https://<your-ngrok-url>/sms/webhook
   #   - Set method to: POST
   # Click Save
   ```

5. **Test it:**
   ```bash
   # Send a test message
   source venv/bin/activate
   python twilio_helper.py test +14157979915 "Test from Jules"
   ```

✅ **You can now send/receive SMS immediately!**

---

### Option B: Submit Toll-Free Verification (Takes 1-3 business days)
**Best for:** Production deployment with toll-free number

1. **Go to toll-free verification form:**
   ```
   https://console.twilio.com/us1/develop/sms/settings/toll-free-verifications
   ```

2. **Click "Create new Toll-Free Verification"**

3. **Fill out the form:**
   ```
   Phone Number: +18664978083

   Business Profile:
   - Business Name: Jules AI
   - Business Type: Technology/Software
   - Business Website: [Your website or GitHub URL]
   - Business Regions: United States
   - Business Industry: Technology - Consumer Software

   Use Case Summary:
   "Conversational AI meal planning assistant that helps families
   manage recipes and plan meals via SMS"

   Use Case Details:
   "Jules is an SMS-based AI assistant that helps families with meal
   planning, recipe management, and pantry tracking. Users explicitly
   opt-in via web signup or by texting START. The service provides
   personalized meal suggestions and recipe organization through
   conversational SMS messages."

   Message Volume:
   - Daily: 100-500 messages
   - Weekly: 500-2000 messages

   Sample Messages:
   1. "Hi! I'm Jules, your AI meal planning assistant 👋 I help with
      recipes, meal planning, and pantry management. Reply HI to get
      started, or STOP to opt out."

   2. "Perfect! Here's your household: • John, 42 • Sarah, 38 (vegetarian)
      Now I can suggest meals that work for everyone! Want to add your
      first recipe?"

   3. "Got it! Any dietary restrictions for Sarah? Like: vegetarian,
      vegan, gluten-free, dairy-free, nut allergy... Or just say 'none'
      if they eat everything!"

   Opt-In Method:
   "Users sign up via web application with explicit consent checkbox.
   Users can also text START to opt-in. Clear service description
   provided before consent is collected."

   Opt-Out Method:
   "Users can text STOP, UNSUBSCRIBE, CANCEL, END, or QUIT to opt-out
   immediately. Automatic confirmation sent. No further messages after
   opt-out."

   Customer Support:
   - Email: [Your email]
   - Phone: [Your phone]
   ```

4. **Submit and wait for approval**
   - Typical approval time: 1-3 business days
   - You'll receive email notification when approved
   - Messages will automatically work after approval

5. **In the meantime, use Option A (local number) for testing**

---

## REQUIRED: Fix ngrok Tunnel (For Both Options)

Your ngrok tunnel is currently offline. Fix this:

1. **Kill any existing ngrok:**
   ```bash
   pkill ngrok
   ```

2. **Start new ngrok tunnel:**
   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL** from the ngrok output:
   ```
   Example: https://juryless-eugena-nonsyntactically.ngrok-free.dev
   ```

4. **Update Twilio webhook:**
   ```
   Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active
   Click on your phone number
   Under "Messaging Configuration":
     - Webhook URL: https://<your-ngrok-url>/sms/webhook
     - HTTP Method: POST
   Click Save
   ```

5. **Important:** You need to do this EVERY TIME you restart ngrok
   (ngrok URLs change on each restart unless you have a paid plan)

---

## Testing Checklist

After implementing either fix:

- [ ] Application is running (python app_housekeeper.py)
- [ ] ngrok is running and shows HTTPS URL
- [ ] Twilio webhook is updated with current ngrok URL
- [ ] Environment variable TWILIO_PHONE_NUMBER is set correctly
- [ ] Test message sent successfully:
  ```bash
  source venv/bin/activate
  python twilio_helper.py test +14157979915 "Test"
  ```
- [ ] Test message shows status "delivered" (not "undelivered"):
  ```bash
  python twilio_helper.py messages
  ```
- [ ] Send SMS from your phone to your Twilio number
- [ ] Receive automated response from Jules

---

## Quick Diagnostic Commands

```bash
# Check if server is running
lsof -i :8000

# Check if ngrok is running
ps aux | grep ngrok

# Check recent messages
source venv/bin/activate
python twilio_helper.py messages

# Check webhook configuration
python twilio_helper.py webhook

# Test send message
python twilio_helper.py test +14157979915 "Test message"

# Check detailed account status
python check_account_details.py

# Full diagnostic report
python debug_sms_delivery.py
```

---

## Production Deployment Notes

Before going to production:

1. **Replace ngrok with stable hosting:**
   - AWS EC2 with Elastic IP
   - Heroku
   - Railway.app
   - Render.com
   - Any service with a stable public URL

2. **Complete A2P 10DLC registration** (if using local number):
   - Required for high volume messaging
   - Takes 1-2 weeks
   - Costs ~$4-15/month depending on volume

3. **Implement enhanced error handling:**
   - Use `sms_delivery_fix.py` as reference
   - Add message retry queue
   - Set up monitoring/alerts

4. **Set spending limits:**
   - Go to Twilio Console > Billing
   - Set daily/monthly spend limits
   - Add cost alerts

---

## Need Help?

**Common Issues:**

1. **"Module not found" errors:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **ngrok URL not working:**
   - Make sure ngrok is running: `ps aux | grep ngrok`
   - Check the URL in ngrok terminal output
   - Test URL in browser: should show error page, not timeout

3. **Messages still failing after fix:**
   - Check webhook logs: `tail -f logs/housekeeper.log`
   - Verify phone number in .env matches Twilio console
   - Check message status: `python twilio_helper.py messages`

4. **Inbound messages not working:**
   - Verify ngrok is running and accessible
   - Check webhook URL is correctly configured
   - Test webhook URL in browser (should get 404 or method not allowed)
   - Check application logs for errors

**Debug Resources:**
- Full report: `logs/sms_delivery_debug_report_2025-12-29.md`
- Diagnostic script: `python debug_sms_delivery.py`
- Account details: `python check_account_details.py`
