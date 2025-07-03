"""
Google Search MCP Adapter for Theodore v2.

Implements multi-provider Google search for company discovery with
intelligent company extraction from search results.
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import re
import logging

from src.core.ports.mcp_search_tool import (
    MCPSearchTool,
    StreamingMCPSearchTool,
    CacheableMCPSearchTool,
    BatchMCPSearchTool,
    MCPToolInfo,
    MCPSearchResult,
    MCPSearchFilters,
    MCPSearchCapability,
    MCPSearchException,
    MCPSearchTimeoutException,
    ProgressCallback
)
from src.core.domain.entities.company import Company
from .config import GoogleSearchConfig, GoogleSearchProvider
from .client import GoogleSearchClient

logger = logging.getLogger(__name__)


class SearchCache:
    """Simple in-memory cache for search results."""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[MCPSearchResult]:
        """Get cached results if valid."""
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            self._evict(key)
            return None
        
        data = self._cache[key]
        # Reconstruct MCPSearchResult
        companies = [Company(**c) for c in data['companies']]
        tool_info = MCPToolInfo(**data['tool_info'])
        
        return MCPSearchResult(
            companies=companies,
            tool_info=tool_info,
            query=data['query'],
            total_found=data['total_found'],
            search_time_ms=data['search_time_ms'],
            confidence_score=data.get('confidence_score'),
            metadata=data.get('metadata'),
            next_page_token=data.get('next_page_token'),
            citations=data.get('citations'),
            cost_incurred=data.get('cost_incurred')
        )
    
    def set(self, key: str, result: MCPSearchResult) -> None:
        """Cache search results."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        # Convert to serializable format
        data = {
            'companies': [c.__dict__ for c in result.companies],
            'tool_info': result.tool_info.__dict__,
            'query': result.query,
            'total_found': result.total_found,
            'search_time_ms': result.search_time_ms,
            'confidence_score': result.confidence_score,
            'metadata': result.metadata,
            'next_page_token': result.next_page_token,
            'citations': result.citations,
            'cost_incurred': result.cost_incurred
        }
        
        self._cache[key] = data
        self._timestamps[key] = time.time()
    
    def _evict(self, key: str) -> None:
        """Evict a specific key."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._timestamps:
            return
        
        oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
        self._evict(oldest_key)
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern."""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            return count
        
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            self._evict(key)
        
        return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        expired_count = sum(
            1 for ts in self._timestamps.values()
            if current_time - ts > self.ttl_seconds
        )
        
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired_count,
            'valid_entries': len(self._cache) - expired_count,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds
        }


class GoogleSearchAdapter(
    CacheableMCPSearchTool,
    StreamingMCPSearchTool,
    BatchMCPSearchTool
):
    """
    Google Search MCP adapter with multi-provider support.
    
    Supports Google Custom Search API, SerpAPI, and DuckDuckGo fallback
    with intelligent company extraction and caching.
    """
    
    def __init__(self, config: Optional[GoogleSearchConfig] = None):
        self.config = config or GoogleSearchConfig()
        self._client = GoogleSearchClient(self.config)
        self._cache = SearchCache(
            max_size=self.config.cache_max_size,
            ttl_seconds=self.config.cache_ttl_seconds
        )
        self._available_providers = self.config.get_available_providers()
        
        if not self._available_providers:
            logger.warning("No search providers available - check API key configuration")
    
    def get_tool_info(self) -> MCPToolInfo:
        """Get information about this MCP tool."""
        return MCPToolInfo(
            tool_name="Google Search",
            tool_version="1.0.0",
            capabilities=self.get_supported_capabilities(),
            tool_config={
                'max_results': self.config.max_results,
                'timeout_seconds': self.config.timeout_seconds,
                'available_providers': [str(p) for p in self._available_providers],
                'enable_caching': self.config.enable_caching
            },
            cost_per_request=0.01,  # Estimated cost
            rate_limit_per_minute=self.config.rate_limit_requests_per_minute,
            max_results_per_query=self.config.max_results,
            supports_filters=True,
            supports_pagination=False,  # Not implemented yet
            metadata={
                'providers': [str(p) for p in self._available_providers],
                'company_extraction': self.config.extract_company_info
            }
        )
    
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
        """
        start_time = time.time()
        
        try:
            # Build search query
            search_query = self._build_search_query(
                company_name, company_website, company_description, filters
            )
            
            if progress_callback:
                progress_callback(f"Searching for companies similar to {company_name}", 0.1, None)
            
            # Generate cache key
            cache_key = self._generate_cache_key(
                company_name, company_website, company_description, limit, filters
            )
            
            # Check cache first
            if self.config.enable_caching:
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for company: {company_name}")
                    if progress_callback:
                        progress_callback("Retrieved from cache", 1.0, None)
                    return cached_result
            
            if progress_callback:
                progress_callback("Executing search", 0.3, None)
            
            # Try providers in order
            last_error = None
            for provider in self._available_providers:
                try:
                    logger.debug(f"Trying search provider: {provider}")
                    raw_results = await self._search_with_provider(provider, search_query, limit)
                    
                    if progress_callback:
                        progress_callback(f"Processing results from {provider}", 0.6, None)
                    
                    # Extract companies from results
                    companies = await self._extract_companies_from_results(
                        raw_results, company_name, filters
                    )
                    
                    if progress_callback:
                        progress_callback("Finalizing results", 0.9, None)
                    
                    # Create result
                    search_time_ms = (time.time() - start_time) * 1000
                    tool_info = self.get_tool_info()
                    
                    result = MCPSearchResult(
                        companies=companies,
                        tool_info=tool_info,
                        query=search_query,
                        total_found=len(companies),
                        search_time_ms=search_time_ms,
                        confidence_score=self._calculate_overall_confidence(companies),
                        metadata={
                            'provider_used': str(provider),
                            'original_company': company_name,
                            'search_query': search_query,
                            'raw_results_count': len(raw_results)
                        },
                        citations=[result.get('url', '') for result in raw_results[:5]],
                        cost_incurred=tool_info.estimate_cost(1)
                    )
                    
                    # Cache result
                    if self.config.enable_caching:
                        self._cache.set(cache_key, result)
                    
                    if progress_callback:
                        progress_callback("Search completed", 1.0, None)
                    
                    logger.info(
                        f"Company search completed with {provider}: {len(companies)} companies "
                        f"found in {search_time_ms:.0f}ms"
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Search provider {provider} failed: {e}")
                    last_error = e
                    continue
            
            # All providers failed
            if last_error:
                if isinstance(last_error, asyncio.TimeoutError):
                    raise MCPSearchTimeoutException(f"All search providers timed out")
                else:
                    raise MCPSearchException(f"All search providers failed: {last_error}")
            else:
                raise MCPSearchException("No search providers available")
                
        except Exception as e:
            search_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Company search failed after {search_time_ms:.0f}ms: {e}")
            
            if progress_callback:
                progress_callback(f"Search failed: {str(e)}", 1.0, str(e))
            
            raise
    
    def _build_search_query(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        company_description: Optional[str] = None,
        filters: Optional[MCPSearchFilters] = None
    ) -> str:
        """Build search query for finding similar companies."""
        query_parts = []
        
        # Base query for similar companies
        if company_description:
            # Use description to find similar companies
            query_parts.append(f'companies like "{company_name}" {company_description}')
        else:
            # Generic similar company search
            query_parts.append(f'companies similar to "{company_name}"')
        
        # Add industry/sector filters if available
        if filters:
            if hasattr(filters, 'industry') and filters.industry:
                query_parts.append(f'industry:{filters.industry}')
            if hasattr(filters, 'location') and filters.location:
                query_parts.append(f'location:{filters.location}')
            if hasattr(filters, 'company_size') and filters.company_size:
                query_parts.append(f'size:{filters.company_size}')
        
        return ' '.join(query_parts)
    
    async def _search_with_provider(
        self, 
        provider: GoogleSearchProvider, 
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search with a specific provider."""
        max_results = min(limit, self.config.max_results)
        
        if provider == GoogleSearchProvider.CUSTOM_SEARCH:
            return await self._client.search_google_custom(query, max_results)
        elif provider == GoogleSearchProvider.SERPAPI:
            return await self._client.search_serpapi(query, max_results)
        elif provider == GoogleSearchProvider.DUCKDUCKGO:
            return await self._client.search_duckduckgo(query, max_results)
        else:
            raise MCPSearchException(f"Unknown provider: {provider}")
    
    async def _extract_companies_from_results(
        self,
        raw_results: List[Dict[str, Any]],
        original_company: str,
        filters: Optional[MCPSearchFilters] = None
    ) -> List[Company]:
        """Extract Company objects from raw search results."""
        companies_with_scores = []
        
        for result in raw_results:
            # Skip excluded domains
            url = result.get('url', '')
            if url and self._should_exclude_url(url):
                continue
            
            # Extract company information
            company_info = self._extract_company_from_result(result)
            
            if company_info and company_info.get('confidence_score', 0) >= self.config.company_confidence_threshold:
                # Create Company object
                company = Company(
                    name=company_info.get('name', 'Unknown Company'),
                    website=company_info.get('domain', url),
                    description=result.get('snippet', '')
                )
                
                # Skip if it's the same as the original company
                if not self._is_same_company(company.name, original_company):
                    # Store company with its confidence score
                    companies_with_scores.append((company, company_info.get('confidence_score', 0.0)))
        
        # Sort by confidence score
        companies_with_scores.sort(key=lambda item: item[1], reverse=True)
        
        # Return just the companies
        return [company for company, score in companies_with_scores]
    
    def _extract_company_from_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract company information from a search result."""
        try:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            url = result.get('url', '')
            
            # Extract potential company name from title
            company_name = self._extract_company_name_from_title(title)
            
            if not company_name:
                return None
            
            # Extract domain
            domain = None
            if url:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
            
            # Calculate confidence score
            confidence = self._calculate_company_confidence(title, snippet, url, company_name)
            
            return {
                'name': company_name,
                'domain': domain,
                'confidence_score': confidence,
                'title': title,
                'snippet': snippet,
                'url': url
            }
            
        except Exception as e:
            logger.warning(f"Company extraction failed: {e}")
            return None
    
    def _extract_company_name_from_title(self, title: str) -> Optional[str]:
        """Extract company name from search result title."""
        # Common patterns for company names in titles
        patterns = [
            r'^([^-|]+?)\s+official\s+(?:website|homepage)$',  # "Company Name official website"
            r'^([^-|]+?)\s+(?:homepage|website)$',  # "Company Name website" (without official)
            r'^([^-|]+?)\s*(?:[-|].*)?$',  # "Company Name - Description"
            r'^(.+?)\s*(?:\.\.\.|:)',  # "Company Name..."
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                # Filter out generic terms and ensure reasonable length
                if (len(potential_name) > 2 and 
                    len(potential_name) < 100 and
                    not potential_name.lower() in ['home', 'about', 'contact', 'company']):
                    return potential_name
        
        return None
    
    def _calculate_company_confidence(
        self, 
        title: str, 
        snippet: str, 
        url: str, 
        company_name: str
    ) -> float:
        """Calculate confidence score for extracted company."""
        score = 0.0
        
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Base score for having a company name
        score += 0.3
        
        # Company keywords in title/snippet
        for keyword in self.config.company_keywords:
            if keyword.lower() in title_lower or keyword.lower() in snippet_lower:
                score += 0.1
        
        # Official indicators
        official_indicators = ['official', 'homepage', 'website', 'corporate']
        for indicator in official_indicators:
            if indicator in title_lower:
                score += 0.2
                break
        
        # Domain quality
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Prefer company domains over general platforms
            if any(platform in domain for platform in ['linkedin', 'facebook', 'twitter', 'wikipedia']):
                score -= 0.2
            elif company_name.lower().replace(' ', '') in domain.replace('.', '').replace('-', ''):
                score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _is_same_company(self, name1: str, name2: str) -> bool:
        """Check if two company names refer to the same company."""
        # Normalize names for comparison
        norm1 = re.sub(r'[^a-zA-Z0-9]', '', name1.lower())
        norm2 = re.sub(r'[^a-zA-Z0-9]', '', name2.lower())
        
        # Remove common suffixes
        suffixes = ['inc', 'corp', 'llc', 'ltd', 'company', 'co']
        for suffix in suffixes:
            norm1 = norm1.replace(suffix, '')
            norm2 = norm2.replace(suffix, '')
        
        # Check if names are very similar
        return norm1 == norm2 or norm1 in norm2 or norm2 in norm1
    
    def _should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Exclude if no domain found (invalid URL)
            if not domain:
                return True
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return self.config.should_exclude_domain(domain)
            
        except Exception:
            return True  # Exclude if we can't parse the URL
    
    def _calculate_overall_confidence(self, companies: List[Company]) -> Optional[float]:
        """Calculate overall confidence score for the search results."""
        if not companies:
            return None
        
        # Since we don't store confidence on Company objects,
        # return a simple confidence based on number of results
        # In a real implementation, you'd store confidence scores separately
        base_confidence = min(0.8, len(companies) * 0.2)
        return base_confidence
    
    def _generate_cache_key(
        self,
        company_name: str,
        company_website: Optional[str],
        company_description: Optional[str],
        limit: int,
        filters: Optional[MCPSearchFilters]
    ) -> str:
        """Generate cache key for search parameters."""
        key_parts = [
            company_name,
            company_website or "",
            company_description or "",
            str(limit),
            str(filters.__dict__ if filters else "")
        ]
        return "|".join(key_parts)
    
    def get_supported_capabilities(self) -> List[MCPSearchCapability]:
        """Get list of search capabilities supported by this tool."""
        return [
            MCPSearchCapability.WEB_SEARCH,
            MCPSearchCapability.COMPANY_RESEARCH,
            MCPSearchCapability.COMPETITIVE_ANALYSIS,
            MCPSearchCapability.REAL_TIME_DATA
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health and availability of the search service."""
        start_time = time.time()
        
        health_info = {
            'service': 'google_search',
            'available_providers': [str(p) for p in self._available_providers],
            'cache_stats': self._cache.get_stats(),
            'config': {
                'max_results': self.config.max_results,
                'timeout_seconds': self.config.timeout_seconds,
                'enable_caching': self.config.enable_caching
            }
        }
        
        # Test each provider
        provider_health = {}
        for provider in self._available_providers:
            try:
                # Simple test search
                await self._search_with_provider(provider, "test company", 1)
                provider_health[str(provider)] = 'healthy'
            except Exception as e:
                provider_health[str(provider)] = f'unhealthy: {str(e)}'
        
        health_info['providers'] = provider_health
        health_info['response_time_ms'] = (time.time() - start_time) * 1000
        
        # Overall status
        healthy_providers = sum(1 for status in provider_health.values() if status == 'healthy')
        health_info['status'] = 'healthy' if healthy_providers > 0 else 'unhealthy'
        
        return health_info
    
    # Cacheable interface methods
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cached search results."""
        return self._cache.clear(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return self._cache.get_stats()
    
    # Streaming interface methods (basic implementation)
    async def search_similar_companies_streaming(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        company_description: Optional[str] = None,
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        page_token: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ):
        """Stream search results as they become available."""
        # For now, implement as batch then stream
        # Future enhancement: implement true streaming
        result = await self.search_similar_companies(
            company_name, company_website, company_description, 
            limit, filters, page_token, progress_callback
        )
        
        for company in result.companies:
            yield company
            # Small delay to simulate streaming
            await asyncio.sleep(0.01)
    
    # Batch interface methods
    async def search_similar_companies_batch(
        self,
        company_names: List[str],
        limit_per_company: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[MCPSearchResult]:
        """Process multiple company search requests concurrently."""
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        
        async def search_with_semaphore(company_name: str) -> MCPSearchResult:
            async with semaphore:
                return await self.search_similar_companies(
                    company_name, limit=limit_per_company, filters=filters, progress_callback=progress_callback
                )
        
        tasks = [search_with_semaphore(name) for name in company_names]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    # Additional required MCP methods
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> MCPSearchResult:
        """Search for companies by keywords."""
        # Convert keywords to search query
        query = ' '.join(keywords) + ' companies'
        return await self.search_similar_companies(
            company_name=query,
            limit=limit,
            filters=filters,
            progress_callback=progress_callback
        )
    
    async def get_company_details(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        requested_fields: Optional[List[str]] = None
    ) -> Optional[Company]:
        """Get detailed information about a specific company."""
        # Use search to find company details
        result = await self.search_similar_companies(
            company_name=company_name,
            company_website=company_website,
            limit=1
        )
        
        # Return the first result if found
        if result.companies:
            return result.companies[0]
        return None
    
    async def validate_configuration(self) -> bool:
        """Validate that the tool is properly configured."""
        # Check if at least one provider is available
        if not self._available_providers:
            return False
        
        # Test connectivity
        try:
            health = await self.health_check()
            return health.get('status') == 'healthy'
        except Exception:
            return False
    
    async def estimate_search_cost(
        self,
        query_count: int,
        average_results_per_query: int = 10
    ) -> float:
        """Estimate the cost for a number of search queries."""
        tool_info = self.get_tool_info()
        return tool_info.estimate_cost(query_count)
    
    # Batch and cache methods from inherited interfaces
    
    async def search_batch_companies(
        self,
        company_names: List[str],
        limit_per_company: int = 5,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, MCPSearchResult]:
        """Search for multiple companies (batch operation)."""
        results = await self.search_similar_companies_batch(
            company_names, limit_per_company, filters, progress_callback
        )
        # Convert list to dictionary mapping company names to results
        return {company_names[i]: results[i] for i in range(len(company_names))}
    
    async def get_batch_company_details(
        self,
        company_names: List[str],
        requested_fields: Optional[List[str]] = None
    ) -> Dict[str, Optional[Company]]:
        """Get details for multiple companies."""
        tasks = [
            self.get_company_details(name, requested_fields=requested_fields)
            for name in company_names
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        # Convert list to dictionary mapping company names to results
        return {company_names[i]: results[i] for i in range(len(company_names))}
    
    async def search_with_cache(
        self,
        company_name: str,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> MCPSearchResult:
        """Search with explicit cache control."""
        # Extract parameters from kwargs
        company_website = kwargs.get('company_website')
        company_description = kwargs.get('company_description')
        limit = kwargs.get('limit', 10)
        filters = kwargs.get('filters')
        force_refresh = kwargs.get('force_refresh', False)
        
        if force_refresh:
            # Clear cache for this specific search
            cache_key = self._generate_cache_key(
                company_name, company_website, company_description, limit, filters
            )
            self._cache.clear(cache_key)
        
        return await self.search_similar_companies(
            company_name=company_name,
            company_website=company_website,
            company_description=company_description,
            limit=limit,
            filters=filters
        )
    
    async def close(self) -> None:
        """Close the adapter and clean up resources."""
        await self._client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()