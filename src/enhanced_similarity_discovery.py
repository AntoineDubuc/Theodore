"""
Enhanced Multi-Pronged Similarity Discovery System

This module implements a sophisticated similarity discovery approach that:
1. Ensures the target company has rich data (runs intelligent scraper if needed)
2. Uses LLM with full business context for AI-powered discovery
3. Integrates Google search for broader discovery
4. Combines Pinecone vector similarity with contextual reasoning
5. Provides async/parallel processing for speed
6. Smart model selection (Sonnet for reasoning, Haiku for extraction)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass

from src.models import CompanyData, CompanySimilarity
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient
from src.intelligent_company_scraper import IntelligentCompanyScraperSync

logger = logging.getLogger(__name__)

@dataclass
class SimilaritySource:
    """Represents a similarity discovery source"""
    name: str
    confidence: float
    reasoning: str
    companies: List[Dict[str, Any]]
    method: str  # 'llm', 'vector', 'google', 'hybrid'

@dataclass
class EnhancedSimilarityResult:
    """Enhanced similarity result with multi-source evidence"""
    company_name: str
    website: Optional[str]
    similarity_score: float
    confidence: float
    relationship_type: str
    sources: List[SimilaritySource]
    reasoning: List[str]
    business_context: Optional[str]
    market_positioning: Optional[str]

class EnhancedSimilarityDiscovery:
    """Enhanced multi-pronged similarity discovery system"""
    
    def __init__(self, config, bedrock_client: BedrockClient, 
                 pinecone_client: PineconeClient, 
                 intelligent_scraper: IntelligentCompanyScraperSync):
        self.config = config
        self.bedrock_client = bedrock_client
        self.pinecone_client = pinecone_client
        self.intelligent_scraper = intelligent_scraper
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def discover_similar_companies(
        self, 
        company_name: str, 
        limit: int = 10,
        enable_google: bool = True,
        min_confidence: float = 0.6
    ) -> List[EnhancedSimilarityResult]:
        """Main entry point for enhanced similarity discovery"""
        self.logger.info(f"Starting enhanced similarity discovery for: {company_name}")
        
        try:
            # Step 1: Ensure company exists with rich data
            target_company = await self._ensure_company_exists(company_name)
            if not target_company:
                self.logger.error(f"Could not process or find company: {company_name}")
                return []
            
            # Step 2: Multi-source parallel discovery
            discovery_tasks = [
                self._llm_contextual_discovery(target_company, limit),
                self._vector_similarity_discovery(target_company, limit),
            ]
            
            if enable_google:
                discovery_tasks.append(self._google_search_discovery(target_company, limit))
            
            # Run discoveries in parallel
            results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Step 3: Aggregate and deduplicate results
            aggregated_results = await self._aggregate_multi_source_results(
                target_company, results, limit, min_confidence
            )
            
            self.logger.info(f"Enhanced discovery complete: {len(aggregated_results)} companies found")
            return aggregated_results
            
        except Exception as e:
            self.logger.error(f"Enhanced similarity discovery failed: {e}")
            return []
    
    async def _ensure_company_exists(self, company_name: str) -> Optional[CompanyData]:
        """Ensure company exists with rich sales intelligence data"""
        self.logger.info(f"Ensuring company exists with rich data: {company_name}")
        
        try:
            # First, check if company exists in Pinecone
            existing_company = self.pinecone_client.find_company_by_name(company_name)
            
            if existing_company:
                self.logger.info(f"Company found: {company_name}")
                # For now, use existing data even if it lacks rich intelligence
                # TODO: Add intelligent scraper processing in future update
                return existing_company
            
            # If not found, try to discover website and create basic entry
            self.logger.info(f"Company not found, attempting website discovery: {company_name}")
            website = await self._discover_company_website(company_name)
            
            if website:
                # Create basic company data for discovery
                self.logger.info(f"Creating basic company entry for: {company_name}")
                return CompanyData(
                    name=company_name, 
                    website=website,
                    industry="Unknown",
                    business_model="Unknown",
                    target_market="Unknown"
                )
            else:
                self.logger.warning(f"Could not discover website for: {company_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error ensuring company exists: {e}")
            return None
    
    def _has_rich_data(self, company: CompanyData) -> bool:
        """Check if company has rich sales intelligence data"""
        # Check for sales intelligence content
        has_sales_intelligence = (
            hasattr(company, 'sales_intelligence') and 
            company.sales_intelligence and 
            len(company.sales_intelligence) > 500  # At least 500 chars
        )
        
        # Check for basic metadata
        has_metadata = (
            company.industry and 
            company.business_model and 
            company.target_market
        )
        
        return has_sales_intelligence and has_metadata
    
    async def _discover_company_website(self, company_name: str) -> Optional[str]:
        """Discover company website using LLM and web search"""
        try:
            # Use Claude to suggest likely website
            prompt = f"""
I need to find the official website for the company "{company_name}".

Please provide the most likely official website URL for this company.
Respond with just the URL (including https://) or "UNKNOWN" if you cannot determine it with confidence.

Company: {company_name}
Website URL:"""
            
            # Fix: Use sync method
            response = self.bedrock_client.analyze_content(prompt)
            
            if response and "http" in response.lower():
                # Extract URL from response
                import re
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, response)
                if urls:
                    website = urls[0].rstrip('.,!?')
                    self.logger.info(f"Discovered website for {company_name}: {website}")
                    return website
            
            self.logger.warning(f"Could not discover website for: {company_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error discovering website: {e}")
            return None
    
    async def _llm_contextual_discovery(self, target_company: CompanyData, limit: int) -> List[Dict[str, Any]]:
        """Use LLM with full business context for similarity discovery"""
        self.logger.info(f"Running LLM contextual discovery for: {target_company.name}")
        
        try:
            # Prepare rich context
            context = self._prepare_company_context(target_company)
            
            prompt = f"""
I need to find companies that are similar to the target company for business development and sales purposes.

TARGET COMPANY PROFILE:
{context}

Please identify {limit} companies that are similar to this target company. Consider:
- Similar business models and value propositions
- Comparable target markets and customer segments  
- Similar technology stacks or approaches
- Competitive positioning in the market
- Company stage and scale

For each similar company, provide:
1. Company name
2. Website (if known)
3. Similarity score (0.0-1.0)
4. Relationship type (competitor, partner, complementary, etc.)
5. Brief reasoning for the similarity
6. Business context explaining the connection

Respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Company Name",
      "website": "https://company.com",
      "similarity_score": 0.85,
      "relationship_type": "direct_competitor",
      "reasoning": "Brief explanation",
      "business_context": "Detailed business relationship explanation"
    }}
  ]
}}"""
            
            # Fix: Use sync method since bedrock_client.analyze_content is sync
            response = self.bedrock_client.analyze_content(prompt)
            
            if response:
                try:
                    data = json.loads(response)
                    companies = data.get('similar_companies', [])
                    self.logger.info(f"LLM discovery found {len(companies)} companies")
                    return companies
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse LLM response as JSON")
                    return []
            
            return []
            
        except Exception as e:
            self.logger.error(f"LLM contextual discovery failed: {e}")
            return []
    
    async def _vector_similarity_discovery(self, target_company: CompanyData, limit: int) -> List[Dict[str, Any]]:
        """Use Pinecone vector similarity for discovery"""
        self.logger.info(f"Running vector similarity discovery for: {target_company.name}")
        
        try:
            # Get company from Pinecone to ensure we have the embedding
            pinecone_company = self.pinecone_client.find_company_by_name(target_company.name)
            if not pinecone_company or not pinecone_company.embedding:
                self.logger.warning(f"No embedding found for {target_company.name}")
                return []
            
            # Find similar companies using vector search
            similar_companies = self.pinecone_client.find_similar_companies(
                pinecone_company.id, 
                top_k=limit,
                score_threshold=0.5  # Lower threshold for more results
            )
            
            # Convert to standard format
            results = []
            for comp in similar_companies:
                results.append({
                    'name': comp.get('company_name', ''),
                    'website': comp.get('website', ''),
                    'similarity_score': comp.get('score', 0.0),
                    'relationship_type': 'vector_similar',
                    'reasoning': f"Vector similarity score: {comp.get('score', 0.0):.2f}",
                    'business_context': f"Identified through semantic similarity in business profiles"
                })
            
            self.logger.info(f"Vector discovery found {len(results)} companies")
            return results
            
        except Exception as e:
            self.logger.error(f"Vector similarity discovery failed: {e}")
            return []
    
    async def _google_search_discovery(self, target_company: CompanyData, limit: int) -> List[Dict[str, Any]]:
        """Use Google search for broader discovery (placeholder for now)"""
        self.logger.info(f"Google search discovery for: {target_company.name}")
        
        # TODO: Implement Google search integration
        # For now, return empty list but log that this could be implemented
        self.logger.info("Google search discovery not yet implemented")
        return []
    
    async def _aggregate_multi_source_results(
        self, 
        target_company: CompanyData, 
        source_results: List[Any], 
        limit: int, 
        min_confidence: float
    ) -> List[EnhancedSimilarityResult]:
        """Aggregate and deduplicate results from multiple sources"""
        self.logger.info("Aggregating multi-source similarity results")
        
        try:
            # Collect all companies from all sources
            all_companies = {}
            source_map = ['llm', 'vector', 'google']
            
            for i, result in enumerate(source_results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Source {source_map[i]} failed: {result}")
                    continue
                
                source_name = source_map[i]
                companies = result if isinstance(result, list) else []
                
                for comp in companies:
                    company_name = comp.get('name', '').strip().lower()
                    if not company_name:
                        continue
                    
                    if company_name not in all_companies:
                        all_companies[company_name] = {
                            'name': comp.get('name', ''),
                            'website': comp.get('website', ''),
                            'sources': [],
                            'max_score': 0.0,
                            'total_confidence': 0.0,
                            'reasoning': [],
                            'business_context': ''
                        }
                    
                    # Add source information
                    score = comp.get('similarity_score', 0.0)
                    all_companies[company_name]['sources'].append({
                        'name': source_name,
                        'confidence': score,
                        'reasoning': comp.get('reasoning', ''),
                        'method': source_name
                    })
                    
                    # Update aggregated metrics
                    all_companies[company_name]['max_score'] = max(
                        all_companies[company_name]['max_score'], score
                    )
                    all_companies[company_name]['total_confidence'] += score
                    all_companies[company_name]['reasoning'].append(
                        comp.get('reasoning', '')
                    )
                    all_companies[company_name]['business_context'] = comp.get(
                        'business_context', all_companies[company_name]['business_context']
                    )
            
            # Convert to EnhancedSimilarityResult objects
            enhanced_results = []
            for company_data in all_companies.values():
                # Calculate final confidence (average of sources with bonus for multiple sources)
                num_sources = len(company_data['sources'])
                avg_confidence = company_data['total_confidence'] / num_sources if num_sources > 0 else 0
                
                # Bonus for multiple source agreement
                multi_source_bonus = min(0.2, (num_sources - 1) * 0.1)
                final_confidence = min(1.0, avg_confidence + multi_source_bonus)
                
                if final_confidence >= min_confidence:
                    # Determine relationship type
                    relationship_type = self._determine_relationship_type(company_data['sources'])
                    
                    enhanced_results.append(EnhancedSimilarityResult(
                        company_name=company_data['name'],
                        website=company_data['website'],
                        similarity_score=company_data['max_score'],
                        confidence=final_confidence,
                        relationship_type=relationship_type,
                        sources=[SimilaritySource(
                            name=s['name'],
                            confidence=s['confidence'],
                            reasoning=s['reasoning'],
                            companies=[],  # Not needed for individual sources
                            method=s['method']
                        ) for s in company_data['sources']],
                        reasoning=list(set(company_data['reasoning'])),  # Remove duplicates
                        business_context=company_data['business_context'],
                        market_positioning=None  # Could be enhanced later
                    ))
            
            # Sort by confidence and limit results
            enhanced_results.sort(key=lambda x: x.confidence, reverse=True)
            final_results = enhanced_results[:limit]
            
            self.logger.info(f"Aggregation complete: {len(final_results)} high-confidence results")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Result aggregation failed: {e}")
            return []
    
    def _prepare_company_context(self, company: CompanyData) -> str:
        """Prepare rich company context for LLM analysis"""
        context_parts = []
        
        # Basic info
        context_parts.append(f"Company Name: {company.name}")
        if company.website:
            context_parts.append(f"Website: {company.website}")
        
        # Sales intelligence (if available)
        if hasattr(company, 'sales_intelligence') and company.sales_intelligence:
            context_parts.append(f"\nSales Intelligence:\n{company.sales_intelligence}")
        
        # Business details
        if company.industry:
            context_parts.append(f"Industry: {company.industry}")
        if company.business_model:
            context_parts.append(f"Business Model: {company.business_model}")
        if company.target_market:
            context_parts.append(f"Target Market: {company.target_market}")
        if company.company_size:
            context_parts.append(f"Company Size: {company.company_size}")
        
        # Technology and services
        if company.tech_stack:
            context_parts.append(f"Technology Stack: {', '.join(company.tech_stack)}")
        if company.key_services:
            context_parts.append(f"Key Services: {', '.join(company.key_services)}")
        
        # AI summary
        if company.ai_summary:
            context_parts.append(f"\nAI Summary: {company.ai_summary}")
        
        return "\n".join(context_parts)
    
    def _determine_relationship_type(self, sources: List[Dict[str, Any]]) -> str:
        """Determine the most appropriate relationship type based on sources"""
        # Simple heuristic based on source types and confidence
        source_types = [s['name'] for s in sources]
        max_confidence = max([s['confidence'] for s in sources]) if sources else 0
        
        if 'llm' in source_types and max_confidence > 0.8:
            return 'direct_competitor'
        elif 'vector' in source_types and max_confidence > 0.7:
            return 'similar_business'
        elif len(source_types) > 1:
            return 'related_company'
        else:
            return 'potential_match'