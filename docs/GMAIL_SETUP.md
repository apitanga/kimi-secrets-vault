# Gmail API Setup Guide

This guide walks you through setting up Gmail API access for kimi-secrets-vault.

## Overview

**What you'll get:**
- Read access to your Gmail (unread emails, search, labels)
- Compose access (create drafts, send emails)
- No delete/modify access (readonly + compose scope only)

**What you need:**
- A Google account
- A Google Cloud project (free tier is fine)
- 15-20 minutes

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the project selector at the top
4. Click **New Project**
5. Enter a name (e.g., "kimi-vault-personal")
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
   - **App name**: "Kimi Vault Personal" (or whatever you want)
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

You have two options:

### Option A: Using kimi-vault-oauth (Easiest)

1. Set your credentials as environment variables:
   ```bash
   export KIMI_VAULT_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   export KIMI_VAULT_CLIENT_SECRET="your-client-secret"
   ```

2. Or add them to your config:
   ```bash
   echo "client_id = your-client-id.apps.googleusercontent.com" >> ~/.config/kimi-vault/config
   echo "client_secret = your-client-secret" >> ~/.config/kimi-vault/config
   ```

3. Run the OAuth helper:
   ```bash
   kimi-vault-oauth
   ```

4. Follow the prompts:
   - Click the authorization URL
   - Sign in with your Google account
   - Grant permissions
   - Copy the callback URL back to the terminal
   - Get your refresh token

### Option B: Using Google's OAuth Playground

1. Go to [OAuth Playground](https://developers.google.com/oauthplayground)
2. Click the **Settings** (gear) icon
3. Check **"Use your own OAuth credentials"**
4. Enter:
   - **OAuth Client ID**: (from your client_secret.json)
   - **OAuth Client Secret**: (from your client_secret.json)
5. Close settings
6. In "Select & authorize APIs":
   - Find and select both:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Click **Authorize APIs**
7. Sign in with your Google account
8. Grant permission
9. Click **Exchange authorization code for tokens**
10. Copy the **Refresh token** (long string starting with `1//`)

## Step 6: Create Your Secrets File

1. Copy the template:
   ```bash
   cp config/secrets.template.json ~/.kimi-vault/secrets.json
   ```

2. Edit `~/.kimi-vault/secrets.json`:
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

3. Get your public key:
   ```bash
   cat ~/.kimi-vault/key.txt.pub
   ```

4. Encrypt the secrets:
   ```bash
   age -r $(cat ~/.kimi-vault/key.txt.pub) \
     -o ~/.kimi-vault/secrets.json.age \
     ~/.kimi-vault/secrets.json
   ```

5. Securely delete the plaintext:
   ```bash
   shred -u ~/.kimi-vault/secrets.json
   # Or on macOS: rm -P ~/.kimi-vault/secrets.json
   ```

6. (Optional) Also delete the downloaded client_secret.json:
   ```bash
   shred -u client_secret.json
   ```

## Step 7: Test!

```bash
# Start a secure session
kimi-vault-session

# Test the CLI
kimi-vault unread
kimi-vault profile

# Or use Python
python3 -c "
from kimi_vault import GmailClient
client = GmailClient()
profile = client.get_profile()
print(f'Email: {profile['emailAddress']}')
print(f'Unread: {len(client.list_unread())} messages')
"
```

## Troubleshooting

### "Access blocked: app not verified"

Google shows a scary warning because it's a personal app (not verified by Google).

1. Click **Advanced**
2. Click **Go to [your app name] (unsafe)**
3. Continue with authorization

This is normal for personal OAuth apps. Since you're the developer and the user, this is fine.

### "Invalid client" errors

- Check that `client_id` ends with `.apps.googleusercontent.com`
- Make sure there are no extra spaces in the JSON
- Verify the client ID matches what's in Google Cloud Console

### "Refresh token expired"

Refresh tokens for "Testing" apps expire after 7 days. This is Google's policy for unverified apps.

**Solutions:**
1. **Re-authorize** - Just run `kimi-vault-oauth` again and get a new refresh token
2. **Publish your app** - Go through Google's verification process (complex, not needed for personal use)
3. **Use a Workspace account** - If you have Google Workspace, your app can stay in "Internal" mode

### "Rate limit exceeded"

The client handles rate limiting automatically with exponential backoff. Just wait a moment.

If you consistently hit limits:
- Check your [API Console quotas](https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas)
- Reduce the frequency of API calls
- Request a quota increase from Google

### No refresh token received

If `kimi-vault-oauth` shows "NOT FOUND" for refresh token:

1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find your app and click it
3. Click **Remove Access**
4. Run `kimi-vault-oauth` again
5. Make sure to check "See and download all your Gmail" during authorization

## Security Notes

- **Scope**: We use `gmail.readonly` + `gmail.compose` - the vault can read and compose emails but cannot delete or modify existing ones
- **Token storage**: Tokens are encrypted at rest with age, decrypted only during sessions
- **Session lifetime**: Secrets exist only in `/tmp/` during the session
- **Cleanup**: Automatically shredded when the session ends

## Next Steps

- See [README.md](../README.md) for full usage documentation
- Learn about [Python API](../README.md#python-api) for programmatic access
- Check out the [CLI reference](../README.md#cli-reference)
