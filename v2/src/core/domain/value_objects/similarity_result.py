#!/usr/bin/env python3
"""
Similarity Result Value Objects
==============================

Value objects for company discovery and similarity search results.
"""

from datetime import datetime, timezone
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
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    source_timing: Dict[str, float] = Field(
        default_factory=dict,
        description="Time per source"
    )
    
    # Quality indicators
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Search completeness")
    freshness_score: float = Field(..., ge=0.0, le=1.0, description="Data recency")
    
    # Search context
    search_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    errors_encountered: List[str] = Field(default_factory=list)

    def get_top_matches(self, limit: int = 10) -> List[CompanyMatch]:
        """Get top N matches sorted by combined score"""
        sorted_matches = sorted(
            self.matches,
            key=lambda m: m.similarity_score * m.confidence_score,
            reverse=True
        )
        return sorted_matches[:limit]

    def get_matches_by_source(self, source: DiscoverySource) -> List[CompanyMatch]:
        """Get all matches from a specific source"""
        return [m for m in self.matches if m.source == source]

    def calculate_source_coverage(self) -> Dict[DiscoverySource, int]:
        """Calculate how many results came from each source"""
        coverage = {}
        for source in DiscoverySource:
            coverage[source] = len(self.get_matches_by_source(source))
        return coverage


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

    def has_filters(self) -> bool:
        """Check if any filters are applied"""
        return any([
            self.industry_filter,
            self.business_model_filter,
            self.location_filter,
            self.size_filter,
            self.min_similarity_score > 0.1
        ])

    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of applied filters"""
        return {
            "industry": self.industry_filter,
            "business_model": self.business_model_filter,
            "location": self.location_filter,
            "size": self.size_filter,
            "min_score": self.min_similarity_score
        }