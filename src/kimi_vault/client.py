"""
Gmail client for Kimi Secrets Vault

Handles Gmail API authentication with automatic token refresh
and provides methods for common email operations.
"""

import json
import sys
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

# Google libraries
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


class GmailAuthError(Exception):
    """Raised when Gmail authentication fails"""
    pass


class GmailClient:
    """
    Gmail client using official Google API libraries with auto-refresh
    
    Usage:
        from kimi_vault import GmailClient
        
        # With explicit secrets file
        client = GmailClient("/path/to/secrets.json")
        
        # With default config
        client = GmailClient()
        emails = client.list_unread()
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, secrets_file: Optional[Union[str, Path]] = None):
        """
        Initialize Gmail client
        
        Args:
            secrets_file: Path to secrets JSON file. If not provided,
                         will use KIMI_BOT_SECRETS env var or look in default location.
        """
        if not GOOGLE_LIBS_AVAILABLE:
            raise ImportError(
                "Google API libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )
        
        self.secrets_file = self._resolve_secrets_file(secrets_file)
        self.creds: Optional[Credentials] = None
        self.service = None
        self._auth_error: Optional[str] = None
        self._secrets_data: Optional[Dict] = None
        self._authenticate()
    
    def _resolve_secrets_file(self, secrets_file: Optional[Union[str, Path]]) -> Path:
        """Resolve secrets file path from argument, env var, or raise error"""
        if secrets_file:
            path = Path(secrets_file)
            if path.exists():
                return path
            raise GmailAuthError(f"Secrets file not found: {path}")
        
        # Try environment variable (set by kimi-vault-session)
        env_path = sys.environ.get('KIMI_VAULT_SECRETS') or sys.environ.get('KIMI_BOT_SECRETS')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
        
        raise GmailAuthError(
            "No secrets file provided. Either:\n"
            "1. Pass secrets_file parameter to GmailClient()\n"
            "2. Set KIMI_VAULT_SECRETS environment variable\n"
            "3. Run within kimi-vault-session"
        )
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load and validate secrets from file"""
        if self._secrets_data is not None:
            return self._secrets_data
        
        try:
            with open(self.secrets_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise GmailAuthError(f"Invalid JSON in secrets file: {e}")
        except Exception as e:
            raise GmailAuthError(f"Failed to read secrets file: {e}")
        
        # Validate Gmail section
        gmail_secrets = data.get('gmail', {})
        required = ['refresh_token', 'client_id', 'client_secret']
        missing = [f for f in required if not gmail_secrets.get(f)]
        if missing:
            raise GmailAuthError(f"Missing required fields in secrets: {missing}")
        
        self._secrets_data = data
        return data
    
    def _ensure_valid_token(self):
        """Refresh token if expired or about to expire (within 5 minutes)"""
        if not self.creds:
            if self._auth_error:
                raise GmailAuthError(self._auth_error)
            return
        
        # Check if token is expired or expires in < 5 minutes
        if self.creds.expiry:
            expires_in = (self.creds.expiry - datetime.utcnow()).total_seconds()
        else:
            expires_in = 0
        
        if not self.creds.valid or expires_in < 300:  # 300 seconds = 5 minutes
            try:
                self._refresh_token()
            except Exception as e:
                error_msg = f"Token refresh failed: {e}"
                self._auth_error = error_msg
                raise GmailAuthError(error_msg)
    
    def _refresh_token(self):
        """Force refresh the access token"""
        if not self.creds:
            raise GmailAuthError("No credentials available to refresh")
        
        try:
            self.creds.refresh(Request())
            self._auth_error = None
        except Exception as e:
            error_str = str(e)
            if "invalid_grant" in error_str:
                raise GmailAuthError(
                    "Refresh token expired or revoked. "
                    "Need to re-authorize with Gmail."
                )
            raise
    
    def _authenticate(self):
        """Authenticate using secrets file"""
        secrets = self._load_secrets()
        gmail_secrets = secrets.get('gmail', {})
        
        try:
            # Create credentials from secrets
            self.creds = Credentials(
                token=None,  # Will be refreshed
                refresh_token=gmail_secrets['refresh_token'],
                token_uri='https://oauth2.googleapis.com/token',
                client_id=gmail_secrets['client_id'],
                client_secret=gmail_secrets['client_secret'],
                scopes=self.SCOPES
            )
            
            # Initial token refresh
            self._refresh_token()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds, static_discovery=False)
            
        except GmailAuthError:
            raise
        except Exception as e:
            raise GmailAuthError(f"Authentication failed: {e}")
    
    def _execute_with_retry(self, api_call, *args, **kwargs):
        """Execute API call with automatic token refresh on 401"""
        try:
            return api_call(*args, **kwargs)
        except HttpError as e:
            # Check if it's a 401 (unauthorized) - token might have just expired
            if hasattr(e, 'resp') and e.resp.status == 401:
                try:
                    self._refresh_token()
                    # Retry the call once with new token
                    return api_call(*args, **kwargs)
                except GmailAuthError:
                    return None
            return self._handle_api_error(e)
        except Exception as e:
            return self._handle_api_error(e)
    
    def _handle_api_error(self, e):
        """Handle API errors and return user-friendly message"""
        error_details = ""
        if hasattr(e, 'resp') and e.resp.status:
            status = e.resp.status
            if status == 401:
                error_details = "Authentication expired. Token refresh failed."
                self._auth_error = error_details
            elif status == 403:
                error_details = "Permission denied. Check Gmail API scopes."
            elif status == 429:
                error_details = "Rate limit exceeded. Please wait and try again."
            else:
                error_details = f"HTTP {status}: {e}"
        else:
            error_details = str(e)
        
        print(f"❌ Gmail API Error: {error_details}", file=sys.stderr)
        return None
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get Gmail profile information"""
        try:
            self._ensure_valid_token()
            return self._execute_with_retry(
                self.service.users().getProfile(userId='me').execute
            )
        except GmailAuthError:
            return None
    
    def list_unread(self, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        List unread emails
        
        Args:
            max_results: Maximum number of emails to return (default: 10)
        
        Returns:
            List of email dictionaries with keys: id, subject, from, date, snippet
        """
        try:
            self._ensure_valid_token()
            
            results = self._execute_with_retry(
                self.service.users().messages().list(
                    userId='me',
                    q='is:unread',
                    maxResults=max_results
                ).execute
            )
            
            if results is None:
                return None
            
            messages = results.get('messages', [])
            if not messages:
                return []
            
            emails = []
            for msg in messages:
                msg_data = self._execute_with_retry(
                    self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'From', 'Date']
                    ).execute
                )
                
                if msg_data:
                    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                    emails.append({
                        'id': msg['id'],
                        'subject': headers.get('Subject', 'No Subject'),
                        'from': headers.get('From', 'Unknown'),
                        'date': headers.get('Date', 'Unknown'),
                        'snippet': msg_data.get('snippet', '')[:150]
                    })
            
            return emails
            
        except GmailAuthError:
            return None
    
    def search_emails(
        self,
        query: str,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search emails by query
        
        Args:
            query: Gmail search query (e.g., "from:boss@example.com")
            max_results: Maximum number of emails to return
        
        Returns:
            List of email dictionaries
        """
        try:
            self._ensure_valid_token()
            
            results = self._execute_with_retry(
                self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results
                ).execute
            )
            
            if results is None:
                return None
            
            messages = results.get('messages', [])
            if not messages:
                return []
            
            emails = []
            for msg in messages:
                msg_data = self._execute_with_retry(
                    self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'From', 'Date']
                    ).execute
                )
                
                if msg_data:
                    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                    emails.append({
                        'id': msg['id'],
                        'subject': headers.get('Subject', 'No Subject'),
                        'from': headers.get('From', 'Unknown'),
                        'date': headers.get('Date', 'Unknown'),
                        'snippet': msg_data.get('snippet', '')[:150]
                    })
            
            return emails
            
        except GmailAuthError:
            return None
    
    def list_labels(self) -> Optional[List[Dict[str, Any]]]:
        """List Gmail labels"""
        try:
            self._ensure_valid_token()
            results = self._execute_with_retry(
                self.service.users().labels().list(userId='me').execute
            )
            return results.get('labels', []) if results else None
        except GmailAuthError:
            return None
    
    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an email draft
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        
        Returns:
            Draft object with 'id' key
        """
        try:
            self._ensure_valid_token()
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            draft_body = {'message': {'raw': raw_message}}
            
            draft = self._execute_with_retry(
                self.service.users().drafts().create(userId='me', body=draft_body).execute
            )
            return draft
            
        except GmailAuthError:
            return None
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send an email immediately
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        
        Returns:
            Sent message object with 'id' key
        """
        try:
            self._ensure_valid_token()
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            email_body = {'raw': raw_message}
            
            sent = self._execute_with_retry(
                self.service.users().messages().send(userId='me', body=email_body).execute
            )
            return sent
            
        except GmailAuthError:
            return None
    
    def reply_to_thread(
        self,
        thread_id: str,
        to: str,
        subject: str,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """
        Reply to an existing email thread
        
        Args:
            thread_id: The Gmail thread ID
            to: Recipient email address
            subject: Email subject
            body: Reply body
        
        Returns:
            Sent message object
        """
        try:
            self._ensure_valid_token()
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent = self._execute_with_retry(
                self.service.users().messages().send(
                    userId='me',
                    body={
                        'raw': raw_message,
                        'threadId': thread_id
                    }
                ).execute
            )
            return sent
            
        except GmailAuthError:
            return None
