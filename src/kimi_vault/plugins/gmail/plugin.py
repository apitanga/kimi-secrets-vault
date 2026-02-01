"""
Gmail Plugin for Kimi Vault

Implements the Plugin interface to provide Gmail functionality
through the vault's plugin system.
"""

from typing import Any, Dict, List

from ...core.plugin import Plugin, PluginCommand, PluginError
from .client import GmailClient, GmailAuthError


class GmailPlugin(Plugin):
    """Plugin providing Gmail integration"""
    
    PLUGIN_NAME = "gmail"
    
    def __init__(self, secrets: Dict[str, Any]):
        self.client: GmailClient = None
        super().__init__(secrets)
    
    @property
    def name(self) -> str:
        return self.PLUGIN_NAME
    
    @property
    def description(self) -> str:
        return "Gmail integration - read, search, and send emails"
    
    def _validate_secrets(self):
        """Validate Gmail secrets are present"""
        required = ['client_id', 'client_secret', 'refresh_token']
        missing = [f for f in required if not self.secrets.get(f)]
        if missing:
            raise PluginError(f"Missing Gmail configuration: {missing}")
    
    def _get_client(self) -> GmailClient:
        """Lazy-load Gmail client"""
        if self.client is None:
            try:
                self.client = GmailClient(self.secrets)
            except GmailAuthError as e:
                raise PluginError(f"Failed to initialize Gmail: {e}")
        return self.client
    
    def get_commands(self) -> List[PluginCommand]:
        """Return Gmail CLI commands"""
        return [
            PluginCommand(
                name="unread",
                description="List unread emails",
                handler=self.cmd_unread,
                args=[("limit", "Maximum number of emails", False)]
            ),
            PluginCommand(
                name="search",
                description="Search emails by query",
                handler=self.cmd_search,
                args=[
                    ("query", "Search query (Gmail syntax)", True),
                    ("limit", "Maximum results", False)
                ]
            ),
            PluginCommand(
                name="labels",
                description="List Gmail labels",
                handler=self.cmd_labels,
                args=[]
            ),
            PluginCommand(
                name="profile",
                description="Show Gmail profile",
                handler=self.cmd_profile,
                args=[]
            ),
            PluginCommand(
                name="draft",
                description="Create an email draft",
                handler=self.cmd_draft,
                args=[
                    ("to", "Recipient email address", True),
                    ("subject", "Email subject", True),
                    ("body", "Email body", True)
                ]
            ),
            PluginCommand(
                name="send",
                description="Send an email",
                handler=self.cmd_send,
                args=[
                    ("to", "Recipient email address", True),
                    ("subject", "Email subject", True),
                    ("body", "Email body", True)
                ]
            ),
        ]
    
    # === Command Handlers ===
    
    def cmd_unread(self, limit: str = "10") -> str:
        """List unread emails"""
        try:
            max_results = int(limit) if limit else 10
        except ValueError:
            max_results = 10
        
        client = self._get_client()
        emails = client.list_unread(max_results=max_results)
        
        if not emails:
            return "No unread emails."
        
        lines = [f"{len(emails)} Unread Email(s):"]
        lines.append("")
        for i, email in enumerate(emails, 1):
            lines.append(f"{i}. Subject: {email['subject']}")
            lines.append(f"   From: {email['from']}")
            lines.append(f"   Date: {email['date']}")
            if email['snippet']:
                lines.append(f"   Preview: {email['snippet'][:100]}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def cmd_search(self, query: str = "", limit: str = "10") -> str:
        """Search emails"""
        if not query:
            return "Error: Search query is required"
        
        try:
            max_results = int(limit) if limit else 10
        except ValueError:
            max_results = 10
        
        client = self._get_client()
        emails = client.search(query, max_results=max_results)
        
        if not emails:
            return f"No emails found for '{query}'."
        
        lines = [f"{len(emails)} Result(s) for '{query}':"]
        lines.append("")
        for i, email in enumerate(emails, 1):
            lines.append(f"{i}. {email['subject']}")
            lines.append(f"   From: {email['from']}")
            lines.append(f"   Date: {email['date']}")
            if email['snippet']:
                lines.append(f"   {email['snippet']}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def cmd_labels(self) -> str:
        """List Gmail labels"""
        client = self._get_client()
        labels = client.list_labels()
        
        if not labels:
            return "No labels found."
        
        lines = [f"{len(labels)} Label(s):"]
        lines.append("")
        for label in labels:
            lines.append(f"  - {label['name']}")
        
        return "\n".join(lines)
    
    def cmd_profile(self) -> str:
        """Show Gmail profile"""
        client = self._get_client()
        profile = client.get_profile()
        
        if not profile:
            return "Could not fetch profile."
        
        lines = [
            "Gmail Profile:"
            f"  Email: {profile.get('emailAddress', 'N/A')}",
            f"  Messages: {profile.get('messagesTotal', 'N/A')}",
            f"  Threads: {profile.get('threadsTotal', 'N/A')}"
        ]
        
        return "\n".join(lines)
    
    def cmd_draft(self, to: str = "", subject: str = "", body: str = "") -> str:
        """Create an email draft"""
        if not all([to, subject, body]):
            return "Error: to, subject, and body are required"
        
        client = self._get_client()
        draft = client.create_draft(to, subject, body)
        
        if draft:
            return f"Draft created with ID: {draft['id']}"
        else:
            return "❌ Failed to create draft"
    
    def cmd_send(self, to: str = "", subject: str = "", body: str = "") -> str:
        """Send an email"""
        if not all([to, subject, body]):
            return "Error: to, subject, and body are required"
        
        client = self._get_client()
        sent = client.send(to, subject, body)
        
        if sent:
            return f"Email sent! Message ID: {sent['id']}"
        else:
            return "❌ Failed to send email"
    
    def health_check(self) -> tuple[bool, str]:
        """Check Gmail connectivity"""
        try:
            client = self._get_client()
            profile = client.get_profile()
            if profile:
                return True, f"Connected as {profile.get('emailAddress', 'unknown')}"
            return False, "Could not fetch profile"
        except Exception as e:
            return False, str(e)
