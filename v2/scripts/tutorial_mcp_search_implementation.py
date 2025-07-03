#!/usr/bin/env python3
"""
TICKET-005 Tutorial: MCP Search Tool Implementation Guide

This script demonstrates how to implement and use the MCP (Model Context Protocol)
search tool system for Theodore v2, showcasing the complete workflow from tool
registration to result aggregation.

Run this script to see the MCP system in action with realistic mock implementations.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

# Configure logging for tutorial
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all MCP components
from src.core.ports.mcp_search_tool import (
    MCPSearchTool, MCPToolInfo, MCPSearchResult, MCPSearchFilters,
    MCPSearchCapability, MCPSearchException, 
    StreamingMCPSearchTool, CacheableMCPSearchTool, BatchMCPSearchTool,
    merge_search_results
)
from src.core.domain.entities.company import Company
from src.core.domain.services.mcp_registry import MCPToolRegistry, ToolStatus
from src.core.domain.services.mcp_aggregator import (
    MCPResultAggregator, DeduplicationStrategy, RankingStrategy
)

# Import mock implementations for demonstration
from tests.unit.ports.test_mcp_search_tool_mock import (
    MockMCPSearchTool, MockStreamingMCPTool, MockCacheableMCPTool,
    MockBatchMCPTool
)


class TutorialMCPPerplexityAdapter(MCPSearchTool):
    """
    Example Perplexity MCP adapter implementation.
    
    This demonstrates how to implement a real MCP tool adapter
    for the Perplexity AI search service.
    """
    
    def __init__(self, api_key: str, model: str = "sonar-medium"):
        self.api_key = api_key
        self.model = model
        self.is_connected = False
    
    def get_tool_info(self) -> MCPToolInfo:
        return MCPToolInfo(
            tool_name="perplexity_search",
            tool_version="1.0.0",
            capabilities=[
                MCPSearchCapability.WEB_SEARCH,
                MCPSearchCapability.NEWS_SEARCH,
                MCPSearchCapability.COMPANY_RESEARCH,
                MCPSearchCapability.REAL_TIME_DATA
            ],
            cost_per_request=0.005,  # $0.005 per request
            rate_limit_per_minute=100,
            max_results_per_query=50,
            supports_filters=True,
            supports_pagination=False,
            metadata={
                "model": self.model,
                "provider": "Perplexity AI",
                "description": "AI-powered search with real-time web access"
            }
        )
    
    async def search_similar_companies(
        self,
        company_name: str,
        company_website: str = None,
        company_description: str = None,
        limit: int = 10,
        filters: MCPSearchFilters = None,
        page_token: str = None,
        progress_callback = None
    ) -> MCPSearchResult:
        """Simulate Perplexity AI search for similar companies."""
        
        if progress_callback:
            progress_callback("Connecting to Perplexity AI...", 0.1, None)
        
        await asyncio.sleep(0.1)  # Simulate API call delay
        
        # Build search query
        query = f"companies similar to {company_name}"
        if company_description:
            query += f" that {company_description}"
        
        if filters:
            if filters.industry:
                query += f" in {filters.industry} industry"
            if filters.location:
                query += f" located in {filters.location}"
        
        if progress_callback:
            progress_callback("Searching for similar companies...", 0.5, query)
        
        await asyncio.sleep(0.2)  # Simulate search time
        
        # Mock similar companies (in real implementation, call Perplexity API)
        similar_companies = [
            Company(
                name=f"Similar Corp {i+1}",
                website=f"https://similar{i+1}.com",
                description=f"Company similar to {company_name} in scope and market",
                industry=filters.industry if filters else "Technology",
                location=filters.location if filters else "San Francisco, CA",
                founded_year=2015 + i,
                employee_count=50 * (i + 1)
            )
            for i in range(min(limit, 5))  # Limit to 5 for demo
        ]
        
        if progress_callback:
            progress_callback("Processing results...", 0.9, f"Found {len(similar_companies)} companies")
        
        await asyncio.sleep(0.1)
        
        if progress_callback:
            progress_callback("Complete", 1.0, None)
        
        return MCPSearchResult(
            companies=similar_companies,
            tool_info=self.get_tool_info(),
            query=query,
            total_found=len(similar_companies),
            search_time_ms=300.0,  # 300ms total
            confidence_score=0.92,
            metadata={
                "search_query": query,
                "model_used": self.model,
                "filters_applied": filters.to_dict() if filters else {}
            },
            citations=[
                "https://perplexity.ai/search/similar-companies",
                f"https://web-results.perplexity.ai/{company_name}"
            ],
            cost_incurred=0.005
        )
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        filters: MCPSearchFilters = None,
        progress_callback = None
    ) -> MCPSearchResult:
        """Search companies by keywords using Perplexity AI."""
        
        query = f"companies related to {' '.join(keywords)}"
        
        # Similar implementation to search_similar_companies
        # In real implementation, call Perplexity API with keyword query
        
        companies = [
            Company(
                name=f"Keyword Match {i+1}",
                website=f"https://keyword{i+1}.com",
                description=f"Company matching keywords: {', '.join(keywords)}",
                industry="Technology"
            )
            for i in range(min(limit, 3))
        ]
        
        return MCPSearchResult(
            companies=companies,
            tool_info=self.get_tool_info(),
            query=query,
            total_found=len(companies),
            search_time_ms=250.0,
            confidence_score=0.85,
            cost_incurred=0.005
        )
    
    async def get_company_details(
        self,
        company_name: str,
        company_website: str = None,
        requested_fields: List[str] = None
    ) -> Company:
        """Get detailed company information using Perplexity AI."""
        
        # In real implementation, use Perplexity AI to research the company
        return Company(
            name=company_name,
            website=company_website or f"https://{company_name.lower().replace(' ', '')}.com",
            description=f"Detailed information about {company_name} from Perplexity AI research",
            industry="Technology",
            founded_year=2018,
            employee_count=150,
            location="San Francisco, CA",
            research_metadata={
                "research_source": "perplexity_ai",
                "research_timestamp": datetime.now().isoformat(),
                "confidence": 0.9
            }
        )
    
    async def validate_configuration(self) -> bool:
        """Validate Perplexity API configuration."""
        if not self.api_key or len(self.api_key) < 10:
            return False
        
        # In real implementation, make test API call
        await asyncio.sleep(0.1)  # Simulate validation
        return True
    
    async def estimate_search_cost(
        self,
        query_count: int,
        average_results_per_query: int = 10
    ) -> float:
        """Estimate cost for Perplexity searches."""
        return query_count * 0.005
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Perplexity API health."""
        # In real implementation, ping Perplexity API
        await asyncio.sleep(0.05)
        
        return {
            "status": "healthy",
            "latency_ms": 50.0,
            "success_rate": 0.98,
            "quota_remaining": 9500,
            "last_error": None,
            "model": self.model
        }
    
    async def close(self) -> None:
        """Clean up Perplexity connection."""
        self.is_connected = False
    
    async def __aenter__(self):
        self.is_connected = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class TutorialMCPTavilyAdapter(MCPSearchTool):
    """
    Example Tavily MCP adapter implementation.
    
    This demonstrates how to implement a real MCP tool adapter
    for the Tavily search service.
    """
    
    def __init__(self, api_key: str, search_depth: int = 2):
        self.api_key = api_key
        self.search_depth = search_depth
    
    def get_tool_info(self) -> MCPToolInfo:
        return MCPToolInfo(
            tool_name="tavily_search",
            tool_version="1.0.0",
            capabilities=[
                MCPSearchCapability.WEB_SEARCH,
                MCPSearchCapability.COMPANY_RESEARCH,
                MCPSearchCapability.REAL_TIME_DATA
            ],
            cost_per_request=0.002,  # $0.002 per request
            rate_limit_per_minute=200,
            max_results_per_query=30,
            supports_filters=True,
            supports_pagination=True,
            metadata={
                "search_depth": self.search_depth,
                "provider": "Tavily",
                "description": "Comprehensive web search with deep crawling"
            }
        )
    
    async def search_similar_companies(
        self,
        company_name: str,
        company_website: str = None,
        company_description: str = None,
        limit: int = 10,
        filters: MCPSearchFilters = None,
        page_token: str = None,
        progress_callback = None
    ) -> MCPSearchResult:
        """Search for similar companies using Tavily."""
        
        if progress_callback:
            progress_callback("Initiating Tavily search...", 0.1, None)
        
        # Build comprehensive search query for Tavily
        query_parts = [f'"{company_name}" competitors', f'companies like "{company_name}"']
        
        if company_description:
            query_parts.append(f'"{company_description}"')
        
        if filters:
            if filters.industry:
                query_parts.append(f'{filters.industry} industry')
            if filters.technologies:
                query_parts.extend(filters.technologies)
        
        query = " ".join(query_parts)
        
        if progress_callback:
            progress_callback("Executing deep web search...", 0.6, f"Depth: {self.search_depth}")
        
        await asyncio.sleep(0.3)  # Simulate longer search time due to depth
        
        # Mock Tavily results (in real implementation, call Tavily API)
        companies = [
            Company(
                name=f"Tavily Found {i+1}",
                website=f"https://tavily{i+1}.com",
                description=f"Company discovered through Tavily's deep search for {company_name}",
                industry=filters.industry if filters else "Software",
                location="Various"
            )
            for i in range(min(limit, 4))
        ]
        
        if progress_callback:
            progress_callback("Complete", 1.0, f"Found {len(companies)} companies")
        
        return MCPSearchResult(
            companies=companies,
            tool_info=self.get_tool_info(),
            query=query,
            total_found=len(companies),
            search_time_ms=400.0,
            confidence_score=0.88,
            metadata={
                "search_depth": self.search_depth,
                "query_parts": query_parts,
                "page_token": page_token
            },
            next_page_token="tavily_page_2" if len(companies) >= limit else None,
            citations=[
                "https://tavily.com/search/companies",
                f"https://results.tavily.com/{company_name.replace(' ', '-')}"
            ],
            cost_incurred=0.002
        )
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        filters: MCPSearchFilters = None,
        progress_callback = None
    ) -> MCPSearchResult:
        """Keyword search using Tavily's comprehensive web crawling."""
        
        # Tavily excels at comprehensive keyword searches
        query = f"companies AND ({' OR '.join(keywords)})"
        
        companies = [
            Company(
                name=f"Tavily Keyword {i+1}",
                website=f"https://keyword-tavily{i+1}.com",
                description=f"Discovered via Tavily keyword search: {', '.join(keywords)}"
            )
            for i in range(min(limit, 3))
        ]
        
        return MCPSearchResult(
            companies=companies,
            tool_info=self.get_tool_info(),
            query=query,
            total_found=len(companies),
            search_time_ms=350.0,
            confidence_score=0.90,
            cost_incurred=0.002
        )
    
    async def get_company_details(
        self,
        company_name: str,
        company_website: str = None,
        requested_fields: List[str] = None
    ) -> Company:
        """Deep company research using Tavily."""
        
        return Company(
            name=company_name,
            website=company_website or f"https://{company_name.lower().replace(' ', '')}.com",
            description=f"Comprehensive research on {company_name} via Tavily's deep crawling",
            industry="Technology",
            founded_year=2019,
            employee_count=75,
            location="Austin, TX",
            research_metadata={
                "research_source": "tavily",
                "search_depth": self.search_depth,
                "crawl_timestamp": datetime.now().isoformat()
            }
        )
    
    async def validate_configuration(self) -> bool:
        """Validate Tavily API configuration."""
        if not self.api_key:
            return False
        
        await asyncio.sleep(0.05)
        return True
    
    async def estimate_search_cost(
        self,
        query_count: int,
        average_results_per_query: int = 10
    ) -> float:
        """Estimate Tavily search costs."""
        return query_count * 0.002
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Tavily API health."""
        return {
            "status": "healthy",
            "latency_ms": 75.0,
            "success_rate": 0.96,
            "quota_remaining": 8000,
            "search_depth": self.search_depth
        }
    
    async def close(self) -> None:
        """Clean up Tavily resources."""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def tutorial_step_1_basic_tool_usage():
    """
    Step 1: Basic MCP Tool Usage
    
    Demonstrates how to use a single MCP tool for company discovery.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 1: Basic MCP Tool Usage")
    print("="*80)
    
    # Create a Perplexity MCP tool
    perplexity_tool = TutorialMCPPerplexityAdapter(api_key="demo_key_perplexity")
    
    print(f"Created tool: {perplexity_tool.get_tool_info().tool_name}")
    print(f"Capabilities: {[c.value for c in perplexity_tool.get_tool_info().capabilities]}")
    
    # Validate configuration
    async with perplexity_tool:
        is_valid = await perplexity_tool.validate_configuration()
        print(f"Configuration valid: {is_valid}")
        
        # Perform a basic search
        print("\n--- Searching for companies similar to 'Stripe' ---")
        
        progress_updates = []
        def progress_callback(message, progress, details):
            progress_updates.append(f"[{progress:.0%}] {message}")
            if details:
                progress_updates[-1] += f" - {details}"
        
        result = await perplexity_tool.search_similar_companies(
            company_name="Stripe",
            company_description="online payment processing",
            limit=3,
            progress_callback=progress_callback
        )
        
        # Show progress updates
        print("Progress updates:")
        for update in progress_updates:
            print(f"  {update}")
        
        # Show results
        print(f"\nSearch Results:")
        print(f"  Query: {result.query}")
        print(f"  Found: {result.total_found} companies")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Search time: {result.search_time_ms}ms")
        print(f"  Cost: ${result.cost_incurred}")
        
        print("\nCompanies found:")
        for i, company in enumerate(result.companies, 1):
            print(f"  {i}. {company.name} - {company.website}")
            print(f"     {company.description}")
        
        # Get detailed information about first company
        if result.companies:
            print(f"\n--- Getting details for '{result.companies[0].name}' ---")
            detailed_company = await perplexity_tool.get_company_details(
                result.companies[0].name,
                result.companies[0].website
            )
            print(f"  Industry: {detailed_company.industry}")
            print(f"  Founded: {detailed_company.founded_year}")
            print(f"  Employees: {detailed_company.employee_count}")
            print(f"  Location: {detailed_company.location}")


async def tutorial_step_2_registry_management():
    """
    Step 2: MCP Tool Registry Management
    
    Demonstrates how to register multiple MCP tools and manage them through
    the registry system.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 2: MCP Tool Registry Management")
    print("="*80)
    
    # Create and start registry
    registry = MCPToolRegistry(
        health_check_interval=60,  # Check health every minute
        max_error_rate=0.1,  # 10% error threshold
        enable_auto_disable=True
    )
    
    await registry.start()
    print("MCP Tool Registry started")
    
    try:
        # Create multiple MCP tools
        perplexity_tool = TutorialMCPPerplexityAdapter(api_key="demo_perplexity")
        tavily_tool = TutorialMCPTavilyAdapter(api_key="demo_tavily")
        mock_tool = MockMCPSearchTool(tool_name="mock_enterprise_search")
        
        # Register tools with different priorities
        await registry.register_tool(perplexity_tool, priority=90, tags=["ai", "premium"])
        await registry.register_tool(tavily_tool, priority=80, tags=["web", "comprehensive"])
        await registry.register_tool(mock_tool, priority=70, tags=["enterprise", "internal"])
        
        print(f"\nRegistered tools: {registry.get_all_tool_names()}")
        print(f"Available tools: {registry.get_available_tools()}")
        
        # Show registry statistics
        stats = registry.get_registry_statistics()
        print(f"\nRegistry Statistics:")
        print(f"  Total tools: {stats['total_tools']}")
        print(f"  Active tools: {stats['active_tools']}")
        print(f"  Available tools: {stats['available_tools']}")
        print(f"  Capability distribution: {stats['capability_distribution']}")
        
        # Find tools by capability
        web_search_tools = registry.get_tools_with_capability(MCPSearchCapability.WEB_SEARCH)
        print(f"\nTools with web search capability: {len(web_search_tools)}")
        for tool in web_search_tools:
            info = tool.get_tool_info()
            print(f"  - {info.tool_name} (priority: {registry._registrations[info.tool_name].priority})")
        
        # Get best tool for a capability
        best_tool = registry.get_best_tool_for_capability(MCPSearchCapability.COMPANY_RESEARCH)
        if best_tool:
            print(f"\nBest tool for company research: {best_tool.get_tool_info().tool_name}")
        
        # Set default tool
        registry.set_default_tool("perplexity_search")
        default_tool = registry.get_default_tool()
        print(f"Default tool: {default_tool.get_tool_info().tool_name}")
        
        # Simulate some searches to generate statistics
        print("\n--- Simulating tool usage ---")
        for tool_name in ["perplexity_search", "tavily_search"]:
            tool = registry.get_tool(tool_name)
            result = await tool.search_similar_companies("Test Company", limit=2)
            
            # Record successful search
            await registry.record_search_result(
                tool_name=tool_name,
                success=True,
                search_time_ms=result.search_time_ms,
                cost=result.cost_incurred
            )
        
        # Show updated tool statistics
        for tool_name in registry.get_all_tool_names():
            tool_stats = registry.get_tool_statistics(tool_name)
            print(f"\n{tool_name} statistics:")
            print(f"  Status: {tool_stats['status']}")
            print(f"  Total searches: {tool_stats['total_searches']}")
            print(f"  Success rate: {tool_stats['success_rate']:.2%}")
            print(f"  Avg search time: {tool_stats['average_search_time_ms']:.1f}ms")
            print(f"  Total cost: ${tool_stats['total_cost_incurred']:.4f}")
        
    finally:
        await registry.stop()
        print("\nMCP Tool Registry stopped")


async def tutorial_step_3_result_aggregation():
    """
    Step 3: MCP Result Aggregation
    
    Demonstrates how to aggregate and deduplicate results from multiple
    MCP tools using different strategies.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 3: MCP Result Aggregation")
    print("="*80)
    
    # Create multiple tools
    perplexity_tool = TutorialMCPPerplexityAdapter(api_key="demo_perplexity")
    tavily_tool = TutorialMCPTavilyAdapter(api_key="demo_tavily")
    
    # Perform searches with each tool
    print("Performing searches with multiple tools...")
    
    async with perplexity_tool, tavily_tool:
        # Search for similar companies to Stripe
        perplexity_result = await perplexity_tool.search_similar_companies(
            "Stripe", 
            company_description="payment processing",
            limit=4
        )
        
        tavily_result = await tavily_tool.search_similar_companies(
            "Stripe",
            company_description="payment processing", 
            limit=4
        )
        
        print(f"Perplexity found: {len(perplexity_result.companies)} companies")
        print(f"Tavily found: {len(tavily_result.companies)} companies")
        
        # Aggregate results using different strategies
        results_by_tool = {
            "perplexity_search": perplexity_result,
            "tavily_search": tavily_result
        }
        
        # Test different deduplication strategies
        strategies = [
            (DeduplicationStrategy.STRICT, "Strict - exact name/domain match"),
            (DeduplicationStrategy.FUZZY, "Fuzzy - similar name matching"),
            (DeduplicationStrategy.SMART, "Smart - ML-based similarity"),
            (DeduplicationStrategy.PERMISSIVE, "Permissive - aggressive merging")
        ]
        
        for strategy, description in strategies:
            print(f"\n--- {description} ---")
            
            aggregator = MCPResultAggregator(
                deduplication_strategy=strategy,
                ranking_strategy=RankingStrategy.HYBRID,
                similarity_threshold=0.85,
                max_results=10
            )
            
            # Set tool priorities for ranking
            aggregator.set_tool_priority("perplexity_search", 90)
            aggregator.set_tool_priority("tavily_search", 80)
            
            # Aggregate results
            aggregated_companies = aggregator.aggregate_results(results_by_tool)
            
            print(f"Aggregated to {len(aggregated_companies)} unique companies:")
            for i, company in enumerate(aggregated_companies, 1):
                print(f"  {i}. {company.name} - {company.website}")
            
            # Show aggregation statistics
            stats = aggregator.get_aggregation_statistics()
            print(f"Aggregation stats:")
            print(f"  Input results: {stats['total_input_results']}")
            print(f"  Output results: {stats['total_output_results']}")
            print(f"  Compression ratio: {stats['compression_ratio']:.2%}")
        
        # Test different ranking strategies
        print(f"\n--- Ranking Strategy Comparison ---")
        
        ranking_strategies = [
            (RankingStrategy.CONFIDENCE, "By Confidence Score"),
            (RankingStrategy.CONSENSUS, "By Tool Consensus"),
            (RankingStrategy.TOOL_PRIORITY, "By Tool Priority"),
            (RankingStrategy.HYBRID, "Hybrid Scoring")
        ]
        
        for ranking_strategy, description in ranking_strategies:
            aggregator = MCPResultAggregator(
                deduplication_strategy=DeduplicationStrategy.SMART,
                ranking_strategy=ranking_strategy,
                max_results=3
            )
            
            aggregator.set_tool_priority("perplexity_search", 90)
            aggregator.set_tool_priority("tavily_search", 80)
            
            ranked_companies = aggregator.aggregate_results(results_by_tool)
            
            print(f"\n{description} - Top 3:")
            for i, company in enumerate(ranked_companies[:3], 1):
                print(f"  {i}. {company.name}")


async def tutorial_step_4_advanced_features():
    """
    Step 4: Advanced MCP Features
    
    Demonstrates streaming, caching, and batch operations with MCP tools.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 4: Advanced MCP Features")
    print("="*80)
    
    # Test streaming functionality
    print("--- Streaming Search Results ---")
    streaming_tool = MockStreamingMCPTool(tool_name="streaming_search")
    
    print("Companies found via streaming:")
    async for company in streaming_tool.search_similar_companies_streaming("Tesla", limit=3):
        print(f"  ⏯️  {company.name} - {company.website}")
        await asyncio.sleep(0.1)  # Show streaming effect
    
    # Test caching functionality
    print("\n--- Cached Search Results ---")
    cacheable_tool = MockCacheableMCPTool(tool_name="cached_search")
    
    # First search (cache miss)
    print("First search for 'Apple' (cache miss):")
    start_time = asyncio.get_event_loop().time()
    result1 = await cacheable_tool.search_with_cache("Apple")
    time1 = (asyncio.get_event_loop().time() - start_time) * 1000
    print(f"  Found {len(result1.companies)} companies in {time1:.1f}ms")
    
    # Second search (cache hit)
    print("Second search for 'Apple' (cache hit):")
    start_time = asyncio.get_event_loop().time()
    result2 = await cacheable_tool.search_with_cache("Apple")
    time2 = (asyncio.get_event_loop().time() - start_time) * 1000
    print(f"  Found {len(result2.companies)} companies in {time2:.1f}ms")
    
    # Show cache statistics
    cache_stats = await cacheable_tool.get_cache_stats()
    print(f"Cache stats: {cache_stats['cache_hits']} hits, {cache_stats['hit_rate']:.1%} hit rate")
    
    # Test batch operations
    print("\n--- Batch Operations ---")
    batch_tool = MockBatchMCPTool(tool_name="batch_search")
    
    companies_to_research = ["Microsoft", "Google", "Amazon"]
    
    print(f"Batch searching for {len(companies_to_research)} companies...")
    
    batch_progress = []
    def batch_progress_callback(message, progress, details):
        batch_progress.append(f"[{progress:.0%}] {message}")
        if details:
            batch_progress[-1] += f" - {details}"
    
    batch_results = await batch_tool.search_batch_companies(
        companies_to_research,
        limit_per_company=2,
        progress_callback=batch_progress_callback
    )
    
    print("Batch progress:")
    for update in batch_progress:
        print(f"  {update}")
    
    print(f"\nBatch results:")
    for company_name, result in batch_results.items():
        print(f"  {company_name}: {len(result.companies)} similar companies found")
    
    # Batch company details
    print("\n--- Batch Company Details ---")
    batch_details = await batch_tool.get_batch_company_details(companies_to_research)
    
    print("Company details:")
    for company_name, company in batch_details.items():
        if company:
            print(f"  {company_name}: {company.industry}, {company.employee_count} employees")


async def tutorial_step_5_error_handling():
    """
    Step 5: Error Handling and Resilience
    
    Demonstrates how the MCP system handles various error conditions
    and provides graceful degradation.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 5: Error Handling and Resilience")
    print("="*80)
    
    # Test configuration validation errors
    print("--- Configuration Validation ---")
    
    invalid_tool = MockMCPSearchTool(fail_validation=True)
    try:
        await invalid_tool.validate_configuration()
        print("❌ Validation should have failed")
    except MCPConfigurationException as e:
        print(f"✅ Configuration error caught: {e}")
    
    # Test search failures
    print("\n--- Search Error Handling ---")
    
    failing_tool = MockMCPSearchTool(fail_searches=True)
    try:
        await failing_tool.search_similar_companies("Test Company")
        print("❌ Search should have failed")
    except MCPSearchException as e:
        print(f"✅ Search error caught: {e}")
    
    # Test rate limiting
    print("\n--- Rate Limiting ---")
    
    rate_limited_tool = MockMCPSearchTool(simulate_rate_limit=True)
    try:
        await rate_limited_tool.search_similar_companies("Test Company")
        print("❌ Should have been rate limited")
    except MCPRateLimitedException as e:
        print(f"✅ Rate limit error caught: {e}")
        print(f"   Retry after: {e.retry_after} seconds")
    
    # Test registry with failing tools
    print("\n--- Registry Error Handling ---")
    
    registry = MCPToolRegistry(enable_auto_disable=True)
    await registry.start()
    
    try:
        # Register a failing tool
        await registry.register_tool(failing_tool, priority=50)
        
        # Try to get the tool (should work for registration)
        tool = registry.get_tool("mock_tool")
        print(f"Tool registered: {tool.get_tool_info().tool_name}")
        
        # Simulate failed search and record it
        try:
            await tool.search_similar_companies("Test")
        except MCPSearchException:
            pass  # Expected
        
        # Record the failure
        await registry.record_search_result(
            tool_name="mock_tool",
            success=False,
            search_time_ms=0.0,
            error=MCPSearchException("Simulated failure")
        )
        
        # Check tool statistics
        stats = registry.get_tool_statistics("mock_tool")
        print(f"Tool stats after failure: {stats['error_count']} errors, {stats['success_rate']:.1%} success rate")
        
    finally:
        await registry.stop()
    
    print("\n--- Health Check Monitoring ---")
    
    # Test health checking
    healthy_tool = MockMCPSearchTool()
    unhealthy_tool = MockMCPSearchTool(fail_searches=True)
    
    healthy_status = await healthy_tool.health_check()
    unhealthy_status = await unhealthy_tool.health_check()
    
    print(f"Healthy tool status: {healthy_status['status']} ({healthy_status['success_rate']:.1%} success)")
    print(f"Unhealthy tool status: {unhealthy_status['status']} ({unhealthy_status['success_rate']:.1%} success)")


async def tutorial_step_6_production_patterns():
    """
    Step 6: Production Usage Patterns
    
    Demonstrates recommended patterns for using MCP tools in production,
    including cost optimization, performance monitoring, and best practices.
    """
    print("\n" + "="*80)
    print("TUTORIAL STEP 6: Production Usage Patterns")
    print("="*80)
    
    # Create production-style registry
    registry = MCPToolRegistry(
        health_check_interval=300,  # 5 minutes
        max_error_rate=0.05,  # 5% error threshold
        enable_auto_disable=True
    )
    await registry.start()
    
    try:
        # Register tools with production-realistic settings
        perplexity_tool = TutorialMCPPerplexityAdapter(api_key="prod_perplexity_key")
        tavily_tool = TutorialMCPTavilyAdapter(api_key="prod_tavily_key")
        enterprise_tool = MockMCPSearchTool(tool_name="enterprise_search")
        
        await registry.register_tool(perplexity_tool, priority=95, tags=["premium", "ai"])
        await registry.register_tool(tavily_tool, priority=85, tags=["comprehensive", "web"])
        await registry.register_tool(enterprise_tool, priority=75, tags=["enterprise", "internal"])
        
        print("Production registry configured with 3 tools")
        
        # Demonstrate cost-aware search selection
        print("\n--- Cost-Aware Tool Selection ---")
        
        query_count = 100
        tools_with_costs = []
        
        for tool_name in registry.get_all_tool_names():
            tool = registry.get_tool(tool_name)
            cost = await tool.estimate_search_cost(query_count)
            info = tool.get_tool_info()
            tools_with_costs.append((tool_name, cost, info.cost_per_request))
        
        print(f"Cost estimates for {query_count} searches:")
        for tool_name, total_cost, per_request_cost in sorted(tools_with_costs, key=lambda x: x[1]):
            print(f"  {tool_name}: ${total_cost:.2f} total (${per_request_cost:.4f} per request)")
        
        # Demonstrate intelligent fallback strategy
        print("\n--- Intelligent Fallback Strategy ---")
        
        search_query = "fintech startups"
        fallback_order = []
        
        # Try tools in priority order
        for capability in [MCPSearchCapability.COMPANY_RESEARCH, MCPSearchCapability.WEB_SEARCH]:
            best_tool = registry.get_best_tool_for_capability(capability)
            if best_tool:
                tool_name = best_tool.get_tool_info().tool_name
                if tool_name not in fallback_order:
                    fallback_order.append(tool_name)
        
        print(f"Fallback order for '{search_query}': {' → '.join(fallback_order)}")
        
        # Simulate fallback scenario
        successful_search = False
        for tool_name in fallback_order:
            try:
                tool = registry.get_tool(tool_name)
                print(f"  Trying {tool_name}...")
                
                # Simulate some tools being unavailable
                if tool_name == "tavily_search":
                    print(f"    ❌ {tool_name} unavailable (simulated)")
                    continue
                
                result = await tool.search_by_keywords([search_query], limit=3)
                print(f"    ✅ {tool_name} succeeded: {len(result.companies)} companies found")
                successful_search = True
                break
                
            except Exception as e:
                print(f"    ❌ {tool_name} failed: {e}")
                continue
        
        if not successful_search:
            print("    ⚠️  All tools failed - would use fallback database search")
        
        # Demonstrate performance monitoring
        print("\n--- Performance Monitoring ---")
        
        # Simulate varied performance across tools
        performance_data = []
        
        for tool_name in registry.get_all_tool_names():
            for i in range(3):  # Simulate 3 searches per tool
                tool = registry.get_tool(tool_name)
                start_time = asyncio.get_event_loop().time()
                
                try:
                    result = await tool.search_similar_companies(f"Company {i+1}", limit=2)
                    search_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    # Record successful search
                    await registry.record_search_result(
                        tool_name=tool_name,
                        success=True,
                        search_time_ms=search_time,
                        cost=result.cost_incurred
                    )
                    
                    performance_data.append((tool_name, search_time, True))
                    
                except Exception:
                    search_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    await registry.record_search_result(
                        tool_name=tool_name,
                        success=False,
                        search_time_ms=search_time
                    )
                    performance_data.append((tool_name, search_time, False))
        
        # Show performance summary
        print("Performance summary:")
        for tool_name in registry.get_all_tool_names():
            stats = registry.get_tool_statistics(tool_name)
            print(f"  {tool_name}:")
            print(f"    Searches: {stats['total_searches']}")
            print(f"    Success rate: {stats['success_rate']:.1%}")
            print(f"    Avg time: {stats['average_search_time_ms']:.1f}ms")
            print(f"    Total cost: ${stats['total_cost_incurred']:.4f}")
        
        # Show overall registry statistics
        registry_stats = registry.get_registry_statistics()
        print(f"\nOverall registry performance:")
        print(f"  Total searches: {registry_stats['total_searches']}")
        print(f"  Overall success rate: {registry_stats['overall_success_rate']:.1%}")
        print(f"  Total cost incurred: ${registry_stats['total_cost_incurred']:.4f}")
        
        # Demonstrate result merging for redundancy
        print("\n--- Multi-Tool Redundancy ---")
        
        primary_tool = registry.get_tool("perplexity_search")
        secondary_tool = registry.get_tool("enterprise_search")
        
        primary_result = await primary_tool.search_similar_companies("Shopify", limit=3)
        secondary_result = await secondary_tool.search_similar_companies("Shopify", limit=3)
        
        # Merge results for redundancy
        merged_result = merge_search_results([primary_result, secondary_result])
        
        print(f"Primary tool found: {len(primary_result.companies)} companies")
        print(f"Secondary tool found: {len(secondary_result.companies)} companies")
        print(f"Merged unique results: {len(merged_result.companies)} companies")
        print(f"Combined search time: {merged_result.search_time_ms:.1f}ms")
        print(f"Total cost: ${merged_result.cost_incurred:.4f}")
        
    finally:
        await registry.stop()


async def main():
    """
    Main tutorial runner.
    
    Executes all tutorial steps in sequence to demonstrate the complete
    MCP search tool system functionality.
    """
    print("🚀 THEODORE V2 - MCP SEARCH TOOL IMPLEMENTATION TUTORIAL")
    print("="*80)
    print("This tutorial demonstrates the complete MCP (Model Context Protocol)")
    print("search tool system implementation for Theodore v2.")
    print()
    print("The tutorial covers:")
    print("  1. Basic MCP tool usage")
    print("  2. Registry management") 
    print("  3. Result aggregation")
    print("  4. Advanced features (streaming, caching, batch)")
    print("  5. Error handling and resilience")
    print("  6. Production usage patterns")
    print()
    print("Each step builds on the previous ones to show a complete workflow.")
    print("="*80)
    
    try:
        await tutorial_step_1_basic_tool_usage()
        await tutorial_step_2_registry_management()
        await tutorial_step_3_result_aggregation()
        await tutorial_step_4_advanced_features()
        await tutorial_step_5_error_handling()
        await tutorial_step_6_production_patterns()
        
        print("\n" + "="*80)
        print("🎉 TUTORIAL COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Takeaways:")
        print("✅ MCP tools provide pluggable search capabilities")
        print("✅ Registry system manages multiple tools with health monitoring")
        print("✅ Result aggregation handles deduplication and ranking")
        print("✅ Advanced features support streaming, caching, and batch operations")
        print("✅ Comprehensive error handling ensures system resilience")
        print("✅ Production patterns optimize for cost, performance, and reliability")
        print("\nThe MCP search tool system is now ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Tutorial failed with error: {e}")
        logger.exception("Tutorial execution failed")
        raise


if __name__ == "__main__":
    # Run the tutorial
    asyncio.run(main())