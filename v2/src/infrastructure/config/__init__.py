"""
Theodore configuration management system.

This module provides:
- Pydantic Settings-based configuration with multiple source support
- Secure credential storage using system keyring
- Comprehensive configuration validation
- Configuration precedence: CLI > env > file > defaults
"""

from .settings import TheodoreSettings, settings, Environment, LogLevel, AIModel
from .secure_storage import SecureStorage, get_secure_credential, ensure_keyring_setup
from .validators import ConfigValidator

__all__ = [
    'TheodoreSettings',
    'settings',
    'Environment', 
    'LogLevel',
    'AIModel',
    'SecureStorage',
    'get_secure_credential',
    'ensure_keyring_setup',
    'ConfigValidator'
]