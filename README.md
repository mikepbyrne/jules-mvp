# Jules Documentation Links

These HTML files provide the required documentation for Twilio toll-free verification and general service compliance.

## Files

### 1. opt-in-process.html
**Purpose:** Proof of consent documentation for Twilio verification
**URL for Twilio form:** Upload this to a web server and provide the URL

**Contents:**
- How users opt-in (web registration + SMS keywords)
- Consent language shown to users
- Confirmation messages sent
- Opt-out process
- Message samples
- Compliance information

### 2. privacy-policy.html
**Purpose:** Privacy policy for SMS service (optional but recommended)
**URL for Twilio form:** Upload to web server if requested

**Contents:**
- Data collection practices
- How data is used
- Data storage and security
- User rights (access, delete, export)
- Third-party sharing (Twilio, Anthropic)
- TCPA/GDPR compliance

### 3. terms-of-service.html
**Purpose:** Terms of service for SMS messaging (optional but recommended)
**URL for Twilio form:** Upload to web server if requested

**Contents:**
- Service description
- SMS messaging terms
- User responsibilities
- Prohibited uses
- Disclaimers and liability limits
- Termination rights

## How to Use These Files

### Option 1: GitHub Pages (Free, Easy)

1. Create a `docs/` folder in your Jules GitHub repository
2. Copy these HTML files to the `docs/` folder
3. Commit and push to GitHub
4. Go to repository Settings → Pages
5. Set source to "main branch /docs folder"
6. Your links will be:
   - `https://[username].github.io/jules-mvp/opt-in-process.html`
   - `https://[username].github.io/jules-mvp/privacy-policy.html`
   - `https://[username].github.io/jules-mvp/terms-of-service.html`

### Option 2: Simple HTTP Server (Testing)

```bash
cd docs/
python3 -m http.server 8080
```

Then use ngrok to create public URL:
```bash
ngrok http 8080
```

**Temporary URL:** `https://[random].ngrok.io/opt-in-process.html`

### Option 3: Deploy to Netlify/Vercel (Permanent)

1. Create a free Netlify or Vercel account
2. Deploy the `docs/` folder
3. Get permanent URLs

## What to Put in Twilio Form

**Proof of consent (opt-in) collected:**
```
https://[your-domain]/opt-in-process.html
```

**Privacy Policy URL (optional):**
```
https://[your-domain]/privacy-policy.html
```

**Terms & Conditions URL (optional):**
```
https://[your-domain]/terms-of-service.html
```

## Important: Update Before Deploying

Before deploying these files, replace placeholders:
- `[Your email address]` → Your actual email
- `[your-username]` → Your GitHub username
- Verify phone number is correct: (866) 497-8083

## Quick Deploy with GitHub Pages

```bash
cd /Users/crucial/Documents/dev/Jules/jules-mvp

# Create docs directory if needed
mkdir -p docs

# Copy HTML files to docs
# (they're already there from the Write commands)

# Initialize git if needed
git init
git add docs/
git commit -m "Add compliance documentation"

# Push to GitHub
git remote add origin https://github.com/[username]/jules-mvp.git
git branch -M main
git push -u origin main

# Enable GitHub Pages in repository settings
```

Then use these URLs in your Twilio verification form:
- `https://[username].github.io/jules-mvp/docs/opt-in-process.html`
- `https://[username].github.io/jules-mvp/docs/privacy-policy.html`
- `https://[username].github.io/jules-mvp/docs/terms-of-service.html`

## Alternative: Paste Content Directly

If you can't host these files publicly yet, you can:
1. Copy the entire HTML content
2. Paste it into a GitHub Gist (https://gist.github.com)
3. Use the "Raw" URL from the gist

This gives you a public URL immediately without setting up full hosting.
