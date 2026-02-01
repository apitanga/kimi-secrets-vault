"""
Integration tests for Gmail plugin (mocked).
"""
import pytest
from unittest.mock import Mock, patch

from kimi_vault.plugins.gmail.plugin import GmailPlugin, PluginError
from kimi_vault.plugins.gmail.client import GmailClient, GmailAuthError


class TestGmailPlugin:
    """Test GmailPlugin class."""
    
    def test_gmail_plugin_init(self, mock_secrets):
        """Test GmailPlugin initialization."""
        gmail_secrets = mock_secrets["gmail"]
        plugin = GmailPlugin(gmail_secrets)
        
        assert plugin.name == "gmail"
        assert plugin.description == "Gmail integration - read, search, and send emails"
        assert plugin.secrets == gmail_secrets
        assert plugin.client is None  # Lazy-loaded
    
    def test_gmail_plugin_missing_secrets(self):
        """Test GmailPlugin with missing secrets."""
        with pytest.raises(PluginError, match="Missing Gmail configuration"):
            GmailPlugin({})
        
        with pytest.raises(PluginError, match="Missing Gmail configuration"):
            GmailPlugin({"client_id": "test"})  # Missing client_secret and refresh_token
    
    def test_gmail_plugin_get_commands(self, mock_secrets):
        """Test GmailPlugin command list."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        commands = plugin.get_commands()
        
        command_names = [cmd.name for cmd in commands]
        assert "unread" in command_names
        assert "search" in command_names
        assert "labels" in command_names
        assert "profile" in command_names
        assert "send" in command_names
        assert "draft" in command_names
    
    @pytest.mark.parametrize("command,args,expected", [
        ("unread", ["5"], "1 unread email(s):"),
        ("recent", ["3"], "1 recent email(s):"),
        ("inbox", ["2"], "1 email(s) in Inbox:"),
        ("search", ["test", "5"], "1 result(s) for 'test':"),
        ("labels", [], "label(s)"),
        ("profile", [], "Gmail Profile"),
    ])
    def test_gmail_plugin_commands(self, command, args, expected, mock_secrets, mock_gmail_client):
        """Test various Gmail plugin commands."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        # Mock the client
        with patch.object(plugin, '_get_client', return_value=mock_gmail_client):
            # Get the command handler
            commands = plugin.get_commands()
            cmd_dict = {cmd.name: cmd.handler for cmd in commands}
            
            # Execute command
            result = cmd_dict[command](*args)
            
            assert expected in result
    
    def test_gmail_plugin_send_command(self, mock_secrets, mock_gmail_client):
        """Test send command."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        with patch.object(plugin, '_get_client', return_value=mock_gmail_client):
            commands = plugin.get_commands()
            cmd_dict = {cmd.name: cmd.handler for cmd in commands}
            
            result = cmd_dict["send"]("to@example.com", "Subject", "Body")
            assert "Email sent" in result
    
    def test_gmail_plugin_draft_command(self, mock_secrets, mock_gmail_client):
        """Test draft command."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        with patch.object(plugin, '_get_client', return_value=mock_gmail_client):
            commands = plugin.get_commands()
            cmd_dict = {cmd.name: cmd.handler for cmd in commands}
            
            result = cmd_dict["draft"]("to@example.com", "Subject", "Body")
            assert "Draft created" in result
    
    def test_gmail_plugin_send_missing_args(self, mock_secrets):
        """Test send command with missing arguments."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        commands = plugin.get_commands()
        cmd_dict = {cmd.name: cmd.handler for cmd in commands}
        
        result = cmd_dict["send"]("", "", "")
        assert "Error: to, subject, and body are required" in result
    
    def test_gmail_plugin_search_missing_query(self, mock_secrets):
        """Test search command with missing query."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        commands = plugin.get_commands()
        cmd_dict = {cmd.name: cmd.handler for cmd in commands}
        
        result = cmd_dict["search"]("", "10")
        assert "Error: Search query is required" in result
    
    def test_gmail_plugin_health_check_success(self, mock_secrets, mock_gmail_client):
        """Test health check when Gmail is accessible."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        with patch.object(plugin, '_get_client', return_value=mock_gmail_client):
            healthy, message = plugin.health_check()
            assert healthy is True
            assert "test@example.com" in message
    
    def test_gmail_plugin_health_check_failure(self, mock_secrets):
        """Test health check when Gmail is not accessible."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        # Mock client to raise exception
        mock_client = Mock()
        mock_client.get_profile.side_effect = Exception("Connection failed")
        
        with patch.object(plugin, '_get_client', return_value=mock_client):
            healthy, message = plugin.health_check()
            assert healthy is False
            assert "Connection failed" in message
    
    def test_gmail_plugin_client_auth_error(self, mock_secrets):
        """Test Gmail client authentication error."""
        plugin = GmailPlugin(mock_secrets["gmail"])
        
        # Mock GmailClient to raise auth error
        with patch('kimi_vault.plugins.gmail.plugin.GmailClient', 
                         side_effect=GmailAuthError("Invalid credentials")):
            with pytest.raises(PluginError, match="Failed to initialize Gmail"):
                plugin._get_client()


class TestGmailClientMock:
    """Test mocked GmailClient interactions."""
    
    def test_gmail_client_list_unread(self, mock_gmail_client):
        """Test list_unread method."""
        emails = mock_gmail_client.list_unread()
        assert len(emails) == 1
        assert emails[0]["subject"] == "Test Email 1"
        assert emails[0]["from"] == "test1@example.com"
    
    def test_gmail_client_list_recent(self, mock_gmail_client):
        """Test list_recent method."""
        emails = mock_gmail_client.list_recent()
        assert len(emails) == 1
        assert emails[0]["subject"] == "Recent Email"
    
    def test_gmail_client_search(self, mock_gmail_client):
        """Test search method."""
        emails = mock_gmail_client.search("test query")
        assert len(emails) == 1
        assert emails[0]["subject"] == "Search Result"
    
    def test_gmail_client_list_labels(self, mock_gmail_client):
        """Test list_labels method."""
        labels = mock_gmail_client.list_labels()
        assert len(labels) == 2
        assert labels[0]["name"] == "INBOX"
        assert labels[1]["name"] == "SENT"
    
    def test_gmail_client_get_profile(self, mock_gmail_client):
        """Test get_profile method."""
        profile = mock_gmail_client.get_profile()
        assert profile["emailAddress"] == "test@example.com"
        assert profile["messagesTotal"] == 100
        assert profile["threadsTotal"] == 50
    
    def test_gmail_client_create_draft(self, mock_gmail_client):
        """Test create_draft method."""
        draft = mock_gmail_client.create_draft("to@example.com", "Subject", "Body")
        assert draft["id"] == "draft123"
    
    def test_gmail_client_send(self, mock_gmail_client):
        """Test send method."""
        sent = mock_gmail_client.send("to@example.com", "Subject", "Body")
        assert sent["id"] == "msg123"