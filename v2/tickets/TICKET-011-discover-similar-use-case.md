# TICKET-011: Discover Similar Companies Use Case

## Overview
Implement the DiscoverSimilarCompanies use case that finds similar companies using vector search and/or Google Search.

## Acceptance Criteria
- [ ] Check if company exists in database
- [ ] If exists: use vector similarity search
- [ ] If not exists: use Google Search discovery
- [ ] Combine results from multiple sources
- [ ] Score and rank results
- [ ] Support filtering by business model, size, etc.

## Technical Details
- Implement hybrid search strategy with MCP tools
- Check MCP tool registry for enabled search droids
- Use MCP tools as primary search method
- Fall back to Google Search if no MCP tools available
- Use LLM to generate tool-specific queries
- Run multiple MCP tools in parallel
- Aggregate and deduplicate results across sources
- Calculate confidence scores with tool attribution
- Return structured similarity results with source tracking

## Testing
- Test with company in database
- Test with unknown company
- Test search query generation
- Test result ranking logic
- Integration test with real data:
  - "Salesforce" (known company)
  - "Lobsters & Mobsters" (unknown restaurant)

## Estimated Time: 3-4 hours

## Dependencies
- TICKET-005: MCP Search Droid Port (for pluggable search tools)
- TICKET-008: AI Provider Port (for query generation)
- TICKET-009: Vector Storage Port (for similarity search)
- TICKET-004: Progress Tracking Port (for discovery progress)
- TICKET-001: Core Domain Models (for similarity entities)

## Files to Create
- `v2/src/core/use_cases/discover_similar.py`
- `v2/src/core/domain/value_objects/similarity_result.py`
- `v2/src/core/domain/services/similarity_scorer.py`
- `v2/tests/unit/use_cases/test_discover_similar.py`
- `v2/tests/integration/test_discovery_flow.py`

---

# Udemy Tutorial Script: Building Intelligent Company Discovery with Hybrid Search

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Intelligent Company Discovery with Hybrid AI Search"]**

"Welcome to this advanced tutorial on building intelligent company discovery systems! Today we're going to create a sophisticated use case that combines vector similarity search with MCP-powered web search to find companies similar to any given company - whether it's already in our database or completely unknown.

By the end of this tutorial, you'll understand how to build hybrid search systems that leverage both semantic similarity and real-time web discovery, orchestrate multiple search tools in parallel, implement intelligent scoring algorithms, and create discovery experiences that feel like magic to your users.

This is the kind of AI-powered discovery that makes your applications stand out from the crowd!"

## Section 1: Understanding Hybrid Search Architecture (5 minutes)

**[SLIDE 2: The Discovery Challenge]**

"Let's start by understanding why company discovery is complex. Look at this naive approach:

```python
# ❌ The NAIVE approach - limited and brittle
def find_similar_companies(company_name):
    # Only database search
    results = database.similarity_search(company_name)
    return results[:10]

# Problems:
# 1. Only works for companies already in database
# 2. No web discovery for unknown companies
# 3. No hybrid scoring across sources
# 4. No real-time market intelligence
# 5. Limited to existing knowledge
```

This approach leaves huge gaps in discovery capabilities!"

**[SLIDE 3: Real-World Discovery Complexity]**

"Here's what we're actually dealing with in production:

```python
# Real discovery scenarios:
discovery_scenarios = [
    {
        "company": "Salesforce",
        "in_database": True,
        "strategy": "Vector similarity + web validation",
        "sources": ["database", "mcp_tools", "google_search"],
        "expected_results": 50
    },
    {
        "company": "New AI Startup XYZ",
        "in_database": False,
        "strategy": "Web discovery + competitor analysis", 
        "sources": ["mcp_tools", "google_search", "real_time_web"],
        "expected_results": 25
    },
    {
        "company": "Lobsters & Mobsters",
        "in_database": False,
        "strategy": "Restaurant industry discovery",
        "sources": ["specialized_search", "industry_databases"],
        "expected_results": 15
    }
]

# Different search tool capabilities:
mcp_tools = [
    {"name": "perplexity", "strength": "real_time_research"},
    {"name": "tavily", "strength": "web_discovery"},
    {"name": "search_droid", "strength": "structured_search"}
]
```

Real discovery requires intelligent orchestration across multiple sources!"

**[SLIDE 4: Hybrid Search Architecture Overview]**

"Here's our sophisticated approach:

```python
# 🎯 Our SMART hybrid discovery system
class DiscoverSimilarCompaniesUseCase:
    def __init__(self,
                 vector_storage: VectorStorage,
                 ai_provider: AIProvider,
                 mcp_tools_registry: MCPToolsRegistry,
                 similarity_scorer: SimilarityScorer):
        # Dependency injection for all search capabilities
        
    async def execute(self, request: DiscoveryRequest) -> DiscoveryResult:
        # Phase 1: Check database existence
        # Phase 2: Vector similarity (if exists)
        # Phase 3: MCP tool discovery (parallel)
        # Phase 4: Result aggregation and scoring
        # Phase 5: Intelligent ranking and deduplication
```

This gives us the best of all worlds - speed, coverage, and intelligence!"

## Section 2: Core Discovery Value Objects (8 minutes)

**[SLIDE 5: Discovery Data Models]**

"Let's build the foundation with comprehensive value objects:

```python
# v2/src/core/domain/value_objects/similarity_result.py
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class DiscoverySource(str, Enum):
    """Source of discovery result"""
    VECTOR_DATABASE = "vector_database"
    MCP_PERPLEXITY = "mcp_perplexity" 
    MCP_TAVILY = "mcp_tavily"
    MCP_SEARCH_DROID = "mcp_search_droid"
    GOOGLE_SEARCH = "google_search"
    MANUAL_RESEARCH = "manual_research"

class CompanyMatch(BaseModel):
    """Individual company match result"""
    company_name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Company website")
    description: Optional[str] = Field(None, description="Company description")
    industry: Optional[str] = Field(None, description="Primary industry")
    business_model: Optional[str] = Field(None, description="B2B/B2C/Marketplace")
    employee_count: Optional[int] = Field(None, description="Estimated employees")
    location: Optional[str] = Field(None, description="Headquarters location")
    
    # Scoring and attribution
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Overall similarity")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Result confidence")
    source: DiscoverySource = Field(..., description="Primary discovery source")
    source_attribution: Dict[DiscoverySource, float] = Field(
        default_factory=dict,
        description="Score contribution by source"
    )
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    search_query_used: Optional[str] = Field(None, description="Query that found this")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw source data")

class DiscoveryResult(BaseModel):
    """Complete discovery operation result"""
    query_company: str = Field(..., description="Original company searched")
    search_strategy: str = Field(..., description="Strategy used")
    total_sources_used: int = Field(..., description="Number of sources queried")
    
    # Results
    matches: List[CompanyMatch] = Field(default_factory=list)
    total_matches: int = Field(..., description="Total matches found")
    
    # Performance metrics
    execution_time_seconds: float = Field(..., description="Total execution time")
    source_timing: Dict[DiscoverySource, float] = Field(
        default_factory=dict,
        description="Time per source"
    )
    
    # Quality indicators
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Search completeness")
    freshness_score: float = Field(..., ge=0.0, le=1.0, description="Data recency")
    
    # Search context
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    errors_encountered: List[str] = Field(default_factory=list)

class DiscoveryRequest(BaseModel):
    """Discovery operation configuration"""
    company_name: str = Field(..., min_length=1, description="Target company")
    
    # Search configuration
    max_results: int = Field(50, ge=1, le=200, description="Maximum results")
    include_database_search: bool = Field(True, description="Search existing database")
    include_web_discovery: bool = Field(True, description="Use web search tools")
    enable_parallel_search: bool = Field(True, description="Parallel tool execution")
    
    # Filtering options
    min_similarity_score: float = Field(0.1, ge=0.0, le=1.0)
    industry_filter: Optional[str] = Field(None, description="Industry constraint")
    business_model_filter: Optional[str] = Field(None, description="B2B/B2C filter")
    location_filter: Optional[str] = Field(None, description="Geographic constraint")
    size_filter: Optional[str] = Field(None, description="Company size filter")
    
    # Advanced options
    prioritize_recent_data: bool = Field(True, description="Favor fresh results")
    include_competitors: bool = Field(True, description="Include direct competitors")
    include_adjacent_markets: bool = Field(True, description="Include related markets")
    custom_search_hints: List[str] = Field(default_factory=list, description="Additional search terms")
```

This gives us complete tracking of discovery results with attribution!"

**[SLIDE 6: Similarity Scoring System]**

"Now let's create our intelligent scoring service:

```python
# v2/src/core/domain/services/similarity_scorer.py
from typing import Dict, List, Optional
from ..value_objects.similarity_result import CompanyMatch, DiscoverySource
import math

class SimilarityScorer:
    """Intelligent scoring for company similarity"""
    
    def __init__(self):
        # Source reliability weights
        self.source_weights = {
            DiscoverySource.VECTOR_DATABASE: 1.0,      # Highest trust
            DiscoverySource.MCP_PERPLEXITY: 0.9,       # High-quality AI search
            DiscoverySource.MCP_TAVILY: 0.85,          # Good web discovery  
            DiscoverySource.MCP_SEARCH_DROID: 0.8,     # Structured search
            DiscoverySource.GOOGLE_SEARCH: 0.7,        # General web search
            DiscoverySource.MANUAL_RESEARCH: 0.95      # Human-validated
        }
        
        # Similarity dimension weights
        self.dimension_weights = {
            'industry_match': 0.3,         # Most important
            'business_model_match': 0.25,  # Very important
            'size_similarity': 0.2,        # Important
            'geographic_proximity': 0.15,  # Somewhat important
            'technology_overlap': 0.1      # Nice to have
        }
    
    def calculate_similarity_score(self, 
                                 company1: CompanyMatch,
                                 company2: CompanyMatch) -> float:
        """Calculate comprehensive similarity between companies"""
        
        scores = {}
        
        # Industry similarity
        scores['industry_match'] = self._calculate_industry_similarity(
            company1.industry, company2.industry
        )
        
        # Business model alignment
        scores['business_model_match'] = self._calculate_business_model_similarity(
            company1.business_model, company2.business_model
        )
        
        # Company size similarity  
        scores['size_similarity'] = self._calculate_size_similarity(
            company1.employee_count, company2.employee_count
        )
        
        # Geographic proximity
        scores['geographic_proximity'] = self._calculate_location_similarity(
            company1.location, company2.location
        )
        
        # Technology/description overlap
        scores['technology_overlap'] = self._calculate_description_similarity(
            company1.description, company2.description
        )
        
        # Weighted final score
        final_score = sum(
            scores[dimension] * self.dimension_weights[dimension]
            for dimension in scores
            if scores[dimension] is not None
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def calculate_confidence_score(self, 
                                 match: CompanyMatch,
                                 search_context: Dict) -> float:
        """Calculate confidence in this match"""
        
        confidence_factors = []
        
        # Source reliability
        source_reliability = self.source_weights.get(match.source, 0.5)
        confidence_factors.append(source_reliability)
        
        # Data completeness (more fields = higher confidence)
        completeness = self._calculate_data_completeness(match)
        confidence_factors.append(completeness)
        
        # Search query relevance
        query_relevance = self._calculate_query_relevance(
            match, search_context.get('original_query', '')
        )
        confidence_factors.append(query_relevance)
        
        # Result freshness
        freshness = self._calculate_freshness_score(match.discovered_at)
        confidence_factors.append(freshness)
        
        # Geometric mean for balanced confidence
        confidence = math.prod(confidence_factors) ** (1.0 / len(confidence_factors))
        return min(max(confidence, 0.0), 1.0)
    
    def _calculate_industry_similarity(self, industry1: Optional[str], 
                                     industry2: Optional[str]) -> Optional[float]:
        """Calculate industry match score"""
        if not industry1 or not industry2:
            return None
            
        # Exact match
        if industry1.lower() == industry2.lower():
            return 1.0
            
        # Industry hierarchy matching (simplified)
        tech_industries = {'software', 'saas', 'technology', 'ai', 'fintech'}
        finance_industries = {'finance', 'banking', 'fintech', 'investment'}
        retail_industries = {'retail', 'ecommerce', 'marketplace', 'consumer'}
        
        industry1_clean = industry1.lower()
        industry2_clean = industry2.lower()
        
        for industry_group in [tech_industries, finance_industries, retail_industries]:
            if industry1_clean in industry_group and industry2_clean in industry_group:
                return 0.8  # High similarity within group
                
        # Partial text matching
        intersection = set(industry1_clean.split()) & set(industry2_clean.split())
        union = set(industry1_clean.split()) | set(industry2_clean.split())
        if union:
            return len(intersection) / len(union) * 0.6
            
        return 0.0
    
    def _calculate_business_model_similarity(self, model1: Optional[str], 
                                           model2: Optional[str]) -> Optional[float]:
        """Calculate business model alignment"""
        if not model1 or not model2:
            return None
            
        model1_clean = model1.lower()
        model2_clean = model2.lower()
        
        # Exact match
        if model1_clean == model2_clean:
            return 1.0
            
        # Similar models
        b2b_variants = {'b2b', 'enterprise', 'saas', 'business'}
        b2c_variants = {'b2c', 'consumer', 'retail', 'direct'}
        marketplace_variants = {'marketplace', 'platform', 'two-sided'}
        
        for variant_group in [b2b_variants, b2c_variants, marketplace_variants]:
            if (any(v in model1_clean for v in variant_group) and 
                any(v in model2_clean for v in variant_group)):
                return 0.8
                
        return 0.2  # Different but not incompatible
    
    def _calculate_size_similarity(self, size1: Optional[int], 
                                 size2: Optional[int]) -> Optional[float]:
        """Calculate company size similarity"""
        if size1 is None or size2 is None:
            return None
            
        # Handle zero/negative values
        if size1 <= 0 or size2 <= 0:
            return 0.5
            
        # Use logarithmic scale for employee count
        log_ratio = abs(math.log10(size1) - math.log10(size2))
        
        # Convert to similarity (closer = higher score)
        similarity = max(0.0, 1.0 - (log_ratio / 3.0))  # 3 orders of magnitude = 0 similarity
        return similarity
    
    def _calculate_location_similarity(self, loc1: Optional[str], 
                                     loc2: Optional[str]) -> Optional[float]:
        """Calculate geographic similarity"""
        if not loc1 or not loc2:
            return None
            
        loc1_clean = loc1.lower()
        loc2_clean = loc2.lower()
        
        # Exact match
        if loc1_clean == loc2_clean:
            return 1.0
            
        # Same country/region matching (simplified)
        us_indicators = {'usa', 'united states', 'california', 'new york', 'texas', 'san francisco'}
        eu_indicators = {'uk', 'london', 'germany', 'france', 'netherlands'}
        asia_indicators = {'china', 'singapore', 'japan', 'india', 'hong kong'}
        
        for region_group in [us_indicators, eu_indicators, asia_indicators]:
            if (any(indicator in loc1_clean for indicator in region_group) and
                any(indicator in loc2_clean for indicator in region_group)):
                return 0.7  # Same region
                
        # City name matching
        loc1_words = set(loc1_clean.split())
        loc2_words = set(loc2_clean.split())
        intersection = loc1_words & loc2_words
        if intersection:
            return 0.5  # Some geographic overlap
            
        return 0.1  # Different regions but not penalized heavily
    
    def _calculate_description_similarity(self, desc1: Optional[str], 
                                        desc2: Optional[str]) -> Optional[float]:
        """Calculate description/technology overlap"""
        if not desc1 or not desc2:
            return None
            
        # Simple keyword overlap (in production, use embeddings)
        desc1_words = set(desc1.lower().split())
        desc2_words = set(desc2.lower().split())
        
        # Remove common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        desc1_words = desc1_words - stop_words
        desc2_words = desc2_words - stop_words
        
        if not desc1_words or not desc2_words:
            return 0.5
            
        intersection = desc1_words & desc2_words
        union = desc1_words | desc2_words
        
        # Jaccard similarity
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_data_completeness(self, match: CompanyMatch) -> float:
        """Calculate how complete the company data is"""
        fields_to_check = [
            match.domain, match.description, match.industry,
            match.business_model, match.employee_count, match.location
        ]
        
        filled_fields = sum(1 for field in fields_to_check if field is not None)
        return filled_fields / len(fields_to_check)
    
    def _calculate_query_relevance(self, match: CompanyMatch, 
                                 original_query: str) -> float:
        """Calculate how relevant match is to original search"""
        if not original_query:
            return 0.8  # Default high relevance
            
        query_words = set(original_query.lower().split())
        
        # Check company name relevance
        name_words = set(match.company_name.lower().split())
        name_overlap = len(query_words & name_words) / max(len(query_words), 1)
        
        # Check description relevance
        desc_relevance = 0.5  # Default
        if match.description:
            desc_words = set(match.description.lower().split())
            desc_overlap = len(query_words & desc_words) / max(len(query_words), 1)
            desc_relevance = desc_overlap
            
        # Weighted combination
        return (name_overlap * 0.7) + (desc_relevance * 0.3)
    
    def _calculate_freshness_score(self, discovered_at: datetime) -> float:
        """Calculate how fresh/recent the data is"""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        age_hours = (now - discovered_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        
        # Exponential decay: fresh data gets higher scores
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.9
        elif age_hours < 168:  # 1 week
            return 0.8
        elif age_hours < 720:  # 1 month
            return 0.6
        else:
            return 0.4  # Old but still valuable
```

This creates sophisticated, multi-dimensional similarity scoring!"

## Section 3: MCP Tools Integration Layer (10 minutes)

**[SLIDE 7: MCP Tools Registry Pattern]**

"Let's build the foundation for managing multiple search tools:

```python
# v2/src/core/use_cases/discover_similar.py (Part 1 - MCP Integration)
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import time
from datetime import datetime

from ..interfaces.vector_storage import VectorStorage  
from ..interfaces.ai_provider import AIProvider
from ..domain.value_objects.similarity_result import (
    DiscoveryRequest, DiscoveryResult, CompanyMatch, DiscoverySource
)
from ..domain.services.similarity_scorer import SimilarityScorer

class MCPToolsRegistry:
    """Registry for managing MCP search tools"""
    
    def __init__(self):
        self.available_tools: Dict[str, Any] = {}
        self.tool_configs: Dict[str, Dict] = {}
        self.tool_health: Dict[str, bool] = {}
    
    def register_tool(self, tool_name: str, tool_instance: Any, config: Dict = None):
        """Register an MCP tool for discovery"""
        self.available_tools[tool_name] = tool_instance
        self.tool_configs[tool_name] = config or {}
        self.tool_health[tool_name] = True
        
    def get_available_tools(self) -> List[str]:
        """Get list of healthy, available tools"""
        return [
            tool_name for tool_name, is_healthy in self.tool_health.items()
            if is_healthy and tool_name in self.available_tools
        ]
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get tool instance if available and healthy"""
        if (tool_name in self.available_tools and 
            self.tool_health.get(tool_name, False)):
            return self.available_tools[tool_name]
        return None
    
    def mark_tool_unhealthy(self, tool_name: str, error: str):
        """Mark tool as temporarily unhealthy"""
        self.tool_health[tool_name] = False
        # In production: implement exponential backoff recovery
    
    async def health_check_all_tools(self):
        """Periodically check tool health"""
        for tool_name, tool in self.available_tools.items():
            try:
                # Basic health check - tool-specific implementation
                if hasattr(tool, 'health_check'):
                    is_healthy = await tool.health_check()
                    self.tool_health[tool_name] = is_healthy
                else:
                    # Assume healthy if no health check method
                    self.tool_health[tool_name] = True
            except Exception:
                self.tool_health[tool_name] = False

class SearchQueryGenerator:
    """Generate optimized search queries for different tools"""
    
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
    
    async def generate_search_queries(self, 
                                    company_name: str,
                                    tool_name: str,
                                    context: Dict = None) -> List[str]:
        """Generate tool-specific search queries"""
        
        # Tool-specific prompt templates
        prompts = {
            'perplexity': self._get_perplexity_prompt(),
            'tavily': self._get_tavily_prompt(), 
            'search_droid': self._get_search_droid_prompt(),
            'google_search': self._get_google_search_prompt()
        }
        
        prompt_template = prompts.get(tool_name, prompts['google_search'])
        
        full_prompt = prompt_template.format(
            company_name=company_name,
            context=context or {}
        )
        
        try:
            response = await self.ai_provider.analyze_text(
                text=full_prompt,
                config=AnalysisConfig(
                    max_tokens=500,
                    temperature=0.3,
                    response_format="json"
                )
            )
            
            # Parse JSON response with multiple query suggestions
            import json
            queries_data = json.loads(response.content)
            return queries_data.get('search_queries', [company_name])
            
        except Exception:
            # Fallback to basic queries
            return [
                company_name,
                f"{company_name} competitors",
                f"companies like {company_name}",
                f"{company_name} similar businesses"
            ]
    
    def _get_perplexity_prompt(self) -> str:
        return '''Generate 3 optimized search queries for Perplexity AI to find companies similar to "{company_name}".
        
Perplexity excels at real-time research and understanding context. Focus on:
- Industry analysis queries
- Competitive landscape questions  
- Market positioning research

Return JSON format:
{
  "search_queries": [
    "query1",
    "query2", 
    "query3"
  ]
}'''
    
    def _get_tavily_prompt(self) -> str:
        return '''Generate 3 optimized search queries for Tavily web search to discover companies similar to "{company_name}".
        
Tavily is great for comprehensive web discovery. Focus on:
- Direct competitor searches
- Industry directory searches
- Market analysis searches

Return JSON format:
{
  "search_queries": [
    "query1",
    "query2",
    "query3"
  ]
}'''
    
    def _get_search_droid_prompt(self) -> str:
        return '''Generate 3 structured search queries for SearchDroid to find companies similar to "{company_name}".
        
SearchDroid works well with structured, specific queries. Focus on:
- Exact industry matches
- Business model searches
- Company size/type searches

Return JSON format:
{
  "search_queries": [
    "query1", 
    "query2",
    "query3"
  ]
}'''
    
    def _get_google_search_prompt(self) -> str:
        return '''Generate 3 Google search queries to find companies similar to "{company_name}".
        
Use Google search best practices:
- Specific industry terms
- Comparison keywords
- Alternative searches

Return JSON format:
{
  "search_queries": [
    "query1",
    "query2", 
    "query3"
  ]
}'''
```

This creates a flexible foundation for managing multiple search tools!"

**[SLIDE 8: Parallel Search Execution]**

"Now let's implement parallel search execution across tools:

```python
# v2/src/core/use_cases/discover_similar.py (Part 2 - Parallel Execution)

class ParallelSearchExecutor:
    """Execute searches across multiple tools in parallel"""
    
    def __init__(self, 
                 mcp_registry: MCPToolsRegistry,
                 query_generator: SearchQueryGenerator,
                 max_concurrent_tools: int = 5):
        self.mcp_registry = mcp_registry
        self.query_generator = query_generator
        self.max_concurrent_tools = max_concurrent_tools
        self.semaphore = asyncio.Semaphore(max_concurrent_tools)
    
    async def execute_parallel_search(self, 
                                    company_name: str,
                                    request: DiscoveryRequest) -> Dict[DiscoverySource, List[CompanyMatch]]:
        """Execute search across all available tools in parallel"""
        
        available_tools = self.mcp_registry.get_available_tools()
        if not available_tools:
            return {}
        
        # Create search tasks for each tool
        search_tasks = []
        for tool_name in available_tools:
            task = asyncio.create_task(
                self._search_with_tool(tool_name, company_name, request)
            )
            search_tasks.append((tool_name, task))
        
        # Execute all searches in parallel
        results = {}
        for tool_name, task in search_tasks:
            try:
                tool_results = await task
                if tool_results:
                    source = self._tool_name_to_source(tool_name)
                    results[source] = tool_results
            except Exception as e:
                # Log error and mark tool unhealthy
                self.mcp_registry.mark_tool_unhealthy(tool_name, str(e))
                continue
        
        return results
    
    async def _search_with_tool(self, 
                              tool_name: str,
                              company_name: str, 
                              request: DiscoveryRequest) -> List[CompanyMatch]:
        """Execute search with a specific tool"""
        
        async with self.semaphore:  # Limit concurrent tool usage
            start_time = time.time()
            
            try:
                # Get tool instance
                tool = self.mcp_registry.get_tool(tool_name)
                if not tool:
                    return []
                
                # Generate optimized queries for this tool
                queries = await self.query_generator.generate_search_queries(
                    company_name, tool_name
                )
                
                # Execute searches for each query
                all_matches = []
                for query in queries[:3]:  # Limit to 3 queries per tool
                    matches = await self._execute_tool_search(tool, tool_name, query, request)
                    all_matches.extend(matches)
                
                # Deduplicate by company name
                seen_companies = set()
                unique_matches = []
                for match in all_matches:
                    company_key = match.company_name.lower().strip()
                    if company_key not in seen_companies:
                        seen_companies.add(company_key)
                        unique_matches.append(match)
                
                execution_time = time.time() - start_time
                
                # Add timing metadata
                for match in unique_matches:
                    match.raw_data['tool_execution_time'] = execution_time
                    match.raw_data['tool_name'] = tool_name
                
                return unique_matches
                
            except Exception as e:
                execution_time = time.time() - start_time
                raise Exception(f"Tool {tool_name} failed after {execution_time:.2f}s: {str(e)}")
    
    async def _execute_tool_search(self, 
                                 tool: Any,
                                 tool_name: str,
                                 query: str,
                                 request: DiscoveryRequest) -> List[CompanyMatch]:
        """Execute actual search with tool"""
        
        try:
            # Tool-specific execution patterns
            if tool_name == 'perplexity':
                return await self._search_with_perplexity(tool, query, request)
            elif tool_name == 'tavily':
                return await self._search_with_tavily(tool, query, request)
            elif tool_name == 'search_droid':
                return await self._search_with_search_droid(tool, query, request)
            else:
                return await self._search_with_generic_tool(tool, query, request)
                
        except Exception as e:
            # Individual query failure shouldn't break the whole search
            return []
    
    async def _search_with_perplexity(self, 
                                    tool: Any,
                                    query: str,
                                    request: DiscoveryRequest) -> List[CompanyMatch]:
        """Perplexity-specific search execution"""
        
        # Perplexity research prompt
        research_prompt = f'''Research companies similar to the company mentioned in: "{query}"
        
Please find 10-15 similar companies and return information in this JSON format:
{{
  "companies": [
    {{
      "name": "Company Name",
      "domain": "website.com",
      "description": "Brief description",
      "industry": "Industry",
      "business_model": "B2B/B2C/Marketplace",
      "employee_count": 100,
      "location": "City, Country"
    }}
  ]
}}

Focus on companies with similar business models, target markets, or technological approaches.'''

        try:
            # Execute Perplexity search
            response = await tool.research(research_prompt)
            
            # Parse response and convert to CompanyMatch objects
            import json
            data = json.loads(response.get('content', '{}'))
            
            matches = []
            for company_data in data.get('companies', []):
                match = CompanyMatch(
                    company_name=company_data.get('name', ''),
                    domain=company_data.get('domain'),
                    description=company_data.get('description'),
                    industry=company_data.get('industry'),
                    business_model=company_data.get('business_model'),
                    employee_count=company_data.get('employee_count'),
                    location=company_data.get('location'),
                    similarity_score=0.8,  # High default for Perplexity
                    confidence_score=0.9,  # High confidence in AI research
                    source=DiscoverySource.MCP_PERPLEXITY,
                    search_query_used=query,
                    raw_data={'perplexity_response': response}
                )
                if match.company_name:
                    matches.append(match)
            
            return matches[:request.max_results // 3]  # Limit per tool
            
        except Exception as e:
            return []
    
    async def _search_with_tavily(self, 
                                tool: Any,
                                query: str,
                                request: DiscoveryRequest) -> List[CompanyMatch]:
        """Tavily-specific search execution"""
        
        try:
            # Execute Tavily web search
            search_results = await tool.search(
                query=query,
                max_results=20,
                include_domains=None,
                exclude_domains=['wikipedia.org']  # Focus on company websites
            )
            
            matches = []
            for result in search_results.get('results', []):
                # Extract company info from search result
                company_name = self._extract_company_name_from_result(result)
                domain = self._extract_domain_from_url(result.get('url', ''))
                
                match = CompanyMatch(
                    company_name=company_name,
                    domain=domain,
                    description=result.get('content', '')[:500],  # Truncate
                    similarity_score=0.7,  # Medium default for web search
                    confidence_score=0.7,
                    source=DiscoverySource.MCP_TAVILY,
                    search_query_used=query,
                    raw_data={'tavily_result': result}
                )
                if match.company_name and match.domain:
                    matches.append(match)
            
            return matches[:request.max_results // 3]
            
        except Exception:
            return []
    
    async def _search_with_search_droid(self, 
                                      tool: Any,
                                      query: str,
                                      request: DiscoveryRequest) -> List[CompanyMatch]:
        """SearchDroid-specific search execution"""
        
        try:
            # Execute structured search
            search_results = await tool.structured_search(
                query=query,
                result_type='companies',
                filters={
                    'active': True,
                    'has_website': True
                }
            )
            
            matches = []
            for result in search_results.get('companies', []):
                match = CompanyMatch(
                    company_name=result.get('name', ''),
                    domain=result.get('website'),
                    description=result.get('description'),
                    industry=result.get('industry'),
                    business_model=result.get('type'),
                    employee_count=result.get('employees'),
                    location=result.get('location'),
                    similarity_score=0.75,  # Good default for structured search
                    confidence_score=0.8,   # High confidence in structured data
                    source=DiscoverySource.MCP_SEARCH_DROID,
                    search_query_used=query,
                    raw_data={'search_droid_result': result}
                )
                if match.company_name:
                    matches.append(match)
            
            return matches[:request.max_results // 3]
            
        except Exception:
            return []
    
    def _tool_name_to_source(self, tool_name: str) -> DiscoverySource:
        """Convert tool name to DiscoverySource enum"""
        mapping = {
            'perplexity': DiscoverySource.MCP_PERPLEXITY,
            'tavily': DiscoverySource.MCP_TAVILY,
            'search_droid': DiscoverySource.MCP_SEARCH_DROID
        }
        return mapping.get(tool_name, DiscoverySource.GOOGLE_SEARCH)
    
    def _extract_company_name_from_result(self, result: Dict) -> str:
        """Extract company name from search result"""
        title = result.get('title', '')
        url = result.get('url', '')
        
        # Simple heuristics to extract company name
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        elif ' | ' in title:
            return title.split(' | ')[0].strip()
        else:
            # Extract from domain
            return self._extract_company_from_domain(url)
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract clean domain from URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''
    
    def _extract_company_from_domain(self, url: str) -> str:
        """Extract company name from domain"""
        domain = self._extract_domain_from_url(url)
        if not domain:
            return 'Unknown Company'
            
        # Remove TLD and clean up
        name_part = domain.split('.')[0]
        return name_part.replace('-', ' ').title()
```

This creates sophisticated parallel search across multiple AI tools!"

## Section 4: Core Discovery Use Case Implementation (12 minutes)

**[SLIDE 9: Main Discovery Use Case]**

"Now let's build the main discovery orchestration:

```python
# v2/src/core/use_cases/discover_similar.py (Part 3 - Main Use Case)

class DiscoverSimilarCompaniesUseCase:
    """Main use case for discovering similar companies"""
    
    def __init__(self,
                 vector_storage: VectorStorage,
                 ai_provider: AIProvider,
                 similarity_scorer: SimilarityScorer,
                 mcp_registry: MCPToolsRegistry,
                 fallback_search: Optional[Any] = None):
        self.vector_storage = vector_storage
        self.ai_provider = ai_provider
        self.similarity_scorer = similarity_scorer
        self.mcp_registry = mcp_registry
        self.fallback_search = fallback_search
        
        # Initialize search components
        self.query_generator = SearchQueryGenerator(ai_provider)
        self.parallel_executor = ParallelSearchExecutor(mcp_registry, self.query_generator)
    
    async def execute(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Execute company discovery with hybrid search strategy"""
        
        start_time = time.time()
        search_strategy = "hybrid"
        sources_used = 0
        all_matches = []
        source_timing = {}
        errors = []
        
        try:
            # Phase 1: Check if company exists in database
            database_matches = []
            if request.include_database_search:
                db_start = time.time()
                try:
                    database_matches = await self._search_vector_database(request)
                    sources_used += 1
                    source_timing[DiscoverySource.VECTOR_DATABASE] = time.time() - db_start
                    all_matches.extend(database_matches)
                except Exception as e:
                    errors.append(f"Database search failed: {str(e)}")
            
            # Phase 2: Web discovery (parallel across tools)
            web_matches = []
            if request.include_web_discovery:
                web_start = time.time()
                try:
                    if request.enable_parallel_search:
                        web_results = await self.parallel_executor.execute_parallel_search(
                            request.company_name, request
                        )
                        # Flatten results from all tools
                        for source, matches in web_results.items():
                            all_matches.extend(matches)
                            sources_used += 1
                            # Individual tool timing captured in parallel_executor
                    else:
                        # Sequential fallback
                        web_matches = await self._sequential_web_search(request)
                        all_matches.extend(web_matches)
                        sources_used += 1
                    
                    source_timing['web_discovery'] = time.time() - web_start
                    
                except Exception as e:
                    errors.append(f"Web discovery failed: {str(e)}")
            
            # Phase 3: Fallback search if needed
            if len(all_matches) < 5 and self.fallback_search:
                fallback_start = time.time()
                try:
                    fallback_matches = await self._fallback_search(request)
                    all_matches.extend(fallback_matches)
                    sources_used += 1
                    source_timing[DiscoverySource.GOOGLE_SEARCH] = time.time() - fallback_start
                except Exception as e:
                    errors.append(f"Fallback search failed: {str(e)}")
            
            # Phase 4: Advanced scoring and ranking
            scored_matches = await self._score_and_rank_matches(
                all_matches, request, database_matches
            )
            
            # Phase 5: Apply filters and limits
            filtered_matches = self._apply_filters(scored_matches, request)
            final_matches = filtered_matches[:request.max_results]
            
            # Calculate quality metrics
            total_time = time.time() - start_time
            quality_metrics = self._calculate_quality_metrics(
                final_matches, database_matches, total_time
            )
            
            return DiscoveryResult(
                query_company=request.company_name,
                search_strategy=search_strategy,
                total_sources_used=sources_used,
                matches=final_matches,
                total_matches=len(final_matches),
                execution_time_seconds=total_time,
                source_timing=source_timing,
                average_confidence=quality_metrics['average_confidence'],
                coverage_score=quality_metrics['coverage_score'],
                freshness_score=quality_metrics['freshness_score'],
                filters_applied=self._get_applied_filters(request),
                errors_encountered=errors
            )
            
        except Exception as e:
            # Complete failure fallback
            total_time = time.time() - start_time
            return DiscoveryResult(
                query_company=request.company_name,
                search_strategy="failed",
                total_sources_used=sources_used,
                matches=[],
                total_matches=0,
                execution_time_seconds=total_time,
                source_timing=source_timing,
                average_confidence=0.0,
                coverage_score=0.0,
                freshness_score=0.0,
                errors_encountered=errors + [f"Complete discovery failure: {str(e)}"]
            )
    
    async def _search_vector_database(self, request: DiscoveryRequest) -> List[CompanyMatch]:
        """Search existing vector database for similar companies"""
        
        try:
            # First, try to find the exact company
            exact_match = await self.vector_storage.find_by_name(
                index_name="companies",
                company_name=request.company_name
            )
            
            if exact_match:
                # Use vector similarity search
                search_config = VectorSearchConfig(
                    vector=exact_match.embedding,
                    top_k=min(request.max_results, 50),
                    include_metadata=True,
                    metadata_filter={
                        'industry': request.industry_filter,
                        'business_model': request.business_model_filter
                    } if request.industry_filter or request.business_model_filter else None
                )
                
                search_result = await self.vector_storage.similarity_search(
                    index_name="companies",
                    config=search_config
                )
                
                matches = []
                for result in search_result.matches:
                    if result.metadata.get('company_name') != request.company_name:
                        match = CompanyMatch(
                            company_name=result.metadata.get('company_name', 'Unknown'),
                            domain=result.metadata.get('domain'),
                            description=result.metadata.get('description'),
                            industry=result.metadata.get('industry'),
                            business_model=result.metadata.get('business_model'),
                            employee_count=result.metadata.get('employee_count'),
                            location=result.metadata.get('location'),
                            similarity_score=result.score,
                            confidence_score=0.95,  # High confidence in vector similarity
                            source=DiscoverySource.VECTOR_DATABASE,
                            raw_data={'vector_id': result.id, 'vector_score': result.score}
                        )
                        matches.append(match)
                
                return matches
            else:
                # Company not in database, return empty list
                return []
                
        except Exception:
            return []
    
    async def _sequential_web_search(self, request: DiscoveryRequest) -> List[CompanyMatch]:
        """Sequential web search fallback"""
        
        available_tools = self.mcp_registry.get_available_tools()
        all_matches = []
        
        for tool_name in available_tools[:3]:  # Limit to 3 tools in sequential mode
            try:
                tool_matches = await self.parallel_executor._search_with_tool(
                    tool_name, request.company_name, request
                )
                all_matches.extend(tool_matches)
            except Exception:
                continue
        
        return all_matches
    
    async def _fallback_search(self, request: DiscoveryRequest) -> List[CompanyMatch]:
        """Google Search fallback when MCP tools fail"""
        
        if not self.fallback_search:
            return []
        
        try:
            # Use basic Google search
            query = f"{request.company_name} competitors similar companies"
            results = await self.fallback_search.search(query, max_results=20)
            
            matches = []
            for result in results:
                company_name = self.parallel_executor._extract_company_name_from_result(result)
                domain = self.parallel_executor._extract_domain_from_url(result.get('url', ''))
                
                match = CompanyMatch(
                    company_name=company_name,
                    domain=domain,
                    description=result.get('snippet', ''),
                    similarity_score=0.5,  # Lower default for fallback
                    confidence_score=0.6,
                    source=DiscoverySource.GOOGLE_SEARCH,
                    search_query_used=query,
                    raw_data={'google_result': result}
                )
                if match.company_name and match.domain:
                    matches.append(match)
            
            return matches[:request.max_results // 2]  # Limit fallback results
            
        except Exception:
            return []
    
    async def _score_and_rank_matches(self,
                                    matches: List[CompanyMatch],
                                    request: DiscoveryRequest,
                                    database_matches: List[CompanyMatch]) -> List[CompanyMatch]:
        """Apply advanced scoring and ranking"""
        
        if not matches:
            return []
        
        # Calculate enhanced similarity scores
        for match in matches:
            # Base similarity score from source
            base_score = match.similarity_score
            
            # Calculate confidence score
            search_context = {
                'original_query': request.company_name,
                'has_database_match': len(database_matches) > 0
            }
            confidence = self.similarity_scorer.calculate_confidence_score(match, search_context)
            match.confidence_score = confidence
            
            # Source attribution
            match.source_attribution = {match.source: 1.0}
            
            # Enhanced similarity for database matches
            if match.source == DiscoverySource.VECTOR_DATABASE:
                match.similarity_score = min(base_score * 1.1, 1.0)  # 10% boost
            
            # Penalize low confidence
            if confidence < 0.5:
                match.similarity_score *= 0.8
        
        # Sort by combined score (similarity * confidence)
        matches.sort(
            key=lambda m: (m.similarity_score * m.confidence_score),
            reverse=True
        )
        
        return matches
    
    def _apply_filters(self, matches: List[CompanyMatch], request: DiscoveryRequest) -> List[CompanyMatch]:
        """Apply user-specified filters"""
        
        filtered = matches
        
        # Minimum similarity filter
        filtered = [m for m in filtered if m.similarity_score >= request.min_similarity_score]
        
        # Industry filter
        if request.industry_filter:
            filtered = [m for m in filtered 
                       if m.industry and request.industry_filter.lower() in m.industry.lower()]
        
        # Business model filter
        if request.business_model_filter:
            filtered = [m for m in filtered
                       if m.business_model and request.business_model_filter.lower() in m.business_model.lower()]
        
        # Location filter
        if request.location_filter:
            filtered = [m for m in filtered
                       if m.location and request.location_filter.lower() in m.location.lower()]
        
        # Size filter (simplified)
        if request.size_filter:
            if request.size_filter.lower() == 'startup':
                filtered = [m for m in filtered if not m.employee_count or m.employee_count < 100]
            elif request.size_filter.lower() == 'enterprise':
                filtered = [m for m in filtered if m.employee_count and m.employee_count > 1000]
        
        return filtered
    
    def _calculate_quality_metrics(self,
                                 matches: List[CompanyMatch],
                                 database_matches: List[CompanyMatch],
                                 execution_time: float) -> Dict[str, float]:
        """Calculate discovery quality metrics"""
        
        if not matches:
            return {
                'average_confidence': 0.0,
                'coverage_score': 0.0,
                'freshness_score': 0.0
            }
        
        # Average confidence
        avg_confidence = sum(m.confidence_score for m in matches) / len(matches)
        
        # Coverage score (diversity of sources)
        unique_sources = len(set(m.source for m in matches))
        max_possible_sources = 4  # database + 3 web tools
        coverage_score = unique_sources / max_possible_sources
        
        # Freshness score (recency of data)
        now = datetime.utcnow()
        freshness_scores = []
        for match in matches:
            age_hours = (now - match.discovered_at).total_seconds() / 3600
            if age_hours < 1:
                freshness_scores.append(1.0)
            elif age_hours < 24:
                freshness_scores.append(0.8)
            else:
                freshness_scores.append(0.6)
        
        avg_freshness = sum(freshness_scores) / len(freshness_scores)
        
        return {
            'average_confidence': avg_confidence,
            'coverage_score': coverage_score,
            'freshness_score': avg_freshness
        }
    
    def _get_applied_filters(self, request: DiscoveryRequest) -> Dict[str, Any]:
        """Get summary of applied filters"""
        return {
            'min_similarity_score': request.min_similarity_score,
            'industry_filter': request.industry_filter,
            'business_model_filter': request.business_model_filter,
            'location_filter': request.location_filter,
            'size_filter': request.size_filter
        }
```

This creates the complete hybrid discovery system!"

## Section 5: Comprehensive Testing Strategy (8 minutes)

**[SLIDE 10: Unit Testing with Mocks]**

"Let's create comprehensive tests for our discovery system:

```python
# v2/tests/unit/use_cases/test_discover_similar.py
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.core.use_cases.discover_similar import DiscoverSimilarCompaniesUseCase
from src.core.domain.value_objects.similarity_result import (
    DiscoveryRequest, CompanyMatch, DiscoverySource
)
from src.core.domain.services.similarity_scorer import SimilarityScorer

class TestDiscoverSimilarCompaniesUseCase:
    """Comprehensive tests for company discovery"""
    
    @pytest.fixture
    def mock_vector_storage(self):
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_ai_provider(self):
        mock = AsyncMock()
        # Mock query generation response
        mock.analyze_text.return_value = Mock(
            content='{"search_queries": ["test query 1", "test query 2", "test query 3"]}'
        )
        return mock
    
    @pytest.fixture
    def mock_similarity_scorer(self):
        mock = Mock(spec=SimilarityScorer)
        mock.calculate_confidence_score.return_value = 0.8
        mock.calculate_similarity_score.return_value = 0.7
        return mock
    
    @pytest.fixture
    def mock_mcp_registry(self):
        mock = Mock()
        mock.get_available_tools.return_value = ['perplexity', 'tavily']
        
        # Mock Perplexity tool
        perplexity_tool = AsyncMock()
        perplexity_tool.research.return_value = {
            'content': '''{"companies": [
                {
                    "name": "Similar Company 1",
                    "domain": "similar1.com",
                    "description": "AI company similar to target",
                    "industry": "AI/ML",
                    "business_model": "B2B",
                    "employee_count": 150,
                    "location": "San Francisco, CA"
                },
                {
                    "name": "Similar Company 2", 
                    "domain": "similar2.com",
                    "description": "Another similar company",
                    "industry": "Technology",
                    "business_model": "SaaS",
                    "employee_count": 75,
                    "location": "New York, NY"
                }
            ]}'''
        }
        
        # Mock Tavily tool
        tavily_tool = AsyncMock()
        tavily_tool.search.return_value = {
            'results': [
                {
                    'title': 'Competitor Company - Leading AI Solutions',
                    'url': 'https://competitor.com/about',
                    'content': 'Competitor Company provides AI solutions similar to the target company.',
                    'score': 0.9
                }
            ]
        }
        
        mock.get_tool.side_effect = lambda name: {
            'perplexity': perplexity_tool,
            'tavily': tavily_tool
        }.get(name)
        
        return mock
    
    @pytest.fixture
    def discovery_use_case(self, mock_vector_storage, mock_ai_provider, 
                          mock_similarity_scorer, mock_mcp_registry):
        return DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_vector_storage,
            ai_provider=mock_ai_provider,
            similarity_scorer=mock_similarity_scorer,
            mcp_registry=mock_mcp_registry
        )
    
    @pytest.mark.asyncio
    async def test_discovery_with_database_match(self, discovery_use_case, mock_vector_storage):
        """Test discovery when company exists in database"""
        
        # Mock database company exists
        mock_company = Mock()
        mock_company.embedding = [0.1] * 1536
        mock_vector_storage.find_by_name.return_value = mock_company
        
        # Mock similarity search results
        mock_search_result = Mock()
        mock_search_result.matches = [
            Mock(
                id='similar-1',
                score=0.95,
                metadata={
                    'company_name': 'Database Similar 1',
                    'domain': 'dbsimilar1.com',
                    'industry': 'Technology',
                    'business_model': 'B2B'
                }
            ),
            Mock(
                id='similar-2',
                score=0.88,
                metadata={
                    'company_name': 'Database Similar 2',
                    'domain': 'dbsimilar2.com',
                    'industry': 'SaaS',
                    'business_model': 'B2B'
                }
            )
        ]
        mock_vector_storage.similarity_search.return_value = mock_search_result
        
        # Execute discovery
        request = DiscoveryRequest(
            company_name="Test Company",
            max_results=10,
            include_database_search=True,
            include_web_discovery=True
        )
        
        result = await discovery_use_case.execute(request)
        
        # Verify results
        assert result.query_company == "Test Company"
        assert result.total_matches > 0
        assert result.search_strategy == "hybrid"
        assert result.total_sources_used >= 2  # Database + web tools
        
        # Check for database results
        db_matches = [m for m in result.matches if m.source == DiscoverySource.VECTOR_DATABASE]
        assert len(db_matches) >= 2
        assert all(m.confidence_score >= 0.8 for m in db_matches)
        
        # Verify vector storage was called correctly
        mock_vector_storage.find_by_name.assert_called_once()
        mock_vector_storage.similarity_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discovery_unknown_company_web_only(self, discovery_use_case, mock_vector_storage):
        """Test discovery for unknown company using web search only"""
        
        # Mock company not in database
        mock_vector_storage.find_by_name.return_value = None
        
        # Execute discovery
        request = DiscoveryRequest(
            company_name="Unknown Startup XYZ",
            max_results=15,
            include_database_search=True,
            include_web_discovery=True
        )
        
        result = await discovery_use_case.execute(request)
        
        # Verify results
        assert result.query_company == "Unknown Startup XYZ"
        assert result.total_matches > 0
        assert result.search_strategy == "hybrid"
        
        # Should only have web results
        web_sources = [DiscoverySource.MCP_PERPLEXITY, DiscoverySource.MCP_TAVILY]
        web_matches = [m for m in result.matches if m.source in web_sources]
        assert len(web_matches) > 0
        
        # No database matches
        db_matches = [m for m in result.matches if m.source == DiscoverySource.VECTOR_DATABASE]
        assert len(db_matches) == 0
        
        # Verify execution time tracking
        assert result.execution_time_seconds > 0
        assert 'web_discovery' in result.source_timing
    
    @pytest.mark.asyncio
    async def test_filtering_application(self, discovery_use_case, mock_vector_storage):
        """Test that filters are properly applied"""
        
        # Mock company not in database to focus on web results
        mock_vector_storage.find_by_name.return_value = None
        
        # Execute discovery with filters
        request = DiscoveryRequest(
            company_name="Test Company",
            max_results=10,
            industry_filter="AI",
            business_model_filter="B2B",
            min_similarity_score=0.6
        )
        
        result = await discovery_use_case.execute(request)
        
        # Verify filters were recorded
        assert result.filters_applied['industry_filter'] == "AI"
        assert result.filters_applied['business_model_filter'] == "B2B"
        assert result.filters_applied['min_similarity_score'] == 0.6
        
        # Verify quality metrics
        assert 0.0 <= result.average_confidence <= 1.0
        assert 0.0 <= result.coverage_score <= 1.0
        assert 0.0 <= result.freshness_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_parallel_search_execution(self, discovery_use_case):
        """Test parallel execution of multiple search tools"""
        
        request = DiscoveryRequest(
            company_name="Test Company",
            enable_parallel_search=True,
            include_database_search=False,
            include_web_discovery=True
        )
        
        start_time = asyncio.get_event_loop().time()
        result = await discovery_use_case.execute(request)
        end_time = asyncio.get_event_loop().time()
        
        execution_time = end_time - start_time
        
        # Parallel execution should be faster than sequential
        # (This is a simplified test - in real scenarios, measure against sequential)
        assert execution_time < 10.0  # Should complete within 10 seconds
        
        # Should have results from multiple sources
        sources_used = set(m.source for m in result.matches)
        assert len(sources_used) >= 1  # At least one tool worked
    
    @pytest.mark.asyncio 
    async def test_error_handling_and_recovery(self, discovery_use_case, mock_vector_storage, mock_mcp_registry):
        """Test graceful error handling when tools fail"""
        
        # Mock database failure
        mock_vector_storage.find_by_name.side_effect = Exception("Database connection failed")
        
        # Mock one tool failure
        failing_tool = AsyncMock()
        failing_tool.research.side_effect = Exception("Tool API failed")
        mock_mcp_registry.get_tool.side_effect = lambda name: {
            'perplexity': failing_tool,  # This tool fails
            'tavily': AsyncMock()        # This tool works
        }.get(name)
        
        request = DiscoveryRequest(company_name="Test Company")
        
        result = await discovery_use_case.execute(request)
        
        # Should still return results (graceful degradation)
        assert result.query_company == "Test Company"
        assert len(result.errors_encountered) > 0  # Errors were recorded
        
        # Should have at least some results from working tools
        # (depending on mock setup)
        assert result.total_sources_used >= 0
    
    def test_similarity_scorer_integration(self, mock_similarity_scorer):
        """Test integration with similarity scoring service"""
        
        # Create test matches
        match1 = CompanyMatch(
            company_name="Company A",
            industry="Technology",
            business_model="B2B",
            employee_count=100,
            similarity_score=0.8,
            confidence_score=0.7,
            source=DiscoverySource.MCP_PERPLEXITY
        )
        
        match2 = CompanyMatch(
            company_name="Company B", 
            industry="Finance",
            business_model="B2C",
            employee_count=50,
            similarity_score=0.6,
            confidence_score=0.9,
            source=DiscoverySource.VECTOR_DATABASE
        )
        
        # Test similarity calculation
        similarity = mock_similarity_scorer.calculate_similarity_score(match1, match2)
        assert 0.0 <= similarity <= 1.0
        
        # Test confidence calculation
        context = {'original_query': 'test company'}
        confidence = mock_similarity_scorer.calculate_confidence_score(match1, context)
        assert 0.0 <= confidence <= 1.0
        
        mock_similarity_scorer.calculate_similarity_score.assert_called_once()
        mock_similarity_scorer.calculate_confidence_score.assert_called_once()
```

**[SLIDE 11: Integration Testing]**

"Now let's create integration tests with real data:

```python
# v2/tests/integration/test_discovery_flow.py
import pytest
import asyncio
from datetime import datetime

from src.core.use_cases.discover_similar import DiscoverSimilarCompaniesUseCase
from src.core.domain.value_objects.similarity_result import DiscoveryRequest, DiscoverySource
from src.core.domain.services.similarity_scorer import SimilarityScorer

# These would be real adapter implementations in integration tests
from src.infrastructure.adapters.vector_storage.pinecone import PineconeVectorStorage
from src.infrastructure.adapters.ai_provider.gemini import GeminiAIProvider

@pytest.mark.integration
class TestDiscoveryIntegration:
    """Integration tests with real company data"""
    
    @pytest.fixture
    def real_discovery_use_case(self):
        """Set up use case with real adapters"""
        # This would use real configuration in integration environment
        vector_storage = PineconeVectorStorage(
            api_key="test-pinecone-key",
            environment="test"
        )
        
        ai_provider = GeminiAIProvider(
            api_key="test-gemini-key"
        )
        
        similarity_scorer = SimilarityScorer()
        
        # Mock MCP registry for controlled testing
        mcp_registry = MockMCPRegistry()
        
        return DiscoverSimilarCompaniesUseCase(
            vector_storage=vector_storage,
            ai_provider=ai_provider,
            similarity_scorer=similarity_scorer,
            mcp_registry=mcp_registry
        )
    
    @pytest.mark.asyncio
    async def test_salesforce_discovery(self, real_discovery_use_case):
        """Test discovery for well-known company (Salesforce)"""
        
        request = DiscoveryRequest(
            company_name="Salesforce",
            max_results=20,
            include_database_search=True,
            include_web_discovery=True,
            min_similarity_score=0.3
        )
        
        result = await real_discovery_use_case.execute(request)
        
        # Verify comprehensive results
        assert result.total_matches >= 10
        assert result.average_confidence > 0.6
        assert result.execution_time_seconds < 30.0
        
        # Should find major CRM competitors
        company_names = [m.company_name.lower() for m in result.matches]
        expected_competitors = ['hubspot', 'microsoft', 'oracle', 'adobe']
        found_competitors = [name for name in expected_competitors 
                           if any(name in company_name for company_name in company_names)]
        assert len(found_competitors) >= 2
        
        # Verify source diversity
        sources_used = set(m.source for m in result.matches)
        assert len(sources_used) >= 2
    
    @pytest.mark.asyncio
    async def test_unknown_restaurant_discovery(self, real_discovery_use_case):
        """Test discovery for unknown local business"""
        
        request = DiscoveryRequest(
            company_name="Lobsters & Mobsters",
            max_results=15,
            include_web_discovery=True,
            industry_filter="restaurant"
        )
        
        result = await real_discovery_use_case.execute(request)
        
        # Should find some restaurant chains or similar concepts
        assert result.total_matches >= 5
        
        # Results should be restaurant-related
        restaurant_keywords = ['restaurant', 'dining', 'food', 'kitchen', 'cafe']
        restaurant_matches = 0
        for match in result.matches:
            description = (match.description or '').lower()
            industry = (match.industry or '').lower()
            if any(keyword in description or keyword in industry 
                   for keyword in restaurant_keywords):
                restaurant_matches += 1
        
        assert restaurant_matches >= result.total_matches * 0.5  # At least 50% relevant
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, real_discovery_use_case):
        """Test performance benchmarks for discovery"""
        
        test_companies = [
            "Apple",
            "Google", 
            "Microsoft",
            "Unknown Startup XYZ123"
        ]
        
        performance_results = []
        
        for company in test_companies:
            request = DiscoveryRequest(
                company_name=company,
                max_results=10,
                enable_parallel_search=True
            )
            
            start_time = datetime.utcnow()
            result = await real_discovery_use_case.execute(request)
            end_time = datetime.utcnow()
            
            performance_results.append({
                'company': company,
                'execution_time': result.execution_time_seconds,
                'matches_found': result.total_matches,
                'sources_used': result.total_sources_used,
                'average_confidence': result.average_confidence
            })
        
        # Performance assertions
        avg_execution_time = sum(r['execution_time'] for r in performance_results) / len(performance_results)
        assert avg_execution_time < 25.0  # Average under 25 seconds
        
        # Quality assertions
        avg_confidence = sum(r['average_confidence'] for r in performance_results) / len(performance_results)
        assert avg_confidence > 0.5  # Average confidence above 50%
        
        # Coverage assertions
        total_matches = sum(r['matches_found'] for r in performance_results)
        assert total_matches >= len(test_companies) * 5  # At least 5 matches per company average

class MockMCPRegistry:
    """Mock MCP registry for integration testing"""
    
    def __init__(self):
        self.tools = {
            'test_search': MockSearchTool()
        }
    
    def get_available_tools(self):
        return list(self.tools.keys())
    
    def get_tool(self, tool_name):
        return self.tools.get(tool_name)

class MockSearchTool:
    """Mock search tool that returns realistic test data"""
    
    async def research(self, prompt):
        return {
            'content': '''{"companies": [
                {
                    "name": "Test Competitor 1",
                    "domain": "testcomp1.com", 
                    "description": "Similar company in same industry",
                    "industry": "Technology",
                    "business_model": "B2B"
                }
            ]}'''
        }
    
    async def search(self, query, max_results=10, **kwargs):
        return {
            'results': [
                {
                    'title': f'Search Result for {query}',
                    'url': 'https://example.com',
                    'content': f'Content related to {query}',
                    'score': 0.8
                }
            ]
        }
```

This creates comprehensive testing for our discovery system!"

## Section 6: Production Deployment Patterns (8 minutes)

**[SLIDE 12: Monitoring and Observability]**

"Let's add production monitoring to our discovery system:

```python
# v2/src/core/use_cases/discover_similar.py (Part 4 - Production Monitoring)

import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Set up observability
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Metrics
discovery_counter = meter.create_counter(
    "company_discovery_requests",
    description="Total discovery requests"
)

discovery_duration = meter.create_histogram(
    "company_discovery_duration_seconds", 
    description="Discovery request duration"
)

discovery_results_counter = meter.create_counter(
    "company_discovery_results",
    description="Discovery results by source"
)

class ProductionDiscoverSimilarCompaniesUseCase(DiscoverSimilarCompaniesUseCase):
    """Production-ready discovery use case with monitoring"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Execute discovery with full monitoring and logging"""
        
        # Start tracing
        with tracer.start_as_current_span("company_discovery") as span:
            span.set_attribute("company_name", request.company_name)
            span.set_attribute("max_results", request.max_results)
            span.set_attribute("include_database_search", request.include_database_search)
            span.set_attribute("include_web_discovery", request.include_web_discovery)
            
            start_time = time.time()
            
            try:
                # Log discovery start
                self.logger.info(
                    "Starting company discovery",
                    extra={
                        "company_name": request.company_name,
                        "max_results": request.max_results,
                        "filters": {
                            "industry": request.industry_filter,
                            "business_model": request.business_model_filter,
                            "location": request.location_filter
                        }
                    }
                )
                
                # Execute discovery
                result = await super().execute(request)
                
                # Record success metrics
                execution_time = time.time() - start_time
                
                discovery_counter.add(1, {
                    "status": "success",
                    "has_database_results": len([m for m in result.matches 
                                               if m.source == DiscoverySource.VECTOR_DATABASE]) > 0,
                    "sources_used": str(result.total_sources_used)
                })
                
                discovery_duration.record(execution_time, {
                    "status": "success",
                    "company_type": self._classify_company_type(request.company_name)
                })
                
                # Record results by source
                for source in DiscoverySource:
                    count = len([m for m in result.matches if m.source == source])
                    if count > 0:
                        discovery_results_counter.add(count, {
                            "source": source.value,
                            "quality": "high" if result.average_confidence > 0.7 else "medium"
                        })
                
                # Set span attributes
                span.set_attribute("total_matches", result.total_matches)
                span.set_attribute("execution_time", execution_time)
                span.set_attribute("average_confidence", result.average_confidence)
                span.set_attribute("sources_used", result.total_sources_used)
                span.set_status(Status(StatusCode.OK))
                
                # Log success
                self.logger.info(
                    "Company discovery completed successfully",
                    extra={
                        "company_name": request.company_name,
                        "total_matches": result.total_matches,
                        "execution_time_seconds": execution_time,
                        "average_confidence": result.average_confidence,
                        "sources_used": result.total_sources_used,
                        "quality_metrics": {
                            "coverage_score": result.coverage_score,
                            "freshness_score": result.freshness_score
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Record failure metrics
                discovery_counter.add(1, {
                    "status": "failure",
                    "error_type": type(e).__name__
                })
                
                discovery_duration.record(execution_time, {
                    "status": "failure"
                })
                
                # Set span error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                # Log error
                self.logger.error(
                    "Company discovery failed",
                    extra={
                        "company_name": request.company_name,
                        "execution_time_seconds": execution_time,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                
                # Re-raise for caller to handle
                raise
    
    def _classify_company_type(self, company_name: str) -> str:
        """Classify company type for metrics"""
        # Simple heuristics for classification
        well_known_companies = {
            'salesforce', 'google', 'microsoft', 'apple', 'amazon', 
            'facebook', 'meta', 'tesla', 'uber', 'airbnb'
        }
        
        if company_name.lower() in well_known_companies:
            return "fortune_500"
        elif len(company_name.split()) == 1 and company_name.islower():
            return "startup_single_word"
        elif "inc" in company_name.lower() or "corp" in company_name.lower():
            return "traditional_business"
        else:
            return "unknown"

# Health check endpoint for production
class DiscoveryHealthChecker:
    """Health checker for discovery system"""
    
    def __init__(self, discovery_use_case: DiscoverSimilarCompaniesUseCase):
        self.discovery_use_case = discovery_use_case
        self.logger = logging.getLogger(__name__)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        try:
            # Check vector storage
            health_status["components"]["vector_storage"] = await self._check_vector_storage()
            
            # Check AI provider
            health_status["components"]["ai_provider"] = await self._check_ai_provider()
            
            # Check MCP tools
            health_status["components"]["mcp_tools"] = await self._check_mcp_tools()
            
            # Overall status
            component_statuses = [comp["status"] for comp in health_status["components"].values()]
            if any(status == "unhealthy" for status in component_statuses):
                health_status["status"] = "degraded"
            if all(status == "unhealthy" for status in component_statuses):
                health_status["status"] = "unhealthy"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            self.logger.error("Health check failed", exc_info=True)
        
        return health_status
    
    async def _check_vector_storage(self) -> Dict[str, Any]:
        """Check vector storage health"""
        try:
            # Simple ping test
            await self.discovery_use_case.vector_storage.health_check()
            return {
                "status": "healthy",
                "message": "Vector storage accessible"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"Vector storage error: {str(e)}"
            }
    
    async def _check_ai_provider(self) -> Dict[str, Any]:
        """Check AI provider health"""
        try:
            # Simple test query
            response = await self.discovery_use_case.ai_provider.analyze_text(
                text="Health check test",
                config=AnalysisConfig(max_tokens=10)
            )
            return {
                "status": "healthy",
                "message": "AI provider responding"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"AI provider error: {str(e)}"
            }
    
    async def _check_mcp_tools(self) -> Dict[str, Any]:
        """Check MCP tools health"""
        try:
            available_tools = self.discovery_use_case.mcp_registry.get_available_tools()
            await self.discovery_use_case.mcp_registry.health_check_all_tools()
            
            healthy_tools = [
                tool for tool in available_tools
                if self.discovery_use_case.mcp_registry.tool_health.get(tool, False)
            ]
            
            return {
                "status": "healthy" if healthy_tools else "degraded",
                "message": f"{len(healthy_tools)}/{len(available_tools)} tools healthy",
                "healthy_tools": healthy_tools
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"MCP tools error: {str(e)}"
            }

# Circuit breaker for resilience
class DiscoveryCircuitBreaker:
    """Circuit breaker for discovery operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self.logger = logging.getLogger(__name__)
    
    async def execute_with_circuit_breaker(self, 
                                         discovery_func,
                                         request: DiscoveryRequest) -> DiscoveryResult:
        """Execute discovery with circuit breaker protection"""
        
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.logger.info("Circuit breaker attempting reset")
            else:
                raise Exception("Circuit breaker is open - discovery unavailable")
        
        try:
            result = await discovery_func(request)
            
            # Success - reset circuit breaker
            if self.state == "half_open":
                self._reset()
                self.logger.info("Circuit breaker reset after successful operation")
            
            return result
            
        except Exception as e:
            self._record_failure()
            
            if self.failure_count >= self.failure_threshold:
                self._trip()
                self.logger.warning(
                    f"Circuit breaker tripped after {self.failure_count} failures"
                )
            
            raise
    
    def _record_failure(self):
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()
    
    def _trip(self):
        """Trip the circuit breaker"""
        self.state = "open"
    
    def _reset(self):
        """Reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset"""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) > self.recovery_timeout
```

This adds comprehensive production monitoring and resilience!"

## Conclusion and Best Practices (5 minutes)

**[SLIDE 13: Discovery Architecture Summary]**

"Let's summarize what we've built:

```python
# Complete discovery system architecture
class EnterpriseDiscoverySystem:
    '''
    🎯 Hybrid Company Discovery System
    
    Architecture Components:
    ├── Discovery Use Case (Core Business Logic)
    │   ├── Vector Database Search (Existing Companies)
    │   ├── Parallel MCP Tools Search (Real-time Web Discovery)
    │   ├── Intelligent Query Generation (Tool-specific optimization)
    │   └── Advanced Scoring & Ranking (Multi-dimensional similarity)
    │
    ├── MCP Tools Integration (Extensible Search)
    │   ├── Perplexity (AI-powered research)
    │   ├── Tavily (Web discovery)
    │   ├── Search Droid (Structured search)
    │   └── Fallback Google Search (Reliability)
    │
    ├── Similarity Engine (Intelligent Scoring)
    │   ├── Multi-dimensional Similarity (Industry, size, model, location)
    │   ├── Source Attribution (Confidence by source)
    │   ├── Quality Scoring (Data completeness, freshness)
    │   └── Intelligent Ranking (Combined similarity + confidence)
    │
    └── Production Infrastructure (Enterprise-ready)
        ├── OpenTelemetry Monitoring (Distributed tracing)
        ├── Circuit Breaker Pattern (Resilience)
        ├── Health Checks (System observability)
        └── Comprehensive Testing (Unit + Integration)
    
    Key Capabilities:
    ✅ Hybrid search strategy (Vector + Web)
    ✅ Parallel tool execution (Performance)
    ✅ Intelligent query generation (AI-optimized)
    ✅ Advanced similarity scoring (Multi-dimensional)
    ✅ Production monitoring (Observable)
    ✅ Graceful error handling (Resilient)
    '''
```

**[SLIDE 14: Production Best Practices]**

"Key patterns for production discovery systems:

1. **Hybrid Search Strategy**: Always combine vector similarity with real-time web discovery
2. **Parallel Execution**: Use asyncio and semaphores to search multiple sources simultaneously  
3. **Intelligent Scoring**: Implement multi-dimensional similarity with source attribution
4. **Graceful Degradation**: System works even when individual tools fail
5. **Comprehensive Monitoring**: Track performance, quality, and reliability metrics
6. **Circuit Breaker Pattern**: Protect against cascading failures
7. **Extensible Architecture**: Easy to add new search tools and scoring dimensions"

**[SLIDE 15: Key Takeaways]**

"What you've learned:

🏗️ **Architecture Patterns**:
- Clean Architecture with Port/Adapter pattern for maximum flexibility
- Dependency injection for testable, loosely-coupled components
- Use cases that orchestrate complex business logic

🔍 **Discovery Techniques**:
- Hybrid search combining vector similarity and real-time web discovery
- Parallel execution across multiple AI-powered search tools
- Intelligent query generation optimized for different tools

📊 **Quality & Performance**:
- Multi-dimensional similarity scoring with confidence attribution
- Production monitoring with OpenTelemetry and custom metrics
- Comprehensive testing strategies for complex async workflows

🛡️ **Production Readiness**:
- Circuit breaker pattern for system resilience
- Health checks for operational visibility
- Graceful error handling and recovery

This architecture scales from prototype to enterprise production!"

## Total Tutorial Time: ~54 minutes

This comprehensive tutorial covers building an intelligent company discovery system that combines the best of vector similarity search with real-time AI-powered web discovery, creating a truly magical user experience while maintaining production-ready reliability and performance.