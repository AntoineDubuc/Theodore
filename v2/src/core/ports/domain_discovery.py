"""
Domain Discovery Port Interface for Theodore.

Defines the contract for discovering company domain names from company names,
supporting various discovery strategies and validation mechanisms.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import asyncio


class DiscoveryStrategy(str, Enum):
    """Domain discovery strategies."""
    
    SEARCH_ENGINE = "search_engine"
    DNS_LOOKUP = "dns_lookup"
    WHOIS_LOOKUP = "whois_lookup"
    SOCIAL_MEDIA = "social_media"
    DIRECTORY_SERVICES = "directory_services"


class DomainValidationLevel(str, Enum):
    """Domain validation levels."""
    
    NONE = "none"  # No validation
    BASIC = "basic"  # Basic format validation
    HTTP_CHECK = "http_check"  # HTTP HEAD request validation
    FULL_CHECK = "full_check"  # Full HTTP + content validation


@dataclass
class DomainDiscoveryResult:
    """Result from domain discovery operation."""
    
    company_name: str
    discovered_domain: Optional[str]
    confidence_score: float  # 0.0 to 1.0
    discovery_strategy: DiscoveryStrategy
    validation_level: DomainValidationLevel
    is_validated: bool
    search_time_ms: float
    metadata: Dict[str, Any]
    alternative_domains: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.alternative_domains is None:
            self.alternative_domains = []


@dataclass
class DomainDiscoveryConfig:
    """Configuration for domain discovery operations."""
    
    strategy: DiscoveryStrategy = DiscoveryStrategy.SEARCH_ENGINE
    validation_level: DomainValidationLevel = DomainValidationLevel.HTTP_CHECK
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    max_alternative_domains: int = 3
    user_agent: str = "Theodore-Domain-Discovery/1.0"
    enable_caching: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    
    # Search-specific options
    search_query_template: str = '"{company_name}" official website'
    max_search_results: int = 10
    
    # Validation options
    http_timeout_seconds: float = 10.0
    follow_redirects: bool = True
    validate_ssl: bool = False


class DomainDiscoveryException(Exception):
    """Base exception for domain discovery errors."""
    pass


class DomainDiscoveryTimeoutException(DomainDiscoveryException):
    """Raised when domain discovery times out."""
    pass


class DomainValidationException(DomainDiscoveryException):
    """Raised when domain validation fails."""
    pass


class DomainDiscoveryPort(ABC):
    """
    Port interface for domain discovery services.
    
    Defines the contract for discovering company domain names from company names
    using various strategies and validation mechanisms.
    """
    
    @abstractmethod
    async def discover_domain(
        self,
        company_name: str,
        config: Optional[DomainDiscoveryConfig] = None
    ) -> DomainDiscoveryResult:
        """
        Discover the primary domain for a company.
        
        Args:
            company_name: Name of the company to find domain for
            config: Optional configuration overrides
            
        Returns:
            DomainDiscoveryResult with discovered domain and metadata
            
        Raises:
            DomainDiscoveryException: If discovery fails
            DomainDiscoveryTimeoutException: If discovery times out
        """
        pass
    
    @abstractmethod
    async def discover_domains_batch(
        self,
        company_names: List[str],
        config: Optional[DomainDiscoveryConfig] = None
    ) -> List[DomainDiscoveryResult]:
        """
        Discover domains for multiple companies.
        
        Args:
            company_names: List of company names
            config: Optional configuration overrides
            
        Returns:
            List of DomainDiscoveryResult objects
        """
        pass
    
    @abstractmethod
    async def validate_domain(
        self,
        domain: str,
        validation_level: DomainValidationLevel = DomainValidationLevel.HTTP_CHECK
    ) -> bool:
        """
        Validate that a domain is accessible and likely correct.
        
        Args:
            domain: Domain to validate
            validation_level: Level of validation to perform
            
        Returns:
            True if domain is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_strategies(self) -> List[DiscoveryStrategy]:
        """
        Get list of discovery strategies supported by this adapter.
        
        Returns:
            List of supported DiscoveryStrategy values
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health and availability of the domain discovery service.
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    # Optional methods for advanced implementations
    
    async def suggest_alternative_domains(
        self,
        company_name: str,
        primary_domain: str,
        config: Optional[DomainDiscoveryConfig] = None
    ) -> List[str]:
        """
        Suggest alternative domains for a company.
        
        Args:
            company_name: Name of the company
            primary_domain: Primary domain already discovered
            config: Optional configuration overrides
            
        Returns:
            List of alternative domain suggestions
        """
        return []
    
    async def get_domain_info(
        self,
        domain: str
    ) -> Dict[str, Any]:
        """
        Get additional information about a domain.
        
        Args:
            domain: Domain to get information for
            
        Returns:
            Dictionary with domain information (registrar, creation date, etc.)
        """
        return {}


class CacheableDomainDiscovery(DomainDiscoveryPort):
    """Extended interface for domain discovery with caching support."""
    
    @abstractmethod
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached domain discovery results.
        
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


class StreamingDomainDiscovery(DomainDiscoveryPort):
    """Extended interface for streaming domain discovery results."""
    
    @abstractmethod
    async def discover_domains_streaming(
        self,
        company_names: List[str],
        config: Optional[DomainDiscoveryConfig] = None
    ) -> AsyncIterator[DomainDiscoveryResult]:
        """
        Stream domain discovery results as they become available.
        
        Args:
            company_names: List of company names
            config: Optional configuration overrides
            
        Yields:
            DomainDiscoveryResult objects as they are discovered
        """
        # Default implementation using batch discovery
        results = await self.discover_domains_batch(company_names, config)
        for result in results:
            yield result


# Utility functions
def normalize_company_name(company_name: str) -> str:
    """
    Normalize company name for domain discovery.
    
    Args:
        company_name: Raw company name
        
    Returns:
        Normalized company name suitable for domain discovery
    """
    import re
    
    # Remove common company suffixes
    suffixes = [
        r'\s+inc\.?$', r'\s+corp\.?$', r'\s+llc\.?$', r'\s+ltd\.?$',
        r'\s+company$', r'\s+co\.?$', r'\s+corporation$'
    ]
    
    normalized = company_name.strip()
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    # Remove special characters that might interfere with search
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name or None if extraction fails
    """
    import re
    from urllib.parse import urlparse
    
    try:
        # Clean up URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Basic validation
        if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            return domain
        
        return None
    except Exception:
        return None


def is_valid_domain_format(domain: str) -> bool:
    """
    Check if domain has valid format.
    
    Args:
        domain: Domain to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    import re
    
    if not domain:
        return False
    
    # Basic domain format validation
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain.lower()))