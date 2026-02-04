"""
Configuration management for Nakimi

Supports configuration via:
1. Environment variables (NAKIMI_*)
2. Config file (~/.config/nakimi/config or $NAKIMI_CONFIG)
3. Sensible defaults
"""

import os
from pathlib import Path
from typing import Optional


class VaultConfig:
    """Configuration manager for nakimi"""
    
    DEFAULT_VAULT_DIR = "~/.nakimi"
    DEFAULT_CONFIG_DIR = "~/.config/nakimi"
    DEFAULT_CONFIG_FILE = "config"
    
    def __init__(self):
        self._vault_dir: Optional[Path] = None
        self._config_dir: Optional[Path] = None
        self._config_file: Optional[Path] = None
        self._key_file: Optional[Path] = None
        self._secrets_file: Optional[Path] = None
        self._yubikey_enabled: Optional[bool] = None
        self._yubikey_slot: Optional[str] = None
        self._yubikey_require_touch: Optional[bool] = None
        self._yubikey_pin_prompt: Optional[bool] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from env vars and/or config file"""
        # Load config file first to get any config values
        config_file_env = os.environ.get("NAKIMI_CONFIG")
        if config_file_env:
            self._config_file = Path(config_file_env).expanduser()
        else:
            # Need a temporary config_dir to find config file
            temp_config_dir = self._get_path_from_env("NAKIMI_CONFIG_DIR", self.DEFAULT_CONFIG_DIR)
            self._config_file = temp_config_dir / self.DEFAULT_CONFIG_FILE
        
        # Load from config file if it exists
        config_values = self._read_config_file()
        
        # Set paths (env var > config file > default)
        self._vault_dir = self._get_path(
            "NAKIMI_DIR",
            config_values.get("vault_dir"),
            Path(self.DEFAULT_VAULT_DIR).expanduser()
        )
        self._config_dir = self._get_path_from_env("NAKIMI_CONFIG_DIR", self.DEFAULT_CONFIG_DIR)
        
        self._key_file = self._get_path(
            "NAKIMI_KEY",
            config_values.get("key_file"),
            self._vault_dir / "key.txt"
        )
        
        self._secrets_file = self._get_path(
            "NAKIMI_SECRETS",
            config_values.get("secrets_file"),
            self._vault_dir / "secrets.json.age"
        )
        
        # YubiKey settings (env var > config file > default)
        self._yubikey_enabled = self._get_bool(
            "NAKIMI_YUBIKEY_ENABLED",
            config_values.get("yubikey_enabled"),
            False
        )
        self._yubikey_slot = self._get_str(
            "NAKIMI_YUBIKEY_SLOT",
            config_values.get("yubikey_slot"),
            "1"
        )
        self._yubikey_require_touch = self._get_bool(
            "NAKIMI_YUBIKEY_REQUIRE_TOUCH",
            config_values.get("yubikey_require_touch"),
            True
        )
        self._yubikey_pin_prompt = self._get_bool(
            "NAKIMI_YUBIKEY_PIN_PROMPT",
            config_values.get("yubikey_pin_prompt"),
            True
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
    
    def _get_bool(self, env_var: str, config_value: Optional[str], default: bool) -> bool:
        """Get boolean value with priority: env var > config file > default"""
        env_val = os.environ.get(env_var)
        if env_val:
            return env_val.lower() in ('true', 'yes', '1', 'on')
        if config_value:
            return config_value.lower() in ('true', 'yes', '1', 'on')
        return default
    
    def _get_str(self, env_var: str, config_value: Optional[str], default: str) -> str:
        """Get string value with priority: env var > config file > default"""
        env_val = os.environ.get(env_var)
        if env_val:
            return env_val
        if config_value:
            return config_value
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
    def yubikey_enabled(self) -> bool:
        """Whether YubiKey is enabled"""
        return self._yubikey_enabled
    
    @property
    def yubikey_slot(self) -> str:
        """YubiKey slot to use"""
        return self._yubikey_slot
    
    @property
    def yubikey_require_touch(self) -> bool:
        """Whether touch is required for YubiKey operations"""
        return self._yubikey_require_touch
    
    @property
    def yubikey_pin_prompt(self) -> bool:
        """Whether to prompt for PIN for YubiKey operations"""
        return self._yubikey_pin_prompt
    
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
