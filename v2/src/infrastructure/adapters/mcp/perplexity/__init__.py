"""
Perplexity AI MCP Search Tool Adapter.

This module provides a production-ready adapter for Perplexity AI's search API,
implementing the MCP search tool port interface for intelligent company discovery.
"""

from .config import PerplexityConfig
from .client import PerplexityClient
from .adapter import PerplexityAdapter

__all__ = [
    "PerplexityConfig",
    "PerplexityClient", 
    "PerplexityAdapter"
]

__version__ = "1.0.0"