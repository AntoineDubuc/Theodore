"""
Tavily AI MCP Search Tool Adapter.

Production-ready adapter for Tavily AI search integration with comprehensive
enterprise features and MCP port interface compliance.
"""

from .config import TavilyConfig, TavilySearchDepth, TavilySearchType, TavilyIncludeFields
from .client import TavilyClient, TavilyResponse, TavilyClientError, TavilyRateLimitError, TavilyQuotaError, TavilyAuthError
from .adapter import TavilyAdapter

__all__ = [
    # Configuration
    "TavilyConfig",
    "TavilySearchDepth", 
    "TavilySearchType",
    "TavilyIncludeFields",
    
    # Client
    "TavilyClient",
    "TavilyResponse",
    "TavilyClientError",
    "TavilyRateLimitError",
    "TavilyQuotaError", 
    "TavilyAuthError",
    
    # Adapter
    "TavilyAdapter"
]

# Version info
__version__ = "1.0.0"
__author__ = "Theodore v2 Team"
__description__ = "Tavily AI MCP Search Tool Adapter for Theodore"

# Tool metadata
TOOL_INFO = {
    "name": "tavily",
    "version": __version__,
    "description": __description__,
    "capabilities": [
        "web_search",
        "news_search",
        "company_research",
        "competitive_analysis",
        "real_time_data",
        "historical_data"
    ],
    "features": [
        "domain_filtering",
        "content_extraction", 
        "date_filtering",
        "result_ranking",
        "caching",
        "streaming",
        "batch_operations"
    ],
    "config_schema": {
        "api_key": {"type": "string", "required": True, "description": "Tavily API key"},
        "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "basic"},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
        "timeout_seconds": {"type": "number", "minimum": 1, "maximum": 300, "default": 30},
        "enable_caching": {"type": "boolean", "default": True},
        "cache_ttl_seconds": {"type": "integer", "minimum": 60, "maximum": 86400, "default": 1800}
    }
}

def create_tavily_adapter(config_dict: dict = None, **kwargs) -> TavilyAdapter:
    """
    Factory function to create a TavilyAdapter instance.
    
    Args:
        config_dict: Configuration dictionary
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured TavilyAdapter instance
        
    Example:
        # From environment variables
        adapter = create_tavily_adapter()
        
        # With explicit configuration
        adapter = create_tavily_adapter({
            "api_key": "tvly-xxx",
            "search_depth": "advanced",
            "max_results": 20
        })
        
        # With kwargs
        adapter = create_tavily_adapter(
            api_key="tvly-xxx",
            search_depth="advanced"
        )
    """
    if config_dict is None and not kwargs:
        # Load from environment variables
        config = TavilyConfig.from_env()
    else:
        # Merge config_dict and kwargs
        config_data = {}
        if config_dict:
            config_data.update(config_dict)
        if kwargs:
            config_data.update(kwargs)
        
        config = TavilyConfig(**config_data)
    
    return TavilyAdapter(config)

def get_tool_info() -> dict:
    """
    Get metadata about the Tavily MCP tool.
    
    Returns:
        Dictionary with tool information
    """
    return TOOL_INFO.copy()