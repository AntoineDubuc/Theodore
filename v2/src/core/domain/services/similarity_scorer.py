#!/usr/bin/env python3
"""
Similarity Scoring Service
=========================

Intelligent scoring for company similarity with multi-dimensional analysis.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import math

from ..value_objects.similarity_result import CompanyMatch, DiscoverySource


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
        if confidence_factors:
            confidence = math.prod(confidence_factors) ** (1.0 / len(confidence_factors))
        else:
            confidence = 0.5
        
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
        tech_industries = {'software', 'saas', 'technology', 'ai', 'fintech', 'ml', 'artificial intelligence'}
        finance_industries = {'finance', 'banking', 'fintech', 'investment', 'insurance'}
        retail_industries = {'retail', 'ecommerce', 'marketplace', 'consumer', 'commerce'}
        healthcare_industries = {'healthcare', 'medical', 'pharmaceutical', 'biotech', 'health'}
        
        industry1_clean = industry1.lower()
        industry2_clean = industry2.lower()
        
        for industry_group in [tech_industries, finance_industries, retail_industries, healthcare_industries]:
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
        b2b_variants = {'b2b', 'enterprise', 'saas', 'business', 'corporate'}
        b2c_variants = {'b2c', 'consumer', 'retail', 'direct', 'personal'}
        marketplace_variants = {'marketplace', 'platform', 'two-sided', 'multi-sided'}
        
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
        us_indicators = {'usa', 'united states', 'california', 'new york', 'texas', 'san francisco', 'silicon valley'}
        eu_indicators = {'uk', 'london', 'germany', 'france', 'netherlands', 'europe', 'berlin'}
        asia_indicators = {'china', 'singapore', 'japan', 'india', 'hong kong', 'asia', 'tokyo'}
        
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
        try:
            now = datetime.now(timezone.utc)
            discovered_utc = discovered_at.replace(tzinfo=timezone.utc) if discovered_at.tzinfo is None else discovered_at
            age_hours = (now - discovered_utc).total_seconds() / 3600
            
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
        except Exception:
            return 0.7  # Default decent score if calculation fails

    def calculate_industry_diversity_score(self, matches: List[CompanyMatch]) -> float:
        """Calculate how diverse the industry representation is"""
        if not matches:
            return 0.0
        
        industries = set()
        for match in matches:
            if match.industry:
                industries.add(match.industry.lower())
        
        # More industries = higher diversity
        diversity_ratio = len(industries) / len(matches) if matches else 0
        return min(diversity_ratio, 1.0)

    def calculate_business_model_diversity_score(self, matches: List[CompanyMatch]) -> float:
        """Calculate business model diversity"""
        if not matches:
            return 0.0
        
        models = set()
        for match in matches:
            if match.business_model:
                models.add(match.business_model.lower())
        
        diversity_ratio = len(models) / len(matches) if matches else 0
        return min(diversity_ratio, 1.0)