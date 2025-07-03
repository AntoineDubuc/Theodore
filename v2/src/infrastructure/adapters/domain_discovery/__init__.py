"""
Domain Discovery Adapters for Theodore v2.

This package contains adapters for discovering company domains from various sources.
"""

from .duckduckgo import DuckDuckGoAdapter

__all__ = [
    'DuckDuckGoAdapter',
]