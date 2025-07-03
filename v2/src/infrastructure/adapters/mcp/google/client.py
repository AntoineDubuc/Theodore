"""
HTTP client for Google Search MCP adapter.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
import aiohttp
import logging
from urllib.parse import urlencode, quote_plus
import json

from .config import GoogleSearchProvider, GoogleSearchConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
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


class GoogleSearchClient:
    """HTTP client for Google search providers."""
    
    def __init__(self, config: GoogleSearchConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_requests_per_minute,
            burst_size=config.rate_limit_burst_size
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            connector = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=self.config.concurrent_requests,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.config.get_headers()
            )
        return self._session
    
    async def search_google_custom(
        self, 
        query: str, 
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        if not self.config.google_api_key or not self.config.google_cse_id:
            raise ValueError("Google Custom Search API key and CSE ID are required")
        
        await self._rate_limiter.acquire()
        session = await self._get_session()
        
        # Build API URL
        params = {
            'key': self.config.google_api_key,
            'cx': self.config.google_cse_id,
            'q': query,
            'num': min(num_results, 10),  # API limit is 10 per request
            'lr': f'lang_{self.config.search_language}',
            'gl': self.config.search_country,
            'safe': 'active' if self.config.enable_safe_search else 'off'
        }
        
        url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Google Custom Search API error: {error_text}"
                    )
                
                data = await response.json()
                return self._parse_google_custom_results(data)
                
        except aiohttp.ClientError as e:
            logger.error(f"Google Custom Search request failed: {e}")
            raise
    
    def _parse_google_custom_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Google Custom Search API results."""
        results = []
        
        items = data.get('items', [])
        for item in items:
            result = {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayed_url': item.get('displayLink', ''),
                'provider': 'google_custom'
            }
            
            # Add additional metadata if available
            if 'pagemap' in item:
                pagemap = item['pagemap']
                if 'organization' in pagemap:
                    result['organization'] = pagemap['organization']
                if 'metatags' in pagemap:
                    result['metatags'] = pagemap['metatags']
            
            results.append(result)
        
        return results
    
    async def search_serpapi(
        self, 
        query: str, 
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI."""
        if not self.config.serpapi_key:
            raise ValueError("SerpAPI key is required")
        
        await self._rate_limiter.acquire()
        session = await self._get_session()
        
        # Build API URL
        params = {
            'api_key': self.config.serpapi_key,
            'engine': self.config.serpapi_engine,
            'q': query,
            'num': num_results,
            'google_domain': f'google.{self.config.search_country}',
            'hl': self.config.search_language,
            'gl': self.config.search_country,
            'safe': 'active' if self.config.enable_safe_search else 'off'
        }
        
        url = f"https://serpapi.com/search?{urlencode(params)}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"SerpAPI error: {error_text}"
                    )
                
                data = await response.json()
                return self._parse_serpapi_results(data)
                
        except aiohttp.ClientError as e:
            logger.error(f"SerpAPI request failed: {e}")
            raise
    
    def _parse_serpapi_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse SerpAPI results."""
        results = []
        
        # Parse organic results
        organic_results = data.get('organic_results', [])
        for item in organic_results:
            result = {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayed_url': item.get('displayed_link', ''),
                'provider': 'serpapi',
                'position': item.get('position', 0)
            }
            
            # Add rich snippets if available
            if 'rich_snippet' in item:
                result['rich_snippet'] = item['rich_snippet']
            
            # Add sitelinks if available
            if 'sitelinks' in item:
                result['sitelinks'] = item['sitelinks']
            
            results.append(result)
        
        # Parse knowledge graph if available
        if 'knowledge_graph' in data:
            kg = data['knowledge_graph']
            results.append({
                'title': kg.get('title', ''),
                'url': kg.get('website', ''),
                'snippet': kg.get('description', ''),
                'displayed_url': kg.get('website', ''),
                'provider': 'serpapi_knowledge_graph',
                'type': kg.get('type', ''),
                'knowledge_graph': kg
            })
        
        return results
    
    async def search_duckduckgo(
        self, 
        query: str, 
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        await self._rate_limiter.acquire()
        session = await self._get_session()
        
        # DuckDuckGo HTML search
        params = {
            'q': query,
            'kl': self.config.duckduckgo_region,
            'safe': self.config.duckduckgo_safe_search
        }
        
        url = f"https://html.duckduckgo.com/html/?{urlencode(params)}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"DuckDuckGo error: {error_text}"
                    )
                
                html_content = await response.text()
                return self._parse_duckduckgo_results(html_content, num_results)
                
        except aiohttp.ClientError as e:
            logger.error(f"DuckDuckGo request failed: {e}")
            raise
    
    def _parse_duckduckgo_results(self, html_content: str, num_results: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results."""
        import re
        
        results = []
        
        # Simple regex-based parsing for DuckDuckGo results
        # In production, consider using BeautifulSoup for more robust parsing
        result_pattern = r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result__a[^"]*"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<span[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</span>'
        
        matches = re.finditer(result_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for i, match in enumerate(matches):
            if i >= num_results:
                break
            
            url = match.group(1)
            title = match.group(2).strip()
            
            # Skip DuckDuckGo internal links
            if 'duckduckgo.com' in url or url.startswith('/'):
                continue
            
            # Extract snippet (simplified)
            snippet = ""
            snippet_match = re.search(snippet_pattern, html_content[match.end():match.end()+1000])
            if snippet_match:
                snippet = snippet_match.group(1).strip()
            
            # Extract displayed URL
            displayed_url = url
            if url.startswith('http'):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                displayed_url = parsed.netloc
            
            results.append({
                'title': title,
                'url': url,
                'snippet': snippet,
                'displayed_url': displayed_url,
                'provider': 'duckduckgo',
                'position': i + 1
            })
        
        return results
    
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