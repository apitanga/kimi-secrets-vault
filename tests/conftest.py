"""
Pytest fixtures for Kimi Vault tests.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kimi_vault.core.config import VaultConfig, get_config, reset_config
from kimi_vault.core.vault import Vault


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    # Reset global config first
    reset_config()
    
    # Create config with environment variables
    import os
    os.environ["KIMI_VAULT_DIR"] = str(temp_dir / ".kimi-vault")
    os.environ["KIMI_VAULT_KEY"] = str(temp_dir / ".kimi-vault" / "key.txt")
    os.environ["KIMI_VAULT_SECRETS"] = str(temp_dir / ".kimi-vault" / "secrets.json.age")
    
    config = get_config()
    return config


@pytest.fixture
def mock_secrets():
    """Mock secrets data for testing."""
    return {
        "gmail": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "refresh_token": "test-refresh-token"
        },
        "github": {
            "api_key": "test-api-key"
        }
    }


@pytest.fixture
def mock_secrets_file(temp_dir, mock_secrets):
    """Create a mock secrets JSON file."""
    secrets_file = temp_dir / "secrets.json"
    secrets_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(secrets_file, 'w') as f:
        json.dump(mock_secrets, f)
    
    return secrets_file


@pytest.fixture
def mock_vault(temp_dir):
    """Create a mock vault with test key."""
    vault_dir = temp_dir / ".kimi-vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a mock key file (age format)
    key_file = vault_dir / "key.txt"
    with open(key_file, 'w') as f:
        f.write("# created: 2026-01-01T00:00:00Z\n")
        f.write("# public key: age1testpublickey1234567890\n")
        f.write("AGE-SECRET-KEY-1TESTPRIVATEKEY1234567890\n")
    
    # Create .pub file
    pub_file = vault_dir / "key.txt.pub"
    with open(pub_file, 'w') as f:
        f.write("age1testpublickey1234567890\n")
    
    return Vault(key_file=key_file, vault_dir=vault_dir)


@pytest.fixture
def mock_gmail_client():
    """Mock GmailClient for testing."""
    mock = Mock()
    mock.list_unread.return_value = [
        {
            "subject": "Test Email 1",
            "from": "test1@example.com",
            "date": "2026-01-01T00:00:00Z",
            "snippet": "Test snippet 1"
        }
    ]
    mock.list_recent.return_value = [
        {
            "subject": "Recent Email",
            "from": "recent@example.com",
            "date": "2026-01-01T00:00:00Z",
            "snippet": "Recent snippet"
        }
    ]
    mock.list_inbox.return_value = [
        {
            "subject": "Inbox Email",
            "from": "inbox@example.com",
            "date": "2026-01-01T00:00:00Z",
            "snippet": "Inbox snippet"
        }
    ]
    mock.search.return_value = [
        {
            "subject": "Search Result",
            "from": "search@example.com",
            "date": "2026-01-01T00:00:00Z",
            "snippet": "Search snippet"
        }
    ]
    mock.list_labels.return_value = [
        {"name": "INBOX"},
        {"name": "SENT"}
    ]
    mock.get_profile.return_value = {
        "emailAddress": "test@example.com",
        "messagesTotal": 100,
        "threadsTotal": 50
    }
    mock.create_draft.return_value = {"id": "draft123"}
    mock.send.return_value = {"id": "msg123"}
    
    return mock


@pytest.fixture
def patch_age_commands():
    """Patch age commands to avoid actual encryption in unit tests."""
    with patch('subprocess.run') as mock_run:
        # Mock age-keygen
        def side_effect(cmd, *args, **kwargs):
            if 'age-keygen' in cmd:
                # Simulate successful key generation
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stderr = "# public key: age1testpublickey1234567890\n"
                return mock_result
            elif 'age' in cmd and '-r' in cmd:
                # Mock encryption
                mock_result = Mock()
                mock_result.returncode = 0
                return mock_result
            elif 'age' in cmd and '-d' in cmd:
                # Mock decryption
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = b'{"gmail": {"client_id": "test"}}'
                return mock_result
            else:
                # Default mock
                mock_result = Mock()
                mock_result.returncode = 0
                return mock_result
        
        mock_run.side_effect = side_effect
        yield mock_run