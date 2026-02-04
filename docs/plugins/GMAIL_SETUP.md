---
title: Gmail Plugin Setup Guide
nav_order: 21
parent: Plugins
---

# Gmail Plugin Setup Guide

This guide walks you through setting up the Gmail plugin for nakimi.

## Overview

**What you'll get:**
- Read access to your Gmail (unread emails, search, labels)
- Compose access (create drafts, send emails)
- No delete/modify access (readonly + compose scope only)

**What you need:**
- A Google account
- A Google Cloud project (free tier is fine)
- 15-20 minutes

## Architecture

The Gmail plugin is a standard nakimi plugin that:
- Loads credentials from the vault's encrypted secrets
- Uses Google's official API libraries
- Auto-refreshes OAuth tokens before expiry
- Provides CLI commands through the plugin system

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User CLI   │────▶│ GmailPlugin │────▶│ GmailClient │
│nakimi   │     │             │     │             │
│gmail.unread │     │ • validate  │     │ • OAuth     │
│gmail.send   │     │ • commands  │     │ • API calls │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │ Vault Core  │
                    │ (encrypted) │
                    └─────────────┘
```

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the project selector at the top
4. Click **New Project**
5. Enter a name (e.g., "nakimi-gmail")
6. Click **Create**
7. Wait for it to create, then select your new project

## Step 2: Enable Gmail API

1. Go to **APIs & Services** → **Library** (in the left sidebar)
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click **Enable**
5. Wait for it to activate (may take a minute)

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (or **Internal** if you have a Workspace org)
3. Click **Create**
4. Fill in:
   - **App name**: "Kimi Vault Gmail" (or whatever you want)
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **Save and Continue**
6. On the **Scopes** page:
   - Click **Add or Remove Scopes**
   - Search for "Gmail API"
   - Select:
     - `.../auth/gmail.readonly`
     - `.../auth/gmail.compose`
   - Click **Update**
   - Click **Save and Continue**
7. On the **Test users** page:
   - Click **Add Users**
   - Add your own email address
   - Click **Add**
   - Click **Save and Continue**
8. Review and click **Back to Dashboard**

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as Application type
4. Enter a name: "Kimi Vault Desktop"
5. Click **Create**
6. You'll see your **Client ID** and **Client Secret**
7. Click **Download JSON** and save it as `client_secret.json`

## Step 5: Get Refresh Token

The refresh token is what the plugin uses to access Gmail on your behalf.

### Option A: Using Google's OAuth Playground (Easiest)

1. Go to [OAuth Playground](https://developers.google.com/oauthplayground)
2. Click the **Settings** (gear) icon
3. Check **"Use your own OAuth credentials"**
4. Enter:
   - **OAuth Client ID**: (from your client_secret.json)
   - **OAuth Client Secret**: (from your client_secret.json)
5. Close settings
6. In "Select & authorize APIs":
   - Find and select both scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Click **Authorize APIs**
7. Sign in with your Google account
8. Grant permission
9. Click **Exchange authorization code for tokens**
10. Copy the **Refresh token** (long string starting with `1//`)

### Option B: Python Script

If you prefer:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
credentials = flow.run_local_server(port=0)

print(f"Refresh token: {credentials.refresh_token}")
```

## Step 6: Add Credentials to Vault

1. Copy the template:
   ```bash
   cp config/secrets.template.json ~/.nakimi/secrets.json
   ```

2. Edit `~/.nakimi/secrets.json`:
   ```json
   {
     "gmail": {
       "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
       "client_secret": "YOUR_CLIENT_SECRET",
       "refresh_token": "YOUR_REFRESH_TOKEN",
       "user": "your-email@example.com"
     }
   }
   ```

3. Encrypt with your vault key:
   ```bash
   age -r $(cat ~/.nakimi/key.txt.pub) \
     -o ~/.nakimi/secrets.json.age \
     ~/.nakimi/secrets.json
   ```

4. Securely delete plaintext:
   ```bash
   shred -u ~/.nakimi/secrets.json
   # Or on macOS: rm -P ~/.nakimi/secrets.json
   ```

5. Also delete the downloaded client_secret.json:
   ```bash
   shred -u client_secret.json
   ```

## Step 7: Test!

```bash
# Check plugin loaded
nakimi plugins list
# Should show: gmail - Gmail integration - read, search, and send emails

# Test commands
nakimi gmail.profile
nakimi gmail.unread
nakimi gmail.labels

# Search
nakimi gmail.search "from:boss@company.com"

# Send a test email (to yourself)
nakimi gmail.send "your-email@example.com" "Test" "This is a test email from nakimi!"
```

## Using in a Session

```bash
# Start a secure session
nakimi session

# Inside the session, same commands work:
$ nakimi gmail.unread 5
$ nakimi gmail.search "subject:invoice"
```

The vault automatically:
- Decrypts secrets when you start the session
- Makes them available to the Gmail plugin
- Securely shreds them when you exit

## Gmail Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `gmail.profile` | Show your Gmail profile | `nakimi gmail.profile` |
| `gmail.unread [limit]` | List unread emails (default: 10) | `nakimi gmail.unread 5` |
| `gmail.labels` | List all labels | `nakimi gmail.labels` |
| `gmail.search <query>` | Search emails | `nakimi gmail.search "from:google"` |
| `gmail.send <to> <subject> <body>` | Send an email | `nakimi gmail.send "test@example.com" "Hi" "Hello"` |
| `gmail.draft <to> <subject> <body>` | Create a draft | `nakimi gmail.draft "test@example.com" "Draft" "Content"` |

## Troubleshooting

### "Access blocked: app not verified"

Google shows a warning because it's a personal app (not verified by Google).

1. Click **Advanced**
2. Click **Go to [your app name] (unsafe)**
3. Continue with authorization

This is normal for personal OAuth apps.

### "Invalid client" errors

- Check that `client_id` ends with `.apps.googleusercontent.com`
- Make sure there are no extra spaces in the JSON
- Verify the client ID matches what's in Google Cloud Console

### "Refresh token expired"

Refresh tokens for "Testing" apps expire after 7 days.

**Solution:** Repeat Step 5 to get a new refresh token, then update your vault.

### Plugin not showing in list

```bash
# Check if secrets file exists
ls ~/.nakimi/secrets.json.age

# Decrypt and verify content
age -d -i ~/.nakimi/key.txt ~/.nakimi/secrets.json.age | python -m json.tool

# Should have "gmail" section with all required fields
```

### "Missing Gmail configuration"

The plugin needs these fields in secrets.json:
- `client_id`
- `client_secret`
- `refresh_token`

Check that all are present:
```bash
age -d -i ~/.nakimi/key.txt ~/.nakimi/secrets.json.age | \
  python -c "import sys, json; d=json.load(sys.stdin); print('gmail' in d and all(k in d['gmail'] for k in ['client_id', 'client_secret', 'refresh_token']))"
```

## Security Notes

- **Scope**: We use `gmail.readonly` + `gmail.compose` - can read and compose emails but cannot delete or modify existing ones
- **Token storage**: Tokens are encrypted at rest with age, decrypted only during sessions
- **Session lifetime**: Secrets exist only in a temp file during the session (`/dev/shm` if available, `/tmp` otherwise)
- **Cleanup**: Automatically shredded when the session ends

## Next Steps

- Learn how to create [custom plugins](../development/PLUGIN_DEVELOPMENT.md)
- Set up additional plugins (Calendar, GitHub coming soon)
- Review the [Architecture](../development/ARCHITECTURE.md) to understand security model