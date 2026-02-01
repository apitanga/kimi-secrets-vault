"""
Unit tests for vault.py - encryption/decryption operations.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from kimi_vault.core.vault import Vault, VaultCryptoError, secure_delete


class TestVault:
    """Test Vault class encryption/decryption operations."""
    
    def test_init_default_paths(self, temp_dir):
        """Test Vault initialization with default paths."""
        vault = Vault()
        assert vault.vault_dir == Path.home() / ".kimi-vault"
        assert vault.key_file == vault.vault_dir / "key.txt"
        assert vault.key_pub_file == vault.vault_dir / "key.txt.pub"
    
    def test_init_custom_paths(self, temp_dir):
        """Test Vault initialization with custom paths."""
        vault = Vault(
            key_file=temp_dir / "custom.key",
            vault_dir=temp_dir / "custom-vault"
        )
        assert vault.vault_dir == temp_dir / "custom-vault"
        assert vault.key_file == temp_dir / "custom.key"
        assert vault.key_pub_file == temp_dir / "custom.key.pub"
    
    def test_check_age_installed_success(self, patch_age_commands):
        """Test age installation check when age is available."""
        vault = Vault()
        # Should not raise an exception
        vault._check_age_installed()
    
    def test_check_age_installed_failure(self):
        """Test age installation check when age is not available."""
        vault = Vault()
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with pytest.raises(VaultCryptoError, match="age is not installed"):
                vault._check_age_installed()
    
    def test_generate_key_success(self, temp_dir, patch_age_commands):
        """Test successful key generation."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        
        # Mock os.chmod to avoid FileNotFoundError
        with patch('os.chmod'):
            public_key = vault.generate_key()
        
        assert public_key == "age1testpublickey1234567890"
        # Note: We can't check file.exists() because the mock doesn't create files
    
    def test_generate_key_already_exists(self, temp_dir):
        """Test key generation when key already exists."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.key_file.parent.mkdir(parents=True, exist_ok=True)
        vault.key_file.touch()
        
        with pytest.raises(VaultCryptoError, match="Key file already exists"):
            vault.generate_key()
    
    def test_get_public_key_from_pub_file(self, temp_dir):
        """Test getting public key from .pub file."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .pub file
        with open(vault.key_pub_file, 'w') as f:
            f.write("age1testpublickeyfrompub\n")
        
        public_key = vault.get_public_key()
        assert public_key == "age1testpublickeyfrompub"
    
    def test_get_public_key_from_private_key(self, temp_dir):
        """Test deriving public key from private key file."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create private key file with embedded public key
        with open(vault.key_file, 'w') as f:
            f.write("# created: 2026-01-01T00:00:00Z\n")
            f.write("# public key: age1testpublickeyembedded\n")
            f.write("AGE-SECRET-KEY-1TESTPRIVATEKEY\n")
        
        public_key = vault.get_public_key()
        assert public_key == "age1testpublickeyembedded"
    
    def test_get_public_key_not_found(self, temp_dir):
        """Test getting public key when no key files exist."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        
        with pytest.raises(VaultCryptoError, match="Key file not found"):
            vault.get_public_key()
    
    def test_encrypt_success(self, temp_dir, patch_age_commands):
        """Test successful file encryption."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test file
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")
        
        # Create .pub file
        with open(vault.key_pub_file, 'w') as f:
            f.write("age1testpublickey\n")
        
        # Mock os.chmod to avoid FileNotFoundError
        with patch('os.chmod'):
            output_file = vault.encrypt(input_file)
        
        # Note: We can't check output_file.exists() because the mock doesn't create files
        # But we can check the path returned
        assert output_file.name == "test.txt.age"
    
    def test_encrypt_input_not_found(self, temp_dir):
        """Test encryption when input file doesn't exist."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        
        with pytest.raises(VaultCryptoError, match="Input file not found"):
            vault.encrypt(temp_dir / "nonexistent.txt")
    
    def test_encrypt_custom_output(self, temp_dir, patch_age_commands):
        """Test encryption with custom output path."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        input_file = temp_dir / "test.txt"
        input_file.write_text("test content")
        
        # Create .pub file
        with open(vault.key_pub_file, 'w') as f:
            f.write("age1testpublickey\n")
        
        output_file = temp_dir / "custom.enc"
        result = vault.encrypt(input_file, ciphertext_path=output_file)
        assert result == output_file
    
    def test_decrypt_success(self, temp_dir, patch_age_commands):
        """Test successful file decryption."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create key file
        vault.key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(vault.key_file, 'w') as f:
            f.write("# public key: age1testpublickey\n")
            f.write("AGE-SECRET-KEY-1TESTPRIVATEKEY\n")
        
        # Create encrypted file
        encrypted_file = temp_dir / "test.txt.age"
        encrypted_file.touch()
        
        result = vault.decrypt(encrypted_file)
        assert result.exists()
        assert "kimi-vault-secrets-" in str(result)
        assert result.suffix == ".json"
    
    def test_decrypt_custom_output(self, temp_dir, patch_age_commands):
        """Test decryption with custom output path."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create key file
        vault.key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(vault.key_file, 'w') as f:
            f.write("# public key: age1testpublickey\n")
            f.write("AGE-SECRET-KEY-1TESTPRIVATEKEY\n")
        
        # Create encrypted file
        encrypted_file = temp_dir / "test.txt.age"
        encrypted_file.touch()
        
        output_file = temp_dir / "decrypted.txt"
        # Mock os.chmod to avoid FileNotFoundError
        with patch('os.chmod'):
            result = vault.decrypt(encrypted_file, plaintext_path=output_file)
        assert result == output_file
    
    def test_decrypt_input_not_found(self, temp_dir):
        """Test decryption when input file doesn't exist."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        
        with pytest.raises(VaultCryptoError, match="Encrypted file not found"):
            vault.decrypt(temp_dir / "nonexistent.txt.age")
    
    def test_decrypt_key_not_found(self, temp_dir):
        """Test decryption when key file doesn't exist."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        
        # Create encrypted file
        encrypted_file = temp_dir / "test.txt.age"
        encrypted_file.touch()
        
        with pytest.raises(VaultCryptoError, match="Private key not found"):
            vault.decrypt(encrypted_file)
    
    def test_decrypt_to_string(self, temp_dir, patch_age_commands):
        """Test decryption to string."""
        vault = Vault(vault_dir=temp_dir / ".kimi-vault")
        vault.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Create key file
        vault.key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(vault.key_file, 'w') as f:
            f.write("# public key: age1testpublickey\n")
            f.write("AGE-SECRET-KEY-1TESTPRIVATEKEY\n")
        
        # Create encrypted file
        encrypted_file = temp_dir / "test.txt.age"
        encrypted_file.touch()
        
        result = vault.decrypt_to_string(encrypted_file)
        assert result == '{"gmail": {"client_id": "test"}}'


class TestSecureDelete:
    """Test secure_delete function."""
    
    def test_secure_delete_file_exists(self, temp_dir):
        """Test secure_delete on existing file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        
        secure_delete(test_file)
        assert not test_file.exists()
    
    def test_secure_delete_file_not_exists(self, temp_dir):
        """Test secure_delete on non-existent file (should not raise)."""
        test_file = temp_dir / "nonexistent.txt"
        secure_delete(test_file)  # Should not raise
    
    @patch('kimi_vault.core.vault.is_ram_disk')
    @patch('subprocess.run')
    def test_secure_delete_with_shred(self, mock_run, mock_is_ram_disk, temp_dir):
        """Test secure_delete using shred command."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Mock as not RAM disk
        mock_is_ram_disk.return_value = False
        
        # Mock shred to succeed
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        secure_delete(test_file)
        mock_run.assert_called_once_with(
            ["shred", "-u", str(test_file)],
            capture_output=True,
            check=True
        )
    
    @patch('kimi_vault.core.vault.is_ram_disk')
    @patch('subprocess.run', side_effect=FileNotFoundError())
    def test_secure_delete_fallback(self, mock_run, mock_is_ram_disk, temp_dir):
        """Test secure_delete falls back to unlink when shred not found."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        
        # Mock as not RAM disk
        mock_is_ram_disk.return_value = False
        
        secure_delete(test_file)
        assert not test_file.exists()
    
    @patch('kimi_vault.core.vault.is_ram_disk')
    def test_secure_delete_on_ram_disk(self, mock_is_ram_disk, temp_dir):
        """Test secure_delete skips shred on RAM disk."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        
        # Mock as RAM disk
        mock_is_ram_disk.return_value = True
        
        secure_delete(test_file)
        assert not test_file.exists()
        # shred should not be called for RAM disk