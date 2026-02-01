"""
Gmail client for Kimi Vault

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
    Gmail client using official Google API libraries with auto-refresh.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, secrets: Dict[str, str]):
        """
        Initialize Gmail client with secrets.
        
        Args:
            secrets: Dictionary with keys: client_id, client_secret, refresh_token
        """
        if not GOOGLE_LIBS_AVAILABLE:
            raise ImportError(
                "Google API libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )
        
        self.secrets = secrets
        self.creds: Optional[Credentials] = None
        self.service = None
        self._auth_error: Optional[str] = None
        
        self._validate_secrets()
        self._authenticate()
    
    def _validate_secrets(self):
        """Validate required secrets are present"""
        required = ['client_id', 'client_secret', 'refresh_token']
        missing = [f for f in required if not self.secrets.get(f)]
        if missing:
            raise GmailAuthError(f"Missing required Gmail secrets: {missing}")
    
    def _authenticate(self):
        """Authenticate using secrets"""
        try:
            self.creds = Credentials(
                token=None,
                refresh_token=self.secrets['refresh_token'],
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.secrets['client_id'],
                client_secret=self.secrets['client_secret'],
                scopes=self.SCOPES
            )
            
            # Initial token refresh
            self.creds.refresh(Request())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds, static_discovery=False)
            
        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg:
                error_msg = "Refresh token expired or revoked. Need to re-authorize."
            raise GmailAuthError(f"Authentication failed: {error_msg}")
    
    def _ensure_valid_token(self):
        """Refresh token if expired or about to expire"""
        if not self.creds:
            return
        
        if self.creds.expiry:
            expires_in = (self.creds.expiry - datetime.utcnow()).total_seconds()
            if not self.creds.valid or expires_in < 300:
                self.creds.refresh(Request())
    
    def _execute_with_retry(self, api_call, *args, **kwargs):
        """Execute API call with automatic token refresh on 401"""
        try:
            return api_call(*args, **kwargs)
        except HttpError as e:
            if hasattr(e, 'resp') and e.resp.status == 401:
                try:
                    self._ensure_valid_token()
                    return api_call(*args, **kwargs)
                except GmailAuthError:
                    return None
            return self._handle_api_error(e)
        except Exception as e:
            return self._handle_api_error(e)
    
    def _handle_api_error(self, e):
        """Handle API errors gracefully"""
        error_details = str(e)
        if hasattr(e, 'resp') and e.resp.status:
            error_details = f"HTTP {e.resp.status}: {e}"
        print(f"❌ Gmail API Error: {error_details}", file=sys.stderr)
        return None
    
    # === Public API Methods ===
    
    def list_unread(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List unread emails"""
        try:
            self._ensure_valid_token()
            
            results = self._execute_with_retry(
                self.service.users().messages().list(
                    userId='me', q='is:unread', maxResults=max_results
                ).execute
            )
            
            if not results:
                return []
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_data = self._execute_with_retry(
                    self.service.users().messages().get(
                        userId='me', id=msg['id'],
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
            return []
    
    def list_recent(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List most recent emails (read or unread)"""
        try:
            self._ensure_valid_token()
            
            results = self._execute_with_retry(
                self.service.users().messages().list(
                    userId='me', maxResults=max_results
                ).execute
            )
            
            if not results:
                return []
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_data = self._execute_with_retry(
                    self.service.users().messages().get(
                        userId='me', id=msg['id'],
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
            return []
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails by query"""
        try:
            self._ensure_valid_token()
            
            results = self._execute_with_retry(
                self.service.users().messages().list(
                    userId='me', q=query, maxResults=max_results
                ).execute
            )
            
            if not results:
                return []
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_data = self._execute_with_retry(
                    self.service.users().messages().get(
                        userId='me', id=msg['id'],
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
            return []
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """List Gmail labels"""
        try:
            self._ensure_valid_token()
            results = self._execute_with_retry(
                self.service.users().labels().list(userId='me').execute
            )
            return results.get('labels', []) if results else []
        except GmailAuthError:
            return []
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get Gmail profile"""
        try:
            self._ensure_valid_token()
            return self._execute_with_retry(
                self.service.users().getProfile(userId='me').execute
            )
        except GmailAuthError:
            return None
    
    def create_draft(self, to: str, subject: str, body: str) -> Optional[Dict[str, Any]]:
        """Create an email draft"""
        try:
            self._ensure_valid_token()
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            draft_body = {'message': {'raw': raw_message}}
            
            return self._execute_with_retry(
                self.service.users().drafts().create(userId='me', body=draft_body).execute
            )
            
        except GmailAuthError:
            return None
    
    def send(self, to: str, subject: str, body: str) -> Optional[Dict[str, Any]]:
        """Send an email immediately"""
        try:
            self._ensure_valid_token()
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            email_body = {'raw': raw_message}
            
            return self._execute_with_retry(
                self.service.users().messages().send(userId='me', body=email_body).execute
            )
            
        except GmailAuthError:
            return None
