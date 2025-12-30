# Twilio Webhook Configuration - READY TO COPY/PASTE

Your ngrok tunnel is active! Here's exactly what to configure in Twilio.

---

## ✅ Your Ngrok URL

**Public URL:** `https://juryless-eugena-nonsyntactically.ngrok-free.dev`

**Webhook Endpoint:** `https://juryless-eugena-nonsyntactically.ngrok-free.dev/sms/webhook`

---

## 📋 Copy/Paste Instructions

### Step 1: Open Twilio Console
Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active

### Step 2: Click Your Phone Number
Click: **+18664978083**

### Step 3: Configure Webhook

Scroll to **"Messaging Configuration"** section

Find: **"A MESSAGE COMES IN"**

**Set these values:**

1. **Configure with:** Webhooks
2. **When a message comes in:**
   - Type: **Webhook** (dropdown)
   - URL: Copy/paste this exactly:
   ```
   https://juryless-eugena-nonsyntactically.ngrok-free.dev/sms/webhook
   ```
   - HTTP: **POST** (dropdown)

### Step 4: Save
Click **"Save"** button at the bottom of the page

---

## ✓ Visual Checklist

Before clicking Save, verify:
- [ ] URL starts with `https://` (not http)
- [ ] URL ends with `/sms/webhook`
- [ ] URL is: `https://juryless-eugena-nonsyntactically.ngrok-free.dev/sms/webhook`
- [ ] HTTP method is: **POST**
- [ ] "A MESSAGE COMES IN" is configured (not other fields)

---

## 🧪 Test the Configuration

After saving, you can test immediately in Twilio console:

1. Scroll to the webhook URL you just entered
2. Look for a small **"Test"** link next to it
3. Click it
4. Should see: **200 OK** response

Or just text your phone:
- Text **+18664978083** with: `START`
- Should receive welcome message within 5 seconds

---

## 🐛 If Something Goes Wrong

### "Invalid URL" error
- Make sure URL starts with `https://` (not http)
- Make sure URL ends with `/sms/webhook`
- No extra spaces

### "Connection failed" when testing
- Check Jules app is running: `curl http://localhost:8000/`
- Check ngrok is running (it is - URL is active)
- Try the test again

### No SMS response
1. Check logs: `tail -f logs/app.log`
2. Verify webhook was saved
3. Send "START" again

---

## 📊 What Happens When You Text

```
Your Phone
    ↓ (SMS: "START")
Twilio Server (+18664978083)
    ↓ (HTTP POST with SMS data)
Ngrok Tunnel (https://juryless-eugena-nonsyntactically.ngrok-free.dev)
    ↓
Jules App (localhost:8000/sms/webhook)
    ↓ (processes message, creates response)
Twilio API (sends SMS back)
    ↓
Your Phone (receives Jules response)
```

---

## 📝 Quick Reference

**Your Phone:** +14157979915
**Twilio Number:** +18664978083
**Webhook URL:** https://juryless-eugena-nonsyntactically.ngrok-free.dev/sms/webhook
**Method:** POST

**First test message:** `START`

---

## ⏭️ Next Steps

1. ✅ Configure webhook (you're doing this now)
2. 📱 Text START to +18664978083
3. ✉️ Receive welcome message
4. 🎉 Start testing Jules!

---

**The exact URL to copy/paste into Twilio:**
```
https://juryless-eugena-nonsyntactically.ngrok-free.dev/sms/webhook
```

Good luck! 🚀
