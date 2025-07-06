"""
DuckDuckGo Domain Discovery - Complete V2 Implementation
Self-contained module for discovering company domains using DuckDuckGo search.

This module ports the entire V2 domain discovery system into a single file,
providing both simple and advanced interfaces for domain discovery.

Usage:
    # Simple usage
    domain = await find_website_url("CloudGeometry")
    # or synchronously:
    domain = find_website_url_sync("CloudGeometry")
    
    # Advanced usage with full result
    result = await discover_domain_detailed("CloudGeometry")
    print(f"Domain: {result.discovered_domain}, Confidence: {result.confidence_score}")
"""

import asyncio
import time
import re
import logging
import os
from typing import Optional, List, Dict, Any, AsyncIterator
from urllib.parse import urlparse, quote_plus
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in parent directories
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("⚠️ No .env file found, using system environment variables")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")

logger = logging.getLogger(__name__)


# Enums and Data Classes
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
    validation_level: DomainValidationLevel = DomainValidationLevel.HTTP_CHECK
    timeout_seconds: float = 10.0
    enable_caching: bool = True
    max_results: int = 10


# Exception Classes
class DomainDiscoveryException(Exception):
    """Base exception for domain discovery operations."""
    pass


class DomainDiscoveryTimeoutException(DomainDiscoveryException):
    """Exception raised when domain discovery times out."""
    pass


class DomainValidationException(DomainDiscoveryException):
    """Exception raised during domain validation."""
    pass


# Helper Functions
def normalize_company_name(company_name: str) -> str:
    """Normalize company name for search."""
    if not company_name:
        return ""
    
    # Remove common suffixes
    suffixes = [
        'inc', 'incorporated', 'corp', 'corporation', 'llc', 'ltd', 'limited',
        'co', 'company', 'group', 'holdings', 'enterprises', 'solutions',
        'services', 'systems', 'technologies', 'tech', 'software', 'labs'
    ]
    
    normalized = company_name.strip().lower()
    
    # Remove punctuation except spaces and dashes
    normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
    
    # Split into words
    words = normalized.split()
    
    # Remove suffixes
    filtered_words = []
    for word in words:
        if word not in suffixes:
            filtered_words.append(word)
    
    return ' '.join(filtered_words).strip()


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not url:
        return None
    
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except Exception:
        return None


def is_valid_domain_format(domain: str) -> bool:
    """Check if domain has valid format."""
    if not domain:
        return False
    
    # Basic domain regex
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    return bool(re.match(domain_pattern, domain)) and len(domain) <= 253


# Configuration Class
class SearchConfig:
    """Configuration for multi-engine domain discovery adapter."""
    
    def __init__(self):
        # Request settings
        self.timeout_seconds = 10.0
        self.max_retries = 3
        self.retry_delay_seconds = 1.0
        self.retry_exponential_base = 2.0
        
        # Search settings
        self.search_query_template = '"{company_name}" official website'
        self.max_search_results = 10
        self.result_analysis_depth = 5
        
        # Domain validation settings
        self.enable_domain_validation = True
        self.validation_timeout_seconds = 5.0
        self.validate_ssl = False
        self.follow_redirects = True
        self.max_redirects = 5
        
        # Caching settings
        self.enable_caching = True
        self.cache_ttl_seconds = 86400  # 24 hours
        self.cache_max_size = 1000
        
        # User agent and headers - use realistic browser UA
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.custom_headers = {}
        
        # Rate limiting - be more conservative to avoid detection
        self.rate_limit_requests_per_minute = 6  # 1 request every 10 seconds
        self.rate_limit_burst_size = 2
        
        # Google Search API settings
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.enable_google_fallback = bool(self.google_api_key and self.google_search_engine_id)
        
        # Content filtering
        self.excluded_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'x.com',
            'instagram.com', 'youtube.com', 'wikipedia.org',
            'bloomberg.com', 'crunchbase.com', 'glassdoor.com', 'indeed.com'
        ]
        
        self.preferred_domains = ['.com', '.net', '.org', '.io', '.co']
        
        # Confidence scoring
        self.confidence_boost_keywords = [
            'official', 'homepage', 'website', 'corporate',
            'company', 'business', 'enterprise'
        ]
        
        self.confidence_penalty_keywords = [
            'wikipedia', 'linkedin', 'facebook', 'twitter',
            'news', 'article', 'blog', 'forum', 'review'
        ]
        
        self.min_confidence_threshold = 0.3
    
    def get_headers(self) -> Dict[str, str]:
        """Get complete headers for requests with realistic browser simulation."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"'
        }
        headers.update(self.custom_headers)
        return headers
    
    def should_exclude_domain(self, domain: str) -> bool:
        """Check if domain should be excluded from results."""
        domain_lower = domain.lower()
        return any(excluded in domain_lower for excluded in self.excluded_domains)
    
    def get_domain_preference_score(self, domain: str) -> float:
        """Get preference score for domain based on extension."""
        domain_lower = domain.lower()
        for i, preferred in enumerate(self.preferred_domains):
            if domain_lower.endswith(preferred):
                # Higher score for earlier preferences
                return 1.0 - (i * 0.1)
        return 0.5  # Neutral score for other extensions


# Cache Implementation
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


# Rate Limiter Implementation
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


# Main Multi-Engine Search Adapter
class MultiEngineSearchAdapter:
    """
    Multi-engine domain discovery adapter.
    
    Uses DuckDuckGo search first, with Google Custom Search API as fallback
    when rate limited. Includes intelligent result analysis and domain validation.
    """
    
    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
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
            # Determine which search engine was used
            search_engine_used = 'unknown'
            if search_results:
                # Check if any result has source info
                for result in search_results:
                    if isinstance(result, dict) and 'source' in result:
                        search_engine_used = result['source']
                        break
                else:
                    # Default to duckduckgo if no source specified
                    search_engine_used = 'duckduckgo'
            
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
                    'search_engine': search_engine_used,
                    'candidates_found': len(domain_candidates),
                    'normalized_name': normalized_name,
                    'search_results_count': len(search_results),
                    'google_fallback_enabled': self.config.enable_google_fallback
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
        """Search for company domain using DuckDuckGo first, Google Custom Search as fallback."""
        query = self.config.search_query_template.format(company_name=company_name)
        
        # Try DuckDuckGo first
        try:
            logger.info(f"Attempting DuckDuckGo search for: {company_name}")
            results = await self._search_duckduckgo(query)
            if results:
                logger.info(f"DuckDuckGo search successful: {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        # Fallback to Google Custom Search API if enabled
        if self.config.enable_google_fallback:
            try:
                logger.info(f"Falling back to Google Custom Search for: {company_name}")
                results = await self._search_google(query)
                if results:
                    logger.info(f"Google search successful: {len(results)} results")
                    return results
            except Exception as e:
                logger.warning(f"Google search failed: {e}")
        
        # If both fail, raise exception
        raise DomainDiscoveryException(f"All search engines failed for query: {query}")
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML interface."""
        encoded_query = quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        session = await self._get_session()
        
        # Add small random delay to appear more human-like
        import random
        await asyncio.sleep(random.uniform(1, 3))
        
        async with session.get(search_url) as response:
            logger.info(f"DuckDuckGo response status: {response.status} for query: {query}")
            
            if response.status == 200:
                html_content = await response.text()
                logger.info(f"DuckDuckGo HTML response length: {len(html_content)} chars")
                
                results = self._parse_search_results(html_content)
                logger.info(f"Parsed {len(results)} search results from DuckDuckGo")
                
                return results
            elif response.status == 202:
                raise DomainDiscoveryException(f"DuckDuckGo rate limited (HTTP 202)")
            else:
                raise DomainDiscoveryException(f"DuckDuckGo search failed with status {response.status}")
    
    async def _search_google(self, query: str) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        if not self.config.google_api_key or not self.config.google_search_engine_id:
            raise DomainDiscoveryException("Google API credentials not configured")
        
        # Google Custom Search API endpoint
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.config.google_api_key,
            'cx': self.config.google_search_engine_id,
            'q': query,
            'num': min(self.config.max_search_results, 10)  # Google API max is 10
        }
        
        session = await self._get_session()
        
        async with session.get(search_url, params=params) as response:
            logger.info(f"Google API response status: {response.status} for query: {query}")
            
            if response.status == 200:
                json_data = await response.json()
                results = self._parse_google_results(json_data)
                logger.info(f"Parsed {len(results)} search results from Google")
                
                return results
            else:
                error_text = await response.text()
                raise DomainDiscoveryException(f"Google search failed with status {response.status}: {error_text}")
    
    def _parse_google_results(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Google Custom Search API JSON response."""
        results = []
        
        if 'items' not in json_data:
            logger.warning("No 'items' field in Google search response")
            return results
        
        for item in json_data['items']:
            try:
                result = {
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'description': item.get('snippet', ''),
                    'source': 'google'
                }
                
                # Skip if missing essential data
                if result['url'] and result['title']:
                    results.append(result)
                    
            except Exception as e:
                logger.warning(f"Error parsing Google result item: {e}")
                continue
        
        return results
    
    def _generate_fallback_domains(self, company_name: str) -> List[Dict[str, Any]]:
        """Generate potential domains based on company name as fallback."""
        normalized_name = normalize_company_name(company_name)
        company_slug = normalized_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        
        # Generate potential domains
        potential_domains = []
        
        if company_slug:
            # Common domain patterns
            patterns = [
                f"{company_slug}.com",
                f"{company_slug}.net", 
                f"{company_slug}.org",
                f"{company_slug}.io",
                f"{company_slug}.co"
            ]
            
            # Also try with first word only for multi-word companies
            first_word = company_slug.split()[0] if ' ' in normalized_name else company_slug
            if first_word != company_slug and len(first_word) > 2:
                patterns.extend([
                    f"{first_word}.com",
                    f"{first_word}.net",
                    f"{first_word}.io"
                ])
            
            for i, domain in enumerate(patterns):
                potential_domains.append({
                    'url': f"https://{domain}",
                    'title': f"{company_name} - Official Website",
                    'description': f"Official website of {company_name}"
                })
                
                # Only generate a reasonable number
                if i >= 8:
                    break
        
        return potential_domains
    
    def _parse_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo search results from HTML with improved patterns."""
        results = []
        
        # Log a sample of the HTML for debugging
        logger.info(f"HTML sample (first 500 chars): {html_content[:500]}")
        
        # DuckDuckGo uses various patterns, let's try multiple approaches
        patterns_to_try = [
            # Pattern 1: Standard result links
            r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>',
            # Pattern 2: Any link with result in class
            r'<a[^>]+class="[^"]*result[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            # Pattern 3: Links in result containers
            r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
            # Pattern 4: Basic links (more permissive)
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
            # Pattern 5: DuckDuckGo specific result pattern
            r'result__a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        ]
        
        for pattern_num, pattern in enumerate(patterns_to_try, 1):
            logger.info(f"Trying pattern {pattern_num}: {pattern[:50]}...")
            
            matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
            pattern_results = []
            
            for i, match in enumerate(matches):
                if i >= self.config.max_search_results:
                    break
                
                url = match.group(1)
                title = match.group(2)
                
                # Skip DuckDuckGo internal links
                if ('duckduckgo.com' in url or 
                    url.startswith('/') or 
                    url.startswith('?') or
                    'javascript:' in url):
                    continue
                
                # Clean up URL - handle DuckDuckGo redirects
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/url?'):
                    # Extract actual URL from redirect
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(url.split('?', 1)[1])
                    if 'uddg' in parsed:
                        url = parsed['uddg'][0]
                
                pattern_results.append({
                    'url': url,
                    'title': title.strip(),
                    'description': f"Found via pattern {pattern_num}"
                })
            
            logger.info(f"Pattern {pattern_num} found {len(pattern_results)} results")
            if pattern_results:
                results.extend(pattern_results)
                break  # Use first successful pattern
        
        # If no patterns worked, try a very basic approach
        if not results:
            logger.warning("No results from regex patterns, trying basic URL extraction")
            url_pattern = r'https?://[^\s<>"\']+\.[a-z]{2,}'
            urls = re.findall(url_pattern, html_content, re.IGNORECASE)
            
            for i, url in enumerate(urls[:10]):  # Limit to 10 URLs
                if ('duckduckgo.com' not in url and 
                    'favicon' not in url and
                    '.css' not in url and
                    '.js' not in url):
                    results.append({
                        'url': url,
                        'title': f"URL found: {url}",
                        'description': "Extracted from HTML"
                    })
        
        logger.info(f"Final result count: {len(results)}")
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


# Public API Functions

async def find_website_url(company_name: str) -> Optional[str]:
    """
    Find the website URL for a company using multi-engine search (DuckDuckGo + Google fallback).
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        The domain name (e.g., "cloudgeometry.com") or None if not found
        
    Example:
        domain = await find_website_url("CloudGeometry")
        print(domain)  # "cloudgeometry.com"
    """
    try:
        async with MultiEngineSearchAdapter() as adapter:
            result = await adapter.discover_domain(company_name)
            return result.discovered_domain
    except Exception as e:
        logger.error(f"Error finding website URL for {company_name}: {e}")
        return None


def find_website_url_sync(company_name: str) -> Optional[str]:
    """
    Synchronous wrapper for find_website_url().
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        The domain name (e.g., "cloudgeometry.com") or None if not found
        
    Example:
        domain = find_website_url_sync("CloudGeometry")
        print(domain)  # "cloudgeometry.com"
    """
    try:
        # Check if there's already a running event loop
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(find_website_url(company_name))
        
        # There's a running loop, create a new one in a thread
        import concurrent.futures
        import threading
        
        def run_in_thread():
            # Create new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(find_website_url(company_name))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=30)  # 30 second timeout
            
    except Exception as e:
        logger.error(f"Error finding website URL for {company_name}: {e}")
        return None


async def discover_domain_detailed(
    company_name: str, 
    config: Optional[DomainDiscoveryConfig] = None
) -> DomainDiscoveryResult:
    """
    Discover domain with detailed results and metadata using multi-engine search.
    
    Args:
        company_name: Name of the company to search for
        config: Optional configuration for the discovery process
        
    Returns:
        Complete DomainDiscoveryResult with confidence scores, alternatives, etc.
        
    Example:
        result = await discover_domain_detailed("CloudGeometry")
        print(f"Domain: {result.discovered_domain}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Alternatives: {result.alternative_domains}")
    """
    async with MultiEngineSearchAdapter() as adapter:
        return await adapter.discover_domain(company_name, config)


def discover_domain_detailed_sync(
    company_name: str, 
    config: Optional[DomainDiscoveryConfig] = None
) -> DomainDiscoveryResult:
    """
    Synchronous wrapper for discover_domain_detailed().
    
    Args:
        company_name: Name of the company to search for
        config: Optional configuration for the discovery process
        
    Returns:
        Complete DomainDiscoveryResult with confidence scores, alternatives, etc.
    """
    try:
        # Check if there's already a running event loop
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(discover_domain_detailed(company_name, config))
        
        # There's a running loop, create a new one in a thread
        import concurrent.futures
        
        def run_in_thread():
            # Create new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(discover_domain_detailed(company_name, config))
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=30)  # 30 second timeout
            
    except Exception as e:
        logger.error(f"Error in detailed domain discovery for {company_name}: {e}")
        # Return error result
        return DomainDiscoveryResult(
            company_name=company_name,
            discovered_domain=None,
            confidence_score=0.0,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=config.validation_level if config else DomainValidationLevel.HTTP_CHECK,
            is_validated=False,
            search_time_ms=0.0,
            metadata={'error': str(e)},
            error_message=str(e)
        )


# Example usage and testing
if __name__ == "__main__":
    async def test_domain_discovery():
        """Test the domain discovery functionality."""
        test_companies = [
            "CloudGeometry",
            "Microsoft",
            "Google",
            "OpenAI",
            "Theodore AI"
        ]
        
        print("Testing multi-engine domain discovery (DuckDuckGo + Google fallback)...")
        
        for company in test_companies:
            print(f"\n--- Testing: {company} ---")
            
            # Simple test
            domain = await find_website_url(company)
            print(f"Simple result: {domain}")
            
            # Detailed test
            result = await discover_domain_detailed(company)
            print(f"Detailed result:")
            print(f"  Domain: {result.discovered_domain}")
            print(f"  Confidence: {result.confidence_score:.2f}")
            print(f"  Validated: {result.is_validated}")
            print(f"  Search time: {result.search_time_ms:.1f}ms")
            print(f"  Search engine: {result.metadata.get('search_engine', 'unknown')}")
            print(f"  Google fallback enabled: {result.metadata.get('google_fallback_enabled', False)}")
            print(f"  Alternatives: {result.alternative_domains}")
    
    # Run test if this file is executed directly
    asyncio.run(test_domain_discovery())