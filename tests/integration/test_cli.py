"""
Integration tests for CLI interface.
"""
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

import pytest

from kimi_vault.cli.main import main


class TestCLIParsing:
    """Test CLI argument parsing."""
    
    def test_parse_args_init(self):
        """Test parsing init command."""
        # We'll test this through the actual CLI execution
        pass
    
    # Note: parse_args is not exported from main.py
    # We'll test CLI parsing through actual execution tests


class TestCLIExecution:
    """Test CLI command execution."""
    
    @patch('kimi_vault.cli.main.Vault')
    @patch('sys.argv', ['kimi-vault', 'init'])
    def test_cli_init(self, mock_vault_class):
        """Test init command execution."""
        mock_vault = Mock()
        mock_vault.generate_key.return_value = "age1testpublickey"
        mock_vault.key_file = Mock()
        mock_vault.key_file.exists.return_value = False
        mock_vault.get_public_key.return_value = "age1testpublickey"
        mock_vault_class.return_value = mock_vault
        
        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Generating new age key pair" in output
        assert "Key generated!" in output
        mock_vault.generate_key.assert_called_once()
    
    @patch('kimi_vault.cli.main.Vault')
    @patch('sys.argv', ['kimi-vault', 'encrypt', 'input.txt', '-o', 'output.age'])
    @patch('pathlib.Path.exists')
    def test_cli_encrypt(self, mock_exists, mock_vault_class):
        """Test encrypt command execution."""
        mock_vault = Mock()
        mock_vault.encrypt.return_value = "/path/to/output.age"
        mock_vault_class.return_value = mock_vault
        mock_exists.return_value = True
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Encrypting input.txt" in output
        assert "Encrypted to: /path/to/output.age" in output
        mock_vault.encrypt.assert_called_once_with(
            Path("input.txt"),
            "output.age"
        )
    
    @patch('kimi_vault.cli.main.Vault')
    @patch('sys.argv', ['kimi-vault', 'decrypt', 'secrets.json.age', '-o', 'output.json'])
    @patch('pathlib.Path.exists')
    def test_cli_decrypt(self, mock_exists, mock_vault_class):
        """Test decrypt command execution."""
        mock_vault = Mock()
        mock_vault.decrypt.return_value = "/tmp/decrypted.json"
        mock_vault_class.return_value = mock_vault
        mock_exists.return_value = True
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Decrypting secrets.json.age" in output
        assert "Decrypted to: /tmp/decrypted.json" in output
        mock_vault.decrypt.assert_called_once_with(
            Path("secrets.json.age"),
            "output.json"
        )
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'plugins', 'list'])
    @patch('pathlib.Path.exists')
    @patch('kimi_vault.cli.main.secure_delete')
    @patch('kimi_vault.cli.main.json.load')
    @patch('builtins.open')
    def test_cli_plugins_list(self, mock_open, mock_json_load, mock_secure_delete, mock_exists, mock_pm_class, mock_vault_class, mock_get_config):
        """Test plugins list command."""
        # Mock config
        mock_config = Mock()
        mock_config.secrets_file = Path("/path/to/secrets.json.age")
        mock_get_config.return_value = mock_config
        
        # Mock vault - return a Path object
        mock_vault = Mock()
        mock_temp_path = Path("/tmp/secrets.json")
        mock_vault.decrypt.return_value = mock_temp_path
        mock_vault_class.return_value = mock_vault
        
        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.list_plugins.return_value = ["gmail", "github"]
        mock_pm_class.return_value = mock_pm
        
        # Mock file exists check
        mock_exists.return_value = True
        
        # Mock open to avoid FileNotFoundError
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock json.load to return secrets
        mock_json_load.return_value = {"gmail": {"token": "test"}}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Loaded plugins:" in output
        assert "gmail" in output
        assert "github" in output
        
        # Verify secrets were loaded
        mock_vault.decrypt.assert_called_once_with(mock_config.secrets_file)
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'plugins', 'commands'])
    @patch('pathlib.Path.exists')
    @patch('kimi_vault.cli.main.secure_delete')
    @patch('kimi_vault.cli.main.json.load')
    @patch('builtins.open')
    def test_cli_plugins_commands(self, mock_open, mock_json_load, mock_secure_delete, mock_exists, mock_pm_class, mock_vault_class, mock_get_config):
        """Test plugins commands command."""
        # Mock config
        mock_config = Mock()
        mock_config.secrets_file = Path("/path/to/secrets.json.age")
        mock_get_config.return_value = mock_config
        
        # Mock vault - return a Path object
        mock_vault = Mock()
        mock_temp_path = Path("/tmp/secrets.json")
        mock_vault.decrypt.return_value = mock_temp_path
        mock_vault_class.return_value = mock_vault
        
        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.list_commands.return_value = ["gmail.unread", "gmail.recent", "gmail.inbox"]
        mock_pm_class.return_value = mock_pm
        
        # Mock file exists check
        mock_exists.return_value = True
        
        # Mock open to avoid FileNotFoundError
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock json.load to return secrets
        mock_json_load.return_value = {"gmail": {"token": "test"}}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "Available commands:" in output
        assert "gmail.unread" in output
        
        mock_pm.list_commands.assert_called_once_with()
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'gmail.unread', '5'])
    @patch('pathlib.Path.exists')
    @patch('kimi_vault.cli.main.secure_delete')
    @patch('kimi_vault.cli.main.json.load')
    @patch('builtins.open')
    def test_cli_plugin_command(self, mock_open, mock_json_load, mock_secure_delete, mock_exists, mock_pm_class, mock_vault_class, mock_get_config):
        """Test executing a plugin command via CLI."""
        # Mock config
        mock_config = Mock()
        mock_config.secrets_file = Path("/path/to/secrets.json.age")
        mock_get_config.return_value = mock_config
        
        # Mock vault - return a Path object
        mock_vault = Mock()
        mock_temp_path = Path("/tmp/secrets.json")
        mock_vault.decrypt.return_value = mock_temp_path
        mock_vault_class.return_value = mock_vault
        
        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.execute_command.return_value = "3 unread emails"
        mock_pm_class.return_value = mock_pm
        
        # Mock file exists check
        mock_exists.return_value = True
        
        # Mock open to avoid FileNotFoundError
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock json.load to return secrets
        mock_json_load.return_value = {"gmail": {"token": "test"}}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "3 unread emails" in output
        
        mock_pm.execute_command.assert_called_once_with("gmail.unread", ["5"])
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'gmail.unread'])
    @patch('pathlib.Path.exists')
    @patch('kimi_vault.cli.main.secure_delete')
    @patch('kimi_vault.cli.main.json.load')
    @patch('builtins.open')
    def test_cli_plugin_command_error(self, mock_open, mock_json_load, mock_secure_delete, mock_exists, mock_pm_class, mock_vault_class, mock_get_config):
        """Test plugin command execution error."""
        # Mock config
        mock_config = Mock()
        mock_config.secrets_file = Path("/path/to/secrets.json.age")
        mock_get_config.return_value = mock_config
        
        # Mock vault - return a Path object
        mock_vault = Mock()
        mock_temp_path = Path("/tmp/secrets.json")
        mock_vault.decrypt.return_value = mock_temp_path
        mock_vault_class.return_value = mock_vault
        
        # Mock plugin manager
        mock_pm = Mock()
        from kimi_vault.core.plugin import PluginError
        mock_pm.execute_command.side_effect = PluginError("Plugin error")
        mock_pm_class.return_value = mock_pm
        
        # Mock file exists check
        mock_exists.return_value = True
        
        # Mock open to avoid FileNotFoundError
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock json.load to return secrets
        mock_json_load.return_value = {"gmail": {"token": "test"}}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "❌" in output
        assert "Plugin error" in output
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'unknown.command'])
    @patch('pathlib.Path.exists')
    @patch('kimi_vault.cli.main.secure_delete')
    @patch('kimi_vault.cli.main.json.load')
    @patch('builtins.open')
    def test_cli_unknown_command(self, mock_open, mock_json_load, mock_secure_delete, mock_exists, mock_pm_class, mock_vault_class, mock_get_config):
        """Test unknown command handling."""
        # Mock config
        mock_config = Mock()
        mock_config.secrets_file = Path("/path/to/secrets.json.age")
        mock_get_config.return_value = mock_config
        
        # Mock vault - return a Path object
        mock_vault = Mock()
        mock_temp_path = Path("/tmp/secrets.json")
        mock_vault.decrypt.return_value = mock_temp_path
        mock_vault_class.return_value = mock_vault
        
        # Mock plugin manager
        mock_pm = Mock()
        from kimi_vault.core.plugin import PluginError
        mock_pm.execute_command.side_effect = PluginError("Unknown command: unknown.command")
        mock_pm_class.return_value = mock_pm
        
        # Mock file exists check
        mock_exists.return_value = True
        
        # Mock open to avoid FileNotFoundError
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock json.load to return secrets
        mock_json_load.return_value = {"gmail": {"token": "test"}}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "❌" in output
    
    @patch('sys.argv', ['kimi-vault', '--help'])
    def test_cli_help(self):
        """Test help command."""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "usage:" in output
        assert "Commands" in output
        assert "Examples" in output
    
    @patch('kimi_vault.cli.main.get_config')
    @patch('kimi_vault.cli.main.Vault')
    @patch('kimi_vault.cli.main.PluginManager')
    @patch('sys.argv', ['kimi-vault', 'session', '--help'])
    def test_cli_session_command(self, mock_pm_class, mock_vault_class, mock_get_config):
        """Test session command (basic test - session is complex)."""
        # This is a basic test since session involves interactive shell
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            main()
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        assert "session" in output