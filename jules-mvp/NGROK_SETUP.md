# Ngrok Setup for Jules MVP

Ngrok is installed but needs authentication to create tunnels.

---

## Quick Setup (5 minutes)

### Step 1: Create Free Ngrok Account
1. Go to https://dashboard.ngrok.com/signup
2. Sign up with email or GitHub
3. Verify your email address

### Step 2: Get Your Authtoken
1. After signup, you'll see your authtoken
2. Or go to: https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy the token (looks like: `2abc...xyz_123...`)

### Step 3: Configure Ngrok
Run this command with your token:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

**Example:**
```bash
ngrok config add-authtoken 2abc123def456ghi789jkl_mnop123qrst456uvwx
```

### Step 4: Start Ngrok Tunnel
```bash
ngrok http 8000
```

You should see:
```
Session Status                online
Account                       your-email@example.com
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

---

## Configure Twilio Webhook

### Step 1: Go to Twilio Console
https://console.twilio.com/us1/develop/phone-numbers/manage/active

### Step 2: Click Your Phone Number
Phone number: **+18664978083**

### Step 3: Configure Messaging
Scroll to "Messaging Configuration"

**A MESSAGE COMES IN:**
- Webhook: `https://your-ngrok-url.ngrok.io/sms/webhook`
- HTTP: **POST**

**Example:**
```
https://abc123.ngrok.io/sms/webhook
```

### Step 4: Save
Click **Save** at bottom of page

---

## Test It!

### Send SMS
Text **+18664978083**: `START`

### Expected Response
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

### Check Logs
```bash
tail -f logs/app.log
```

Should see:
```json
{"time":"...","level":"INFO","msg":"msg_received phone=+14157979915 msg=START"}
{"time":"...","level":"INFO","msg":"sms_sent to=+14157979915 sid=SM..."}
```

---

## Troubleshooting

### Ngrok URL Changed
**Problem:** Free ngrok gives new URL each restart

**Fix:**
1. Get new URL from ngrok terminal
2. Update Twilio webhook with new URL
3. Save in Twilio console

**Alternative:** Ngrok paid plan ($5/month) for static URLs

### No Response from Jules
**Checklist:**
- [ ] Is `python app.py` still running?
- [ ] Is ngrok still running?
- [ ] Did you update Twilio webhook with current ngrok URL?
- [ ] Check `tail -f logs/app.log` for errors

### Twilio Webhook Test
In Twilio console:
1. Phone Numbers → Active Number → Messaging
2. Scroll to bottom
3. Click "Test" next to webhook URL
4. Should see 200 OK response

---

## Alternative to Ngrok

If ngrok doesn't work, try **localtunnel**:

```bash
# Install
npm install -g localtunnel

# Start
lt --port 8000

# Copy the URL and use in Twilio
```

Or **Cloudflare Tunnel** (free, no auth needed):
```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8000
```

---

## Current Status

- ✅ Ngrok installed
- ⚠️ Needs authentication
- ⚠️ Needs to be started
- 🔒 Jules app running and ready

## Next Steps

1. **Sign up:** https://dashboard.ngrok.com/signup
2. **Get token:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Run:** `ngrok config add-authtoken YOUR_TOKEN`
4. **Start:** `ngrok http 8000`
5. **Configure:** Update Twilio webhook
6. **Test:** Text START to +18664978083

---

**After setup, you'll be ready to test Jules end-to-end!** 🚀
