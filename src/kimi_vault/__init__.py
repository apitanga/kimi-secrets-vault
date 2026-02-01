"""
Kimi Secrets Vault - Secure, just-in-time access to API credentials

A secure vault for managing API credentials with age encryption,
just-in-time decryption, and automatic cleanup.
"""

__version__ = "1.0.0"
__author__ = "Andre Pitanga"
__license__ = "MIT"

from .client import GmailClient, GmailAuthError
from .crypto import VaultCrypto
from .config import VaultConfig

__all__ = [
    "GmailClient",
    "GmailAuthError", 
    "VaultCrypto",
    "VaultConfig",
]
