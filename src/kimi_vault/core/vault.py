"""
Core vault operations - encryption/decryption with age
"""

import subprocess
import tempfile
import os
import platform
from pathlib import Path
from typing import Optional, Union


class VaultCryptoError(Exception):
    """Raised when encryption/decryption operations fail"""
    pass


def get_secure_temp_dir() -> Optional[Path]:
    """
    Get the best available secure temp directory.
    
    Priority:
    1. /dev/shm (RAM - Linux, never hits disk)
    2. /private/tmp (RAM-backed on macOS)
    3. System temp (fallback - may hit disk)
    
    Returns None if no secure option available.
    """
    # Linux: /dev/shm is a RAM-backed tmpfs
    if platform.system() == "Linux":
        shm_path = Path("/dev/shm")
        if shm_path.exists() and shm_path.is_dir():
            # Check if we can write to it
            try:
                test_file = shm_path / ".kimi-vault-test"
                test_file.touch()
                test_file.unlink()
                return shm_path
            except (PermissionError, OSError):
                pass
    
    # macOS: /private/tmp is usually RAM-backed
    if platform.system() == "Darwin":
        mac_tmp = Path("/private/tmp")
        if mac_tmp.exists() and mac_tmp.is_dir():
            return mac_tmp
    
    # Fallback: None (use system default)
    return None


class Vault:
    """
    Core vault for managing encrypted secrets.
    
    This is the low-level encryption layer - no business logic,
    just encrypt/decrypt with age.
    """
    
    def __init__(
        self,
        key_file: Optional[Union[str, Path]] = None,
        vault_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize vault.
        
        Args:
            key_file: Path to age private key (default: ~/.kimi-vault/key.txt)
            vault_dir: Directory for vault files (default: ~/.kimi-vault)
        """
        self.vault_dir = Path(vault_dir).expanduser() if vault_dir else Path.home() / ".kimi-vault"
        self.key_file = Path(key_file).expanduser() if key_file else self.vault_dir / "key.txt"
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
        
        # Ensure vault directory exists
        self.vault_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        try:
            result = subprocess.run(
                ["age-keygen", "-o", str(self.key_file)],
                capture_output=True,
                text=True,
                check=True
            )
            # Extract public key from stderr output
            public_key = None
            for line in result.stderr.split('\n'):
                if 'public key:' in line:
                    public_key = line.split('public key:')[1].strip()
                    break
            
            # Also read from key file if not in stderr
            if not public_key:
                with open(self.key_file, 'r') as f:
                    for line in f:
                        if line.startswith('# public key:'):
                            public_key = line.split(':')[1].strip()
                            break
            
            # Create .pub file
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
        plaintext_path: Union[str, Path],
        ciphertext_path: Optional[Union[str, Path]] = None,
        recipient: Optional[str] = None
    ) -> Path:
        """
        Encrypt a file using age.
        
        Args:
            plaintext_path: File to encrypt
            ciphertext_path: Output file (default: input + ".age")
            recipient: Public key to encrypt to (default: self)
        
        Returns:
            Path to encrypted file
        """
        self._check_age_installed()
        
        input_path = Path(plaintext_path).expanduser()
        if not input_path.exists():
            raise VaultCryptoError(f"Input file not found: {input_path}")
        
        if ciphertext_path is None:
            output_path = Path(str(input_path) + ".age")
        else:
            output_path = Path(ciphertext_path).expanduser()
        
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
        ciphertext_path: Union[str, Path],
        plaintext_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Decrypt a file using age.
        
        Args:
            ciphertext_path: File to decrypt (.age file)
            plaintext_path: Output file (default: secure tempfile)
        
        Returns:
            Path to decrypted file
        """
        self._check_age_installed()
        
        input_path = Path(ciphertext_path).expanduser()
        if not input_path.exists():
            raise VaultCryptoError(f"Encrypted file not found: {input_path}")
        
        if not self.key_file.exists():
            raise VaultCryptoError(f"Private key not found: {self.key_file}")
        
        if plaintext_path is None:
            # Create secure temp file in RAM if possible
            temp_dir = get_secure_temp_dir()
            if temp_dir:
                # Use RAM-backed temp directory
                fd, output_path = tempfile.mkstemp(
                    prefix="kimi-vault-secrets-",
                    suffix=".json",
                    dir=str(temp_dir)
                )
                os.close(fd)
                output_path = Path(output_path)
            else:
                # Fallback to system temp
                fd, output_path = tempfile.mkstemp(prefix="kimi-vault-secrets-", suffix=".json")
                os.close(fd)
                output_path = Path(output_path)
        else:
            output_path = Path(plaintext_path).expanduser()
        
        try:
            subprocess.run(
                ["age", "-d", "-i", str(self.key_file), "-o", str(output_path), str(input_path)],
                capture_output=True,
                check=True
            )
            # Secure the temp file
            os.chmod(output_path, 0o600)
            return output_path
        except subprocess.CalledProcessError as e:
            # Clean up temp file on failure
            if plaintext_path is None and output_path.exists():
                output_path.unlink()
            raise VaultCryptoError(f"Decryption failed: {e.stderr.decode()}")
    
    def decrypt_to_string(self, ciphertext_path: Union[str, Path]) -> str:
        """
        Decrypt a file and return contents as string.
        
        Warning: Be careful - secrets will be in memory.
        """
        self._check_age_installed()
        
        input_path = Path(ciphertext_path).expanduser()
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


def is_ram_disk(path: Union[str, Path]) -> bool:
    """Check if path is on a RAM-backed filesystem (tmpfs)"""
    try:
        result = subprocess.run(
            ["df", "-T", str(path)],
            capture_output=True,
            text=True,
            check=True
        )
        return "tmpfs" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def secure_delete(file_path: Union[str, Path]):
    """
    Securely delete a file.
    
    If the file is on a RAM disk (tmpfs), regular delete is sufficient
    since the data was never on physical disk.
    
    Otherwise, use shred to overwrite before deleting (best effort on SSDs).
    """
    path = Path(file_path).expanduser()
    if not path.exists():
        return
    
    # Check if on RAM disk
    if is_ram_disk(path):
        # On RAM disk - regular delete is sufficient
        # Data was never on physical storage
        path.unlink()
        return
    
    # On physical storage - try shred first
    try:
        subprocess.run(
            ["shred", "-u", str(path)],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to regular delete
        path.unlink()
