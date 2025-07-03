"""
Custom CLI exceptions for Theodore.
"""

import click

class TheodoreCliError(click.ClickException):
    """Base exception for Theodore CLI errors"""
    
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code

class ConfigurationError(TheodoreCliError):
    """Raised when configuration is invalid or missing"""
    pass

class APIConnectionError(TheodoreCliError):
    """Raised when API connections fail"""
    pass

class ResearchError(TheodoreCliError):
    """Raised when research operations fail"""
    pass

class ExportError(TheodoreCliError):
    """Raised when export operations fail"""
    pass

class PluginError(TheodoreCliError):
    """Raised when plugin operations fail"""
    pass