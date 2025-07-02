# TICKET-017: MCP Perplexity Adapter

## Overview
Implement the Perplexity AI search adapter following the MCP search tool port interface, enabling Theodore to use Perplexity's advanced search capabilities for finding similar companies.

## Problem Statement
Need a concrete implementation of the MCP search tool port for Perplexity AI, which offers superior search capabilities with real-time web data and AI-powered result ranking.

## Acceptance Criteria
- [ ] Perplexity adapter implements MCPSearchToolPort interface
- [ ] Configuration supports all Perplexity API options
- [ ] Handles rate limiting and API errors gracefully
- [ ] Transforms Perplexity results to standard format
- [ ] Includes confidence scoring based on result quality
- [ ] Supports different Perplexity models (sonar-small, sonar-medium)
- [ ] Unit tests with mocked API responses
- [ ] Integration test with real Perplexity API (if key available)

## Technical Details

### Interface Contract
Implements the `MCPSearchToolPort` interface defined in TICKET-005 (MCP Search Droid Support). The interface provides standardized methods for company discovery using Perplexity AI's search capabilities.

### Configuration Integration
Must integrate with Theodore's configuration system (TICKET-003):
```yaml
# config/search_tools.yml
mcp_search_tools:
  perplexity:
    enabled: true
    api_key: "${PERPLEXITY_API_KEY}"
    model: "sonar-medium"
    search_depth: "comprehensive"
    max_results: 10
    rate_limit_requests_per_minute: 20
    enable_caching: true
    cache_ttl_seconds: 3600
```

### Dependency Injection
Must register in container (following established pattern):
```python
# In container setup
container.register(
    MCPSearchToolPort,
    PerplexityAdapter,
    config=container.resolve(PerplexityConfig),
    name="perplexity"
)
```

### File Structure
All files created in Theodore v2 structure:
- `v2/src/infrastructure/adapters/mcp/perplexity/`
- Following established adapter patterns from other tickets

### Implementation Requirements
1. **Authentication**: API key configuration with secure storage
2. **Search Types**: Web search, news search, company-specific search
3. **Result Parsing**: Extract company names, URLs, descriptions with AI-powered relevance scoring
4. **Error Handling**: Rate limits, quota exceeded, network errors with exponential backoff
5. **Caching**: Smart result caching to reduce API calls and costs

### Perplexity-Specific Features
- Model selection (sonar-small vs sonar-medium vs sonar-large)
- Search focus parameters (web, news, academic, shopping)
- Citation handling and source attribution
- Freshness filtering and recency controls
- Search depth configuration (quick vs comprehensive)
- Result ranking and confidence scoring

## Example Implementation

```python
class PerplexityAdapter(MCPSearchToolPort):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = config.get("model", "sonar-medium")
        self.client = PerplexityClient(api_key=self.api_key)
    
    async def search_similar_companies(
        self, 
        company_name: str,
        search_params: MCPSearchParams
    ) -> MCPSearchResult:
        # Generate search query
        query = self._build_query(company_name, search_params)
        
        # Execute search
        response = await self.client.search(
            query=query,
            model=self.model,
            search_depth="comprehensive",
            search_recency=search_params.recency_filter
        )
        
        # Parse and transform results
        companies = self._extract_companies(response)
        
        return MCPSearchResult(
            tool_name="perplexity",
            tool_version="1.0",
            companies=companies,
            metadata={
                "model_used": self.model,
                "citations": response.citations
            }
        )
```

## Testing Strategy
- Mock Perplexity API responses for unit tests
- Test various search scenarios
- Verify error handling
- Performance testing with concurrent searches

## Estimated Time: 4-6 hours

## Dependencies
- TICKET-005: MCP Search Droid Support (port interface)
- TICKET-003: Configuration System (for API keys)

## Files to Create
- `v2/src/infrastructure/adapters/mcp/perplexity/__init__.py`
- `v2/src/infrastructure/adapters/mcp/perplexity/adapter.py`
- `v2/src/infrastructure/adapters/mcp/perplexity/client.py`
- `v2/src/infrastructure/adapters/mcp/perplexity/config.py`
- `v2/src/infrastructure/adapters/mcp/perplexity/query_builder.py`
- `v2/src/infrastructure/adapters/mcp/perplexity/result_parser.py`
- `v2/tests/unit/adapters/mcp/test_perplexity_adapter.py`
- `v2/tests/integration/adapters/mcp/test_perplexity_integration.py`
- `v2/tests/fixtures/perplexity_responses.json`

## Notes
- Follow Perplexity's API documentation for best practices
- Consider implementing exponential backoff for rate limiting
- Cache results when appropriate to reduce costs
- Support both streaming and non-streaming responses

---

# Udemy Tutorial Script: Building Advanced AI-Powered Search with Perplexity

## Introduction (4 minutes)

**[SLIDE 1: Title - "Building Enterprise AI Search with Perplexity and Model Context Protocol"]**

"Welcome to this cutting-edge tutorial on building enterprise-grade AI search systems! Today we're going to implement a Perplexity AI adapter that demonstrates the future of intelligent company discovery using the Model Context Protocol (MCP).

By the end of this tutorial, you'll understand how to integrate Perplexity's advanced AI search capabilities into your applications, implement proper caching and rate limiting, handle real-time search results with citations, and build a system that can intelligently find similar companies using natural language processing.

This is the kind of AI-powered search that's transforming how businesses discover and analyze competitors, partners, and market opportunities!"

## Section 1: Understanding Perplexity AI and MCP Architecture (6 minutes)

**[SLIDE 2: The Perplexity AI Advantage]**

"Let's start by understanding why Perplexity AI is revolutionizing search for enterprise applications:

```python
# Traditional search limitations:
traditional_search_problems = {
    'google_search': {
        'challenge': 'Static results without context',
        'issues': ['SEO manipulation', 'Outdated information', 'No analysis'],
        'example': 'Search "AI companies" → Generic lists without insights'
    },
    'basic_apis': {
        'challenge': 'Raw data without intelligence',
        'issues': ['No relevance ranking', 'Manual result parsing', 'No context'],
        'example': 'Company APIs → Raw JSON without business insights'
    }
}

# Perplexity AI advantages:
perplexity_advantages = {
    'real_time_analysis': {
        'feature': 'Live web crawling with AI analysis',
        'benefit': 'Up-to-date company information and market insights',
        'example': 'Find "AI companies like OpenAI" → Get recent funding, team changes, product launches'
    },
    'contextual_understanding': {
        'feature': 'Natural language query processing',
        'benefit': 'Ask complex questions, get intelligent answers',
        'example': 'Query: "SaaS companies in fintech with < 100 employees" → Precise results'
    },
    'citation_tracking': {
        'feature': 'Source attribution for every claim',
        'benefit': 'Verify information and explore original sources',
        'example': 'Each fact includes direct links to source articles'
    },
    'model_selection': {
        'feature': 'Choose between speed (sonar-small) vs depth (sonar-large)',
        'benefit': 'Optimize for your use case and budget',
        'example': 'Quick checks vs comprehensive market research'
    }
}
```

This combination makes Perplexity perfect for company intelligence gathering!"

**[SLIDE 3: Model Context Protocol (MCP) Benefits]**

"The Model Context Protocol allows us to build pluggable search systems:

```python
# MCP Architecture Benefits:
mcp_architecture = {
    'plugin_system': {
        'concept': 'Interchangeable search tools',
        'benefit': 'Easy switching between Perplexity, Tavily, Google',
        'code_impact': 'Same interface, different implementations'
    },
    'standardized_interface': {
        'concept': 'Common API for all search tools',
        'benefit': 'Consistent integration patterns',
        'example': 'search_similar_companies() works with any adapter'
    },
    'configuration_driven': {
        'concept': 'Enable/disable tools without code changes',
        'benefit': 'Runtime flexibility and cost control',
        'example': 'Switch to cheaper tool during high-volume periods'
    },
    'composable_results': {
        'concept': 'Combine results from multiple search tools',
        'benefit': 'More comprehensive and accurate results',
        'example': 'Perplexity for analysis + Google for coverage'
    }
}

# Real-world usage patterns:
usage_patterns = {
    'development': 'Use free/cheap tools for testing',
    'production': 'Premium tools for accurate results', 
    'cost_optimization': 'Smart tool selection based on query complexity',
    'reliability': 'Fallback chains when primary tools fail'
}
```

This architecture scales from prototype to enterprise!"

**[SLIDE 4: Understanding Search Intelligence Levels]**

"Different search scenarios require different intelligence levels:

```python
# Search complexity hierarchy:
search_intelligence_levels = {
    'level_1_basic': {
        'query': 'Find companies like Stripe',
        'tool': 'Google Search API',
        'result': 'List of payment companies',
        'intelligence': 'Keyword matching only'
    },
    'level_2_contextual': {
        'query': 'Find fintech companies with similar payment infrastructure to Stripe',
        'tool': 'Perplexity Sonar-Small',
        'result': 'Payment processors with API-first approach',
        'intelligence': 'Context understanding + categorization'
    },
    'level_3_analytical': {
        'query': 'Find companies that compete with Stripe in enterprise payments but focus on B2B marketplaces',
        'tool': 'Perplexity Sonar-Large',
        'result': 'Detailed analysis of competitive landscape with market positioning',
        'intelligence': 'Multi-dimensional analysis + strategic insights'
    },
    'level_4_predictive': {
        'query': 'Find emerging fintech companies that could disrupt Stripe in the next 2 years',
        'tool': 'Perplexity + Custom AI Analysis',
        'result': 'Trend analysis with disruption probability scores',
        'intelligence': 'Predictive analytics + market intelligence'
    }
}

# Our Perplexity adapter targets Level 2-3 with Level 4 potential
target_capabilities = {
    'context_understanding': 'Parse complex business queries',
    'real_time_data': 'Current market information and trends',
    'source_attribution': 'Credible citations for all claims',
    'intelligent_ranking': 'Relevance scoring beyond keyword matching'
}
```

We're building enterprise-grade intelligence, not just search!"

## Section 2: Designing the Perplexity Adapter Architecture (7 minutes)

**[SLIDE 5: Clean Architecture for Search Adapters]**

"Let's design our Perplexity adapter following clean architecture principles:

```python
# v2/src/infrastructure/adapters/mcp/perplexity/adapter.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class SearchDepth(Enum):
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"
    DEEP = "deep"

class PerplexityModel(Enum):
    SONAR_SMALL = "llama-3.1-sonar-small-128k-online"
    SONAR_MEDIUM = "llama-3.1-sonar-large-128k-online"
    SONAR_LARGE = "llama-3.1-sonar-huge-128k-online"

@dataclass
class PerplexityConfig:
    """Configuration for Perplexity adapter with enterprise features."""
    
    # Authentication
    api_key: str
    
    # Model Configuration
    default_model: PerplexityModel = PerplexityModel.SONAR_MEDIUM
    search_depth: SearchDepth = SearchDepth.COMPREHENSIVE
    max_results: int = 10
    
    # Performance & Cost Control
    rate_limit_requests_per_minute: int = 20
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Caching Configuration
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    cache_key_prefix: str = "perplexity_search"
    
    # Search Customization
    search_focus: List[str] = None  # ['web', 'news', 'academic']
    freshness_filter: Optional[str] = None  # '1d', '1w', '1m', '1y'
    region_preference: Optional[str] = None  # 'us', 'eu', 'global'
    
    @classmethod
    def from_environment(cls) -> 'PerplexityConfig':
        """Create configuration from environment variables."""
        import os
        return cls(
            api_key=os.getenv('PERPLEXITY_API_KEY'),
            default_model=PerplexityModel(os.getenv('PERPLEXITY_MODEL', 'llama-3.1-sonar-large-128k-online')),
            max_results=int(os.getenv('PERPLEXITY_MAX_RESULTS', '10')),
            rate_limit_requests_per_minute=int(os.getenv('PERPLEXITY_RATE_LIMIT', '20')),
            enable_caching=os.getenv('PERPLEXITY_ENABLE_CACHING', 'true').lower() == 'true'
        )

@dataclass
class SearchQuery:
    """Structured search query for Perplexity."""
    
    company_name: str
    search_intent: str
    business_context: Optional[str] = None
    industry_filter: Optional[str] = None
    size_filter: Optional[str] = None
    geographic_filter: Optional[str] = None
    freshness_requirement: Optional[str] = None
    
    def to_natural_language(self) -> str:
        """Convert structured query to natural language for Perplexity."""
        
        base_query = f"Find companies similar to {self.company_name}"
        
        if self.search_intent:
            base_query += f" {self.search_intent}"
        
        filters = []
        if self.industry_filter:
            filters.append(f"in the {self.industry_filter} industry")
        if self.size_filter:
            filters.append(f"with {self.size_filter}")
        if self.geographic_filter:
            filters.append(f"based in {self.geographic_filter}")
        
        if filters:
            base_query += " " + ", ".join(filters)
        
        if self.business_context:
            base_query += f". Focus on {self.business_context}"
        
        return base_query
```

This gives us a professional foundation with enterprise controls!"

**[SLIDE 6: Advanced Query Building System]**

"Let's create an intelligent query builder that optimizes searches for Perplexity:

```python
# v2/src/infrastructure/adapters/mcp/perplexity/query_builder.py
from typing import Dict, List, Optional
import re

class PerplexityQueryBuilder:
    """Intelligent query builder for Perplexity AI searches."""
    
    def __init__(self, config: PerplexityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def build_similarity_query(
        self, 
        company_name: str, 
        search_params: 'MCPSearchParams'
    ) -> str:
        """Build optimized query for finding similar companies."""
        
        # Start with core similarity query
        query_parts = [
            f"Find companies similar to {company_name}"
        ]
        
        # Add business model context if available
        if search_params.business_model:
            query_parts.append(f"with a {search_params.business_model} business model")
        
        # Add industry specificity
        if search_params.industry:
            query_parts.append(f"in the {search_params.industry} sector")
        
        # Add size constraints
        if search_params.company_size:
            size_query = self._build_size_query(search_params.company_size)
            if size_query:
                query_parts.append(size_query)
        
        # Add geographic constraints
        if search_params.region:
            query_parts.append(f"operating in {search_params.region}")
        
        # Add recency requirements
        if search_params.include_recent_news:
            query_parts.append("Include recent news and developments")
        
        # Add analysis depth
        analysis_suffix = self._get_analysis_suffix(search_params)
        if analysis_suffix:
            query_parts.append(analysis_suffix)
        
        # Combine into natural language
        query = " ".join(query_parts) + "."
        
        self.logger.debug(f"Built query: {query}")
        return query
    
    def build_market_analysis_query(
        self, 
        company_name: str, 
        analysis_type: str = "competitive_landscape"
    ) -> str:
        """Build query for market analysis."""
        
        query_templates = {
            'competitive_landscape': f"Analyze the competitive landscape for {company_name}. Who are their main competitors and how do they differentiate?",
            'market_position': f"What is {company_name}'s market position and competitive advantages in their industry?",
            'growth_trends': f"What are the growth trends and market opportunities for companies like {company_name}?",
            'funding_landscape': f"Analyze the funding landscape and investor interest for companies similar to {company_name}",
            'technology_stack': f"What technology stack and technical approach do companies similar to {company_name} typically use?"
        }
        
        return query_templates.get(analysis_type, query_templates['competitive_landscape'])
    
    def build_news_monitoring_query(
        self, 
        company_name: str, 
        time_period: str = "1w"
    ) -> str:
        """Build query for monitoring recent company news."""
        
        time_mapping = {
            '1d': 'past 24 hours',
            '1w': 'past week', 
            '1m': 'past month',
            '3m': 'past 3 months'
        }
        
        time_phrase = time_mapping.get(time_period, 'recent')
        
        return f"What are the latest news and developments about {company_name} in the {time_phrase}? Include funding, partnerships, product launches, and market moves."
    
    def _build_size_query(self, size_indicator: str) -> Optional[str]:
        """Convert size indicators to natural language."""
        
        size_mappings = {
            'startup': 'early-stage startup companies',
            'small': 'small companies with under 50 employees',
            'medium': 'medium-sized companies with 50-500 employees', 
            'large': 'large companies with 500+ employees',
            'enterprise': 'enterprise-level companies',
            'public': 'publicly traded companies',
            'private': 'private companies'
        }
        
        return size_mappings.get(size_indicator.lower())
    
    def _get_analysis_suffix(self, search_params: 'MCPSearchParams') -> Optional[str]:
        """Get analysis depth suffix based on search parameters."""
        
        if search_params.require_detailed_analysis:
            return "Provide detailed business analysis including revenue models, target markets, and strategic positioning"
        elif search_params.include_financial_data:
            return "Include available financial information and funding history"
        elif search_params.focus_on_technology:
            return "Focus on their technology stack and technical differentiation"
        
        return "Provide business overview and key differentiators"
    
    def optimize_query_for_model(
        self, 
        query: str, 
        model: PerplexityModel
    ) -> str:
        """Optimize query based on the selected Perplexity model."""
        
        if model == PerplexityModel.SONAR_SMALL:
            # For small model, keep queries concise and focused
            query = self._simplify_query(query)
        elif model == PerplexityModel.SONAR_LARGE:
            # For large model, we can add more complexity and nuance
            query = self._enhance_query_complexity(query)
        
        return query
    
    def _simplify_query(self, query: str) -> str:
        """Simplify query for smaller models."""
        
        # Remove complex analysis requests
        simplified = re.sub(r'Provide detailed.*?analysis.*?\.', '', query)
        simplified = re.sub(r'Include.*?financial.*?\.', '', query)
        
        # Keep core search intent
        if len(simplified.split()) > 20:
            # Truncate to core similarity request
            words = simplified.split()
            simplified = " ".join(words[:20]) + "."
        
        return simplified.strip()
    
    def _enhance_query_complexity(self, query: str) -> str:
        """Add complexity for larger models."""
        
        enhancements = [
            "Consider business model innovation and market disruption potential.",
            "Analyze competitive moats and defensibility factors.",
            "Include insights on market trends and growth trajectories."
        ]
        
        if not any(enhancement.lower() in query.lower() for enhancement in enhancements):
            # Add one enhancement based on query content
            if "business model" in query.lower():
                query += " " + enhancements[0]
            elif "competitive" in query.lower():
                query += " " + enhancements[1]
            else:
                query += " " + enhancements[2]
        
        return query
```

This query builder creates intelligent, context-aware searches!"

**[SLIDE 7: Production-Grade HTTP Client]**

"Now let's build a robust HTTP client that handles Perplexity's API professionally:

```python
# v2/src/infrastructure/adapters/mcp/perplexity/client.py
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import logging

class PerplexityAPIError(Exception):
    """Custom exception for Perplexity API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class RateLimiter:
    """Smart rate limiter for Perplexity API."""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0
        self.request_count = 0
        self.window_start = time.time()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        current_time = time.time()
        
        # Reset window if needed
        if current_time - self.window_start >= 60.0:
            self.request_count = 0
            self.window_start = current_time
        
        # Check if we're at rate limit
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60.0 - (current_time - self.window_start)
            if sleep_time > 0:
                logging.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Reset after sleep
                self.request_count = 0
                self.window_start = time.time()
        
        # Ensure minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1

class PerplexityClient:
    """Production-grade client for Perplexity AI API."""
    
    def __init__(self, config: PerplexityConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_requests_per_minute)
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API endpoints
        self.base_url = "https://api.perplexity.ai"
        self.chat_endpoint = f"{self.base_url}/chat/completions"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Theodore-AI/2.0 (Enterprise Search)"
                }
            )
    
    async def search(
        self, 
        query: str, 
        model: Optional[PerplexityModel] = None,
        search_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute search query with Perplexity AI."""
        
        await self._ensure_session()
        model = model or self.config.default_model
        
        # Build request payload
        payload = {
            "model": model.value,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a business intelligence assistant specialized in finding and analyzing companies. Provide factual, well-researched information with proper citations."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": self._get_max_tokens_for_model(model),
            "temperature": 0.1,  # Low temperature for factual searches
            "top_p": 0.9,
            "return_citations": True,
            "search_domain_filter": ["perplexity.ai"],
            "return_images": False
        }
        
        # Add search options if provided
        if search_options:
            payload.update(search_options)
        
        # Add freshness filter if configured
        if self.config.freshness_filter:
            payload["search_recency_filter"] = self.config.freshness_filter
        
        # Execute request with retries
        for attempt in range(self.config.max_retries):
            try:
                await self.rate_limiter.acquire()
                
                start_time = time.time()
                
                async with self.session.post(self.chat_endpoint, json=payload) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    
                    if response.status == 200:
                        self.logger.info(
                            f"Perplexity search successful: query_length={len(query)}, "
                            f"model={model.value}, response_time={response_time:.2f}s"
                        )
                        
                        # Add metadata
                        response_data['_metadata'] = {
                            'model_used': model.value,
                            'response_time': response_time,
                            'attempt': attempt + 1,
                            'query_length': len(query)
                        }
                        
                        return response_data
                    
                    elif response.status == 429:  # Rate limited
                        if attempt < self.config.max_retries - 1:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise PerplexityAPIError(
                                "Rate limit exceeded and max retries reached",
                                response.status,
                                response_data
                            )
                    
                    elif response.status == 401:
                        raise PerplexityAPIError(
                            "Authentication failed - check API key",
                            response.status,
                            response_data
                        )
                    
                    elif response.status >= 500:
                        if attempt < self.config.max_retries - 1:
                            backoff_delay = 2 ** attempt
                            self.logger.warning(f"Server error {response.status}, retrying in {backoff_delay}s")
                            await asyncio.sleep(backoff_delay)
                            continue
                        else:
                            raise PerplexityAPIError(
                                f"Server error: {response.status}",
                                response.status,
                                response_data
                            )
                    
                    else:
                        raise PerplexityAPIError(
                            f"API error: {response.status}",
                            response.status,
                            response_data
                        )
            
            except asyncio.TimeoutError:
                if attempt < self.config.max_retries - 1:
                    self.logger.warning(f"Request timeout, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise PerplexityAPIError("Request timeout after all retries")
            
            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    self.logger.warning(f"HTTP client error: {e}, retrying")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise PerplexityAPIError(f"HTTP client error: {e}")
        
        # Should never reach here due to exception handling above
        raise PerplexityAPIError("Unexpected error: exhausted retries without resolution")
    
    def _get_max_tokens_for_model(self, model: PerplexityModel) -> int:
        """Get appropriate max tokens for different models."""
        
        token_limits = {
            PerplexityModel.SONAR_SMALL: 1000,
            PerplexityModel.SONAR_MEDIUM: 2000,
            PerplexityModel.SONAR_LARGE: 4000
        }
        
        return token_limits.get(model, 2000)
    
    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible."""
        try:
            test_query = "What is the current date?"
            response = await self.search(
                query=test_query,
                model=PerplexityModel.SONAR_SMALL  # Use cheapest model for health check
            )
            
            return 'choices' in response and len(response['choices']) > 0
            
        except Exception as e:
            self.logger.warning(f"Perplexity health check failed: {e}")
            return False
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics (if available)."""
        # Note: Perplexity API doesn't provide usage endpoints
        # This is a placeholder for future functionality
        return {
            'rate_limit_remaining': self.config.rate_limit_requests_per_minute - self.rate_limiter.request_count,
            'current_window_start': self.rate_limiter.window_start,
            'requests_in_window': self.rate_limiter.request_count
        }
```

This client provides enterprise-grade reliability with comprehensive error handling!"

## Section 3: Building the Result Parser and Intelligence Engine (8 minutes)

**[SLIDE 8: Intelligent Result Parsing System]**

"Now let's build a sophisticated parser that extracts structured business intelligence from Perplexity's responses:

```python
# v2/src/infrastructure/adapters/mcp/perplexity/result_parser.py
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

@dataclass
class CompanyMatch:
    """Structured company information extracted from search results."""
    
    name: str
    description: str
    website: Optional[str] = None
    industry: Optional[str] = None
    founding_year: Optional[int] = None
    headquarters: Optional[str] = None
    employee_count: Optional[str] = None
    funding_info: Optional[str] = None
    business_model: Optional[str] = None
    key_products: List[str] = None
    confidence_score: float = 0.0
    citations: List[str] = None
    
    def __post_init__(self):
        if self.key_products is None:
            self.key_products = []
        if self.citations is None:
            self.citations = []

@dataclass
class ParsedSearchResult:
    """Complete parsed result from Perplexity search."""
    
    companies: List[CompanyMatch]
    search_summary: str
    total_companies_found: int
    market_insights: Optional[str] = None
    trend_analysis: Optional[str] = None
    citations: List[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []

class PerplexityResultParser:
    """Advanced parser for extracting structured data from Perplexity responses."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for extracting structured information
        self.company_patterns = {
            'name': r'(?:^|\n)(?:\d+\.\s*)?(\*\*)?([A-Z][a-zA-Z\s&\-\.]+?)(?:\*\*)?(?:\s*\([^)]+\))?(?:\s*[-–—:]|\s*\n)',
            'website': r'(?:website|site|url):\s*(https?://[^\s]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,})',
            'founding': r'(?:founded|established|started)(?:\s+in)?\s+(\d{4})',
            'employees': r'(?:employees?|staff|team|workforce):\s*([0-9,]+(?:\+)?|[a-zA-Z\s]+)',
            'funding': r'(?:raised|funding|investment):\s*\$([0-9]+(?:\.[0-9]+)?[BMK]?)',
            'headquarters': r'(?:headquarter|based|located)(?:\s+in)?\s+([A-Z][a-zA-Z\s,]+)',
            'industry': r'(?:industry|sector|field):\s*([a-zA-Z\s,&\-]+)'
        }
    
    def parse_search_response(self, response: Dict[str, Any]) -> ParsedSearchResult:
        """Parse complete Perplexity response into structured data."""
        
        try:
            # Extract main content
            choices = response.get('choices', [])
            if not choices:
                self.logger.warning("No choices found in Perplexity response")
                return self._empty_result()
            
            main_content = choices[0].get('message', {}).get('content', '')
            citations = self._extract_citations(response)
            
            # Parse companies from content
            companies = self._extract_companies(main_content, citations)
            
            # Extract market insights
            market_insights = self._extract_market_insights(main_content)
            trend_analysis = self._extract_trend_analysis(main_content)
            
            # Generate search summary
            search_summary = self._generate_search_summary(main_content, len(companies))
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(companies, main_content)
            
            result = ParsedSearchResult(
                companies=companies,
                search_summary=search_summary,
                total_companies_found=len(companies),
                market_insights=market_insights,
                trend_analysis=trend_analysis,
                citations=citations,
                confidence_score=confidence_score
            )
            
            self.logger.info(f"Parsed {len(companies)} companies with {confidence_score:.2f} confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing Perplexity response: {e}")
            return self._empty_result()
    
    def _extract_companies(self, content: str, citations: List[str]) -> List[CompanyMatch]:
        """Extract individual companies from content."""
        
        companies = []
        
        # Split content into sections that likely contain company information
        company_sections = self._identify_company_sections(content)
        
        for section in company_sections:
            company = self._parse_company_section(section, citations)
            if company and self._is_valid_company(company):
                companies.append(company)
        
        # Sort by confidence score
        companies.sort(key=lambda c: c.confidence_score, reverse=True)
        
        return companies[:10]  # Limit to top 10 results
    
    def _identify_company_sections(self, content: str) -> List[str]:
        """Identify sections that contain company information."""
        
        sections = []
        
        # Method 1: Split by numbered lists
        numbered_sections = re.split(r'\n\d+\.\s+', content)
        if len(numbered_sections) > 1:
            sections.extend(numbered_sections[1:])  # Skip first split which is before first number
        
        # Method 2: Split by company indicators
        company_indicators = [
            r'\n\*\*[A-Z][a-zA-Z\s&\-\.]+\*\*',  # Bold company names
            r'\n[A-Z][a-zA-Z\s&\-\.]+:',         # Company names with colons
            r'\n[A-Z][a-zA-Z\s&\-\.]+\s+\(',    # Company names with parentheses
        ]
        
        for pattern in company_indicators:
            matches = re.split(pattern, content)
            if len(matches) > 1:
                sections.extend(matches[1:])
        
        # Method 3: Split by paragraph breaks with company-like content
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if self._looks_like_company_section(para):
                sections.append(para)
        
        # Remove duplicates and empty sections
        unique_sections = []
        for section in sections:
            section = section.strip()
            if section and len(section) > 20 and section not in unique_sections:
                unique_sections.append(section)
        
        return unique_sections
    
    def _looks_like_company_section(self, text: str) -> bool:
        """Check if text looks like it contains company information."""
        
        company_indicators = [
            'founded', 'employees', 'headquarters', 'website', 'funding',
            'startup', 'company', 'business', 'platform', 'service',
            'technology', 'software', 'solution', 'industry'
        ]
        
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in company_indicators if indicator in text_lower)
        
        # Must have at least 2 company indicators and be substantial
        return indicator_count >= 2 and len(text) > 50
    
    def _parse_company_section(self, section: str, citations: List[str]) -> Optional[CompanyMatch]:
        """Parse a single company section into structured data."""
        
        try:
            # Extract company name (usually first prominent text)
            name = self._extract_company_name(section)
            if not name:
                return None
            
            # Extract other fields using patterns
            description = self._extract_description(section, name)
            website = self._extract_field(section, 'website')
            industry = self._extract_field(section, 'industry')
            founding_year = self._extract_founding_year(section)
            headquarters = self._extract_field(section, 'headquarters')
            employee_count = self._extract_field(section, 'employees')
            funding_info = self._extract_field(section, 'funding')
            business_model = self._extract_business_model(section)
            key_products = self._extract_key_products(section)
            
            # Find relevant citations for this company
            company_citations = self._find_relevant_citations(section, name, citations)
            
            # Calculate confidence score
            confidence_score = self._calculate_company_confidence(
                name, description, website, industry, section
            )
            
            return CompanyMatch(
                name=name,
                description=description,
                website=website,
                industry=industry,
                founding_year=founding_year,
                headquarters=headquarters,
                employee_count=employee_count,
                funding_info=funding_info,
                business_model=business_model,
                key_products=key_products,
                confidence_score=confidence_score,
                citations=company_citations
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing company section: {e}")
            return None
    
    def _extract_company_name(self, section: str) -> Optional[str]:
        """Extract company name from section."""
        
        # Pattern 1: Bold text at start
        bold_match = re.search(r'\*\*([A-Z][a-zA-Z\s&\-\.]+?)\*\*', section)
        if bold_match:
            return bold_match.group(1).strip()
        
        # Pattern 2: First capitalized phrase
        first_line = section.split('\n')[0]
        name_match = re.search(r'^([A-Z][a-zA-Z\s&\-\.]+?)(?:\s*[-–—:]|\s*\()', first_line)
        if name_match:
            return name_match.group(1).strip()
        
        # Pattern 3: Capitalized phrase followed by description
        cap_match = re.search(r'^([A-Z][a-zA-Z\s&\-\.]{3,30}?)(?:\s+is\s+|\s+provides\s+|\s+offers\s+)', section)
        if cap_match:
            return cap_match.group(1).strip()
        
        return None
    
    def _extract_description(self, section: str, company_name: str) -> str:
        """Extract company description."""
        
        # Remove company name from section to get description
        section_clean = section.replace(f"**{company_name}**", "").replace(company_name, "", 1)
        
        # Get first substantial sentence
        sentences = re.split(r'[.!?]', section_clean)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and not sentence.startswith(('Founded', 'Website', 'Employees')):
                return sentence + "."
        
        # Fallback: first 200 characters
        return section_clean.strip()[:200] + "..." if len(section_clean) > 200 else section_clean.strip()
    
    def _extract_field(self, section: str, field_type: str) -> Optional[str]:
        """Extract specific field using regex patterns."""
        
        if field_type not in self.company_patterns:
            return None
        
        pattern = self.company_patterns[field_type]
        match = re.search(pattern, section, re.IGNORECASE)
        
        if match:
            # Get the first capture group (the actual value)
            value = match.group(1) if match.groups() else match.group(0)
            return value.strip()
        
        return None
    
    def _extract_founding_year(self, section: str) -> Optional[int]:
        """Extract founding year as integer."""
        
        year_str = self._extract_field(section, 'founding')
        if year_str:
            try:
                year = int(year_str)
                if 1800 <= year <= 2024:  # Reasonable year range
                    return year
            except ValueError:
                pass
        
        return None
    
    def _extract_business_model(self, section: str) -> Optional[str]:
        """Extract business model information."""
        
        business_model_indicators = [
            (r'(B2B|business[-\s]to[-\s]business)', 'B2B'),
            (r'(B2C|business[-\s]to[-\s]consumer)', 'B2C'),
            (r'(SaaS|software[-\s]as[-\s]a[-\s]service)', 'SaaS'),
            (r'(marketplace|platform)', 'Marketplace'),
            (r'(subscription|recurring)', 'Subscription'),
            (r'(freemium)', 'Freemium'),
            (r'(enterprise)', 'Enterprise')
        ]
        
        for pattern, model_type in business_model_indicators:
            if re.search(pattern, section, re.IGNORECASE):
                return model_type
        
        return None
    
    def _extract_key_products(self, section: str) -> List[str]:
        """Extract key products or services."""
        
        products = []
        
        # Look for product/service mentions
        product_patterns = [
            r'(?:products?|services?|solutions?|platforms?):\s*([^.]+)',
            r'(?:offers?|provides?)\s+([^.]+?)(?:\s+to\s+|\s+for\s+|\.)',
            r'specializes?\s+in\s+([^.]+)',
        ]
        
        for pattern in product_patterns:
            matches = re.finditer(pattern, section, re.IGNORECASE)
            for match in matches:
                product_text = match.group(1).strip()
                # Split by commas and clean up
                product_items = [item.strip() for item in product_text.split(',')]
                products.extend(product_items[:3])  # Limit to 3 products per pattern
        
        # Clean and deduplicate
        clean_products = []
        for product in products:
            if len(product) > 5 and len(product) < 100:  # Reasonable length
                clean_products.append(product)
        
        return list(set(clean_products))[:5]  # Max 5 products
    
    def _calculate_company_confidence(
        self, 
        name: str, 
        description: str, 
        website: Optional[str],
        industry: Optional[str],
        full_section: str
    ) -> float:
        """Calculate confidence score for extracted company data."""
        
        score = 0.0
        
        # Base score for having a name
        if name and len(name) > 2:
            score += 0.3
        
        # Bonus for substantial description
        if description and len(description) > 50:
            score += 0.2
        
        # Bonus for having website
        if website:
            score += 0.2
        
        # Bonus for industry information
        if industry:
            score += 0.1
        
        # Bonus for business details (funding, employees, etc.)
        business_indicators = ['founded', 'employees', 'funding', 'headquarters']
        for indicator in business_indicators:
            if indicator in full_section.lower():
                score += 0.05
        
        # Penalty for very short sections (likely incomplete data)
        if len(full_section) < 100:
            score *= 0.7
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _extract_citations(self, response: Dict[str, Any]) -> List[str]:
        """Extract citations from Perplexity response."""
        
        citations = []
        
        # Look for citations in various places
        if 'citations' in response:
            citations.extend(response['citations'])
        
        # Check in choices metadata
        choices = response.get('choices', [])
        for choice in choices:
            if 'citations' in choice:
                citations.extend(choice['citations'])
        
        # Remove duplicates and validate URLs
        unique_citations = []
        for citation in citations:
            if citation not in unique_citations and self._is_valid_url(citation):
                unique_citations.append(citation)
        
        return unique_citations
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _find_relevant_citations(
        self, 
        section: str, 
        company_name: str, 
        all_citations: List[str]
    ) -> List[str]:
        """Find citations relevant to this specific company."""
        
        relevant = []
        
        for citation in all_citations:
            # Simple heuristic: if citation domain contains company name
            try:
                domain = urlparse(citation).netloc.lower()
                company_lower = company_name.lower().replace(' ', '')
                if company_lower in domain or any(word in domain for word in company_lower.split()):
                    relevant.append(citation)
            except:
                continue
        
        return relevant[:3]  # Limit to 3 most relevant
    
    def _extract_market_insights(self, content: str) -> Optional[str]:
        """Extract market-level insights from content."""
        
        insight_indicators = [
            'market trend', 'industry trend', 'market size', 'growth rate',
            'competitive landscape', 'market opportunity', 'industry analysis'
        ]
        
        for indicator in insight_indicators:
            pattern = rf'([^.]*{re.escape(indicator)}[^.]*\.)'
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_trend_analysis(self, content: str) -> Optional[str]:
        """Extract trend analysis from content."""
        
        trend_patterns = [
            r'(trends?\s+(?:show|indicate|suggest)[^.]+\.)',
            r'((?:growing|emerging|declining)\s+trend[^.]+\.)',
            r'(market\s+is\s+(?:expanding|growing|shifting)[^.]+\.)'
        ]
        
        for pattern in trend_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _generate_search_summary(self, content: str, company_count: int) -> str:
        """Generate a summary of the search results."""
        
        # Extract first substantial paragraph as summary
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 100 and not para.startswith(('1.', '2.', '3.')):
                summary = para[:300] + "..." if len(para) > 300 else para
                return f"Found {company_count} companies. {summary}"
        
        return f"Found {company_count} similar companies based on the search criteria."
    
    def _calculate_overall_confidence(self, companies: List[CompanyMatch], content: str) -> float:
        """Calculate overall confidence in the search results."""
        
        if not companies:
            return 0.0
        
        # Average company confidence scores
        avg_company_confidence = sum(c.confidence_score for c in companies) / len(companies)
        
        # Bonus for content quality
        content_quality = min(len(content) / 1000, 1.0)  # Longer content generally better
        
        # Bonus for having multiple companies
        diversity_bonus = min(len(companies) / 5, 0.2)  # Up to 0.2 bonus for 5+ companies
        
        overall_score = (avg_company_confidence * 0.7) + (content_quality * 0.2) + diversity_bonus
        
        return min(overall_score, 1.0)
    
    def _is_valid_company(self, company: CompanyMatch) -> bool:
        """Check if extracted company data is valid."""
        
        # Must have name and description
        if not company.name or not company.description:
            return False
        
        # Name must be reasonable length
        if len(company.name) < 2 or len(company.name) > 100:
            return False
        
        # Description must be substantial
        if len(company.description) < 20:
            return False
        
        # Confidence must be above minimum threshold
        if company.confidence_score < 0.3:
            return False
        
        return True
    
    def _empty_result(self) -> ParsedSearchResult:
        """Return empty result for error cases."""
        return ParsedSearchResult(
            companies=[],
            search_summary="No companies found due to parsing error.",
            total_companies_found=0,
            confidence_score=0.0
        )
```

This parser extracts rich business intelligence from unstructured AI responses!"

## Section 4: Implementing the Complete Adapter with Caching (10 minutes)

**[SLIDE 9: Complete Perplexity Adapter Implementation]**

"Now let's bring everything together in the main adapter with intelligent caching:

```python
# v2/src/infrastructure/adapters/mcp/perplexity/adapter.py
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional, List
from src.core.interfaces.mcp_search import MCPSearchToolPort, MCPSearchParams, MCPSearchResult, MCPToolInfo
from .client import PerplexityClient, PerplexityAPIError
from .config import PerplexityConfig
from .query_builder import PerplexityQueryBuilder
from .result_parser import PerplexityResultParser, CompanyMatch
import logging

class PerplexityAdapter(MCPSearchToolPort):
    """Production-ready Perplexity adapter with intelligent caching and error handling."""
    
    def __init__(self, config: PerplexityConfig, cache_store: Optional[Any] = None):
        self.config = config
        self.client = PerplexityClient(config)
        self.query_builder = PerplexityQueryBuilder(config)
        self.result_parser = PerplexityResultParser()
        self.cache_store = cache_store  # Redis, in-memory, etc.
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.request_count = 0
        self.cache_hits = 0
        self.total_response_time = 0.0
        
    async def search_similar_companies(
        self, 
        company_name: str,
        search_params: MCPSearchParams
    ) -> MCPSearchResult:
        """Search for companies similar to the given company using Perplexity AI."""
        
        start_time = time.time()
        
        try:
            # Build optimized search query
            query = self.query_builder.build_similarity_query(company_name, search_params)
            
            # Check cache first
            cached_result = await self._get_cached_result(query, search_params)
            if cached_result:
                self.cache_hits += 1
                self.logger.info(f"Cache hit for query: {company_name}")
                return cached_result
            
            # Execute search with Perplexity
            search_response = await self._execute_search(query, search_params)
            
            # Parse results into structured format
            parsed_result = self.result_parser.parse_search_response(search_response)
            
            # Convert to MCP format
            mcp_result = self._convert_to_mcp_result(parsed_result, search_params)
            
            # Cache the result
            await self._cache_result(query, search_params, mcp_result)
            
            # Update performance metrics
            self.request_count += 1
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            self.logger.info(
                f"Perplexity search completed: company={company_name}, "
                f"found={len(mcp_result.companies)}, time={response_time:.2f}s, "
                f"confidence={mcp_result.confidence_score:.2f}"
            )
            
            return mcp_result
            
        except PerplexityAPIError as e:
            self.logger.error(f"Perplexity API error for {company_name}: {e}")
            return self._create_error_result(f"Search failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error searching for {company_name}: {e}")
            return self._create_error_result(f"Search failed due to unexpected error: {e}")
    
    async def _execute_search(
        self, 
        query: str, 
        search_params: MCPSearchParams
    ) -> Dict[str, Any]:
        """Execute search with appropriate model selection and options."""
        
        # Select optimal model based on search complexity
        model = self._select_optimal_model(query, search_params)
        
        # Build search options
        search_options = {
            "max_tokens": self._calculate_max_tokens(search_params),
            "temperature": 0.1,  # Low for factual searches
            "search_domain_filter": self._get_domain_filters(search_params),
            "return_citations": True
        }
        
        # Add freshness filter if specified
        if search_params.recency_filter:
            search_options["search_recency_filter"] = search_params.recency_filter
        
        async with self.client:
            response = await self.client.search(
                query=query,
                model=model,
                search_options=search_options
            )
        
        return response
    
    def _select_optimal_model(
        self, 
        query: str, 
        search_params: MCPSearchParams
    ) -> 'PerplexityModel':
        """Select the optimal model based on query complexity and requirements."""
        
        from .client import PerplexityModel
        
        # Factors for model selection
        query_complexity = len(query.split())
        requires_deep_analysis = (
            search_params.require_detailed_analysis or
            search_params.include_financial_data or
            search_params.include_market_trends
        )
        
        # Decision logic
        if requires_deep_analysis or query_complexity > 30:
            return PerplexityModel.SONAR_LARGE
        elif query_complexity > 15 or search_params.max_results > 5:
            return PerplexityModel.SONAR_MEDIUM
        else:
            return PerplexityModel.SONAR_SMALL
    
    def _calculate_max_tokens(self, search_params: MCPSearchParams) -> int:
        """Calculate appropriate max tokens based on search requirements."""
        
        base_tokens = 1000
        
        if search_params.require_detailed_analysis:
            base_tokens += 1500
        if search_params.include_financial_data:
            base_tokens += 500
        if search_params.max_results > 5:
            base_tokens += (search_params.max_results - 5) * 200
        
        return min(base_tokens, 4000)  # Cap at reasonable limit
    
    def _get_domain_filters(self, search_params: MCPSearchParams) -> List[str]:
        """Get domain filters for more focused searches."""
        
        filters = []
        
        if search_params.focus_on_news:
            filters.extend([
                "techcrunch.com", "venturebeat.com", "reuters.com", 
                "bloomberg.com", "wsj.com"
            ])
        
        if search_params.focus_on_business:
            filters.extend([
                "crunchbase.com", "pitchbook.com", "forbes.com",
                "inc.com", "fastcompany.com"
            ])
        
        return filters
    
    def _convert_to_mcp_result(
        self, 
        parsed_result: 'ParsedSearchResult', 
        search_params: MCPSearchParams
    ) -> MCPSearchResult:
        """Convert parsed result to MCP standard format."""
        
        from src.core.interfaces.mcp_search import MCPCompany
        
        # Convert companies to MCP format
        mcp_companies = []
        for company in parsed_result.companies:
            mcp_company = MCPCompany(
                name=company.name,
                description=company.description,
                website=company.website,
                industry=company.industry,
                confidence_score=company.confidence_score,
                metadata={
                    'founding_year': company.founding_year,
                    'headquarters': company.headquarters,
                    'employee_count': company.employee_count,
                    'funding_info': company.funding_info,
                    'business_model': company.business_model,
                    'key_products': company.key_products,
                    'citations': company.citations
                }
            )
            mcp_companies.append(mcp_company)
        
        # Create MCP result
        return MCPSearchResult(
            tool_name="perplexity",
            tool_version="1.0",
            companies=mcp_companies,
            search_summary=parsed_result.search_summary,
            confidence_score=parsed_result.confidence_score,
            metadata={
                'total_found': parsed_result.total_companies_found,
                'market_insights': parsed_result.market_insights,
                'trend_analysis': parsed_result.trend_analysis,
                'citations': parsed_result.citations,
                'search_model': self.config.default_model.value,
                'search_depth': self.config.search_depth.value
            }
        )
    
    async def _get_cached_result(
        self, 
        query: str, 
        search_params: MCPSearchParams
    ) -> Optional[MCPSearchResult]:
        """Retrieve cached result if available and valid."""
        
        if not self.config.enable_caching or not self.cache_store:
            return None
        
        try:
            cache_key = self._generate_cache_key(query, search_params)
            
            if hasattr(self.cache_store, 'get'):
                # Redis-like interface
                cached_data = await self.cache_store.get(cache_key)
            else:
                # Simple dict-like interface
                cached_data = self.cache_store.get(cache_key)
            
            if cached_data:
                if isinstance(cached_data, str):
                    cached_data = json.loads(cached_data)
                
                # Check if cache is still valid
                cache_time = cached_data.get('cached_at', 0)
                if time.time() - cache_time < self.config.cache_ttl_seconds:
                    result_data = cached_data.get('result')
                    if result_data:
                        return MCPSearchResult.from_dict(result_data)
            
        except Exception as e:
            self.logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_result(
        self, 
        query: str, 
        search_params: MCPSearchParams, 
        result: MCPSearchResult
    ):
        """Cache search result for future use."""
        
        if not self.config.enable_caching or not self.cache_store:
            return
        
        try:
            cache_key = self._generate_cache_key(query, search_params)
            cache_data = {
                'cached_at': time.time(),
                'result': result.to_dict()
            }
            
            if hasattr(self.cache_store, 'setex'):
                # Redis-like interface with TTL
                await self.cache_store.setex(
                    cache_key, 
                    self.config.cache_ttl_seconds,
                    json.dumps(cache_data)
                )
            else:
                # Simple dict-like interface
                self.cache_store[cache_key] = cache_data
            
        except Exception as e:
            self.logger.warning(f"Cache storage error: {e}")
    
    def _generate_cache_key(self, query: str, search_params: MCPSearchParams) -> str:
        """Generate unique cache key for query and parameters."""
        
        # Combine query and relevant parameters
        key_components = [
            query,
            str(search_params.max_results),
            str(search_params.include_recent_news),
            str(search_params.require_detailed_analysis),
            search_params.region or "",
            search_params.industry or "",
            search_params.recency_filter or ""
        ]
        
        key_string = "|".join(key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.config.cache_key_prefix}:{key_hash}"
    
    def _create_error_result(self, error_message: str) -> MCPSearchResult:
        """Create error result for failed searches."""
        
        return MCPSearchResult(
            tool_name="perplexity",
            tool_version="1.0",
            companies=[],
            search_summary=f"Search failed: {error_message}",
            confidence_score=0.0,
            metadata={
                'error': error_message,
                'timestamp': time.time()
            }
        )
    
    def get_tool_info(self) -> MCPToolInfo:
        """Get information about this search tool."""
        
        return MCPToolInfo(
            name="perplexity",
            version="1.0",
            description="Advanced AI-powered search using Perplexity's real-time web intelligence",
            capabilities=[
                "real_time_search",
                "contextual_analysis", 
                "citation_tracking",
                "multi_model_support",
                "intelligent_caching"
            ],
            supported_search_types=[
                "company_similarity",
                "market_analysis",
                "competitive_intelligence",
                "trend_analysis"
            ],
            rate_limits={
                "requests_per_minute": self.config.rate_limit_requests_per_minute,
                "daily_limit": self.config.rate_limit_requests_per_minute * 24 * 60
            },
            cost_model="per_request",
            metadata={
                "models_available": [model.value for model in PerplexityModel],
                "max_results": self.config.max_results,
                "caching_enabled": self.config.enable_caching,
                "cache_ttl": self.config.cache_ttl_seconds
            }
        )
    
    async def health_check(self) -> bool:
        """Check if Perplexity search tool is available and working."""
        
        try:
            async with self.client:
                return await self.client.health_check()
        except Exception as e:
            self.logger.warning(f"Perplexity health check failed: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0.0
        )
        
        cache_hit_rate = (
            self.cache_hits / (self.request_count + self.cache_hits)
            if (self.request_count + self.cache_hits) > 0 else 0.0
        )
        
        return {
            'total_requests': self.request_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'avg_response_time': avg_response_time,
            'health_status': await self.health_check(),
            'rate_limit_status': await self.client.get_usage_stats() if hasattr(self.client, 'get_usage_stats') else {}
        }
    
    async def clear_cache(self) -> bool:
        """Clear cached search results."""
        
        if not self.cache_store:
            return True
        
        try:
            if hasattr(self.cache_store, 'flushdb'):
                # Redis-like interface
                await self.cache_store.flushdb()
            elif hasattr(self.cache_store, 'clear'):
                # Dict-like interface
                self.cache_store.clear()
            
            self.cache_hits = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Cache clear failed: {e}")
            return False
```

This adapter provides enterprise-grade functionality with intelligent caching and monitoring!"

## Section 5: Comprehensive Testing and Production Setup (8 minutes)

**[SLIDE 10: Comprehensive Testing Strategy]**

"Let's create a thorough testing suite that validates all functionality:

```python
# v2/tests/unit/adapters/mcp/test_perplexity_adapter.py
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from src.infrastructure.adapters.mcp.perplexity.adapter import PerplexityAdapter
from src.infrastructure.adapters.mcp.perplexity.config import PerplexityConfig
from src.core.interfaces.mcp_search import MCPSearchParams

class TestPerplexityAdapter:
    """Comprehensive tests for Perplexity adapter."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return PerplexityConfig(
            api_key="test-key",
            rate_limit_requests_per_minute=20,
            enable_caching=True,
            cache_ttl_seconds=3600
        )
    
    @pytest.fixture
    def mock_cache(self):
        """Mock cache store."""
        return {}
    
    @pytest.fixture
    def adapter(self, config, mock_cache):
        """Create adapter with mocked dependencies."""
        return PerplexityAdapter(config, mock_cache)
    
    @pytest.mark.asyncio
    async def test_successful_company_search(self, adapter):
        """Test successful company similarity search."""
        
        # Mock Perplexity API response
        mock_response = {
            'choices': [{
                'message': {
                    'content': '''Here are companies similar to Stripe:

1. **Square** - A financial services company that provides payment processing and point-of-sale solutions. Founded in 2009, Square offers a comprehensive ecosystem for businesses to accept payments.

2. **Adyen** - A Dutch payment company that provides payment solutions for businesses. Founded in 2006, Adyen serves major companies like Uber, Netflix, and Spotify.

3. **PayPal** - A well-established digital payments platform. Founded in 1998, PayPal enables online money transfers and serves as an electronic alternative to traditional paper methods.'''
                }
            }],
            'citations': [
                'https://square.com',
                'https://adyen.com', 
                'https://paypal.com'
            ]
        }
        
        # Mock the client
        with patch.object(adapter.client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_response
            
            # Execute search
            search_params = MCPSearchParams(
                max_results=5,
                include_recent_news=False,
                require_detailed_analysis=True
            )
            
            result = await adapter.search_similar_companies("Stripe", search_params)
            
            # Verify request was made correctly
            mock_search.assert_called_once()
            
            # Verify result structure
            assert result.tool_name == "perplexity"
            assert result.tool_version == "1.0"
            assert len(result.companies) == 3
            assert result.confidence_score > 0.0
            
            # Verify company data
            companies = {c.name: c for c in result.companies}
            assert "Square" in companies
            assert "Adyen" in companies
            assert "PayPal" in companies
            
            # Verify company details
            square = companies["Square"]
            assert "financial services" in square.description.lower()
            assert square.confidence_score > 0.0
            
            # Verify metadata
            assert 'total_found' in result.metadata
            assert 'citations' in result.metadata
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, adapter, mock_cache):
        """Test that caching works correctly."""
        
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Test company: **TestCorp** - A test company for caching.'
                }
            }],
            'citations': []
        }
        
        with patch.object(adapter.client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_response
            
            search_params = MCPSearchParams(max_results=5)
            
            # First search - should hit API
            result1 = await adapter.search_similar_companies("TestCorp", search_params)
            assert mock_search.call_count == 1
            
            # Second search - should hit cache
            result2 = await adapter.search_similar_companies("TestCorp", search_params)
            assert mock_search.call_count == 1  # No additional API call
            assert adapter.cache_hits == 1
            
            # Results should be identical
            assert result1.companies[0].name == result2.companies[0].name
    
    @pytest.mark.asyncio
    async def test_error_handling(self, adapter):
        """Test error handling for API failures."""
        
        with patch.object(adapter.client, 'search', new_callable=AsyncMock) as mock_search:
            # Mock API error
            from src.infrastructure.adapters.mcp.perplexity.client import PerplexityAPIError
            mock_search.side_effect = PerplexityAPIError("Rate limit exceeded", 429)
            
            search_params = MCPSearchParams(max_results=5)
            result = await adapter.search_similar_companies("TestCorp", search_params)
            
            # Should return error result instead of raising
            assert result.tool_name == "perplexity"
            assert len(result.companies) == 0
            assert result.confidence_score == 0.0
            assert "Search failed" in result.search_summary
            assert "error" in result.metadata
    
    @pytest.mark.asyncio
    async def test_model_selection(self, adapter):
        """Test automatic model selection based on query complexity."""
        
        mock_response = {
            'choices': [{'message': {'content': 'Test response'}}],
            'citations': []
        }
        
        with patch.object(adapter.client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_response
            
            # Simple search should use small model
            simple_params = MCPSearchParams(max_results=3)
            await adapter.search_similar_companies("Simple Corp", simple_params)
            
            # Complex search should use larger model
            complex_params = MCPSearchParams(
                max_results=10,
                require_detailed_analysis=True,
                include_financial_data=True
            )
            await adapter.search_similar_companies("Complex Corporation Name", complex_params)
            
            # Verify different models were selected
            calls = mock_search.call_args_list
            assert len(calls) == 2
            
            # The complex search should have higher max_tokens
            simple_options = calls[0][1]['search_options']
            complex_options = calls[1][1]['search_options']
            assert complex_options['max_tokens'] > simple_options['max_tokens']
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check functionality."""
        
        with patch.object(adapter.client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            
            is_healthy = await adapter.health_check()
            assert is_healthy is True
            
            mock_health.return_value = False
            is_healthy = await adapter.health_check()
            assert is_healthy is False
    
    def test_tool_info(self, adapter):
        """Test tool information metadata."""
        
        tool_info = adapter.get_tool_info()
        
        assert tool_info.name == "perplexity"
        assert tool_info.version == "1.0"
        assert "real_time_search" in tool_info.capabilities
        assert "company_similarity" in tool_info.supported_search_types
        assert tool_info.rate_limits["requests_per_minute"] == 20
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, adapter):
        """Test performance metrics tracking."""
        
        # Initial metrics
        metrics = await adapter.get_performance_metrics()
        assert metrics['total_requests'] == 0
        assert metrics['cache_hits'] == 0
        assert metrics['cache_hit_rate'] == 0.0
        
        # Simulate some requests
        adapter.request_count = 10
        adapter.cache_hits = 3
        adapter.total_response_time = 25.0
        
        metrics = await adapter.get_performance_metrics()
        assert metrics['total_requests'] == 10
        assert metrics['cache_hits'] == 3
        assert metrics['cache_hit_rate'] == 0.23  # 3/(10+3)
        assert metrics['avg_response_time'] == 2.5  # 25/10

class TestPerplexityQueryBuilder:
    """Test query building functionality."""
    
    @pytest.fixture
    def config(self):
        return PerplexityConfig(api_key="test")
    
    @pytest.fixture
    def query_builder(self, config):
        from src.infrastructure.adapters.mcp.perplexity.query_builder import PerplexityQueryBuilder
        return PerplexityQueryBuilder(config)
    
    def test_basic_similarity_query(self, query_builder):
        """Test building basic similarity query."""
        
        search_params = MCPSearchParams(max_results=5)
        query = query_builder.build_similarity_query("Stripe", search_params)
        
        assert "Stripe" in query
        assert "similar" in query.lower()
    
    def test_complex_query_with_filters(self, query_builder):
        """Test building complex query with multiple filters."""
        
        search_params = MCPSearchParams(
            max_results=10,
            industry="fintech",
            region="North America",
            company_size="startup",
            business_model="B2B"
        )
        
        query = query_builder.build_similarity_query("Stripe", search_params)
        
        assert "Stripe" in query
        assert "fintech" in query.lower()
        assert "North America" in query
        assert "startup" in query.lower()
        assert "B2B" in query
    
    def test_market_analysis_query(self, query_builder):
        """Test building market analysis queries."""
        
        query = query_builder.build_market_analysis_query("Stripe", "competitive_landscape")
        assert "Stripe" in query
        assert "competitive" in query.lower()
        assert "landscape" in query.lower()
        
        query = query_builder.build_market_analysis_query("Stripe", "growth_trends")
        assert "growth" in query.lower()
        assert "trends" in query.lower()

class TestPerplexityResultParser:
    """Test result parsing functionality."""
    
    @pytest.fixture
    def parser(self):
        from src.infrastructure.adapters.mcp.perplexity.result_parser import PerplexityResultParser
        return PerplexityResultParser()
    
    def test_company_extraction(self, parser):
        """Test extracting companies from response text."""
        
        mock_response = {
            'choices': [{
                'message': {
                    'content': '''Here are similar companies:

1. **Square Inc.** - A financial services company providing payment processing solutions. Founded in 2009, Square has grown to serve millions of businesses worldwide.

2. **Adyen N.V.** - A Dutch payment company founded in 2006. Adyen provides payment solutions for major enterprises including Uber and Netflix.'''
                }
            }],
            'citations': ['https://square.com', 'https://adyen.com']
        }
        
        result = parser.parse_search_response(mock_response)
        
        assert len(result.companies) == 2
        assert result.companies[0].name in ["Square Inc.", "Square"]
        assert result.companies[1].name in ["Adyen N.V.", "Adyen"]
        assert result.total_companies_found == 2
        assert result.confidence_score > 0.0
    
    def test_citation_extraction(self, parser):
        """Test extracting citations from response."""
        
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Test content'
                }
            }],
            'citations': ['https://example.com', 'https://test.com']
        }
        
        result = parser.parse_search_response(mock_response)
        assert len(result.citations) == 2
        assert 'https://example.com' in result.citations
    
    def test_empty_response_handling(self, parser):
        """Test handling empty or invalid responses."""
        
        empty_response = {'choices': []}
        result = parser.parse_search_response(empty_response)
        
        assert len(result.companies) == 0
        assert result.total_companies_found == 0
        assert result.confidence_score == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

This test suite provides comprehensive coverage of all adapter functionality!"

**[SLIDE 11: Integration Tests and Performance Benchmarks]**

"Finally, let's create integration tests that validate real-world performance:

```python
# v2/tests/integration/adapters/mcp/test_perplexity_integration.py
import pytest
import asyncio
import os
import time
from src.infrastructure.adapters.mcp.perplexity.adapter import PerplexityAdapter
from src.infrastructure.adapters.mcp.perplexity.config import PerplexityConfig
from src.core.interfaces.mcp_search import MCPSearchParams

class TestPerplexityIntegration:
    """Integration tests with real Perplexity API."""
    
    @pytest.fixture
    def real_config(self):
        """Real Perplexity configuration from environment."""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key:
            pytest.skip("PERPLEXITY_API_KEY not available for integration testing")
        
        return PerplexityConfig.from_environment()
    
    @pytest.fixture
    def adapter(self, real_config):
        """Real Perplexity adapter for integration testing."""
        return PerplexityAdapter(real_config)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_company_search(self, adapter):
        """Test real company search with Perplexity API."""
        
        search_params = MCPSearchParams(
            max_results=5,
            require_detailed_analysis=True,
            include_recent_news=False  # Avoid rate limiting
        )
        
        result = await adapter.search_similar_companies("Stripe", search_params)
        
        # Verify successful response
        assert result.tool_name == "perplexity"
        assert len(result.companies) > 0
        assert result.confidence_score > 0.0
        
        # Verify at least one company has good data
        best_company = max(result.companies, key=lambda c: c.confidence_score)
        assert best_company.name is not None
        assert len(best_company.description) > 20
        assert best_company.confidence_score > 0.3
        
        # Verify business intelligence quality
        descriptions = [c.description.lower() for c in result.companies]
        business_terms = ['payment', 'financial', 'fintech', 'commerce', 'transaction']
        assert any(term in " ".join(descriptions) for term in business_terms)
        
        print(f"✅ Found {len(result.companies)} companies with {result.confidence_score:.2f} confidence")
        for company in result.companies[:3]:
            print(f"  - {company.name}: {company.confidence_score:.2f}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_performance(self, adapter):
        """Test search performance and response times."""
        
        search_params = MCPSearchParams(max_results=3)
        
        # Test multiple companies for performance baseline
        test_companies = ["Airbnb", "Uber", "Zoom"]
        results = []
        
        for company in test_companies:
            start_time = time.time()
            result = await adapter.search_similar_companies(company, search_params)
            response_time = time.time() - start_time
            
            results.append({
                'company': company,
                'response_time': response_time,
                'companies_found': len(result.companies),
                'confidence': result.confidence_score
            })
            
            # Add delay to respect rate limits
            await asyncio.sleep(5)
        
        # Analyze performance
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        avg_companies_found = sum(r['companies_found'] for r in results) / len(results)
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        
        print(f"\\n📊 Performance Results:")
        print(f"  Average response time: {avg_response_time:.2f}s")
        print(f"  Average companies found: {avg_companies_found:.1f}")
        print(f"  Average confidence: {avg_confidence:.2f}")
        
        # Performance assertions
        assert avg_response_time < 15.0  # Should respond within 15 seconds
        assert avg_companies_found >= 2   # Should find at least 2 similar companies
        assert avg_confidence > 0.4       # Should have reasonable confidence
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_different_search_complexities(self, adapter):
        """Test different search complexity levels."""
        
        # Simple search
        simple_params = MCPSearchParams(max_results=3)
        simple_result = await adapter.search_similar_companies("Tesla", simple_params)
        
        await asyncio.sleep(3)  # Rate limiting
        
        # Complex search
        complex_params = MCPSearchParams(
            max_results=8,
            require_detailed_analysis=True,
            include_financial_data=True,
            industry="automotive",
            region="global"
        )
        complex_result = await adapter.search_similar_companies("Tesla", complex_params)
        
        # Complex search should potentially return more or better results
        assert len(complex_result.companies) >= len(simple_result.companies)
        
        # Complex search should have more detailed metadata
        assert 'market_insights' in complex_result.metadata
        
        print(f"✅ Simple search: {len(simple_result.companies)} companies")
        print(f"✅ Complex search: {len(complex_result.companies)} companies")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_and_monitoring(self, adapter):
        """Test health check and monitoring features."""
        
        # Health check
        is_healthy = await adapter.health_check()
        assert is_healthy is True
        
        # Performance metrics (after running some searches)
        metrics = await adapter.get_performance_metrics()
        assert 'health_status' in metrics
        assert 'total_requests' in metrics
        assert metrics['health_status'] is True
        
        print("✅ Health check and monitoring working correctly")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_resilience(self, adapter):
        """Test error handling with edge cases."""
        
        # Test with very vague query
        vague_params = MCPSearchParams(max_results=5)
        vague_result = await adapter.search_similar_companies("X", vague_params)
        
        # Should handle gracefully, even if results are poor
        assert vague_result.tool_name == "perplexity"
        assert isinstance(vague_result.companies, list)
        
        # Test with complex but nonsensical query
        nonsense_result = await adapter.search_similar_companies(
            "XYZ Quantum Blockchain AI Unicorn Corp", 
            vague_params
        )
        
        # Should still return a valid result structure
        assert nonsense_result.tool_name == "perplexity"
        
        print("✅ Error resilience tests passed")

# Performance benchmark for cost and speed analysis
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_perplexity_benchmark():
    """Comprehensive benchmark of Perplexity adapter."""
    
    config = PerplexityConfig.from_environment()
    if not config.api_key:
        pytest.skip("PERPLEXITY_API_KEY required for benchmark")
    
    adapter = PerplexityAdapter(config)
    
    # Benchmark different query types
    test_scenarios = [
        {
            'name': 'Quick Lookup',
            'company': 'Spotify',
            'params': MCPSearchParams(max_results=3),
            'expected_time': 10.0
        },
        {
            'name': 'Detailed Analysis', 
            'company': 'Netflix',
            'params': MCPSearchParams(
                max_results=7,
                require_detailed_analysis=True,
                include_financial_data=True
            ),
            'expected_time': 20.0
        },
        {
            'name': 'Market Research',
            'company': 'Slack',
            'params': MCPSearchParams(
                max_results=10,
                require_detailed_analysis=True,
                include_market_trends=True,
                industry="SaaS"
            ),
            'expected_time': 25.0
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        start_time = time.time()
        result = await adapter.search_similar_companies(
            scenario['company'], 
            scenario['params']
        )
        response_time = time.time() - start_time
        
        scenario_result = {
            'scenario': scenario['name'],
            'company': scenario['company'],
            'response_time': response_time,
            'expected_time': scenario['expected_time'],
            'companies_found': len(result.companies),
            'confidence': result.confidence_score,
            'within_expected': response_time <= scenario['expected_time']
        }
        results.append(scenario_result)
        
        # Rate limiting
        await asyncio.sleep(6)
    
    # Print benchmark results
    print("\\n📊 Perplexity Adapter Benchmark Results:")
    print("=" * 60)
    for result in results:
        status = "✅" if result['within_expected'] else "⚠️"
        print(f"{status} {result['scenario']}:")
        print(f"    Company: {result['company']}")
        print(f"    Response Time: {result['response_time']:.2f}s (expected: {result['expected_time']:.1f}s)")
        print(f"    Companies Found: {result['companies_found']}")
        print(f"    Confidence: {result['confidence']:.2f}")
        print()
    
    # Overall benchmark assessment
    avg_response_time = sum(r['response_time'] for r in results) / len(results)
    success_rate = sum(1 for r in results if r['within_expected']) / len(results)
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    
    print(f"📈 Overall Performance:")
    print(f"    Average Response Time: {avg_response_time:.2f}s")
    print(f"    Success Rate: {success_rate:.1%}")
    print(f"    Average Confidence: {avg_confidence:.2f}")
    
    # Performance assertions
    assert avg_response_time < 20.0  # Overall average should be reasonable
    assert success_rate >= 0.8       # At least 80% should meet expectations
    assert avg_confidence > 0.5      # Results should be reasonably confident

if __name__ == "__main__":
    # Run integration tests with real API
    pytest.main([
        __file__,
        "-v", 
        "-m", "integration",
        "--tb=short",
        "-s"  # Show print outputs
    ])
```

These integration tests validate real-world performance and reliability!"

## Conclusion and Best Practices (3 minutes)

**[SLIDE 12: Production Deployment and Best Practices]**

"Congratulations! You've built a sophisticated Perplexity AI adapter that demonstrates the future of intelligent search. Let's review what you've accomplished:

🏗️ **Enterprise Architecture:**
- Clean MCP port/adapter pattern for maximum flexibility
- Intelligent query building with context optimization
- Advanced result parsing with business intelligence extraction
- Production-grade caching and rate limiting

🧠 **AI-Powered Intelligence:**
- Real-time web search with citation tracking
- Multi-model support optimized for query complexity
- Natural language to structured data transformation
- Confidence scoring and quality assessment

⚡ **Performance & Reliability:**
- Smart caching reduces API costs and improves speed
- Exponential backoff with jitter for resilient error handling
- Comprehensive monitoring and health checks
- Batch-optimized operations for high throughput

🔧 **Production Ready:**
- Environment-based configuration management
- Comprehensive test coverage (unit + integration + performance)
- Detailed logging and monitoring capabilities
- Cost optimization and usage tracking

**Production Deployment Checklist:**
1. **Set up API credentials** - Store Perplexity API key securely
2. **Configure rate limits** - Match your API plan and usage patterns
3. **Set up caching** - Redis recommended for production scale
4. **Monitor performance** - Track response times, success rates, confidence scores
5. **Implement alerts** - Monitor for API failures and performance degradation
6. **Cost management** - Track API usage and implement budgets

**Next Steps for Your AI Search Projects:**
1. **Implement other MCP adapters** - Tavily, Google, Bing using same pattern
2. **Build search orchestration** - Combine multiple tools for better coverage
3. **Add semantic ranking** - Use embeddings to improve result relevance
4. **Create search analytics** - Track query patterns and result quality
5. **Build adaptive intelligence** - Learn from user feedback to improve results

This Perplexity adapter showcases how to build production-grade AI search systems that provide real business value. You now have the foundation to create intelligent applications that can understand context, find relevant information, and provide actionable business insights!

Thank you for joining this comprehensive tutorial. Now go build amazing AI-powered search experiences!"

---

**Total Tutorial Time: Approximately 75 minutes**

**Key Takeaways:**
- Perplexity AI provides real-time search with business intelligence
- MCP architecture enables pluggable search tool ecosystems
- Advanced parsing converts unstructured AI responses to structured business data
- Production systems require comprehensive caching, monitoring, and error handling
- Integration testing validates real-world performance and reliability