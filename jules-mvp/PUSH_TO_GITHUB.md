# Push Jules to GitHub - Step by Step

Your username: **mikepbyrne**
Repository: **jules-mvp**

## Step 1: Create the Repository on GitHub

1. Go to: https://github.com/new
2. Fill in:
   - **Owner:** mikepbyrne
   - **Repository name:** `jules-mvp`
   - **Description:** "Jules - AI-powered meal planning assistant via SMS"
   - **Public** (required for GitHub Pages)
   - ❌ **DO NOT check** "Add a README file"
   - ❌ **DO NOT check** "Add .gitignore"
   - ❌ **DO NOT check** "Choose a license"
3. Click **"Create repository"**

## Step 2: Push Your Code

Your files are already committed locally. Now push them:

### Option A: Using GitHub CLI (Easiest if installed)

```bash
cd /Users/crucial/Documents/dev/Jules/jules-mvp

# Authenticate (one-time)
gh auth login

# Push
git push -u origin main
```

### Option B: Using Personal Access Token

1. **Create a token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Note: "Jules MVP access"
   - Expiration: 90 days (or custom)
   - Select scopes: ✅ **repo** (check all)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Push using token:**
   ```bash
   cd /Users/crucial/Documents/dev/Jules/jules-mvp

   git push -u origin main
   ```

   When prompted:
   - **Username:** `mikepbyrne`
   - **Password:** `<paste your token here>`

### Option C: Using SSH (If you have SSH keys set up)

```bash
cd /Users/crucial/Documents/dev/Jules/jules-mvp

# Change to SSH URL
git remote set-url origin git@github.com:mikepbyrne/jules-mvp.git

# Push
git push -u origin main
```

## Step 3: Enable GitHub Pages

1. Go to: https://github.com/mikepbyrne/jules-mvp/settings/pages
2. Under "Build and deployment":
   - **Source:** Deploy from a branch
   - **Branch:** main
   - **Folder:** /docs
3. Click **"Save"**
4. Wait 1-2 minutes for deployment

## Step 4: Verify Your URLs Work

After GitHub Pages deploys, your documentation will be available at:

✅ **Opt-in process:**
```
https://mikepbyrne.github.io/jules-mvp/opt-in-process.html
```

✅ **Privacy policy:**
```
https://mikepbyrne.github.io/jules-mvp/privacy-policy.html
```

✅ **Terms of service:**
```
https://mikepbyrne.github.io/jules-mvp/terms-of-service.html
```

**Test them:** Open each URL in your browser to confirm they load correctly.

## Step 5: Use URLs in Twilio Verification Form

In the Twilio toll-free verification form:

**Proof of consent (opt-in) collected:**
```
https://mikepbyrne.github.io/jules-mvp/opt-in-process.html
```

**Privacy Policy URL (optional):**
```
https://mikepbyrne.github.io/jules-mvp/privacy-policy.html
```

**Terms & Conditions URL (optional):**
```
https://mikepbyrne.github.io/jules-mvp/terms-of-service.html
```

---

## Current Status

✅ All files committed locally (3 commits total)
✅ Git remote configured (https://github.com/mikepbyrne/jules-mvp.git)
✅ Email placeholders updated to support@jules-app.com
✅ Ready to push to GitHub
⏳ **Next step:** Create repository on GitHub
⏳ **Then:** Push commits to GitHub
⏳ **Finally:** Enable GitHub Pages

## Quick Commands Reference

```bash
# Navigate to project
cd /Users/crucial/Documents/dev/Jules/jules-mvp

# Check what's committed
git log --oneline

# Check remote
git remote -v

# Push (after creating repo and setting up auth)
git push -u origin main

# Check if Pages is deployed
# Visit: https://github.com/mikepbyrne/jules-mvp/settings/pages
```

## Troubleshooting

**Error: "repository not found"**
→ Create the repository first at https://github.com/new

**Error: "authentication failed"**
→ Use a Personal Access Token as your password

**Pages not working?**
→ Make sure repository is Public and branch is set to "main" with folder "/docs"

**URLs showing 404?**
→ Wait 2-3 minutes after enabling Pages, then refresh

---

## Alternative: GitHub Desktop (GUI)

If you prefer a visual interface:

1. Download GitHub Desktop: https://desktop.github.com/
2. Sign in with your GitHub account
3. Add existing repository: `/Users/crucial/Documents/dev/Jules/jules-mvp`
4. Click "Publish repository"
5. Set name to `jules-mvp`, make it Public
6. Click "Publish"

Then enable Pages in Settings as described above.

---

**Ready when you are!** Let me know if you need help with any step.
