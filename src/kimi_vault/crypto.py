"""
Encryption/decryption operations using age

Requires age to be installed: https://age-encryption.org
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Union


class VaultCryptoError(Exception):
    """Raised when encryption/decryption operations fail"""
    pass


class VaultCrypto:
    """Handles age encryption and decryption for the vault"""
    
    def __init__(self, key_file: Optional[Union[str, Path]] = None):
        from .config import get_config
        self.config = get_config()
        self.key_file = Path(key_file) if key_file else self.config.key_file
        self.key_pub_file = Path(str(self.key_file) + ".pub")
    
    def _check_age_installed(self):
        """Check if age is installed"""
        try:
            subprocess.run(["age", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise VaultCryptoError(
                "age is not installed. Install it from https://age-encryption.org"
            )
    
    def generate_key(self) -> str:
        """Generate a new age key pair"""
        self._check_age_installed()
        
        if self.key_file.exists():
            raise VaultCryptoError(
                f"Key file already exists: {self.key_file}\n"
                "Delete it first if you want to generate a new key."
            )
        
        try:
            result = subprocess.run(
                ["age-keygen", "-o", str(self.key_file)],
                capture_output=True,
                text=True,
                check=True
            )
            # Extract public key from output
            public_key = None
            for line in result.stderr.split('\n'):
                if line.startswith('# public key:'):
                    public_key = line.split(':')[1].strip()
                    break
            
            # Also create .pub file
            if public_key:
                with open(self.key_pub_file, 'w') as f:
                    f.write(public_key + '\n')
            
            # Secure the key file
            os.chmod(self.key_file, 0o600)
            
            return public_key
            
        except subprocess.CalledProcessError as e:
            raise VaultCryptoError(f"Failed to generate key: {e.stderr}")
    
    def get_public_key(self) -> str:
        """Get the public key from the .pub file or derive from private key"""
        if self.key_pub_file.exists():
            with open(self.key_pub_file, 'r') as f:
                return f.read().strip()
        
        # Derive from private key
        if not self.key_file.exists():
            raise VaultCryptoError(f"Key file not found: {self.key_file}")
        
        with open(self.key_file, 'r') as f:
            for line in f:
                if line.startswith('# public key:'):
                    return line.split(':')[1].strip()
        
        raise VaultCryptoError("Could not find public key")
    
    def encrypt(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        recipient: Optional[str] = None
    ) -> Path:
        """
        Encrypt a file using age
        
        Args:
            input_file: File to encrypt
            output_file: Output file (default: input_file + ".age")
            recipient: Public key to encrypt to (default: use self key)
        
        Returns:
            Path to encrypted file
        """
        self._check_age_installed()
        
        input_path = Path(input_file)
        if not input_path.exists():
            raise VaultCryptoError(f"Input file not found: {input_path}")
        
        if output_file is None:
            output_path = Path(str(input_path) + ".age")
        else:
            output_path = Path(output_file)
        
        pub_key = recipient or self.get_public_key()
        
        try:
            subprocess.run(
                ["age", "-r", pub_key, "-o", str(output_path), str(input_path)],
                capture_output=True,
                check=True
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise VaultCryptoError(f"Encryption failed: {e.stderr.decode()}")
    
    def decrypt(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Decrypt a file using age
        
        Args:
            input_file: File to decrypt (.age file)
            output_file: Output file (default: tempfile)
        
        Returns:
            Path to decrypted file
        """
        self._check_age_installed()
        
        input_path = Path(input_file)
        if not input_path.exists():
            raise VaultCryptoError(f"Encrypted file not found: {input_path}")
        
        if not self.key_file.exists():
            raise VaultCryptoError(f"Private key not found: {self.key_file}")
        
        if output_file is None:
            # Create secure temp file
            fd, output_path = tempfile.mkstemp(prefix="kimi-vault-secrets-", suffix=".json")
            os.close(fd)
            output_path = Path(output_path)
        else:
            output_path = Path(output_file)
        
        try:
            subprocess.run(
                ["age", "-d", "-i", str(self.key_file), "-o", str(output_path), str(input_path)],
                capture_output=True,
                check=True
            )
            return output_path
        except subprocess.CalledProcessError as e:
            # Clean up temp file on failure
            if output_file is None and output_path.exists():
                output_path.unlink()
            raise VaultCryptoError(f"Decryption failed: {e.stderr.decode()}")
    
    def decrypt_to_memory(self, input_file: Union[str, Path]) -> str:
        """
        Decrypt a file and return contents as string
        
        Warning: Be careful with this - secrets will be in memory
        """
        self._check_age_installed()
        
        input_path = Path(input_file)
        if not input_path.exists():
            raise VaultCryptoError(f"Encrypted file not found: {input_path}")
        
        try:
            result = subprocess.run(
                ["age", "-d", "-i", str(self.key_file), str(input_path)],
                capture_output=True,
                check=True
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            raise VaultCryptoError(f"Decryption failed: {e.stderr.decode()}")


def secure_delete(file_path: Union[str, Path]):
    """
    Securely delete a file using shred if available, otherwise regular delete
    """
    path = Path(file_path)
    if not path.exists():
        return
    
    # Try shred first (Linux/Mac)
    try:
        subprocess.run(
            ["shred", "-u", str(path)],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to regular delete
        path.unlink()
