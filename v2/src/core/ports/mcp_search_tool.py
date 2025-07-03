"""
MCP Search Tool port interface for Theodore.

This module defines the contract for MCP (Model Context Protocol) search tools,
enabling pluggable search providers for company discovery and research.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

from src.core.domain.entities.company import Company
from src.core.ports.progress import ProgressTracker


# Type aliases for cleaner signatures
from typing import Callable
ProgressCallback = Callable[[str, float, Optional[str]], None]


class MCPSearchCapability(str, Enum):
    """Capabilities that MCP search tools can provide."""
    
    WEB_SEARCH = "web_search"
    NEWS_SEARCH = "news_search" 
    COMPANY_RESEARCH = "company_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    REAL_TIME_DATA = "real_time_data"
    HISTORICAL_DATA = "historical_data"
    FINANCIAL_DATA = "financial_data"
    SOCIAL_MEDIA = "social_media"
    PATENT_SEARCH = "patent_search"
    ACADEMIC_SEARCH = "academic_search"
    CUSTOM_ENTERPRISE = "custom_enterprise"


class MCPSearchException(Exception):
    """Base exception for MCP search tool errors"""
    pass


class MCPRateLimitedException(MCPSearchException):
    """Raised when MCP tool is rate limited"""
    
    def __init__(self, tool_name: str, retry_after: Optional[int] = None):
        self.tool_name = tool_name
        self.retry_after = retry_after
        message = f"Rate limited by {tool_name}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message)


class MCPQuotaExceededException(MCPSearchException):
    """Raised when MCP tool quota is exceeded"""
    
    def __init__(self, tool_name: str, quota_type: str = "requests"):
        self.tool_name = tool_name
        self.quota_type = quota_type
        super().__init__(f"Quota exceeded for {tool_name}: {quota_type}")


class MCPConfigurationException(MCPSearchException):
    """Raised when MCP tool configuration is invalid"""
    
    def __init__(self, tool_name: str, config_issue: str):
        self.tool_name = tool_name
        self.config_issue = config_issue
        super().__init__(f"Configuration error for {tool_name}: {config_issue}")


class MCPSearchTimeoutException(MCPSearchException):
    """Raised when MCP search times out"""
    
    def __init__(self, tool_name: str, timeout: float):
        self.tool_name = tool_name
        self.timeout = timeout
        super().__init__(f"Search timeout after {timeout}s for {tool_name}")


class MCPToolInfo:
    """Information about an MCP search tool."""
    
    def __init__(
        self,
        tool_name: str,
        tool_version: str = "1.0",
        capabilities: Optional[List[MCPSearchCapability]] = None,
        tool_config: Optional[Dict[str, Any]] = None,
        cost_per_request: Optional[float] = None,
        rate_limit_per_minute: Optional[int] = None,
        max_results_per_query: int = 100,
        supports_filters: bool = True,
        supports_pagination: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.capabilities = capabilities or []
        self.tool_config = tool_config or {}
        self.cost_per_request = cost_per_request
        self.rate_limit_per_minute = rate_limit_per_minute
        self.max_results_per_query = max_results_per_query
        self.supports_filters = supports_filters
        self.supports_pagination = supports_pagination
        self.metadata = metadata or {}
    
    def has_capability(self, capability: Union[str, MCPSearchCapability]) -> bool:
        """Check if this tool has a specific capability."""
        if isinstance(capability, str):
            capability = MCPSearchCapability(capability)
        return capability in self.capabilities
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.tool_config.get(key, default)
    
    def estimate_cost(self, query_count: int) -> float:
        """Estimate cost for a number of queries."""
        if self.cost_per_request is None:
            return 0.0
        return query_count * self.cost_per_request
    
    def can_handle_rate(self, queries_per_minute: int) -> bool:
        """Check if tool can handle the requested query rate."""
        if self.rate_limit_per_minute is None:
            return True
        return queries_per_minute <= self.rate_limit_per_minute


class MCPSearchResult:
    """Result from an MCP search operation."""
    
    def __init__(
        self,
        companies: List[Company],
        tool_info: MCPToolInfo,
        query: str,
        total_found: int,
        search_time_ms: float,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        next_page_token: Optional[str] = None,
        citations: Optional[List[str]] = None,
        cost_incurred: Optional[float] = None
    ):
        self.companies = companies
        self.tool_info = tool_info
        self.query = query
        self.total_found = total_found
        self.search_time_ms = search_time_ms
        self.confidence_score = confidence_score
        self.metadata = metadata or {}
        self.next_page_token = next_page_token
        self.citations = citations or []
        self.cost_incurred = cost_incurred
    
    def has_more_results(self) -> bool:
        """Check if more results are available."""
        return self.next_page_token is not None
    
    def get_result_count(self) -> int:
        """Get number of companies returned."""
        return len(self.companies)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if results have high confidence."""
        if self.confidence_score is None:
            return False
        return self.confidence_score >= threshold


class MCPSearchFilters:
    """Filters for MCP search operations."""
    
    def __init__(
        self,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        location: Optional[str] = None,
        funding_stage: Optional[str] = None,
        founded_after: Optional[int] = None,
        founded_before: Optional[int] = None,
        revenue_range: Optional[str] = None,
        employee_count_min: Optional[int] = None,
        employee_count_max: Optional[int] = None,
        technologies: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        custom_filters: Optional[Dict[str, Any]] = None
    ):
        self.industry = industry
        self.company_size = company_size
        self.location = location
        self.funding_stage = funding_stage
        self.founded_after = founded_after
        self.founded_before = founded_before
        self.revenue_range = revenue_range
        self.employee_count_min = employee_count_min
        self.employee_count_max = employee_count_max
        self.technologies = technologies or []
        self.keywords = keywords or []
        self.exclude_keywords = exclude_keywords or []
        self.custom_filters = custom_filters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filters to dictionary format."""
        filters = {}
        
        if self.industry:
            filters["industry"] = self.industry
        if self.company_size:
            filters["company_size"] = self.company_size
        if self.location:
            filters["location"] = self.location
        if self.funding_stage:
            filters["funding_stage"] = self.funding_stage
        if self.founded_after:
            filters["founded_after"] = self.founded_after
        if self.founded_before:
            filters["founded_before"] = self.founded_before
        if self.revenue_range:
            filters["revenue_range"] = self.revenue_range
        if self.employee_count_min:
            filters["employee_count_min"] = self.employee_count_min
        if self.employee_count_max:
            filters["employee_count_max"] = self.employee_count_max
        if self.technologies:
            filters["technologies"] = self.technologies
        if self.keywords:
            filters["keywords"] = self.keywords
        if self.exclude_keywords:
            filters["exclude_keywords"] = self.exclude_keywords
        
        filters.update(self.custom_filters)
        return filters
    
    def is_empty(self) -> bool:
        """Check if any filters are set."""
        return len(self.to_dict()) == 0


class MCPSearchTool(ABC):
    """
    Port interface for MCP search tools.
    
    This interface defines the contract for all MCP search adapters,
    enabling pluggable search providers for company discovery.
    """
    
    @abstractmethod
    def get_tool_info(self) -> MCPToolInfo:
        """
        Get information about this MCP tool.
        
        Returns:
            MCPToolInfo with tool metadata and capabilities
        """
        pass
    
    @abstractmethod
    async def search_similar_companies(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        company_description: Optional[str] = None,
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        page_token: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> MCPSearchResult:
        """
        Search for companies similar to the given company.
        
        Args:
            company_name: Name of the target company
            company_website: Optional website URL for additional context
            company_description: Optional description for better matching
            limit: Maximum number of results to return
            filters: Optional search filters
            page_token: Optional token for pagination
            progress_callback: Optional callback for progress updates
            
        Returns:
            MCPSearchResult with discovered companies
            
        Raises:
            MCPRateLimitedException: If rate limited
            MCPQuotaExceededException: If quota exceeded
            MCPSearchTimeoutException: If search times out
            MCPSearchException: For other search errors
        """
        pass
    
    @abstractmethod
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> MCPSearchResult:
        """
        Search for companies by keywords.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results to return
            filters: Optional search filters
            progress_callback: Optional callback for progress updates
            
        Returns:
            MCPSearchResult with discovered companies
        """
        pass
    
    @abstractmethod
    async def get_company_details(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        requested_fields: Optional[List[str]] = None
    ) -> Optional[Company]:
        """
        Get detailed information about a specific company.
        
        Args:
            company_name: Name of the company
            company_website: Optional website for better matching
            requested_fields: Optional list of specific fields to retrieve
            
        Returns:
            Company object with details, or None if not found
        """
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        """
        Validate that the tool is properly configured.
        
        Returns:
            True if configuration is valid and tool is ready to use
            
        Raises:
            MCPConfigurationException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def estimate_search_cost(
        self,
        query_count: int,
        average_results_per_query: int = 10
    ) -> float:
        """
        Estimate the cost for a number of search queries.
        
        Args:
            query_count: Number of queries to estimate for
            average_results_per_query: Average results expected per query
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health and availability of the MCP tool.
        
        Returns:
            Dictionary with health information including:
            - status: "healthy", "degraded", or "unhealthy"
            - latency_ms: Average response latency
            - success_rate: Success rate as float (0.0-1.0)
            - quota_remaining: Remaining quota (if available)
            - last_error: Last error encountered (if any)
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
    
    # Context manager support for resource management
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        pass


class StreamingMCPSearchTool(MCPSearchTool):
    """
    Extended interface for MCP tools supporting streaming results.
    """
    
    @abstractmethod
    async def search_similar_companies_streaming(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None
    ) -> AsyncIterator[Company]:
        """
        Stream search results as they become available.
        
        Args:
            company_name: Name of the target company
            company_website: Optional website URL
            limit: Maximum number of results
            filters: Optional search filters
            
        Yields:
            Company objects as they are discovered
        """
        pass


class CacheableMCPSearchTool(MCPSearchTool):
    """
    Extended interface for MCP tools supporting result caching.
    """
    
    @abstractmethod
    async def search_with_cache(
        self,
        company_name: str,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> MCPSearchResult:
        """
        Search with caching support.
        
        Args:
            company_name: Name of the target company
            cache_ttl: Cache time-to-live in seconds
            **kwargs: Additional search parameters
            
        Returns:
            MCPSearchResult (may be from cache)
        """
        pass
    
    @abstractmethod
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached search results.
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            Number of cache entries cleared
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        pass


class BatchMCPSearchTool(MCPSearchTool):
    """
    Extended interface for MCP tools supporting batch operations.
    """
    
    @abstractmethod
    async def search_batch_companies(
        self,
        company_names: List[str],
        limit_per_company: int = 5,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, MCPSearchResult]:
        """
        Search for similar companies for multiple target companies.
        
        Args:
            company_names: List of target company names
            limit_per_company: Maximum results per company
            filters: Optional search filters
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary mapping company names to search results
        """
        pass
    
    @abstractmethod
    async def get_batch_company_details(
        self,
        company_names: List[str],
        requested_fields: Optional[List[str]] = None
    ) -> Dict[str, Optional[Company]]:
        """
        Get detailed information for multiple companies.
        
        Args:
            company_names: List of company names
            requested_fields: Optional list of fields to retrieve
            
        Returns:
            Dictionary mapping company names to Company objects
        """
        pass


# Factory interface for creating MCP search tools
class MCPSearchToolFactory(ABC):
    """
    Factory for creating MCP search tool instances.
    """
    
    @abstractmethod
    def create_tool(
        self,
        tool_type: str,
        config: Dict[str, Any]
    ) -> MCPSearchTool:
        """
        Create an MCP search tool instance.
        
        Args:
            tool_type: Type of tool to create (e.g., "perplexity", "tavily")
            config: Configuration for the tool
            
        Returns:
            MCPSearchTool implementation
            
        Raises:
            ValueError: If tool_type is not supported
            MCPConfigurationException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool types.
        
        Returns:
            List of tool type names that can be created
        """
        pass
    
    @abstractmethod
    def get_tool_info(self, tool_type: str) -> Dict[str, Any]:
        """
        Get information about a specific tool type.
        
        Args:
            tool_type: Type of tool to get info for
            
        Returns:
            Dictionary with tool information
        """
        pass


# Constants for MCP search tool features
class MCPSearchToolFeatures:
    """Constants for common MCP search tool features"""
    
    SIMILARITY_SEARCH = "similarity_search"
    KEYWORD_SEARCH = "keyword_search"
    COMPANY_DETAILS = "company_details"
    BATCH_OPERATIONS = "batch_operations"
    STREAMING = "streaming"
    CACHING = "caching"
    PAGINATION = "pagination"
    COST_ESTIMATION = "cost_estimation"
    REAL_TIME = "real_time"
    FILTERING = "filtering"


# Utility functions for MCP operations
def merge_search_results(results: List[MCPSearchResult]) -> MCPSearchResult:
    """
    Merge multiple search results into a single result.
    
    Args:
        results: List of MCPSearchResult objects to merge
        
    Returns:
        Merged MCPSearchResult
    """
    if not results:
        raise ValueError("Cannot merge empty results list")
    
    if len(results) == 1:
        return results[0]
    
    # Combine all companies
    all_companies = []
    all_citations = []
    total_search_time = 0.0
    total_cost = 0.0
    
    for result in results:
        all_companies.extend(result.companies)
        all_citations.extend(result.citations)
        total_search_time += result.search_time_ms
        if result.cost_incurred:
            total_cost += result.cost_incurred
    
    # Remove duplicates by name and website
    seen = set()
    unique_companies = []
    
    for company in all_companies:
        key = (company.name.lower(), company.website or "")
        if key not in seen:
            seen.add(key)
            unique_companies.append(company)
    
    # Create merged result
    primary_result = results[0]
    return MCPSearchResult(
        companies=unique_companies,
        tool_info=primary_result.tool_info,  # Use first tool's info
        query=primary_result.query,
        total_found=len(unique_companies),
        search_time_ms=total_search_time,
        citations=all_citations,
        cost_incurred=total_cost if total_cost > 0 else None,
        metadata={
            "merged_from_tools": [r.tool_info.tool_name for r in results],
            "original_result_counts": [r.get_result_count() for r in results]
        }
    )


def validate_mcp_tool_config(config: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate MCP tool configuration.
    
    Args:
        config: Configuration dictionary to validate
        required_fields: List of required field names
        
    Raises:
        MCPConfigurationException: If configuration is invalid
    """
    missing_fields = []
    for field in required_fields:
        if field not in config or config[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise MCPConfigurationException(
            "unknown",
            f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate common field types
    if "api_key" in config and not isinstance(config["api_key"], str):
        raise MCPConfigurationException("unknown", "api_key must be a string")
    
    if "timeout" in config:
        try:
            float(config["timeout"])
        except (ValueError, TypeError):
            raise MCPConfigurationException("unknown", "timeout must be a number")
    
    if "max_results" in config:
        try:
            max_results = int(config["max_results"])
            if max_results <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise MCPConfigurationException("unknown", "max_results must be a positive integer")