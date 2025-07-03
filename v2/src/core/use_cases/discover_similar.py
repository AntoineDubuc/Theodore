#!/usr/bin/env python3
"""
Discover Similar Companies Use Case
==================================

Hybrid discovery system combining vector search with real-time web discovery.
"""

from typing import Dict, List, Optional, Any
import asyncio
import time
from datetime import datetime, timezone
import logging
import json

from ..use_cases.base import BaseUseCase
from ..domain.value_objects.similarity_result import (
    DiscoveryRequest, DiscoveryResult, CompanyMatch, DiscoverySource
)
from ..domain.services.similarity_scorer import SimilarityScorer

logger = logging.getLogger(__name__)


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
        logger.warning(f"Tool {tool_name} marked unhealthy: {error}")
    
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
    
    def __init__(self, ai_provider):
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
        
        # Use safe string formatting to avoid KeyError with complex prompt templates
        try:
            full_prompt = prompt_template.format(
                company_name=company_name,
                context=context or {}
            )
        except KeyError:
            # Fallback to simple replacement if format fails
            full_prompt = prompt_template.replace("{company_name}", company_name)
        
        try:
            # Mock response for now (would use real AI provider)
            # In real implementation: response = await self.ai_provider.analyze_text(...)
            
            # Generate realistic queries based on tool type
            if tool_name == 'perplexity':
                queries = [
                    f"What companies are similar to {company_name} in business model and industry?",
                    f"Who are {company_name}'s main competitors and similar businesses?",
                    f"Find companies that operate like {company_name} in the same market"
                ]
            elif tool_name == 'tavily':
                queries = [
                    f"{company_name} competitors",
                    f"companies like {company_name}",
                    f"{company_name} similar businesses alternatives"
                ]
            elif tool_name == 'search_droid':
                queries = [
                    f"{company_name} industry competitors",
                    f"{company_name} business model similar companies",
                    f"{company_name} market alternatives"
                ]
            else:
                queries = [
                    company_name,
                    f"{company_name} competitors",
                    f"companies similar to {company_name}"
                ]
            
            return queries[:3]  # Limit to 3 queries
            
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
        """Execute actual search with tool - MOCK implementation for testing"""
        
        try:
            # This is a mock implementation that generates realistic test data
            # In real implementation, would call actual tool APIs
            
            matches = []
            
            if tool_name == 'perplexity':
                # Mock Perplexity-style results
                mock_companies = [
                    {
                        "name": f"AI Competitor of {query.split()[0] if query.split() else 'Target'}",
                        "domain": "ai-competitor.com",
                        "description": "AI company providing similar solutions to the target company",
                        "industry": "Artificial Intelligence",
                        "business_model": "B2B",
                        "employee_count": 150,
                        "location": "San Francisco, CA"
                    },
                    {
                        "name": f"Tech Similar to {query.split()[0] if query.split() else 'Target'}", 
                        "domain": "tech-similar.com",
                        "description": "Technology company with similar business approach",
                        "industry": "Technology",
                        "business_model": "SaaS",
                        "employee_count": 75,
                        "location": "New York, NY"
                    }
                ]
                
                for company_data in mock_companies:
                    match = CompanyMatch(
                        company_name=company_data["name"],
                        domain=company_data["domain"],
                        description=company_data["description"],
                        industry=company_data["industry"],
                        business_model=company_data["business_model"],
                        employee_count=company_data["employee_count"],
                        location=company_data["location"],
                        similarity_score=0.8,  # High default for AI research
                        confidence_score=0.9,  # High confidence in AI research
                        source=DiscoverySource.MCP_PERPLEXITY,
                        search_query_used=query,
                        raw_data={'mock_perplexity_result': company_data}
                    )
                    matches.append(match)
            
            elif tool_name == 'tavily':
                # Mock Tavily-style web search results
                match = CompanyMatch(
                    company_name=f"Web Found Similar to {query.split()[0] if query.split() else 'Target'}",
                    domain="web-similar.com",
                    description=f"Company found through web search related to: {query}",
                    similarity_score=0.7,  # Medium default for web search
                    confidence_score=0.7,
                    source=DiscoverySource.MCP_TAVILY,
                    search_query_used=query,
                    raw_data={'mock_tavily_result': {'query': query}}
                )
                matches.append(match)
            
            elif tool_name == 'search_droid':
                # Mock SearchDroid structured results
                match = CompanyMatch(
                    company_name=f"Structured Match for {query.split()[0] if query.split() else 'Target'}",
                    domain="structured-match.com",
                    description="Company found through structured search",
                    industry="Technology",
                    business_model="B2B",
                    employee_count=200,
                    location="Austin, TX",
                    similarity_score=0.75,  # Good default for structured search
                    confidence_score=0.8,   # High confidence in structured data
                    source=DiscoverySource.MCP_SEARCH_DROID,
                    search_query_used=query,
                    raw_data={'mock_search_droid_result': {'query': query}}
                )
                matches.append(match)
            
            return matches[:request.max_results // 3]  # Limit per tool
            
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


class DiscoverSimilarCompaniesUseCase(BaseUseCase[DiscoveryRequest, DiscoveryResult]):
    """Main use case for discovering similar companies"""
    
    def __init__(self,
                 vector_storage=None,
                 ai_provider=None,
                 similarity_scorer: SimilarityScorer = None,
                 mcp_registry: MCPToolsRegistry = None,
                 fallback_search: Optional[Any] = None,
                 progress_tracker=None):
        super().__init__(progress_tracker)
        self.vector_storage = vector_storage
        self.ai_provider = ai_provider
        self.similarity_scorer = similarity_scorer or SimilarityScorer()
        self.mcp_registry = mcp_registry or MCPToolsRegistry()
        self.fallback_search = fallback_search
        
        # Initialize search components
        if ai_provider:
            self.query_generator = SearchQueryGenerator(ai_provider)
            self.parallel_executor = ParallelSearchExecutor(self.mcp_registry, self.query_generator)
        else:
            # Mock components for testing
            self.query_generator = None
            self.parallel_executor = ParallelSearchExecutor(self.mcp_registry, None)
    
    async def execute(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Execute company discovery with hybrid search strategy"""
        
        start_time = time.time()
        search_strategy = "hybrid"
        sources_used = 0
        all_matches = []
        source_timing = {}
        errors = []
        
        try:
            # Emit initial progress
            await self._emit_progress("discovery", "starting", 0, f"Starting discovery for {request.company_name}")
            
            # Phase 1: Check if company exists in database (20% progress)
            database_matches = []
            if request.include_database_search and self.vector_storage:
                db_start = time.time()
                try:
                    await self._emit_progress("discovery", "database_search", 20, "Searching vector database")
                    database_matches = await self._search_vector_database(request)
                    sources_used += 1
                    source_timing['database_search'] = time.time() - db_start
                    all_matches.extend(database_matches)
                except Exception as e:
                    errors.append(f"Database search failed: {str(e)}")
            
            # Phase 2: Web discovery (parallel across tools) (60% progress)
            if request.include_web_discovery:
                web_start = time.time()
                try:
                    await self._emit_progress("discovery", "web_search", 60, "Discovering companies via web search")
                    
                    if request.enable_parallel_search:
                        web_results = await self.parallel_executor.execute_parallel_search(
                            request.company_name, request
                        )
                        # Flatten results from all tools
                        for source, matches in web_results.items():
                            all_matches.extend(matches)
                            sources_used += 1
                    else:
                        # Sequential fallback
                        web_matches = await self._sequential_web_search(request)
                        all_matches.extend(web_matches)
                        sources_used += 1
                    
                    source_timing['web_discovery'] = time.time() - web_start
                    
                except Exception as e:
                    errors.append(f"Web discovery failed: {str(e)}")
            
            # Phase 3: Fallback search if needed (80% progress)
            if len(all_matches) < 5 and self.fallback_search:
                fallback_start = time.time()
                try:
                    await self._emit_progress("discovery", "fallback_search", 80, "Using fallback search")
                    fallback_matches = await self._fallback_search(request)
                    all_matches.extend(fallback_matches)
                    sources_used += 1
                    source_timing['fallback_search'] = time.time() - fallback_start
                except Exception as e:
                    errors.append(f"Fallback search failed: {str(e)}")
            
            # Phase 4: Advanced scoring and ranking (90% progress)
            await self._emit_progress("discovery", "scoring", 90, "Scoring and ranking results")
            scored_matches = await self._score_and_rank_matches(
                all_matches, request, database_matches
            )
            
            # Phase 5: Apply filters and limits (100% progress)
            await self._emit_progress("discovery", "filtering", 100, "Applying filters and finalizing")
            filtered_matches = self._apply_filters(scored_matches, request)
            final_matches = filtered_matches[:request.max_results]
            
            # Calculate quality metrics
            total_time = time.time() - start_time
            quality_metrics = self._calculate_quality_metrics(
                final_matches, database_matches, total_time
            )
            
            result = DiscoveryResult(
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
            
            logger.info(f"Discovery completed for {request.company_name}: {len(final_matches)} matches in {total_time:.2f}s")
            return result
            
        except Exception as e:
            # Complete failure fallback
            total_time = time.time() - start_time
            error_result = DiscoveryResult(
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
            
            logger.error(f"Discovery failed for {request.company_name}: {str(e)}")
            return error_result
    
    async def _search_vector_database(self, request: DiscoveryRequest) -> List[CompanyMatch]:
        """Search existing vector database for similar companies - MOCK implementation"""
        
        try:
            # Mock implementation for testing
            # In real implementation would call actual vector storage
            
            # Simulate finding the company in database
            if request.company_name.lower() in ['salesforce', 'microsoft', 'google', 'apple']:
                # Mock vector similarity results for well-known companies
                mock_matches = [
                    CompanyMatch(
                        company_name=f"Vector Similar 1 to {request.company_name}",
                        domain="vector-similar-1.com",
                        description=f"Company similar to {request.company_name} found in vector database",
                        industry="Technology",
                        business_model="B2B",
                        employee_count=500,
                        location="San Francisco, CA",
                        similarity_score=0.95,
                        confidence_score=0.95,  # High confidence in vector similarity
                        source=DiscoverySource.VECTOR_DATABASE,
                        raw_data={'vector_score': 0.95, 'database_match': True}
                    ),
                    CompanyMatch(
                        company_name=f"Vector Similar 2 to {request.company_name}",
                        domain="vector-similar-2.com",
                        description=f"Another similar company from vector database",
                        industry="Software",
                        business_model="SaaS",
                        employee_count=300,
                        location="New York, NY",
                        similarity_score=0.88,
                        confidence_score=0.92,
                        source=DiscoverySource.VECTOR_DATABASE,
                        raw_data={'vector_score': 0.88, 'database_match': True}
                    )
                ]
                
                return mock_matches
            else:
                # Company not in database
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
        """Google Search fallback when MCP tools fail - MOCK implementation"""
        
        if not self.fallback_search:
            return []
        
        try:
            # Mock Google search fallback
            query = f"{request.company_name} competitors similar companies"
            
            match = CompanyMatch(
                company_name=f"Fallback Similar to {request.company_name}",
                domain="fallback-similar.com",
                description=f"Company found through fallback search for {request.company_name}",
                similarity_score=0.5,  # Lower default for fallback
                confidence_score=0.6,
                source=DiscoverySource.GOOGLE_SEARCH,
                search_query_used=query,
                raw_data={'fallback_search': True}
            )
            
            return [match]
            
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
        now = datetime.now(timezone.utc)
        freshness_scores = []
        for match in matches:
            age_hours = (now - match.discovered_at).total_seconds() / 3600
            if age_hours < 1:
                freshness_scores.append(1.0)
            elif age_hours < 24:
                freshness_scores.append(0.8)
            else:
                freshness_scores.append(0.6)
        
        avg_freshness = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0
        
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