"""
Configuration management for Kimi Secrets Vault

Supports configuration via:
1. Environment variables (KIMI_VAULT_*)
2. Config file (~/.config/kimi-vault/config or $KIMI_VAULT_CONFIG)
3. Sensible defaults
"""

import os
from pathlib import Path
from typing import Optional


class VaultConfig:
    """Configuration manager for kimi-vault"""
    
    DEFAULT_VAULT_DIR = "~/.kimi-vault"
    DEFAULT_CONFIG_DIR = "~/.config/kimi-vault"
    DEFAULT_CONFIG_FILE = "config"
    
    def __init__(self):
        self._vault_dir: Optional[Path] = None
        self._config_dir: Optional[Path] = None
        self._config_file: Optional[Path] = None
        self._key_file: Optional[Path] = None
        self._secrets_file: Optional[Path] = None
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from env vars and/or config file"""
        # Environment variables take precedence
        self._vault_dir = self._get_path_from_env("KIMI_VAULT_DIR", self.DEFAULT_VAULT_DIR)
        self._config_dir = self._get_path_from_env("KIMI_VAULT_CONFIG_DIR", self.DEFAULT_CONFIG_DIR)
        
        config_file_env = os.environ.get("KIMI_VAULT_CONFIG")
        if config_file_env:
            self._config_file = Path(config_file_env).expanduser()
        else:
            self._config_file = self._config_dir / self.DEFAULT_CONFIG_FILE
        
        # Load from config file if it exists
        config_values = self._read_config_file()
        
        # Set paths (env var > config file > default)
        self._key_file = self._get_path(
            "KIMI_VAULT_KEY",
            config_values.get("key_file"),
            self._vault_dir / "key.txt"
        )
        
        self._secrets_file = self._get_path(
            "KIMI_VAULT_SECRETS",
            config_values.get("secrets_file"),
            self._vault_dir / "secrets.json.age"
        )
        
        # OAuth credentials (these can be in config or env)
        self._client_id = os.environ.get(
            "KIMI_VAULT_CLIENT_ID",
            config_values.get("client_id")
        )
        self._client_secret = os.environ.get(
            "KIMI_VAULT_CLIENT_SECRET",
            config_values.get("client_secret")
        )
    
    def _get_path_from_env(self, env_var: str, default: str) -> Path:
        """Get path from environment variable or use default"""
        value = os.environ.get(env_var, default)
        return Path(value).expanduser()
    
    def _get_path(self, env_var: str, config_value: Optional[str], default: Path) -> Path:
        """Get path with priority: env var > config file > default"""
        if os.environ.get(env_var):
            return Path(os.environ[env_var]).expanduser()
        if config_value:
            return Path(config_value).expanduser()
        return default
    
    def _read_config_file(self) -> dict:
        """Read configuration from file if it exists"""
        if not self._config_file.exists():
            return {}
        
        values = {}
        try:
            with open(self._config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        values[key.strip()] = value.strip().strip('"\'')
        except Exception:
            pass
        return values
    
    @property
    def vault_dir(self) -> Path:
        """Directory where vault files are stored"""
        return self._vault_dir
    
    @property
    def config_dir(self) -> Path:
        """Directory for configuration files"""
        return self._config_dir
    
    @property
    def key_file(self) -> Path:
        """Path to age private key"""
        return self._key_file
    
    @property
    def key_pub_file(self) -> Path:
        """Path to age public key"""
        return Path(str(self._key_file) + ".pub")
    
    @property
    def secrets_file(self) -> Path:
        """Path to encrypted secrets file"""
        return self._secrets_file
    
    @property
    def client_id(self) -> Optional[str]:
        """OAuth client ID for Gmail API"""
        return self._client_id
    
    @property
    def client_secret(self) -> Optional[str]:
        """OAuth client secret for Gmail API"""
        return self._client_secret
    
    @property
    def has_oauth_credentials(self) -> bool:
        """Check if OAuth credentials are configured"""
        return bool(self._client_id and self._client_secret)
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self._vault_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    
    def __repr__(self) -> str:
        return (
            f"VaultConfig("
            f"vault_dir='{self.vault_dir}', "
            f"key_file='{self.key_file}', "
            f"secrets_file='{self.secrets_file}'"
            f")"
        )


# Global config instance
_config: Optional[VaultConfig] = None


def get_config() -> VaultConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = VaultConfig()
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None
