# Twilio Webhook Setup - Step by Step

**Goal:** Connect Twilio to your local Jules app so SMS messages trigger your webhook

---

## Prerequisites

✅ Jules app running on port 8000 (already done)
⚠️ **Need ngrok tunnel** (see below)

---

## Part 1: Start Ngrok Tunnel

### Option A: If You Have Ngrok Account

```bash
# In a NEW terminal window
ngrok http 8000
```

**Copy the HTTPS URL** from the output:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
            ^^^^^^^^^^^^^^^^^^^^^^^^
            Copy this URL
```

### Option B: If You DON'T Have Ngrok Account (Quick Setup)

1. Go to https://dashboard.ngrok.com/signup
2. Sign up (takes 30 seconds)
3. You'll see your authtoken on the dashboard
4. Run these commands:

```bash
# Add your authtoken (one-time setup)
ngrok config add-authtoken 2abc...YOUR_TOKEN_HERE...xyz

# Start the tunnel
ngrok http 8000
```

**Keep this terminal window open!** Copy the HTTPS URL.

**Example URL:** `https://f2a8-73-162-123-45.ngrok-free.app`

---

## Part 2: Configure Twilio Webhook

### Step 1: Open Twilio Console

**Go to:** https://console.twilio.com/us1/develop/phone-numbers/manage/active

**Or:**
1. Go to https://console.twilio.com
2. Click "Phone Numbers" in left sidebar
3. Click "Manage"
4. Click "Active numbers"

### Step 2: Select Your Phone Number

Click on: **+18664978083**

You'll see a page with your phone number details.

### Step 3: Scroll to Messaging Configuration

Scroll down to the section labeled **"Messaging Configuration"**

You'll see several options. Find the one that says:
**"A MESSAGE COMES IN"**

### Step 4: Configure the Webhook

**For "A MESSAGE COMES IN":**

1. **Select:** Webhook (dropdown)
2. **URL:** Enter your ngrok URL + `/sms/webhook`

   **Format:** `https://YOUR-NGROK-URL/sms/webhook`

   **Example:** `https://f2a8-73-162-123-45.ngrok-free.app/sms/webhook`

3. **HTTP Method:** Select **POST** (dropdown)

### Step 5: Save Configuration

**IMPORTANT:** Scroll to the bottom of the page and click the **"Save"** button

You should see a success message.

---

## Part 3: Test the Webhook

### Visual Test (In Twilio Console)

1. While still on the phone number configuration page
2. Scroll to the webhook URL you just entered
3. Look for a small **"Test"** link next to it
4. Click "Test"

**Expected Result:**
- Status: 200 OK
- Response: `<?xml version="1.0" encoding="UTF-8"?><Response></Response>`

If you see this, the webhook is working!

### Real Test (Send SMS)

**From your phone**, text **+18664978083**:
```
START
```

**Expected Response (within 5 seconds):**
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

## Visual Configuration Example

Here's exactly what your Twilio configuration should look like:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MESSAGING CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Configure With: Webhooks, TwiML Bins, Functions...

A MESSAGE COMES IN
┌─────────────────────────────────────────────┐
│ Webhook ▼                                   │
├─────────────────────────────────────────────┤
│ https://YOUR-URL.ngrok.io/sms/webhook      │
│                                             │
│ HTTP POST ▼                                 │
└─────────────────────────────────────────────┘

PRIMARY HANDLER FAILS
┌─────────────────────────────────────────────┐
│ Leave empty                                 │
└─────────────────────────────────────────────┘

                              [ Save Configuration ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

### ❌ "Webhook returned status 500"

**Problem:** Jules app crashed or has an error

**Fix:**
1. Check if Jules is still running:
   ```bash
   curl http://localhost:8000/
   ```
2. Check logs:
   ```bash
   tail -20 logs/app.log
   ```
3. Restart if needed:
   ```bash
   # Kill old process and restart
   cd /Users/crucial/Documents/dev/Jules/jules-mvp
   source venv/bin/activate
   python app.py
   ```

### ❌ "Connection refused" or "Connection timeout"

**Problem:** Ngrok tunnel not working

**Fix:**
1. Make sure ngrok is still running (check terminal)
2. Copy the current ngrok URL (it changes on restart)
3. Update Twilio webhook with new URL
4. Save again

### ❌ "Invalid URL" in Twilio

**Problem:** URL format is wrong

**Good URLs:**
- ✅ `https://abc123.ngrok.io/sms/webhook`
- ✅ `https://f2a8-73-162-123-45.ngrok-free.app/sms/webhook`

**Bad URLs:**
- ❌ `http://abc123.ngrok.io/sms/webhook` (http, not https)
- ❌ `https://abc123.ngrok.io` (missing /sms/webhook)
- ❌ `https://localhost:8000/sms/webhook` (localhost won't work)

### ❌ No response when texting

**Checklist:**
1. Is Jules app running?
   ```bash
   curl http://localhost:8000/
   # Should return: {"status": "ok", "app": "Jules MVP"}
   ```

2. Is ngrok running?
   ```bash
   # Check the ngrok terminal - should show requests
   ```

3. Is Twilio webhook configured correctly?
   - Go back to Twilio console
   - Verify URL ends with `/sms/webhook`
   - Verify method is POST
   - Click Save again

4. Check Twilio logs:
   - Go to https://console.twilio.com/us1/monitor/logs/sms
   - Find your recent message
   - Check webhook status

### ❌ Ngrok URL keeps changing

**Problem:** Free ngrok gives new URL each time you restart it

**Solution:**
- **Option 1:** Keep ngrok running (don't close the terminal)
- **Option 2:** Pay for ngrok static URL ($5/month)
- **Option 3:** Each time ngrok restarts:
  1. Copy new URL
  2. Update Twilio webhook
  3. Save

---

## Quick Reference Commands

```bash
# Check Jules app is running
curl http://localhost:8000/

# View recent logs
tail -20 logs/app.log

# Follow logs in real-time (new terminal)
tail -f logs/app.log

# Start ngrok (if not running)
ngrok http 8000

# Restart Jules app (if needed)
cd /Users/crucial/Documents/dev/Jules/jules-mvp
source venv/bin/activate
python app.py
```

---

## What the URLs Mean

**Your ngrok URL:** `https://abc123.ngrok.io`
- This is the public internet address
- Points to your computer
- Changes each time ngrok restarts (free tier)

**Webhook endpoint:** `/sms/webhook`
- The specific route in Jules app
- Handles incoming SMS messages

**Complete webhook URL:** `https://abc123.ngrok.io/sms/webhook`
- This is what you put in Twilio
- When someone texts your Twilio number, Twilio sends a POST request here

---

## Verification Checklist

Before testing, verify:

- [ ] Jules app running (curl http://localhost:8000/ works)
- [ ] Ngrok running (terminal shows "Forwarding https://...")
- [ ] Copied correct ngrok URL
- [ ] Added `/sms/webhook` to the end
- [ ] Twilio webhook set to POST method
- [ ] Clicked Save in Twilio console
- [ ] Webhook URL starts with `https://` (not http)

If all checked, send "START" to +18664978083!

---

## Success Indicators

**You'll know it's working when:**

1. **In ngrok terminal:** You see POST requests coming in
   ```
   POST /sms/webhook   200 OK
   ```

2. **In Jules logs:** You see messages being processed
   ```bash
   tail -f logs/app.log
   # Should show: msg_received, sms_sent
   ```

3. **On your phone:** You receive a response from Jules within 5 seconds

4. **In Twilio console:** Logs show successful webhook delivery

---

## Next Steps After Webhook Setup

Once you receive the welcome message:

1. **Test basic flow:**
   ```
   You: RECIPE
   Jules: What's the recipe name?
   You: Test Recipe
   Jules: Nice! What are the main ingredients?
   ```

2. **Add real recipes** (3-5 recipes)

3. **Try planning:**
   ```
   You: PLAN
   Jules: (shows recipes)
   You: 1,2,3
   Jules: (shows plan)
   You: YES
   Jules: (sends shopping list)
   ```

4. **Have your wife text START** to test 2-person use

---

## Summary

**Webhook URL Format:**
```
https://[YOUR-NGROK-URL]/sms/webhook
```

**Where to configure:**
https://console.twilio.com/us1/develop/phone-numbers/manage/active
→ Click +18664978083
→ Scroll to "Messaging Configuration"
→ "A MESSAGE COMES IN" = Webhook, POST
→ Save

**Test:**
Text +18664978083: "START"

**You're done when:** You receive a welcome message from Jules! 🎉

---

**Need help?** Check logs: `tail -f logs/app.log`
