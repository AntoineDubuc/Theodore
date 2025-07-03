"""
Google Search MCP Adapters for Theodore v2.

This package contains MCP adapters for Google search services including
Custom Search API, SerpAPI, and DuckDuckGo fallback.
"""

from .adapter import GoogleSearchAdapter
from .config import GoogleSearchConfig

__all__ = [
    'GoogleSearchAdapter',
    'GoogleSearchConfig',
]