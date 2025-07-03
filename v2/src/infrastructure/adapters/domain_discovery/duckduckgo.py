"""
DuckDuckGo Domain Discovery Adapter for Theodore v2.

Implements domain discovery using DuckDuckGo search with intelligent
result analysis and domain validation.
"""

import asyncio
import time
from typing import Optional, List, Dict, Any, AsyncIterator
from urllib.parse import urlparse, quote_plus
import re
import aiohttp
from dataclasses import asdict
import logging

from src.core.ports.domain_discovery import (
    DomainDiscoveryPort,
    CacheableDomainDiscovery,
    StreamingDomainDiscovery,
    DomainDiscoveryResult,
    DomainDiscoveryConfig,
    DiscoveryStrategy,
    DomainValidationLevel,
    DomainDiscoveryException,
    DomainDiscoveryTimeoutException,
    DomainValidationException,
    normalize_company_name,
    extract_domain_from_url,
    is_valid_domain_format
)
from .config import DuckDuckGoConfig

logger = logging.getLogger(__name__)


class DomainCache:
    """Simple in-memory cache for domain discovery results."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 86400):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[DomainDiscoveryResult]:
        """Get cached result if valid."""
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            self._evict(key)
            return None
        
        data = self._cache[key]
        return DomainDiscoveryResult(**data)
    
    def set(self, key: str, result: DomainDiscoveryResult) -> None:
        """Cache a result."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        self._cache[key] = asdict(result)
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
        
        # Simple pattern matching (contains)
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
            'ttl_seconds': self.ttl_seconds,
            'hit_rate': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
        }


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 30, burst_size: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token from the rate limiter."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Add tokens based on time passed
            tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            
            # Wait for next token
            wait_time = (1.0 - self.tokens) * (60.0 / self.requests_per_minute)
            await asyncio.sleep(wait_time)
            self.tokens = 0.0


class DuckDuckGoAdapter(CacheableDomainDiscovery, StreamingDomainDiscovery):
    """
    DuckDuckGo-based domain discovery adapter.
    
    Uses DuckDuckGo search to find company domains with intelligent
    result analysis and domain validation.
    """
    
    def __init__(self, config: Optional[DuckDuckGoConfig] = None):
        self.config = config or DuckDuckGoConfig()
        self._cache = DomainCache(
            max_size=self.config.cache_max_size,
            ttl_seconds=self.config.cache_ttl_seconds
        )
        self._rate_limiter = RateLimiter(
            requests_per_minute=self.config.rate_limit_requests_per_minute,
            burst_size=self.config.rate_limit_burst_size
        )
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.config.get_headers()
            )
        return self._session
    
    async def discover_domain(
        self,
        company_name: str,
        config: Optional[DomainDiscoveryConfig] = None
    ) -> DomainDiscoveryResult:
        """
        Discover the primary domain for a company.
        """
        start_time = time.time()
        
        try:
            # Normalize company name
            normalized_name = normalize_company_name(company_name)
            cache_key = f"domain:{normalized_name}"
            
            # Check cache first
            if self.config.enable_caching:
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for company: {company_name}")
                    return cached_result
            
            # Perform search
            await self._rate_limiter.acquire()
            search_results = await self._search_company_domain(normalized_name)
            
            # Analyze results
            domain_candidates = self._extract_domain_candidates(search_results, normalized_name)
            
            # Select best domain
            best_domain = await self._select_best_domain(domain_candidates, normalized_name)
            
            # Validate domain if enabled and found
            is_validated = False
            validation_level = config.validation_level if config else DomainValidationLevel.HTTP_CHECK
            
            if best_domain and self.config.enable_domain_validation:
                is_validated = await self.validate_domain(best_domain, validation_level)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                best_domain, domain_candidates, normalized_name, is_validated
            )
            
            # Create result
            search_time_ms = (time.time() - start_time) * 1000
            result = DomainDiscoveryResult(
                company_name=company_name,
                discovered_domain=best_domain,
                confidence_score=confidence,
                discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
                validation_level=validation_level,
                is_validated=is_validated,
                search_time_ms=search_time_ms,
                metadata={
                    'search_engine': 'duckduckgo',
                    'candidates_found': len(domain_candidates),
                    'normalized_name': normalized_name,
                    'search_results_count': len(search_results)
                },
                alternative_domains=[
                    candidate['domain'] for candidate in domain_candidates[1:4]
                    if candidate['domain'] != best_domain
                ]
            )
            
            # Cache result
            if self.config.enable_caching:
                self._cache.set(cache_key, result)
            
            logger.info(
                f"Domain discovery completed for {company_name}: "
                f"{best_domain} (confidence: {confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            search_time_ms = (time.time() - start_time) * 1000
            error_message = str(e)
            
            if isinstance(e, asyncio.TimeoutError):
                error_message = f"Search timeout after {self.config.timeout_seconds}s"
                raise DomainDiscoveryTimeoutException(error_message)
            
            logger.error(f"Domain discovery failed for {company_name}: {error_message}")
            
            return DomainDiscoveryResult(
                company_name=company_name,
                discovered_domain=None,
                confidence_score=0.0,
                discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
                validation_level=config.validation_level if config else DomainValidationLevel.HTTP_CHECK,
                is_validated=False,
                search_time_ms=search_time_ms,
                metadata={'error': error_message},
                error_message=error_message
            )
    
    async def _search_company_domain(self, company_name: str) -> List[Dict[str, Any]]:
        """Search for company domain using DuckDuckGo."""
        query = self.config.search_query_template.format(company_name=company_name)
        encoded_query = quote_plus(query)
        
        # DuckDuckGo HTML search URL
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        session = await self._get_session()
        
        try:
            async with session.get(search_url) as response:
                if response.status != 200:
                    raise DomainDiscoveryException(f"Search request failed: {response.status}")
                
                html_content = await response.text()
                return self._parse_search_results(html_content)
                
        except aiohttp.ClientError as e:
            raise DomainDiscoveryException(f"Network error during search: {e}")
    
    def _parse_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo search results from HTML."""
        results = []
        
        # Simple regex-based parsing for DuckDuckGo results
        # This is a basic implementation - production code might use BeautifulSoup
        result_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
        description_pattern = r'<span[^>]*class="[^"]*snippet[^"]*"[^>]*>([^<]+)</span>'
        
        matches = re.finditer(result_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for i, match in enumerate(matches):
            if i >= self.config.max_search_results:
                break
            
            url = match.group(1)
            title = match.group(2)
            
            # Skip if this is a DuckDuckGo internal link
            if 'duckduckgo.com' in url or url.startswith('/'):
                continue
            
            # Extract description (simplified)
            description = ""
            desc_match = re.search(description_pattern, html_content[match.end():match.end()+500])
            if desc_match:
                description = desc_match.group(1)
            
            results.append({
                'url': url,
                'title': title.strip(),
                'description': description.strip()
            })
        
        return results
    
    def _extract_domain_candidates(
        self, 
        search_results: List[Dict[str, Any]], 
        company_name: str
    ) -> List[Dict[str, Any]]:
        """Extract and score domain candidates from search results."""
        candidates = []
        seen_domains = set()
        
        for result in search_results[:self.config.result_analysis_depth]:
            domain = extract_domain_from_url(result['url'])
            
            if not domain or domain in seen_domains:
                continue
            
            # Skip excluded domains
            if self.config.should_exclude_domain(domain):
                continue
            
            seen_domains.add(domain)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(
                domain, result['title'], result['description'], company_name
            )
            
            candidates.append({
                'domain': domain,
                'relevance_score': relevance_score,
                'title': result['title'],
                'description': result['description'],
                'url': result['url']
            })
        
        # Sort by relevance score
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        return candidates
    
    def _calculate_relevance_score(
        self, 
        domain: str, 
        title: str, 
        description: str, 
        company_name: str
    ) -> float:
        """Calculate relevance score for a domain candidate."""
        score = 0.0
        
        # Base score from domain preference
        score += self.config.get_domain_preference_score(domain)
        
        # Company name similarity
        company_words = set(company_name.lower().split())
        domain_words = set(re.split(r'[.-]', domain.lower()))
        
        if company_words & domain_words:
            score += 0.3  # Boost for matching words
        
        # Title and description analysis
        content = f"{title} {description}".lower()
        
        # Boost for positive keywords
        for keyword in self.config.confidence_boost_keywords:
            if keyword in content:
                score += 0.1
        
        # Penalty for negative keywords
        for keyword in self.config.confidence_penalty_keywords:
            if keyword in content:
                score -= 0.15
        
        # Company name in title/description
        if company_name.lower() in content:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    async def _select_best_domain(
        self, 
        candidates: List[Dict[str, Any]], 
        company_name: str
    ) -> Optional[str]:
        """Select the best domain from candidates."""
        if not candidates:
            return None
        
        # Filter by minimum confidence
        valid_candidates = [
            c for c in candidates 
            if c['relevance_score'] >= self.config.min_confidence_threshold
        ]
        
        if not valid_candidates:
            return None
        
        return valid_candidates[0]['domain']
    
    def _calculate_confidence(
        self,
        domain: Optional[str],
        candidates: List[Dict[str, Any]],
        company_name: str,
        is_validated: bool
    ) -> float:
        """Calculate overall confidence score."""
        if not domain:
            return 0.0
        
        # Find the selected domain in candidates
        domain_candidate = next(
            (c for c in candidates if c['domain'] == domain), 
            None
        )
        
        if not domain_candidate:
            return 0.0
        
        confidence = domain_candidate['relevance_score']
        
        # Boost for validation
        if is_validated:
            confidence += 0.2
        
        # Boost if significantly better than alternatives
        if len(candidates) > 1:
            second_best = candidates[1]['relevance_score']
            if confidence > second_best + 0.2:
                confidence += 0.1
        
        return min(1.0, confidence)
    
    async def validate_domain(
        self,
        domain: str,
        validation_level: DomainValidationLevel = DomainValidationLevel.HTTP_CHECK
    ) -> bool:
        """
        Validate that a domain is accessible and likely correct.
        """
        if validation_level == DomainValidationLevel.NONE:
            return True
        
        if validation_level == DomainValidationLevel.BASIC:
            return is_valid_domain_format(domain)
        
        # HTTP validation
        if validation_level in [DomainValidationLevel.HTTP_CHECK, DomainValidationLevel.FULL_CHECK]:
            try:
                session = await self._get_session()
                
                # Try HTTPS first, then HTTP
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}"
                    
                    try:
                        timeout = aiohttp.ClientTimeout(total=self.config.validation_timeout_seconds)
                        async with session.head(
                            url, 
                            timeout=timeout,
                            allow_redirects=self.config.follow_redirects,
                            max_redirects=self.config.max_redirects
                        ) as response:
                            if 200 <= response.status < 400:
                                return True
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        continue  # Try next protocol
                
                return False
                
            except Exception as e:
                logger.warning(f"Domain validation failed for {domain}: {e}")
                return False
        
        return False
    
    async def discover_domains_batch(
        self,
        company_names: List[str],
        config: Optional[DomainDiscoveryConfig] = None
    ) -> List[DomainDiscoveryResult]:
        """
        Discover domains for multiple companies.
        """
        tasks = [
            self.discover_domain(name, config)
            for name in company_names
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def discover_domains_streaming(
        self,
        company_names: List[str],
        config: Optional[DomainDiscoveryConfig] = None
    ) -> AsyncIterator[DomainDiscoveryResult]:
        """
        Stream domain discovery results as they become available.
        """
        tasks = [
            self.discover_domain(name, config)
            for name in company_names
        ]
        
        # Use asyncio.as_completed for streaming results
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result
    
    def get_supported_strategies(self) -> List[DiscoveryStrategy]:
        """
        Get list of discovery strategies supported by this adapter.
        """
        return [DiscoveryStrategy.SEARCH_ENGINE]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health and availability of the domain discovery service.
        """
        start_time = time.time()
        
        try:
            # Test search functionality
            session = await self._get_session()
            test_url = "https://html.duckduckgo.com/html/?q=test"
            
            async with session.get(test_url) as response:
                response_time = (time.time() - start_time) * 1000
                
                return {
                    'status': 'healthy' if response.status == 200 else 'degraded',
                    'response_time_ms': response_time,
                    'service': 'duckduckgo',
                    'cache_stats': self._cache.get_stats(),
                    'config': {
                        'timeout_seconds': self.config.timeout_seconds,
                        'max_retries': self.config.max_retries,
                        'enable_caching': self.config.enable_caching,
                        'enable_validation': self.config.enable_domain_validation
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': (time.time() - start_time) * 1000,
                'service': 'duckduckgo'
            }
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached domain discovery results.
        """
        return self._cache.clear(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        """
        return self._cache.get_stats()
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()