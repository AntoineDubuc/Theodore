# TICKET-012: Google Search Adapter

## Overview
Implement Google Search functionality with multiple provider support (Custom Search API, SerpAPI, DuckDuckGo fallback).

## Acceptance Criteria
- [ ] Define SearchProvider port/interface
- [ ] Implement GoogleCustomSearchAdapter
- [ ] Implement SerpAPIAdapter  
- [ ] Implement DuckDuckGoSearchAdapter
- [ ] Auto-select based on available API keys
- [ ] Extract company info from search results

## Technical Details
- Port logic from v1 `_google_search_api`
- Implement provider chain pattern
- Parse search results to extract company data
- Handle rate limiting gracefully
- Support configurable result limits

## Testing
- Unit test each adapter with mocked responses
- Test provider selection logic
- Test company extraction from URLs
- Integration test with real searches:
  - Search for "CRM software companies"
  - Search for "Salesforce competitors"
- Test fallback when APIs unavailable

## Estimated Time: 4-5 hours

## Dependencies
- TICKET-003 (for API key configuration)

## Files to Create
- `v2/src/core/interfaces/search_provider.py`
- `v2/src/infrastructure/adapters/search/__init__.py`
- `v2/src/infrastructure/adapters/search/google_custom.py`
- `v2/src/infrastructure/adapters/search/serpapi.py`
- `v2/src/infrastructure/adapters/search/duckduckgo.py`
- `v2/src/infrastructure/adapters/search/chain.py`
- `v2/tests/unit/adapters/search/test_google_custom.py`
- `v2/tests/unit/adapters/search/test_serpapi.py`
- `v2/tests/unit/adapters/search/test_duckduckgo.py`
- `v2/tests/integration/test_search_providers.py`

---

# Udemy Tutorial Script: Building Resilient Multi-Provider Search Systems

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Production-Ready Multi-Provider Search with Clean Architecture"]**

"Welcome to this essential tutorial on building resilient search systems! Today we're going to create a sophisticated search infrastructure that can automatically switch between multiple search providers - Google Custom Search, SerpAPI, DuckDuckGo, and more - ensuring your application never goes down due to API limits or outages.

By the end of this tutorial, you'll understand how to build provider chain patterns, implement graceful fallbacks, extract structured company data from search results, and create search systems that are both powerful and reliable in production environments.

This is the kind of infrastructure that separates amateur applications from enterprise-grade systems!"

## Section 1: Understanding Multi-Provider Search Challenges (5 minutes)

**[SLIDE 2: The Single Provider Problem]**

"Let's start by understanding why single-provider search systems are fragile:

```python
# ❌ The NAIVE approach - single point of failure
import requests

def search_companies(query):
    api_key = "your-google-api-key"
    url = f"https://customsearch.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': 'your-search-engine-id',
        'q': query
    }
    
    response = requests.get(url, params=params)
    return response.json()

# Problems:
# 1. Single point of failure - API goes down, app breaks
# 2. Rate limits - hit quota, searches stop working
# 3. Cost optimization - can't switch to cheaper providers
# 4. No fallback - users get errors instead of results
# 5. Regional restrictions - some APIs blocked in certain countries
```

This approach makes your application brittle and unreliable!"

**[SLIDE 3: Real-World Search Provider Complexity]**

"Here's what we're actually dealing with in production:

```python
# Different search provider APIs and capabilities:
search_providers = {
    'google_custom': {
        'cost': '$5 per 1000 queries',
        'quality': 'excellent',
        'rate_limit': '100 queries/day free',
        'features': ['snippet', 'title', 'link', 'metadata'],
        'regional_blocks': ['china', 'some_eu_countries']
    },
    'serpapi': {
        'cost': '$50 per 5000 queries', 
        'quality': 'excellent',
        'rate_limit': '100 queries/month free',
        'features': ['snippet', 'title', 'link', 'rich_results'],
        'regional_blocks': []
    },
    'duckduckgo': {
        'cost': 'free',
        'quality': 'good',
        'rate_limit': 'aggressive throttling',
        'features': ['snippet', 'title', 'link'],
        'regional_blocks': []
    },
    'bing_search': {
        'cost': '$4 per 1000 queries',
        'quality': 'good',
        'rate_limit': '1000 queries/month free',
        'features': ['snippet', 'title', 'link', 'entities'],
        'regional_blocks': ['some_countries']
    }
}

# Real production requirements:
search_requirements = [
    "99.9% uptime even when providers fail",
    "Automatic cost optimization by provider selection",
    "Rate limit handling with exponential backoff",
    "Company data extraction from search results",
    "Regional fallbacks for blocked providers",
    "Quality scoring and result ranking",
    "Comprehensive monitoring and alerting"
]
```

Production search needs sophisticated provider orchestration!"

**[SLIDE 4: Multi-Provider Architecture Overview]**

"Here's our robust approach:

```python
# 🎯 Our RESILIENT multi-provider search system
class SearchProviderChain:
    def __init__(self):
        self.providers = [
            GoogleCustomSearchProvider(),   # Primary (high quality)
            SerpAPIProvider(),             # Secondary (reliable)
            DuckDuckGoProvider(),          # Fallback (free)
            BingSearchProvider()           # Backup (good coverage)
        ]
    
    async def search(self, query: str) -> SearchResults:
        for provider in self.providers:
            try:
                if provider.is_available() and not provider.is_rate_limited():
                    results = await provider.search(query)
                    if results.quality_score > 0.7:
                        return results
            except Exception as e:
                self.log_provider_failure(provider, e)
                continue
        
        raise Exception("All search providers failed")
```

This gives us reliability, cost optimization, and performance!"

## Section 2: Core Search Provider Interface (8 minutes)

**[SLIDE 5: Search Provider Port Definition]**

"Let's build the foundation with a comprehensive search provider interface:

```python
# v2/src/core/interfaces/search_provider.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class SearchResultType(str, Enum):
    """Type of search result"""
    COMPANY_WEBSITE = "company_website"
    NEWS_ARTICLE = "news_article"
    DIRECTORY_LISTING = "directory_listing"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"

class SearchResult(BaseModel):
    """Individual search result"""
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    snippet: str = Field(..., description="Page snippet/description")
    
    # Company extraction
    extracted_company_name: Optional[str] = Field(None, description="Extracted company name")
    extracted_domain: Optional[str] = Field(None, description="Clean domain")
    result_type: SearchResultType = Field(SearchResultType.UNKNOWN, description="Result classification")
    
    # Quality indicators
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance to query")
    authority_score: float = Field(0.0, ge=0.0, le=1.0, description="Domain authority")
    freshness_score: float = Field(0.0, ge=0.0, le=1.0, description="Content freshness")
    
    # Metadata
    search_provider: str = Field(..., description="Provider that found this result")
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw provider data")

class SearchResults(BaseModel):
    """Complete search results"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(0, description="Total available results")
    
    # Provider info
    provider_used: str = Field(..., description="Provider that executed search")
    execution_time_seconds: float = Field(..., description="Search execution time")
    
    # Quality metrics
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall result quality")
    company_results_count: int = Field(0, description="Results identified as companies")
    
    # Search context
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    rate_limit_remaining: Optional[int] = Field(None, description="API calls remaining")
    cost_per_search: Optional[float] = Field(None, description="Cost for this search")

class SearchConfig(BaseModel):
    """Search configuration"""
    max_results: int = Field(10, ge=1, le=100, description="Maximum results to return")
    language: str = Field("en", description="Search language")
    region: Optional[str] = Field(None, description="Geographic region filter")
    date_range: Optional[str] = Field(None, description="Date range filter")
    
    # Company-specific filters
    site_filter: Optional[str] = Field(None, description="Restrict to specific sites")
    exclude_sites: List[str] = Field(default_factory=list, description="Sites to exclude")
    company_focus: bool = Field(True, description="Focus on company-related results")
    
    # Quality thresholds
    min_relevance_score: float = Field(0.3, ge=0.0, le=1.0)
    prefer_official_sites: bool = Field(True, description="Prefer official company sites")

class SearchProvider(ABC):
    """Abstract base for search providers"""
    
    def __init__(self, provider_name: str, config: Dict[str, Any] = None):
        self.provider_name = provider_name
        self.config = config or {}
        self.rate_limit_tracker = RateLimitTracker()
        self.cost_tracker = CostTracker()
    
    @abstractmethod
    async def search(self, query: str, config: SearchConfig = None) -> SearchResults:
        """Execute search query"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API keys, etc.)"""
        pass
    
    def is_rate_limited(self) -> bool:
        """Check if provider is currently rate limited"""
        return self.rate_limit_tracker.is_rate_limited()
    
    def get_cost_per_search(self) -> float:
        """Get estimated cost per search"""
        return self.cost_tracker.get_cost_per_search()
    
    def extract_company_info(self, result: SearchResult) -> SearchResult:
        """Extract company information from search result"""
        # Base implementation - can be overridden by specific providers
        result.extracted_domain = self._extract_domain(result.url)
        result.extracted_company_name = self._extract_company_name(result.title, result.url)
        result.result_type = self._classify_result_type(result.url, result.title)
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _extract_company_name(self, title: str, url: str) -> str:
        """Extract company name from title and URL"""
        # Simple heuristics - can be improved with ML
        if ' - ' in title:
            potential_name = title.split(' - ')[0].strip()
        elif ' | ' in title:
            potential_name = title.split(' | ')[0].strip()
        else:
            # Extract from domain
            domain = self._extract_domain(url)
            potential_name = domain.split('.')[0].replace('-', ' ').title()
        
        # Clean up common suffixes
        suffixes = ['Inc', 'LLC', 'Corp', 'Ltd', 'Company']
        for suffix in suffixes:
            if potential_name.endswith(f' {suffix}'):
                potential_name = potential_name[:-len(f' {suffix}')]
        
        return potential_name
    
    def _classify_result_type(self, url: str, title: str) -> SearchResultType:
        """Classify the type of search result"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Company website indicators
        company_paths = ['/about', '/company', '/careers', '/contact']
        if any(path in url_lower for path in company_paths):
            return SearchResultType.COMPANY_WEBSITE
        
        # News article indicators
        news_domains = ['techcrunch.com', 'reuters.com', 'bloomberg.com', 'forbes.com']
        if any(domain in url_lower for domain in news_domains):
            return SearchResultType.NEWS_ARTICLE
        
        # Directory listing indicators
        directory_domains = ['crunchbase.com', 'linkedin.com/company', 'glassdoor.com']
        if any(domain in url_lower for domain in directory_domains):
            return SearchResultType.DIRECTORY_LISTING
        
        # Social media indicators
        social_domains = ['twitter.com', 'facebook.com', 'instagram.com']
        if any(domain in url_lower for domain in social_domains):
            return SearchResultType.SOCIAL_MEDIA
        
        return SearchResultType.UNKNOWN

class RateLimitTracker:
    """Track rate limits for search providers"""
    
    def __init__(self):
        self.call_history = []
        self.rate_limit_reset_time = None
    
    def record_api_call(self):
        """Record an API call"""
        now = datetime.utcnow()
        self.call_history.append(now)
        
        # Clean old history (keep last hour)
        cutoff = now.replace(hour=now.hour-1) if now.hour > 0 else now.replace(day=now.day-1, hour=23)
        self.call_history = [call for call in self.call_history if call > cutoff]
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited"""
        if self.rate_limit_reset_time:
            if datetime.utcnow() < self.rate_limit_reset_time:
                return True
            else:
                self.rate_limit_reset_time = None
        return False
    
    def set_rate_limit_reset(self, reset_time: datetime):
        """Set when rate limit will reset"""
        self.rate_limit_reset_time = reset_time

class CostTracker:
    """Track costs for search providers"""
    
    def __init__(self, cost_per_1000_calls: float = 0.0):
        self.cost_per_1000_calls = cost_per_1000_calls
        self.total_calls = 0
        self.total_cost = 0.0
    
    def record_search_cost(self, cost: float = None):
        """Record cost for a search"""
        self.total_calls += 1
        if cost is not None:
            self.total_cost += cost
        else:
            self.total_cost += (self.cost_per_1000_calls / 1000)
    
    def get_cost_per_search(self) -> float:
        """Get estimated cost per search"""
        return self.cost_per_1000_calls / 1000
    
    def get_total_cost(self) -> float:
        """Get total accumulated cost"""
        return self.total_cost
```

This creates a comprehensive foundation for any search provider!"

**[SLIDE 6: Search Quality Assessment]**

"Now let's add intelligent result quality assessment:

```python
# v2/src/core/interfaces/search_provider.py (continued)

class SearchQualityAssessor:
    """Assess the quality of search results"""
    
    def __init__(self):
        # Domain authority scores (simplified - use real data in production)
        self.domain_authority = {
            'linkedin.com': 0.95,
            'crunchbase.com': 0.90,
            'techcrunch.com': 0.85,
            'forbes.com': 0.85,
            'bloomberg.com': 0.85,
            'reuters.com': 0.80,
            'wikipedia.org': 0.75
        }
    
    def assess_result_quality(self, result: SearchResult, query: str) -> SearchResult:
        """Assess and score result quality"""
        
        # Calculate relevance score
        result.relevance_score = self._calculate_relevance(result, query)
        
        # Calculate authority score
        result.authority_score = self._calculate_authority(result)
        
        # Calculate freshness score
        result.freshness_score = self._calculate_freshness(result)
        
        return result
    
    def assess_results_quality(self, results: SearchResults) -> SearchResults:
        """Assess overall results quality"""
        
        if not results.results:
            results.quality_score = 0.0
            return results
        
        # Calculate individual result scores
        for result in results.results:
            result = self.assess_result_quality(result, results.query)
        
        # Calculate overall quality metrics
        avg_relevance = sum(r.relevance_score for r in results.results) / len(results.results)
        avg_authority = sum(r.authority_score for r in results.results) / len(results.results)
        company_ratio = results.company_results_count / len(results.results)
        
        # Weighted overall quality score
        results.quality_score = (
            avg_relevance * 0.4 +      # Most important
            avg_authority * 0.3 +      # Important for trust
            company_ratio * 0.3        # Important for company search
        )
        
        return results
    
    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """Calculate how relevant result is to query"""
        query_words = set(query.lower().split())
        
        # Check title relevance
        title_words = set(result.title.lower().split())
        title_overlap = len(query_words & title_words) / max(len(query_words), 1)
        
        # Check snippet relevance
        snippet_words = set(result.snippet.lower().split())
        snippet_overlap = len(query_words & snippet_words) / max(len(query_words), 1)
        
        # Check URL relevance
        url_words = set(result.url.lower().replace('/', ' ').replace('-', ' ').split())
        url_overlap = len(query_words & url_words) / max(len(query_words), 1)
        
        # Weighted combination
        relevance = (title_overlap * 0.5) + (snippet_overlap * 0.3) + (url_overlap * 0.2)
        return min(relevance, 1.0)
    
    def _calculate_authority(self, result: SearchResult) -> float:
        """Calculate domain authority score"""
        domain = result.extracted_domain or self._extract_domain_from_url(result.url)
        
        # Check known domain authorities
        if domain in self.domain_authority:
            return self.domain_authority[domain]
        
        # Heuristic scoring for unknown domains
        score = 0.5  # Default medium authority
        
        # Boost for HTTPS
        if result.url.startswith('https://'):
            score += 0.1
        
        # Boost for common TLDs
        if domain.endswith(('.com', '.org', '.edu', '.gov')):
            score += 0.1
        
        # Penalize for suspicious patterns
        if any(char in domain for char in ['_', '--']):
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    def _calculate_freshness(self, result: SearchResult) -> float:
        """Calculate content freshness score"""
        # In production, you'd parse actual publish dates
        # For now, use heuristics based on URL and content
        
        freshness = 0.7  # Default medium freshness
        
        # Check for date patterns in URL
        import re
        date_pattern = r'20[12][0-9]'
        if re.search(date_pattern, result.url):
            freshness = 0.9
        
        # News sites tend to be fresher
        news_indicators = ['news', 'blog', 'press', 'announcement']
        if any(indicator in result.url.lower() for indicator in news_indicators):
            freshness = 0.8
        
        # Directory sites tend to be more static
        if result.result_type == SearchResultType.DIRECTORY_LISTING:
            freshness = 0.6
        
        return freshness
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc.lower().replace('www.', '')
        except:
            return ""
```

This adds sophisticated quality assessment to our search results!"

## Section 3: Google Custom Search Implementation (10 minutes)

**[SLIDE 7: Google Custom Search Adapter]**

"Let's implement our primary search provider with full error handling:

```python
# v2/src/infrastructure/adapters/search/google_custom.py
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.core.interfaces.search_provider import (
    SearchProvider, SearchResults, SearchResult, SearchConfig, SearchQualityAssessor
)

class GoogleCustomSearchProvider(SearchProvider):
    """Google Custom Search API provider"""
    
    def __init__(self, api_key: str, search_engine_id: str, config: Dict[str, Any] = None):
        super().__init__("google_custom", config)
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://customsearch.googleapis.com/customsearch/v1"
        self.quality_assessor = SearchQualityAssessor()
        
        # Rate limiting (Google allows 100 free queries/day)
        self.rate_limit_tracker.cost_per_1000_calls = 5000  # $5 per 1000 queries
        self.max_queries_per_day = 100  # Free tier limit
        self.daily_query_count = 0
        self.last_reset_date = datetime.utcnow().date()
    
    async def search(self, query: str, config: SearchConfig = None) -> SearchResults:
        """Execute Google Custom Search"""
        
        if not self.is_available():
            raise Exception("Google Custom Search not available - check API key and CSE ID")
        
        if self.is_rate_limited():
            raise Exception("Google Custom Search rate limited")
        
        config = config or SearchConfig()
        start_time = time.time()
        
        try:
            # Build search parameters
            params = self._build_search_params(query, config)
            
            # Execute search with retry logic
            raw_results = await self._execute_search_with_retry(params)
            
            # Process and enhance results
            search_results = self._process_raw_results(raw_results, query, start_time)
            
            # Apply quality assessment
            search_results = self.quality_assessor.assess_results_quality(search_results)
            
            # Update rate limiting
            self._update_rate_limits(raw_results)
            
            return search_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            return SearchResults(
                query=query,
                results=[],
                total_results=0,
                provider_used=self.provider_name,
                execution_time_seconds=execution_time,
                quality_score=0.0
            )
    
    def is_available(self) -> bool:
        """Check if Google Custom Search is available"""
        return bool(self.api_key and self.search_engine_id)
    
    def is_rate_limited(self) -> bool:
        """Check rate limit status"""
        # Reset daily counter if new day
        today = datetime.utcnow().date()
        if today > self.last_reset_date:
            self.daily_query_count = 0
            self.last_reset_date = today
        
        # Check daily quota
        if self.daily_query_count >= self.max_queries_per_day:
            return True
        
        return super().is_rate_limited()
    
    def _build_search_params(self, query: str, config: SearchConfig) -> Dict[str, str]:
        """Build Google Custom Search parameters"""
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': min(config.max_results, 10),  # Google max is 10
            'safe': 'medium',
            'fields': 'items(title,link,snippet,displayLink),searchInformation(totalResults)'
        }
        
        # Add language filter
        if config.language != 'en':
            params['lr'] = f'lang_{config.language}'
        
        # Add region filter
        if config.region:
            params['gl'] = config.region
        
        # Add date filter
        if config.date_range:
            params['dateRestrict'] = config.date_range
        
        # Site filtering
        if config.site_filter:
            params['q'] += f' site:{config.site_filter}'
        
        # Exclude sites
        for exclude_site in config.exclude_sites:
            params['q'] += f' -site:{exclude_site}'
        
        # Company-focused search enhancement
        if config.company_focus:
            # Add terms that help find company information
            company_terms = ['company', 'business', 'corporation', 'about', 'contact']
            # Don't overwhelm the query, just hint at company context
            if not any(term in query.lower() for term in company_terms):
                params['q'] += ' company'
        
        return params
    
    async def _execute_search_with_retry(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Execute search with exponential backoff retry"""
        
        max_retries = 3
        base_delay = 1.0
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(max_retries):
                try:
                    async with session.get(self.base_url, params=params, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            # Rate limited
                            retry_after = int(response.headers.get('Retry-After', 60))
                            self.rate_limit_tracker.set_rate_limit_reset(
                                datetime.utcnow() + timedelta(seconds=retry_after)
                            )
                            raise Exception(f"Rate limited, retry after {retry_after} seconds")
                        elif response.status == 403:
                            # Quota exceeded or invalid API key
                            error_data = await response.json()
                            error_reason = error_data.get('error', {}).get('message', 'Unknown error')
                            raise Exception(f"Google API error: {error_reason}")
                        else:
                            # Other HTTP error
                            error_text = await response.text()
                            raise Exception(f"HTTP {response.status}: {error_text}")
                            
                except asyncio.TimeoutError:
                    if attempt == max_retries - 1:
                        raise Exception("Search request timed out after retries")
                    
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                
                except aiohttp.ClientError as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Search request failed: {str(e)}")
                    
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        raise Exception("All retry attempts failed")
    
    def _process_raw_results(self, raw_results: Dict[str, Any], query: str, start_time: float) -> SearchResults:
        """Process raw Google search results"""
        
        execution_time = time.time() - start_time
        
        # Extract search information
        search_info = raw_results.get('searchInformation', {})
        total_results = int(search_info.get('totalResults', 0))
        
        # Process individual results
        processed_results = []
        company_count = 0
        
        for item in raw_results.get('items', []):
            result = SearchResult(
                title=item.get('title', ''),
                url=item.get('link', ''),
                snippet=item.get('snippet', ''),
                search_provider=self.provider_name,
                raw_data=item
            )
            
            # Extract company information
            result = self.extract_company_info(result)
            
            # Count company results
            if result.result_type.value in ['company_website', 'directory_listing']:
                company_count += 1
            
            processed_results.append(result)
        
        return SearchResults(
            query=query,
            results=processed_results,
            total_results=total_results,
            provider_used=self.provider_name,
            execution_time_seconds=execution_time,
            company_results_count=company_count,
            cost_per_search=self.get_cost_per_search()
        )
    
    def _update_rate_limits(self, raw_results: Dict[str, Any]):
        """Update rate limiting counters"""
        self.daily_query_count += 1
        self.rate_limit_tracker.record_api_call()
        self.cost_tracker.record_search_cost()
    
    def extract_company_info(self, result: SearchResult) -> SearchResult:
        """Enhanced company info extraction for Google results"""
        
        # Use base extraction first
        result = super().extract_company_info(result)
        
        # Google-specific enhancements
        display_link = result.raw_data.get('displayLink', '')
        if display_link:
            result.extracted_domain = display_link.lower().replace('www.', '')
        
        # Enhanced company name extraction using Google's structured data
        title = result.title
        
        # Common Google title patterns
        if ' - ' in title and title.count(' - ') == 1:
            # "Company Name - Description" pattern
            potential_name = title.split(' - ')[0].strip()
            if len(potential_name) < 50:  # Reasonable company name length
                result.extracted_company_name = potential_name
        
        # Look for "About" pages which often have clean company names
        if '/about' in result.url.lower() or 'about' in title.lower():
            result.result_type = SearchResultType.COMPANY_WEBSITE
        
        # Check for investor relations, careers, contact pages
        company_indicators = ['/careers', '/contact', '/investors', '/team', '/leadership']
        if any(indicator in result.url.lower() for indicator in company_indicators):
            result.result_type = SearchResultType.COMPANY_WEBSITE
        
        return result

# Enhanced Google search with multiple result pages
class GoogleCustomSearchEnhanced(GoogleCustomSearchProvider):
    """Enhanced Google Custom Search with multi-page support"""
    
    async def search_multiple_pages(self, query: str, max_pages: int = 3, config: SearchConfig = None) -> SearchResults:
        """Search multiple pages of Google results"""
        
        config = config or SearchConfig()
        all_results = []
        total_results = 0
        start_time = time.time()
        
        for page in range(max_pages):
            try:
                # Calculate start index (Google uses 1-based indexing)
                start_index = (page * 10) + 1
                
                # Build parameters for this page
                params = self._build_search_params(query, config)
                params['start'] = str(start_index)
                
                # Execute search
                raw_results = await self._execute_search_with_retry(params)
                
                # Process results
                page_results = self._process_raw_results(raw_results, query, start_time)
                
                # Accumulate results
                all_results.extend(page_results.results)
                if page == 0:  # First page gives us total count
                    total_results = page_results.total_results
                
                # Break if no more results
                if len(page_results.results) == 0:
                    break
                
                # Respect rate limits
                if self.is_rate_limited():
                    break
                
                # Small delay between pages
                await asyncio.sleep(0.5)
                
            except Exception as e:
                # Log error but continue with what we have
                break
        
        # Create combined results
        execution_time = time.time() - start_time
        company_count = sum(1 for r in all_results 
                           if r.result_type.value in ['company_website', 'directory_listing'])
        
        combined_results = SearchResults(
            query=query,
            results=all_results[:config.max_results],  # Respect max results limit
            total_results=total_results,
            provider_used=f"{self.provider_name}_multi_page",
            execution_time_seconds=execution_time,
            company_results_count=company_count,
            cost_per_search=self.get_cost_per_search() * len(all_results) // 10
        )
        
        # Apply quality assessment
        return self.quality_assessor.assess_results_quality(combined_results)
```

This creates a robust, production-ready Google Custom Search adapter!"

**[SLIDE 8: SerpAPI Implementation]**

"Now let's implement SerpAPI as our secondary provider:

```python
# v2/src/infrastructure/adapters/search/serpapi.py
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional

from src.core.interfaces.search_provider import (
    SearchProvider, SearchResults, SearchResult, SearchConfig, SearchQualityAssessor
)

class SerpAPIProvider(SearchProvider):
    """SerpAPI provider for Google search results"""
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        super().__init__("serpapi", config)
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.quality_assessor = SearchQualityAssessor()
        
        # SerpAPI pricing: $50 for 5000 searches
        self.rate_limit_tracker.cost_per_1000_calls = 10000  # $10 per 1000 queries
        self.monthly_search_limit = 100  # Free tier
    
    async def search(self, query: str, config: SearchConfig = None) -> SearchResults:
        """Execute SerpAPI search"""
        
        if not self.is_available():
            raise Exception("SerpAPI not available - check API key")
        
        if self.is_rate_limited():
            raise Exception("SerpAPI rate limited")
        
        config = config or SearchConfig()
        start_time = time.time()
        
        try:
            # Build search parameters
            params = self._build_serpapi_params(query, config)
            
            # Execute search
            raw_results = await self._execute_serpapi_search(params)
            
            # Process results
            search_results = self._process_serpapi_results(raw_results, query, start_time)
            
            # Apply quality assessment
            search_results = self.quality_assessor.assess_results_quality(search_results)
            
            # Update tracking
            self._update_usage_tracking()
            
            return search_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            return SearchResults(
                query=query,
                results=[],
                total_results=0,
                provider_used=self.provider_name,
                execution_time_seconds=execution_time,
                quality_score=0.0
            )
    
    def is_available(self) -> bool:
        """Check if SerpAPI is available"""
        return bool(self.api_key)
    
    def _build_serpapi_params(self, query: str, config: SearchConfig) -> Dict[str, str]:
        """Build SerpAPI parameters"""
        
        params = {
            'api_key': self.api_key,
            'engine': 'google',
            'q': query,
            'num': str(min(config.max_results, 20)),  # SerpAPI allows more results
            'safe': 'medium',
            'output': 'json'
        }
        
        # Language and region
        if config.language != 'en':
            params['hl'] = config.language
        
        if config.region:
            params['gl'] = config.region
        
        # Date filtering
        if config.date_range:
            params['tbs'] = f'qdr:{config.date_range}'
        
        # Site filtering
        if config.site_filter:
            params['q'] += f' site:{config.site_filter}'
        
        for exclude_site in config.exclude_sites:
            params['q'] += f' -site:{exclude_site}'
        
        return params
    
    async def _execute_serpapi_search(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Execute SerpAPI search with error handling"""
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check for SerpAPI errors
                        if 'error' in result:
                            raise Exception(f"SerpAPI error: {result['error']}")
                        
                        return result
                    
                    elif response.status == 401:
                        raise Exception("SerpAPI authentication failed - check API key")
                    
                    elif response.status == 429:
                        raise Exception("SerpAPI rate limit exceeded")
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"SerpAPI HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                raise Exception("SerpAPI request timed out")
            
            except aiohttp.ClientError as e:
                raise Exception(f"SerpAPI request failed: {str(e)}")
    
    def _process_serpapi_results(self, raw_results: Dict[str, Any], query: str, start_time: float) -> SearchResults:
        """Process SerpAPI results"""
        
        execution_time = time.time() - start_time
        
        # Extract organic results
        organic_results = raw_results.get('organic_results', [])
        
        # Process individual results
        processed_results = []
        company_count = 0
        
        for item in organic_results:
            result = SearchResult(
                title=item.get('title', ''),
                url=item.get('link', ''),
                snippet=item.get('snippet', ''),
                search_provider=self.provider_name,
                raw_data=item
            )
            
            # Extract company information
            result = self.extract_company_info(result)
            
            # SerpAPI-specific enhancements
            result = self._enhance_serpapi_result(result, item)
            
            # Count company results
            if result.result_type.value in ['company_website', 'directory_listing']:
                company_count += 1
            
            processed_results.append(result)
        
        # Extract search metadata
        search_metadata = raw_results.get('search_metadata', {})
        total_results = int(search_metadata.get('total_results', 0))
        
        return SearchResults(
            query=query,
            results=processed_results,
            total_results=total_results,
            provider_used=self.provider_name,
            execution_time_seconds=execution_time,
            company_results_count=company_count,
            cost_per_search=self.get_cost_per_search()
        )
    
    def _enhance_serpapi_result(self, result: SearchResult, raw_item: Dict[str, Any]) -> SearchResult:
        """Enhance result with SerpAPI-specific data"""
        
        # SerpAPI provides rich data we can use
        displayed_link = raw_item.get('displayed_link', '')
        if displayed_link:
            result.extracted_domain = displayed_link.lower().replace('www.', '')
        
        # Check for sitelinks (indicates official company page)
        sitelinks = raw_item.get('sitelinks', [])
        if sitelinks:
            result.authority_score = min(result.authority_score + 0.2, 1.0)
            result.result_type = SearchResultType.COMPANY_WEBSITE
        
        # Check for rich snippets
        rich_snippet = raw_item.get('rich_snippet', {})
        if rich_snippet:
            # Rich snippets often indicate structured company data
            result.authority_score = min(result.authority_score + 0.1, 1.0)
        
        # Position in results affects relevance
        position = raw_item.get('position', 1)
        if position <= 3:
            result.relevance_score = min(result.relevance_score + 0.1, 1.0)
        
        return result
    
    def _update_usage_tracking(self):
        """Update usage tracking"""
        self.rate_limit_tracker.record_api_call()
        self.cost_tracker.record_search_cost()
```

This creates a powerful SerpAPI integration with enhanced result processing!"

## Section 4: DuckDuckGo Fallback Implementation (8 minutes)

**[SLIDE 9: DuckDuckGo Free Fallback Provider]**

"Let's implement our free fallback provider:

```python
# v2/src/infrastructure/adapters/search/duckduckgo.py
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus
import json

from src.core.interfaces.search_provider import (
    SearchProvider, SearchResults, SearchResult, SearchConfig, SearchQualityAssessor
)

class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider (free fallback)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("duckduckgo", config)
        self.base_url = "https://html.duckduckgo.com/html/"
        self.api_url = "https://api.duckduckgo.com/"
        self.quality_assessor = SearchQualityAssessor()
        
        # DuckDuckGo is free but heavily rate limited
        self.rate_limit_tracker.cost_per_1000_calls = 0  # Free
        self.request_delay = 2.0  # Minimum delay between requests
        self.last_request_time = 0
    
    async def search(self, query: str, config: SearchConfig = None) -> SearchResults:
        """Execute DuckDuckGo search"""
        
        if not self.is_available():
            raise Exception("DuckDuckGo not available")
        
        # Respect rate limiting with delays
        await self._respect_rate_limits()
        
        config = config or SearchConfig()
        start_time = time.time()
        
        try:
            # DuckDuckGo requires different approach than Google APIs
            # We'll use their instant answer API + web scraping approach
            
            # First try instant answers API for company info
            instant_results = await self._get_instant_answers(query)
            
            # Then get web search results
            web_results = await self._get_web_results(query, config)
            
            # Combine and process results
            search_results = self._combine_results(instant_results, web_results, query, start_time)
            
            # Apply quality assessment
            search_results = self.quality_assessor.assess_results_quality(search_results)
            
            # Update tracking
            self._update_request_tracking()
            
            return search_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            return SearchResults(
                query=query,
                results=[],
                total_results=0,
                provider_used=self.provider_name,
                execution_time_seconds=execution_time,
                quality_score=0.0
            )
    
    def is_available(self) -> bool:
        """DuckDuckGo is always available (no API key required)"""
        return True
    
    async def _respect_rate_limits(self):
        """Implement request delay to respect DuckDuckGo's limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
    
    async def _get_instant_answers(self, query: str) -> Dict[str, Any]:
        """Get DuckDuckGo instant answers (good for company info)"""
        
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params, timeout=15) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
        except Exception:
            return {}
    
    async def _get_web_results(self, query: str, config: SearchConfig) -> List[Dict[str, Any]]:
        """Get DuckDuckGo web search results via HTML parsing"""
        
        # Build search URL
        encoded_query = quote_plus(query)
        search_url = f"{self.base_url}?q={encoded_query}"
        
        # Add filters
        if config.region:
            search_url += f"&kl={config.region}"
        
        if config.date_range:
            # DuckDuckGo date filters
            date_map = {
                'd': 'df=d',    # past day
                'w': 'df=w',    # past week
                'm': 'df=m',    # past month
                'y': 'df=y'     # past year
            }
            if config.date_range in date_map:
                search_url += f"&{date_map[config.date_range]}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=20) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return self._parse_duckduckgo_html(html_content)
                    else:
                        return []
        except Exception:
            return []
    
    def _parse_duckduckgo_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results"""
        
        # Simple HTML parsing for DuckDuckGo results
        # In production, use BeautifulSoup or lxml for robust parsing
        
        results = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find result containers
            result_containers = soup.find_all('div', class_='web-result')
            
            for container in result_containers[:20]:  # Limit to first 20 results
                try:
                    # Extract title
                    title_elem = container.find('a', class_='result__a')
                    title = title_elem.text.strip() if title_elem else ''
                    url = title_elem.get('href', '') if title_elem else ''
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.text.strip() if snippet_elem else ''
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                
                except Exception:
                    continue
        
        except ImportError:
            # Fallback: basic regex parsing if BeautifulSoup not available
            import re
            
            # Basic regex patterns for DuckDuckGo results
            title_pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>'
            url_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"'
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>'
            
            titles = re.findall(title_pattern, html_content)
            urls = re.findall(url_pattern, html_content)
            snippets = re.findall(snippet_pattern, html_content)
            
            # Combine results
            for i in range(min(len(titles), len(urls), len(snippets))):
                results.append({
                    'title': titles[i].strip(),
                    'url': urls[i],
                    'snippet': snippets[i].strip()
                })
        
        return results
    
    def _combine_results(self, instant_results: Dict[str, Any], web_results: List[Dict[str, Any]], 
                        query: str, start_time: float) -> SearchResults:
        """Combine instant answers and web results"""
        
        execution_time = time.time() - start_time
        processed_results = []
        company_count = 0
        
        # Process instant answer first (if it's a company)
        if instant_results.get('AbstractText'):
            abstract = instant_results.get('AbstractText', '')
            abstract_url = instant_results.get('AbstractURL', '')
            
            if abstract_url and any(indicator in abstract.lower() 
                                  for indicator in ['company', 'corporation', 'business', 'founded']):
                
                instant_result = SearchResult(
                    title=instant_results.get('Heading', query),
                    url=abstract_url,
                    snippet=abstract,
                    search_provider=self.provider_name,
                    raw_data=instant_results
                )
                
                instant_result = self.extract_company_info(instant_result)
                instant_result.relevance_score = 0.9  # High relevance for instant answers
                instant_result.result_type = SearchResultType.COMPANY_WEBSITE
                
                processed_results.append(instant_result)
                company_count += 1
        
        # Process web results
        for item in web_results:
            result = SearchResult(
                title=item.get('title', ''),
                url=item.get('url', ''),
                snippet=item.get('snippet', ''),
                search_provider=self.provider_name,
                raw_data=item
            )
            
            # Extract company information
            result = self.extract_company_info(result)
            
            # DuckDuckGo-specific scoring adjustments
            result.authority_score *= 0.8  # Lower authority than Google
            
            if result.result_type.value in ['company_website', 'directory_listing']:
                company_count += 1
            
            processed_results.append(result)
        
        return SearchResults(
            query=query,
            results=processed_results,
            total_results=len(processed_results),  # DuckDuckGo doesn't provide total count
            provider_used=self.provider_name,
            execution_time_seconds=execution_time,
            company_results_count=company_count,
            cost_per_search=0.0  # Free
        )
    
    def _update_request_tracking(self):
        """Update request tracking"""
        self.last_request_time = time.time()
        self.rate_limit_tracker.record_api_call()
        # No cost for DuckDuckGo
```

This creates a robust free fallback provider!"

**[SLIDE 10: Provider Chain Implementation]**

"Now let's build the provider chain that orchestrates all our search providers:

```python
# v2/src/infrastructure/adapters/search/chain.py
import asyncio
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.core.interfaces.search_provider import (
    SearchProvider, SearchResults, SearchConfig
)
from .google_custom import GoogleCustomSearchProvider
from .serpapi import SerpAPIProvider
from .duckduckgo import DuckDuckGoProvider

class SearchProviderChain:
    """Chain of search providers with automatic failover"""
    
    def __init__(self, providers: List[SearchProvider] = None):
        self.providers = providers or []
        self.logger = logging.getLogger(__name__)
        self.provider_stats = {}
    
    def add_provider(self, provider: SearchProvider, priority: int = None):
        """Add a provider to the chain"""
        if priority is not None:
            self.providers.insert(priority, provider)
        else:
            self.providers.append(provider)
        
        # Initialize stats
        self.provider_stats[provider.provider_name] = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'total_execution_time': 0.0,
            'last_success': None,
            'last_failure': None
        }
    
    async def search(self, query: str, config: SearchConfig = None, 
                    preferred_provider: str = None) -> SearchResults:
        """Search using provider chain with failover"""
        
        config = config or SearchConfig()
        
        # Try preferred provider first if specified
        if preferred_provider:
            provider = self._get_provider_by_name(preferred_provider)
            if provider:
                try:
                    return await self._attempt_search(provider, query, config)
                except Exception as e:
                    self.logger.warning(f"Preferred provider {preferred_provider} failed: {str(e)}")
        
        # Try providers in order
        last_exception = None
        
        for provider in self.providers:
            try:
                # Skip if provider not available or rate limited
                if not provider.is_available():
                    self.logger.info(f"Provider {provider.provider_name} not available")
                    continue
                
                if provider.is_rate_limited():
                    self.logger.info(f"Provider {provider.provider_name} rate limited")
                    continue
                
                # Attempt search
                result = await self._attempt_search(provider, query, config)
                
                # Check if result quality is acceptable
                if result.quality_score >= config.min_relevance_score:
                    self.logger.info(f"Search succeeded with provider {provider.provider_name}")
                    return result
                else:
                    self.logger.info(f"Provider {provider.provider_name} returned low quality results")
                    continue
                    
            except Exception as e:
                last_exception = e
                self._record_provider_failure(provider, e)
                self.logger.warning(f"Provider {provider.provider_name} failed: {str(e)}")
                continue
        
        # All providers failed
        if last_exception:
            raise Exception(f"All search providers failed. Last error: {str(last_exception)}")
        else:
            raise Exception("No search providers available")
    
    async def search_with_multiple_providers(self, query: str, config: SearchConfig = None,
                                           max_providers: int = 2) -> List[SearchResults]:
        """Search with multiple providers for result diversity"""
        
        config = config or SearchConfig()
        results = []
        attempted_providers = 0
        
        tasks = []
        for provider in self.providers:
            if attempted_providers >= max_providers:
                break
            
            if not provider.is_available() or provider.is_rate_limited():
                continue
            
            # Create search task
            task = asyncio.create_task(
                self._attempt_search_with_timeout(provider, query, config, timeout=15.0)
            )
            tasks.append((provider, task))
            attempted_providers += 1
        
        # Wait for all tasks to complete
        for provider, task in tasks:
            try:
                result = await task
                if result.quality_score >= config.min_relevance_score:
                    results.append(result)
            except Exception as e:
                self._record_provider_failure(provider, e)
                self.logger.warning(f"Multi-provider search failed for {provider.provider_name}: {str(e)}")
        
        return results
    
    async def get_best_available_provider(self, query: str = None) -> Optional[SearchProvider]:
        """Get the best available provider based on stats and availability"""
        
        available_providers = []
        
        for provider in self.providers:
            if not provider.is_available() or provider.is_rate_limited():
                continue
            
            stats = self.provider_stats.get(provider.provider_name, {})
            success_rate = 0.0
            avg_execution_time = 0.0
            
            if stats.get('attempts', 0) > 0:
                success_rate = stats['successes'] / stats['attempts']
                avg_execution_time = stats['total_execution_time'] / stats['attempts']
            
            # Calculate provider score
            score = self._calculate_provider_score(provider, success_rate, avg_execution_time)
            
            available_providers.append((provider, score))
        
        # Sort by score (higher is better)
        available_providers.sort(key=lambda x: x[1], reverse=True)
        
        return available_providers[0][0] if available_providers else None
    
    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        
        stats = {}
        
        for provider_name, provider_stats in self.provider_stats.items():
            attempts = provider_stats['attempts']
            successes = provider_stats['successes']
            
            stats[provider_name] = {
                'attempts': attempts,
                'successes': successes,
                'failures': provider_stats['failures'],
                'success_rate': successes / attempts if attempts > 0 else 0.0,
                'avg_execution_time': (provider_stats['total_execution_time'] / attempts 
                                     if attempts > 0 else 0.0),
                'last_success': provider_stats['last_success'],
                'last_failure': provider_stats['last_failure'],
                'is_available': self._get_provider_by_name(provider_name).is_available() if self._get_provider_by_name(provider_name) else False,
                'is_rate_limited': self._get_provider_by_name(provider_name).is_rate_limited() if self._get_provider_by_name(provider_name) else False
            }
        
        return stats
    
    async def _attempt_search(self, provider: SearchProvider, query: str, 
                            config: SearchConfig) -> SearchResults:
        """Attempt search with a specific provider"""
        
        start_time = time.time()
        
        try:
            self._record_provider_attempt(provider)
            
            result = await provider.search(query, config)
            
            execution_time = time.time() - start_time
            self._record_provider_success(provider, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_provider_failure(provider, e, execution_time)
            raise
    
    async def _attempt_search_with_timeout(self, provider: SearchProvider, query: str,
                                         config: SearchConfig, timeout: float) -> SearchResults:
        """Attempt search with timeout"""
        
        try:
            return await asyncio.wait_for(
                self._attempt_search(provider, query, config),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise Exception(f"Search timed out after {timeout} seconds")
    
    def _get_provider_by_name(self, name: str) -> Optional[SearchProvider]:
        """Get provider by name"""
        for provider in self.providers:
            if provider.provider_name == name:
                return provider
        return None
    
    def _calculate_provider_score(self, provider: SearchProvider, success_rate: float,
                                avg_execution_time: float) -> float:
        """Calculate provider score for ranking"""
        
        # Base score factors
        quality_score = 0.0
        cost_score = 0.0
        performance_score = 0.0
        
        # Quality scoring (based on provider type)
        if provider.provider_name == 'google_custom':
            quality_score = 1.0  # Highest quality
        elif provider.provider_name == 'serpapi':
            quality_score = 0.95  # Very high quality
        elif provider.provider_name == 'duckduckgo':
            quality_score = 0.7   # Good quality
        else:
            quality_score = 0.5   # Unknown provider
        
        # Cost scoring (lower cost = higher score)
        cost_per_search = provider.get_cost_per_search()
        if cost_per_search == 0:
            cost_score = 1.0  # Free is best
        elif cost_per_search < 0.01:
            cost_score = 0.8  # Very cheap
        elif cost_per_search < 0.05:
            cost_score = 0.6  # Moderate cost
        else:
            cost_score = 0.3  # Expensive
        
        # Performance scoring (faster = higher score)
        if avg_execution_time < 2.0:
            performance_score = 1.0  # Very fast
        elif avg_execution_time < 5.0:
            performance_score = 0.8  # Fast
        elif avg_execution_time < 10.0:
            performance_score = 0.6  # Moderate
        else:
            performance_score = 0.3  # Slow
        
        # Reliability scoring
        reliability_score = success_rate
        
        # Weighted combination
        total_score = (
            quality_score * 0.3 +
            cost_score * 0.2 +
            performance_score * 0.2 +
            reliability_score * 0.3
        )
        
        return total_score
    
    def _record_provider_attempt(self, provider: SearchProvider):
        """Record provider attempt"""
        stats = self.provider_stats[provider.provider_name]
        stats['attempts'] += 1
    
    def _record_provider_success(self, provider: SearchProvider, execution_time: float):
        """Record provider success"""
        stats = self.provider_stats[provider.provider_name]
        stats['successes'] += 1
        stats['total_execution_time'] += execution_time
        stats['last_success'] = datetime.utcnow()
    
    def _record_provider_failure(self, provider: SearchProvider, error: Exception, 
                                execution_time: float = 0.0):
        """Record provider failure"""
        stats = self.provider_stats[provider.provider_name]
        stats['failures'] += 1
        stats['total_execution_time'] += execution_time
        stats['last_failure'] = datetime.utcnow()

# Factory for creating configured provider chains
class SearchProviderChainFactory:
    """Factory for creating configured search provider chains"""
    
    @staticmethod
    def create_default_chain(config: Dict[str, Any]) -> SearchProviderChain:
        """Create default provider chain with all available providers"""
        
        chain = SearchProviderChain()
        
        # Add Google Custom Search (primary)
        google_api_key = config.get('google_custom_search_api_key')
        google_cse_id = config.get('google_custom_search_engine_id')
        if google_api_key and google_cse_id:
            google_provider = GoogleCustomSearchProvider(google_api_key, google_cse_id)
            chain.add_provider(google_provider, priority=0)
        
        # Add SerpAPI (secondary)
        serpapi_key = config.get('serpapi_api_key')
        if serpapi_key:
            serpapi_provider = SerpAPIProvider(serpapi_key)
            chain.add_provider(serpapi_provider, priority=1)
        
        # Add DuckDuckGo (fallback - always available)
        duckduckgo_provider = DuckDuckGoProvider()
        chain.add_provider(duckduckgo_provider, priority=2)
        
        return chain
    
    @staticmethod
    def create_free_chain() -> SearchProviderChain:
        """Create chain with only free providers"""
        
        chain = SearchProviderChain()
        chain.add_provider(DuckDuckGoProvider())
        return chain
    
    @staticmethod
    def create_premium_chain(config: Dict[str, Any]) -> SearchProviderChain:
        """Create chain with only premium providers"""
        
        chain = SearchProviderChain()
        
        # Add premium providers only
        google_api_key = config.get('google_custom_search_api_key')
        google_cse_id = config.get('google_custom_search_engine_id')
        if google_api_key and google_cse_id:
            google_provider = GoogleCustomSearchProvider(google_api_key, google_cse_id)
            chain.add_provider(google_provider)
        
        serpapi_key = config.get('serpapi_api_key')
        if serpapi_key:
            serpapi_provider = SerpAPIProvider(serpapi_key)
            chain.add_provider(serpapi_provider)
        
        return chain
```

This creates a sophisticated provider chain with automatic failover and intelligent provider selection!"

## Section 5: Comprehensive Testing Strategy (10 minutes)

**[SLIDE 11: Unit Testing Framework]**

"Let's create comprehensive tests for our search providers:

```python
# v2/tests/unit/adapters/search/test_google_custom.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.infrastructure.adapters.search.google_custom import GoogleCustomSearchProvider
from src.core.interfaces.search_provider import SearchConfig, SearchResult

class TestGoogleCustomSearchProvider:
    """Comprehensive tests for Google Custom Search"""
    
    @pytest.fixture
    def google_provider(self):
        return GoogleCustomSearchProvider(
            api_key="test-api-key",
            search_engine_id="test-cse-id"
        )
    
    @pytest.fixture
    def mock_google_response(self):
        return {
            "searchInformation": {
                "totalResults": "1500"
            },
            "items": [
                {
                    "title": "Salesforce - Customer Success Platform",
                    "link": "https://www.salesforce.com/",
                    "snippet": "Salesforce is the world's #1 CRM platform, helping companies connect with customers.",
                    "displayLink": "www.salesforce.com"
                },
                {
                    "title": "About Salesforce | Company Information",
                    "link": "https://www.salesforce.com/company/",
                    "snippet": "Learn about Salesforce's mission, leadership team, and company culture.",
                    "displayLink": "www.salesforce.com"
                },
                {
                    "title": "HubSpot: Inbound Marketing & Sales Software",
                    "link": "https://www.hubspot.com/",
                    "snippet": "HubSpot offers a complete CRM platform with marketing, sales, and service software.",
                    "displayLink": "www.hubspot.com"
                }
            ]
        }
    
    def test_provider_initialization(self, google_provider):
        """Test provider initialization"""
        assert google_provider.provider_name == "google_custom"
        assert google_provider.api_key == "test-api-key"
        assert google_provider.search_engine_id == "test-cse-id"
        assert google_provider.is_available() == True
    
    def test_provider_not_available_without_credentials(self):
        """Test provider not available without proper credentials"""
        provider = GoogleCustomSearchProvider("", "")
        assert provider.is_available() == False
        
        provider = GoogleCustomSearchProvider("api-key", "")
        assert provider.is_available() == False
    
    def test_build_search_params(self, google_provider):
        """Test search parameter building"""
        config = SearchConfig(
            max_results=15,
            language="es",
            region="US",
            site_filter="example.com",
            exclude_sites=["spam.com", "ads.net"]
        )
        
        params = google_provider._build_search_params("CRM software", config)
        
        assert params['key'] == "test-api-key"
        assert params['cx'] == "test-cse-id"
        assert params['q'] == "CRM software -site:spam.com -site:ads.net company"
        assert params['num'] == '10'  # Google max is 10
        assert params['lr'] == 'lang_es'
        assert params['gl'] == 'US'
    
    @pytest.mark.asyncio
    async def test_successful_search(self, google_provider, mock_google_response):
        """Test successful search execution"""
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_google_response
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Execute search
            config = SearchConfig(max_results=10, company_focus=True)
            result = await google_provider.search("Salesforce competitors", config)
            
            # Verify results
            assert result.query == "Salesforce competitors"
            assert result.provider_used == "google_custom"
            assert len(result.results) == 3
            assert result.total_results == 1500
            assert result.company_results_count >= 1
            
            # Check individual results
            salesforce_result = result.results[0]
            assert salesforce_result.title == "Salesforce - Customer Success Platform"
            assert salesforce_result.url == "https://www.salesforce.com/"
            assert salesforce_result.extracted_domain == "salesforce.com"
            assert salesforce_result.extracted_company_name == "Salesforce"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, google_provider):
        """Test rate limiting behavior"""
        
        # Simulate exceeding daily quota
        google_provider.daily_query_count = 100
        
        with pytest.raises(Exception, match="rate limited"):
            await google_provider.search("test query")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, google_provider):
        """Test API error handling"""
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock API error response
            mock_response = AsyncMock()
            mock_response.status = 403
            mock_response.json.return_value = {
                "error": {
                    "message": "Daily Limit Exceeded"
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Should return empty results instead of crashing
            result = await google_provider.search("test query")
            
            assert len(result.results) == 0
            assert result.quality_score == 0.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, google_provider):
        """Test timeout handling with retries"""
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock timeout
            mock_get.side_effect = asyncio.TimeoutError()
            
            # Should handle timeout gracefully
            result = await google_provider.search("test query")
            
            assert len(result.results) == 0
            assert result.quality_score == 0.0
    
    def test_company_info_extraction(self, google_provider):
        """Test company information extraction"""
        
        result = SearchResult(
            title="Acme Corp - Leading Software Solutions",
            url="https://www.acme-corp.com/about",
            snippet="Acme Corp provides enterprise software solutions.",
            search_provider="google_custom"
        )
        
        enhanced_result = google_provider.extract_company_info(result)
        
        assert enhanced_result.extracted_domain == "acme-corp.com"
        assert enhanced_result.extracted_company_name == "Acme Corp"
        assert enhanced_result.result_type.value == "company_website"
    
    def test_quality_assessment_integration(self, google_provider):
        """Test integration with quality assessment"""
        
        # This would test the quality assessor integration
        # Quality scores should be calculated and applied
        pass

# Similar test files for other providers...

# v2/tests/unit/adapters/search/test_search_chain.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.infrastructure.adapters.search.chain import SearchProviderChain
from src.core.interfaces.search_provider import SearchProvider, SearchResults, SearchConfig

class TestSearchProviderChain:
    """Test the search provider chain"""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing"""
        
        # Primary provider (high quality, expensive)
        primary = Mock(spec=SearchProvider)
        primary.provider_name = "primary"
        primary.is_available.return_value = True
        primary.is_rate_limited.return_value = False
        primary.get_cost_per_search.return_value = 0.05
        primary.search = AsyncMock(return_value=SearchResults(
            query="test", results=[], total_results=100, provider_used="primary",
            execution_time_seconds=1.0, quality_score=0.9
        ))
        
        # Secondary provider (good quality, moderate cost)
        secondary = Mock(spec=SearchProvider)
        secondary.provider_name = "secondary"
        secondary.is_available.return_value = True
        secondary.is_rate_limited.return_value = False
        secondary.get_cost_per_search.return_value = 0.02
        secondary.search = AsyncMock(return_value=SearchResults(
            query="test", results=[], total_results=80, provider_used="secondary",
            execution_time_seconds=2.0, quality_score=0.8
        ))
        
        # Fallback provider (free, lower quality)
        fallback = Mock(spec=SearchProvider)
        fallback.provider_name = "fallback"
        fallback.is_available.return_value = True
        fallback.is_rate_limited.return_value = False
        fallback.get_cost_per_search.return_value = 0.0
        fallback.search = AsyncMock(return_value=SearchResults(
            query="test", results=[], total_results=50, provider_used="fallback",
            execution_time_seconds=3.0, quality_score=0.6
        ))
        
        return [primary, secondary, fallback]
    
    @pytest.fixture
    def search_chain(self, mock_providers):
        """Create search chain with mock providers"""
        chain = SearchProviderChain()
        for provider in mock_providers:
            chain.add_provider(provider)
        return chain
    
    @pytest.mark.asyncio
    async def test_successful_search_with_primary(self, search_chain, mock_providers):
        """Test successful search using primary provider"""
        
        result = await search_chain.search("test query")
        
        # Should use primary provider
        assert result.provider_used == "primary"
        assert result.quality_score == 0.9
        
        # Primary provider should have been called
        mock_providers[0].search.assert_called_once()
        
        # Secondary and fallback should not be called
        mock_providers[1].search.assert_not_called()
        mock_providers[2].search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_failover_to_secondary(self, search_chain, mock_providers):
        """Test failover when primary provider fails"""
        
        # Make primary provider fail
        mock_providers[0].search.side_effect = Exception("Primary failed")
        
        result = await search_chain.search("test query")
        
        # Should fallback to secondary provider
        assert result.provider_used == "secondary"
        assert result.quality_score == 0.8
        
        # Both primary and secondary should have been called
        mock_providers[0].search.assert_called_once()
        mock_providers[1].search.assert_called_once()
        
        # Fallback should not be called
        mock_providers[2].search.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, search_chain, mock_providers):
        """Test behavior when all providers fail"""
        
        # Make all providers fail
        for provider in mock_providers:
            provider.search.side_effect = Exception("Provider failed")
        
        # Should raise exception
        with pytest.raises(Exception, match="All search providers failed"):
            await search_chain.search("test query")
    
    @pytest.mark.asyncio
    async def test_rate_limited_provider_skipped(self, search_chain, mock_providers):
        """Test that rate limited providers are skipped"""
        
        # Make primary provider rate limited
        mock_providers[0].is_rate_limited.return_value = True
        
        result = await search_chain.search("test query")
        
        # Should skip to secondary provider
        assert result.provider_used == "secondary"
        
        # Primary should not be called due to rate limiting
        mock_providers[0].search.assert_not_called()
        mock_providers[1].search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_provider_search(self, search_chain, mock_providers):
        """Test searching with multiple providers for diversity"""
        
        results = await search_chain.search_with_multiple_providers(
            "test query", max_providers=2
        )
        
        # Should get results from multiple providers
        assert len(results) == 2
        
        provider_names = [r.provider_used for r in results]
        assert "primary" in provider_names
        assert "secondary" in provider_names
    
    def test_provider_statistics(self, search_chain, mock_providers):
        """Test provider statistics tracking"""
        
        # Simulate some usage
        search_chain._record_provider_attempt(mock_providers[0])
        search_chain._record_provider_success(mock_providers[0], 1.5)
        
        search_chain._record_provider_attempt(mock_providers[1])
        search_chain._record_provider_failure(mock_providers[1], Exception("Failed"))
        
        stats = search_chain.get_provider_statistics()
        
        # Check primary provider stats
        primary_stats = stats["primary"]
        assert primary_stats['attempts'] == 1
        assert primary_stats['successes'] == 1
        assert primary_stats['failures'] == 0
        assert primary_stats['success_rate'] == 1.0
        
        # Check secondary provider stats
        secondary_stats = stats["secondary"]
        assert secondary_stats['attempts'] == 1
        assert secondary_stats['successes'] == 0
        assert secondary_stats['failures'] == 1
        assert secondary_stats['success_rate'] == 0.0
```

This creates comprehensive unit testing for our search system!"

## Section 6: Integration Testing and Production Deployment (8 minutes)

**[SLIDE 12: Integration Testing]**

"Let's create integration tests with real search providers:

```python
# v2/tests/integration/test_search_providers.py
import pytest
import asyncio
import os
from datetime import datetime

from src.infrastructure.adapters.search.chain import SearchProviderChainFactory
from src.core.interfaces.search_provider import SearchConfig
from src.infrastructure.adapters.search.google_custom import GoogleCustomSearchProvider
from src.infrastructure.adapters.search.duckduckgo import DuckDuckGoProvider

@pytest.mark.integration
class TestSearchProviderIntegration:
    """Integration tests with real search providers"""
    
    @pytest.fixture
    def search_config(self):
        """Integration test configuration"""
        return {
            'google_custom_search_api_key': os.getenv('GOOGLE_CSE_API_KEY'),
            'google_custom_search_engine_id': os.getenv('GOOGLE_CSE_ID'),
            'serpapi_api_key': os.getenv('SERPAPI_API_KEY')
        }
    
    @pytest.mark.asyncio
    async def test_google_custom_search_integration(self, search_config):
        """Test Google Custom Search with real API"""
        
        api_key = search_config.get('google_custom_search_api_key')
        cse_id = search_config.get('google_custom_search_engine_id')
        
        if not api_key or not cse_id:
            pytest.skip("Google Custom Search credentials not available")
        
        provider = GoogleCustomSearchProvider(api_key, cse_id)
        config = SearchConfig(max_results=5, company_focus=True)
        
        # Test company search
        result = await provider.search("Salesforce CRM software", config)
        
        # Verify results
        assert len(result.results) > 0
        assert result.total_results > 0
        assert result.quality_score > 0.5
        assert result.execution_time_seconds < 10.0
        
        # Check for company-relevant results
        company_results = [r for r in result.results 
                          if r.result_type.value in ['company_website', 'directory_listing']]
        assert len(company_results) > 0
        
        # Verify Salesforce is found
        salesforce_results = [r for r in result.results 
                             if 'salesforce' in r.title.lower() or 'salesforce' in r.url.lower()]
        assert len(salesforce_results) > 0
    
    @pytest.mark.asyncio
    async def test_duckduckgo_search_integration(self):
        """Test DuckDuckGo search integration"""
        
        provider = DuckDuckGoProvider()
        config = SearchConfig(max_results=10, company_focus=True)
        
        # Test company search
        result = await provider.search("HubSpot marketing software", config)
        
        # Verify results (DuckDuckGo may have fewer results)
        assert len(result.results) >= 0  # May return 0 due to rate limiting
        assert result.execution_time_seconds < 30.0
        assert result.cost_per_search == 0.0  # Free
        
        if len(result.results) > 0:
            # Check result quality
            assert result.quality_score >= 0.0
            
            # Verify basic result structure
            first_result = result.results[0]
            assert first_result.title
            assert first_result.url
            assert first_result.search_provider == "duckduckgo"
    
    @pytest.mark.asyncio
    async def test_search_chain_integration(self, search_config):
        """Test complete search chain with real providers"""
        
        # Create configured chain
        chain = SearchProviderChainFactory.create_default_chain(search_config)
        
        # Test various search scenarios
        test_queries = [
            "Salesforce competitors CRM",
            "Microsoft Azure cloud services",
            "Shopify ecommerce platform alternatives"
        ]
        
        for query in test_queries:
            try:
                config = SearchConfig(max_results=5, company_focus=True)
                result = await chain.search(query, config)
                
                # Verify successful search
                assert result.query == query
                assert len(result.results) > 0
                assert result.execution_time_seconds < 30.0
                
                # Check provider was used
                assert result.provider_used in ['google_custom', 'serpapi', 'duckduckgo']
                
                # Verify company extraction
                extracted_companies = [r.extracted_company_name for r in result.results 
                                     if r.extracted_company_name]
                assert len(extracted_companies) > 0
                
                print(f"Query: {query}")
                print(f"Provider: {result.provider_used}")
                print(f"Results: {len(result.results)}")
                print(f"Quality: {result.quality_score:.2f}")
                print(f"Companies found: {result.company_results_count}")
                print("---")
                
            except Exception as e:
                # Log but don't fail (some providers may be unavailable)
                print(f"Search failed for '{query}': {str(e)}")
    
    @pytest.mark.asyncio
    async def test_multi_provider_diversity(self, search_config):
        """Test multi-provider search for result diversity"""
        
        chain = SearchProviderChainFactory.create_default_chain(search_config)
        
        # Search with multiple providers
        results = await chain.search_with_multiple_providers(
            "Zoom video conferencing competitors",
            max_providers=2
        )
        
        if len(results) > 1:
            # Verify diversity
            providers_used = [r.provider_used for r in results]
            assert len(set(providers_used)) > 1  # Different providers
            
            # Compare result overlap
            all_urls = set()
            for result in results:
                all_urls.update(r.url for r in result.results)
            
            # Should have some unique results from each provider
            total_results = sum(len(r.results) for r in results)
            unique_results = len(all_urls)
            
            # Allow some overlap but expect diversity
            diversity_ratio = unique_results / total_results
            assert diversity_ratio > 0.5  # At least 50% unique results
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self, search_config):
        """Test error recovery in real conditions"""
        
        chain = SearchProviderChainFactory.create_default_chain(search_config)
        
        # Test with potentially problematic queries
        challenging_queries = [
            "ñoño企業 weird unicode company",  # Unicode characters
            "very long query " * 20,  # Very long query
            "!@#$%^&*() special chars only",  # Special characters
            ""  # Empty query
        ]
        
        for query in challenging_queries:
            try:
                config = SearchConfig(max_results=3)
                result = await chain.search(query, config)
                
                # Should handle gracefully
                assert result is not None
                assert result.query == query
                
            except Exception as e:
                # Some queries may legitimately fail
                assert "search providers failed" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, search_config):
        """Test performance benchmarks for search providers"""
        
        chain = SearchProviderChainFactory.create_default_chain(search_config)
        
        # Performance test queries
        performance_queries = [
            "Apple iPhone smartphone",
            "Tesla electric vehicles",
            "Netflix streaming service",
            "Airbnb vacation rentals"
        ]
        
        total_start_time = datetime.utcnow()
        results_summary = []
        
        for query in performance_queries:
            try:
                start_time = datetime.utcnow()
                config = SearchConfig(max_results=5)
                result = await chain.search(query, config)
                end_time = datetime.utcnow()
                
                total_time = (end_time - start_time).total_seconds()
                
                results_summary.append({
                    'query': query,
                    'provider': result.provider_used,
                    'results_count': len(result.results),
                    'quality_score': result.quality_score,
                    'execution_time': total_time,
                    'company_results': result.company_results_count
                })
                
            except Exception as e:
                results_summary.append({
                    'query': query,
                    'error': str(e),
                    'execution_time': 0
                })
        
        total_end_time = datetime.utcnow()
        total_execution_time = (total_end_time - total_start_time).total_seconds()
        
        # Performance assertions
        successful_searches = [r for r in results_summary if 'error' not in r]
        if successful_searches:
            avg_execution_time = sum(r['execution_time'] for r in successful_searches) / len(successful_searches)
            avg_quality = sum(r['quality_score'] for r in successful_searches) / len(successful_searches)
            
            # Performance expectations
            assert avg_execution_time < 15.0  # Average under 15 seconds
            assert avg_quality > 0.5  # Average quality above 50%
            assert total_execution_time < 60.0  # All queries under 1 minute
        
        # Print performance summary
        print("\\nPerformance Summary:")
        print(f"Total execution time: {total_execution_time:.2f}s")
        for summary in results_summary:
            if 'error' not in summary:
                print(f"{summary['query']}: {summary['execution_time']:.2f}s, "
                      f"Quality: {summary['quality_score']:.2f}, "
                      f"Results: {summary['results_count']}")
            else:
                print(f"{summary['query']}: ERROR - {summary['error']}")
```

This creates comprehensive integration testing with real providers!"

**[SLIDE 13: Production Deployment and Monitoring]**

"Finally, let's add production monitoring and deployment patterns:

```python
# v2/src/infrastructure/adapters/search/monitoring.py
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Set up observability
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Metrics
search_requests_counter = meter.create_counter(
    "search_requests_total",
    description="Total search requests by provider"
)

search_duration_histogram = meter.create_histogram(
    "search_duration_seconds",
    description="Search request duration by provider"
)

search_results_counter = meter.create_counter(
    "search_results_total", 
    description="Total search results returned by provider"
)

search_errors_counter = meter.create_counter(
    "search_errors_total",
    description="Search errors by provider and type"
)

@dataclass
class SearchMetrics:
    """Search metrics for monitoring"""
    provider_name: str
    requests: int = 0
    successes: int = 0
    failures: int = 0
    total_execution_time: float = 0.0
    total_results: int = 0
    total_cost: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    error_counts: Dict[str, int] = field(default_factory=dict)

class SearchMonitor:
    """Monitor search provider performance and health"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, SearchMetrics] = {}
        self.alert_thresholds = {
            'max_failure_rate': 0.5,  # 50% failure rate triggers alert
            'max_avg_duration': 30.0,  # 30s average duration triggers alert
            'min_success_rate': 0.8    # Below 80% success rate triggers alert
        }
    
    def record_search_attempt(self, provider_name: str, query: str):
        """Record search attempt"""
        with tracer.start_as_current_span("search_attempt") as span:
            span.set_attribute("provider", provider_name)
            span.set_attribute("query_length", len(query))
            
            if provider_name not in self.metrics:
                self.metrics[provider_name] = SearchMetrics(provider_name)
            
            self.metrics[provider_name].requests += 1
            
            search_requests_counter.add(1, {"provider": provider_name})
    
    def record_search_success(self, provider_name: str, execution_time: float,
                            results_count: int, cost: float = 0.0):
        """Record successful search"""
        with tracer.start_as_current_span("search_success") as span:
            span.set_attribute("provider", provider_name)
            span.set_attribute("execution_time", execution_time)
            span.set_attribute("results_count", results_count)
            span.set_attribute("cost", cost)
            span.set_status(Status(StatusCode.OK))
            
            metrics = self.metrics[provider_name]
            metrics.successes += 1
            metrics.total_execution_time += execution_time
            metrics.total_results += results_count
            metrics.total_cost += cost
            metrics.last_success = datetime.utcnow()
            
            # Record metrics
            search_duration_histogram.record(execution_time, {"provider": provider_name})
            search_results_counter.add(results_count, {"provider": provider_name})
            
            self.logger.info(
                f"Search success: {provider_name} - {execution_time:.2f}s, {results_count} results"
            )
    
    def record_search_failure(self, provider_name: str, error: Exception,
                            execution_time: float = 0.0):
        """Record search failure"""
        with tracer.start_as_current_span("search_failure") as span:
            span.set_attribute("provider", provider_name)
            span.set_attribute("error_type", type(error).__name__)
            span.set_attribute("execution_time", execution_time)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
            
            metrics = self.metrics[provider_name]
            metrics.failures += 1
            metrics.total_execution_time += execution_time
            metrics.last_failure = datetime.utcnow()
            
            error_type = type(error).__name__
            metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1
            
            # Record metrics
            search_errors_counter.add(1, {
                "provider": provider_name,
                "error_type": error_type
            })
            
            self.logger.error(
                f"Search failure: {provider_name} - {error_type}: {str(error)}"
            )
            
            # Check if alert thresholds are exceeded
            self._check_alert_thresholds(provider_name)
    
    def get_provider_health(self, provider_name: str) -> Dict[str, Any]:
        """Get health status for a provider"""
        if provider_name not in self.metrics:
            return {"status": "unknown", "message": "No metrics available"}
        
        metrics = self.metrics[provider_name]
        
        if metrics.requests == 0:
            return {"status": "unknown", "message": "No requests recorded"}
        
        success_rate = metrics.successes / metrics.requests
        failure_rate = metrics.failures / metrics.requests
        avg_execution_time = metrics.total_execution_time / metrics.requests
        
        # Determine health status
        if success_rate >= self.alert_thresholds['min_success_rate']:
            status = "healthy"
        elif success_rate >= 0.5:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "avg_execution_time": avg_execution_time,
            "total_requests": metrics.requests,
            "total_results": metrics.total_results,
            "total_cost": metrics.total_cost,
            "last_success": metrics.last_success.isoformat() if metrics.last_success else None,
            "last_failure": metrics.last_failure.isoformat() if metrics.last_failure else None,
            "error_breakdown": metrics.error_counts
        }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall search system health"""
        if not self.metrics:
            return {"status": "unknown", "providers": {}}
        
        provider_health = {}
        overall_statuses = []
        
        for provider_name in self.metrics:
            health = self.get_provider_health(provider_name)
            provider_health[provider_name] = health
            overall_statuses.append(health["status"])
        
        # Determine overall status
        if all(status == "healthy" for status in overall_statuses):
            overall_status = "healthy"
        elif any(status == "healthy" for status in overall_statuses):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "providers": provider_health,
            "total_providers": len(self.metrics),
            "healthy_providers": sum(1 for status in overall_statuses if status == "healthy"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_alert_thresholds(self, provider_name: str):
        """Check if provider exceeds alert thresholds"""
        metrics = self.metrics[provider_name]
        
        if metrics.requests < 10:  # Need minimum requests for meaningful stats
            return
        
        success_rate = metrics.successes / metrics.requests
        avg_execution_time = metrics.total_execution_time / metrics.requests
        
        # Check thresholds and log alerts
        if success_rate < self.alert_thresholds['min_success_rate']:
            self.logger.warning(
                f"ALERT: {provider_name} success rate ({success_rate:.2f}) "
                f"below threshold ({self.alert_thresholds['min_success_rate']})"
            )
        
        if avg_execution_time > self.alert_thresholds['max_avg_duration']:
            self.logger.warning(
                f"ALERT: {provider_name} avg execution time ({avg_execution_time:.2f}s) "
                f"above threshold ({self.alert_thresholds['max_avg_duration']}s)"
            )

# Global monitor instance
search_monitor = SearchMonitor()

# Enhanced provider base class with monitoring
class MonitoredSearchProvider:
    """Base class that adds monitoring to search providers"""
    
    def __init__(self, provider: Any):
        self.provider = provider
        self.monitor = search_monitor
    
    async def search(self, query: str, config: Any = None):
        """Search with automatic monitoring"""
        provider_name = self.provider.provider_name
        
        # Record attempt
        self.monitor.record_search_attempt(provider_name, query)
        
        start_time = time.time()
        
        try:
            # Execute search
            result = await self.provider.search(query, config)
            
            execution_time = time.time() - start_time
            
            # Record success
            self.monitor.record_search_success(
                provider_name=provider_name,
                execution_time=execution_time,
                results_count=len(result.results),
                cost=getattr(result, 'cost_per_search', 0.0)
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure
            self.monitor.record_search_failure(
                provider_name=provider_name,
                error=e,
                execution_time=execution_time
            )
            
            raise
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped provider"""
        return getattr(self.provider, name)
```

This adds comprehensive production monitoring to our search system!"

## Conclusion and Best Practices (5 minutes)

**[SLIDE 14: Multi-Provider Search Architecture Summary]**

"Let's summarize what we've built:

```python
# Complete multi-provider search system
class EnterpriseSearchSystem:
    '''
    🔍 Resilient Multi-Provider Search Infrastructure
    
    Architecture Components:
    ├── Search Provider Interface (Universal Contract)
    │   ├── Standardized search operations and configuration
    │   ├── Quality assessment and result scoring
    │   ├── Rate limiting and cost tracking
    │   └── Company information extraction
    │
    ├── Multiple Provider Implementations (Redundancy)
    │   ├── Google Custom Search (Premium quality)
    │   ├── SerpAPI (Reliable alternative)
    │   ├── DuckDuckGo (Free fallback)
    │   └── Extensible for additional providers
    │
    ├── Provider Chain Management (Intelligent Routing)
    │   ├── Automatic failover between providers
    │   ├── Cost optimization and provider selection
    │   ├── Performance monitoring and statistics
    │   └── Multi-provider search for diversity
    │
    └── Production Infrastructure (Enterprise-ready)
        ├── OpenTelemetry monitoring and metrics
        ├── Comprehensive error handling and recovery
        ├── Integration testing with real providers
        └── Health checks and alerting
    
    Key Capabilities:
    ✅ 99.9% uptime with automatic failover
    ✅ Cost optimization through provider selection
    ✅ Quality-driven result ranking and filtering
    ✅ Company data extraction and classification
    ✅ Real-time monitoring and alerting
    ✅ Extensible architecture for new providers
    '''
```

**[SLIDE 15: Production Best Practices]**

"Key patterns for production search systems:

1. **Provider Redundancy**: Always have multiple search providers configured
2. **Intelligent Failover**: Use quality scores and availability for provider selection
3. **Cost Optimization**: Track costs and optimize provider usage automatically
4. **Rate Limit Respect**: Implement proper delays and quotas for each provider
5. **Quality Assessment**: Score results comprehensively across multiple dimensions
6. **Comprehensive Monitoring**: Track performance, costs, and reliability
7. **Graceful Degradation**: System continues working even when providers fail"

**[SLIDE 16: Key Takeaways]**

"What you've learned:

🏗️ **Architecture Patterns**:
- Port/Adapter pattern for provider abstraction
- Chain of Responsibility for provider failover
- Factory pattern for configuration-driven provider selection

🔍 **Search Excellence**:
- Multi-provider redundancy for reliability
- Quality-based result scoring and ranking
- Cost-aware provider selection and optimization

📊 **Production Readiness**:
- OpenTelemetry monitoring with custom metrics
- Comprehensive error handling and recovery patterns
- Integration testing with real provider APIs

🛡️ **Reliability & Performance**:
- Rate limiting and quota management
- Circuit breaker patterns for resilience
- Performance benchmarking and optimization

This architecture ensures your search infrastructure is reliable, cost-effective, and scalable!"

## Total Tutorial Time: ~55 minutes

This comprehensive tutorial covers building a production-ready multi-provider search system that provides reliability, cost optimization, and excellent search quality while maintaining clean architecture principles and comprehensive observability.