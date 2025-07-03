"""
MCP Result Aggregator for Theodore.

This module provides intelligent aggregation and deduplication of results
from multiple MCP (Model Context Protocol) search tools.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import difflib

from src.core.ports.mcp_search_tool import MCPSearchResult, MCPToolInfo
from src.core.domain.entities.company import Company


logger = logging.getLogger(__name__)


class DeduplicationStrategy(str, Enum):
    """Strategies for deduplicating company results."""
    
    STRICT = "strict"          # Exact name + domain match
    FUZZY = "fuzzy"           # Fuzzy name matching + domain
    SMART = "smart"           # ML-based similarity
    PERMISSIVE = "permissive"  # Aggressive deduplication


class RankingStrategy(str, Enum):
    """Strategies for ranking aggregated results."""
    
    CONFIDENCE = "confidence"         # By confidence scores
    TOOL_PRIORITY = "tool_priority"   # By tool priority
    CONSENSUS = "consensus"           # By number of tools finding same company
    HYBRID = "hybrid"                # Combination of factors


@dataclass
class CompanyMatch:
    """Information about a company match across tools."""
    
    company: Company
    source_tools: List[MCPToolInfo]
    confidence_scores: List[float]
    metadata_by_tool: Dict[str, Dict[str, Any]]
    match_quality: float  # 0.0-1.0
    
    @property
    def consensus_score(self) -> float:
        """Get consensus score based on number of tools."""
        return len(self.source_tools) / 10.0  # Normalize to max 10 tools
    
    @property
    def average_confidence(self) -> float:
        """Get average confidence across tools."""
        if not self.confidence_scores:
            return 0.5
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    @property
    def max_confidence(self) -> float:
        """Get maximum confidence across tools."""
        if not self.confidence_scores:
            return 0.5
        return max(self.confidence_scores)


class MCPResultAggregator:
    """
    Aggregates and deduplicates results from multiple MCP search tools.
    
    Provides intelligent merging of company data with configurable
    deduplication and ranking strategies.
    """
    
    def __init__(
        self,
        deduplication_strategy: DeduplicationStrategy = DeduplicationStrategy.SMART,
        ranking_strategy: RankingStrategy = RankingStrategy.HYBRID,
        similarity_threshold: float = 0.85,
        max_results: int = 50
    ):
        self.deduplication_strategy = deduplication_strategy
        self.ranking_strategy = ranking_strategy
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        
        # Tool priority mapping (higher = better)
        self.tool_priorities: Dict[str, int] = {}
        
        # Performance tracking
        self.aggregation_count = 0
        self.total_input_results = 0
        self.total_output_results = 0
    
    def set_tool_priority(self, tool_name: str, priority: int) -> None:
        """
        Set priority for a specific tool.
        
        Args:
            tool_name: Name of the tool
            priority: Priority value (higher = better)
        """
        self.tool_priorities[tool_name] = priority
    
    def aggregate_results(
        self,
        results_by_tool: Dict[str, MCPSearchResult]
    ) -> List[Company]:
        """
        Aggregate results from multiple MCP tools.
        
        Args:
            results_by_tool: Dictionary mapping tool names to their results
            
        Returns:
            List of deduplicated and ranked companies
        """
        if not results_by_tool:
            return []
        
        self.aggregation_count += 1
        
        # Extract all companies with their source information
        all_companies = self._extract_companies_with_sources(results_by_tool)
        self.total_input_results += len(all_companies)
        
        # Deduplicate companies
        deduplicated_matches = self._deduplicate_companies(all_companies)
        
        # Rank companies
        ranked_companies = self._rank_companies(deduplicated_matches)
        
        # Limit results
        final_results = ranked_companies[:self.max_results]
        self.total_output_results += len(final_results)
        
        logger.info(
            f"Aggregated {len(all_companies)} companies from {len(results_by_tool)} tools "
            f"to {len(final_results)} unique results"
        )
        
        return final_results
    
    def _extract_companies_with_sources(
        self,
        results_by_tool: Dict[str, MCPSearchResult]
    ) -> List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]:
        """
        Extract companies with their source tool information.
        
        Returns:
            List of (company, tool_info, confidence, metadata) tuples
        """
        companies_with_sources = []
        
        for tool_name, result in results_by_tool.items():
            tool_info = result.tool_info
            
            for company in result.companies:
                # Get confidence score
                confidence = result.confidence_score or 0.5
                
                # Extract company-specific metadata if available
                metadata = {}
                if hasattr(company, 'research_metadata'):
                    metadata = company.research_metadata or {}
                
                companies_with_sources.append((
                    company, tool_info, confidence, metadata
                ))
        
        return companies_with_sources
    
    def _deduplicate_companies(
        self,
        companies_with_sources: List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]
    ) -> List[CompanyMatch]:
        """
        Deduplicate companies using the configured strategy.
        
        Args:
            companies_with_sources: List of company tuples
            
        Returns:
            List of deduplicated CompanyMatch objects
        """
        if self.deduplication_strategy == DeduplicationStrategy.STRICT:
            return self._deduplicate_strict(companies_with_sources)
        elif self.deduplication_strategy == DeduplicationStrategy.FUZZY:
            return self._deduplicate_fuzzy(companies_with_sources)
        elif self.deduplication_strategy == DeduplicationStrategy.SMART:
            return self._deduplicate_smart(companies_with_sources)
        elif self.deduplication_strategy == DeduplicationStrategy.PERMISSIVE:
            return self._deduplicate_permissive(companies_with_sources)
        else:
            return self._deduplicate_smart(companies_with_sources)
    
    def _deduplicate_strict(
        self,
        companies_with_sources: List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]
    ) -> List[CompanyMatch]:
        """Strict deduplication: exact name and domain match."""
        matches = {}
        
        for company, tool_info, confidence, metadata in companies_with_sources:
            # Create key from normalized name and domain
            key = self._create_strict_key(company)
            
            if key not in matches:
                matches[key] = CompanyMatch(
                    company=company,
                    source_tools=[tool_info],
                    confidence_scores=[confidence],
                    metadata_by_tool={tool_info.tool_name: metadata},
                    match_quality=1.0
                )
            else:
                # Merge with existing match
                existing_match = matches[key]
                existing_match.source_tools.append(tool_info)
                existing_match.confidence_scores.append(confidence)
                existing_match.metadata_by_tool[tool_info.tool_name] = metadata
                
                # Update company with better data if available
                existing_match.company = self._merge_company_data(
                    existing_match.company, company
                )
        
        return list(matches.values())
    
    def _deduplicate_fuzzy(
        self,
        companies_with_sources: List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]
    ) -> List[CompanyMatch]:
        """Fuzzy deduplication: similar names and domains."""
        matches = []
        
        for company, tool_info, confidence, metadata in companies_with_sources:
            # Find existing matches
            matching_index = self._find_fuzzy_match(company, matches)
            
            if matching_index is None:
                # Create new match
                matches.append(CompanyMatch(
                    company=company,
                    source_tools=[tool_info],
                    confidence_scores=[confidence],
                    metadata_by_tool={tool_info.tool_name: metadata},
                    match_quality=1.0
                ))
            else:
                # Merge with existing match
                existing_match = matches[matching_index]
                existing_match.source_tools.append(tool_info)
                existing_match.confidence_scores.append(confidence)
                existing_match.metadata_by_tool[tool_info.tool_name] = metadata
                
                # Update company with better data
                existing_match.company = self._merge_company_data(
                    existing_match.company, company
                )
        
        return matches
    
    def _deduplicate_smart(
        self,
        companies_with_sources: List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]
    ) -> List[CompanyMatch]:
        """Smart deduplication: ML-based similarity."""
        # For now, implement as enhanced fuzzy matching
        # Could be extended with ML models for better similarity detection
        matches = []
        
        for company, tool_info, confidence, metadata in companies_with_sources:
            # Calculate similarity with all existing matches
            best_match_index = None
            best_similarity = 0.0
            
            for i, existing_match in enumerate(matches):
                similarity = self._calculate_company_similarity(
                    company, existing_match.company
                )
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match_index = i
            
            if best_match_index is None:
                # Create new match
                matches.append(CompanyMatch(
                    company=company,
                    source_tools=[tool_info],
                    confidence_scores=[confidence],
                    metadata_by_tool={tool_info.tool_name: metadata},
                    match_quality=1.0
                ))
            else:
                # Merge with best match
                existing_match = matches[best_match_index]
                existing_match.source_tools.append(tool_info)
                existing_match.confidence_scores.append(confidence)
                existing_match.metadata_by_tool[tool_info.tool_name] = metadata
                existing_match.match_quality = best_similarity
                
                # Update company with better data
                existing_match.company = self._merge_company_data(
                    existing_match.company, company
                )
        
        return matches
    
    def _deduplicate_permissive(
        self,
        companies_with_sources: List[Tuple[Company, MCPToolInfo, float, Dict[str, Any]]]
    ) -> List[CompanyMatch]:
        """Permissive deduplication: aggressive merging."""
        # Use smart strategy but with lower threshold
        original_threshold = self.similarity_threshold
        self.similarity_threshold = 0.7  # Lower threshold
        
        matches = self._deduplicate_smart(companies_with_sources)
        
        # Restore original threshold
        self.similarity_threshold = original_threshold
        
        return matches
    
    def _create_strict_key(self, company: Company) -> str:
        """Create a strict key for exact matching."""
        name = company.name.lower().strip()
        
        # Extract domain from website if available
        domain = ""
        if company.website:
            domain = company.website.lower()
            # Remove protocol and www
            domain = domain.replace("https://", "").replace("http://", "")
            domain = domain.replace("www.", "")
            # Take only the domain part
            domain = domain.split("/")[0]
        
        return f"{name}|{domain}"
    
    def _find_fuzzy_match(
        self,
        company: Company,
        existing_matches: List[CompanyMatch]
    ) -> Optional[int]:
        """Find fuzzy match in existing matches."""
        for i, match in enumerate(existing_matches):
            similarity = self._calculate_company_similarity(company, match.company)
            if similarity >= self.similarity_threshold:
                return i
        return None
    
    def _calculate_company_similarity(
        self,
        company1: Company,
        company2: Company
    ) -> float:
        """Calculate similarity between two companies."""
        # Name similarity (most important)
        name_similarity = self._calculate_string_similarity(
            company1.name, company2.name
        )
        
        # Website similarity
        website_similarity = 0.0
        if company1.website and company2.website:
            domain1 = self._extract_domain(company1.website)
            domain2 = self._extract_domain(company2.website)
            website_similarity = 1.0 if domain1 == domain2 else 0.0
        
        # Description similarity (if available)
        description_similarity = 0.0
        if hasattr(company1, 'description') and hasattr(company2, 'description'):
            if company1.description and company2.description:
                description_similarity = self._calculate_string_similarity(
                    company1.description, company2.description
                )
        
        # Weighted combination
        if website_similarity == 1.0:
            # Same domain = definitely same company
            return 1.0
        
        # Weight name most heavily
        total_similarity = (
            name_similarity * 0.7 +
            website_similarity * 0.2 +
            description_similarity * 0.1
        )
        
        return total_similarity
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Use SequenceMatcher for similarity
        similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
        return similarity
    
    def _extract_domain(self, website: str) -> str:
        """Extract domain from website URL."""
        domain = website.lower()
        domain = domain.replace("https://", "").replace("http://", "")
        domain = domain.replace("www.", "")
        domain = domain.split("/")[0]
        return domain
    
    def _merge_company_data(self, company1: Company, company2: Company) -> Company:
        """
        Merge data from two companies, keeping the best information.
        
        Args:
            company1: Primary company data
            company2: Secondary company data to merge
            
        Returns:
            Merged company with best data from both
        """
        # Start with company1 as base
        merged_data = company1.model_dump()
        company2_data = company2.model_dump()
        
        # Merge fields, preferring non-empty values
        for field, value in company2_data.items():
            if value and (not merged_data.get(field) or 
                         (isinstance(value, str) and len(value) > len(str(merged_data.get(field, ""))))):
                merged_data[field] = value
        
        # Create new company with merged data
        return Company(**merged_data)
    
    def _rank_companies(self, matches: List[CompanyMatch]) -> List[Company]:
        """
        Rank companies using the configured strategy.
        
        Args:
            matches: List of deduplicated company matches
            
        Returns:
            List of companies sorted by rank
        """
        if self.ranking_strategy == RankingStrategy.CONFIDENCE:
            return self._rank_by_confidence(matches)
        elif self.ranking_strategy == RankingStrategy.TOOL_PRIORITY:
            return self._rank_by_tool_priority(matches)
        elif self.ranking_strategy == RankingStrategy.CONSENSUS:
            return self._rank_by_consensus(matches)
        elif self.ranking_strategy == RankingStrategy.HYBRID:
            return self._rank_hybrid(matches)
        else:
            return self._rank_hybrid(matches)
    
    def _rank_by_confidence(self, matches: List[CompanyMatch]) -> List[Company]:
        """Rank by confidence scores."""
        sorted_matches = sorted(
            matches,
            key=lambda m: m.max_confidence,
            reverse=True
        )
        return [match.company for match in sorted_matches]
    
    def _rank_by_tool_priority(self, matches: List[CompanyMatch]) -> List[Company]:
        """Rank by tool priority."""
        def get_max_tool_priority(match: CompanyMatch) -> int:
            max_priority = 0
            for tool_info in match.source_tools:
                priority = self.tool_priorities.get(tool_info.tool_name, 50)
                max_priority = max(max_priority, priority)
            return max_priority
        
        sorted_matches = sorted(
            matches,
            key=get_max_tool_priority,
            reverse=True
        )
        return [match.company for match in sorted_matches]
    
    def _rank_by_consensus(self, matches: List[CompanyMatch]) -> List[Company]:
        """Rank by consensus (number of tools)."""
        sorted_matches = sorted(
            matches,
            key=lambda m: len(m.source_tools),
            reverse=True
        )
        return [match.company for match in sorted_matches]
    
    def _rank_hybrid(self, matches: List[CompanyMatch]) -> List[Company]:
        """Rank using hybrid scoring."""
        def calculate_hybrid_score(match: CompanyMatch) -> float:
            # Confidence component (0-40 points)
            confidence_score = match.max_confidence * 40
            
            # Consensus component (0-30 points)
            consensus_score = min(len(match.source_tools) / 5.0, 1.0) * 30
            
            # Tool priority component (0-20 points)
            max_priority = 0
            for tool_info in match.source_tools:
                priority = self.tool_priorities.get(tool_info.tool_name, 50)
                max_priority = max(max_priority, priority)
            priority_score = (max_priority / 100.0) * 20
            
            # Match quality component (0-10 points)
            quality_score = match.match_quality * 10
            
            return confidence_score + consensus_score + priority_score + quality_score
        
        sorted_matches = sorted(
            matches,
            key=calculate_hybrid_score,
            reverse=True
        )
        return [match.company for match in sorted_matches]
    
    def get_aggregation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about aggregation performance.
        
        Returns:
            Dictionary with aggregation statistics
        """
        avg_input = 0.0
        avg_output = 0.0
        compression_ratio = 0.0
        
        if self.aggregation_count > 0:
            avg_input = self.total_input_results / self.aggregation_count
            avg_output = self.total_output_results / self.aggregation_count
            
            if self.total_input_results > 0:
                compression_ratio = self.total_output_results / self.total_input_results
        
        return {
            "aggregation_count": self.aggregation_count,
            "total_input_results": self.total_input_results,
            "total_output_results": self.total_output_results,
            "average_input_per_aggregation": avg_input,
            "average_output_per_aggregation": avg_output,
            "compression_ratio": compression_ratio,
            "deduplication_strategy": self.deduplication_strategy.value,
            "ranking_strategy": self.ranking_strategy.value,
            "similarity_threshold": self.similarity_threshold,
            "max_results": self.max_results
        }