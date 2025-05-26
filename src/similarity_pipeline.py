"""
End-to-end similarity discovery pipeline
Orchestrates company discovery, crawling, validation, and storage
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.company_discovery import CompanyDiscoveryService, CompanySuggestion, DiscoveryResult
from src.similarity_validator import SimilarityValidator, SimilarityResult
from src.crawl4ai_scraper import Crawl4AICompanyScraper
from src.pinecone_client import PineconeClient
from src.bedrock_client import BedrockClient
from src.models import CompanyData, CompanySimilarity, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


class SimilarityDiscoveryPipeline:
    """
    End-to-end pipeline for discovering and validating similar companies
    """
    
    def __init__(self, config: Optional[CompanyIntelligenceConfig] = None):
        self.config = config or CompanyIntelligenceConfig()
        
        # Initialize services (clients initialized by main pipeline)
        self.bedrock_client = None
        self.discovery_service = None
        self.similarity_validator = None
        self.scraper = Crawl4AICompanyScraper(self.config)
        self.pinecone_client = None
        
        # Pipeline settings
        self.max_candidates = 10
        self.similarity_threshold = 0.6
        self.require_votes = 2
        
    async def discover_and_validate_similar_companies(self, 
                                                    company_id: str,
                                                    limit: int = 5) -> List[CompanySimilarity]:
        """
        Complete pipeline: discover → crawl → validate → store similar companies
        
        Args:
            company_id: ID of company to find similarities for
            limit: Maximum number of similar companies to find
            
        Returns:
            List of validated CompanySimilarity objects
        """
        logger.info(f"Starting similarity discovery pipeline for company: {company_id}")
        
        try:
            # Step 1: Get the target company data
            target_company = await self._get_company_data(company_id)
            if not target_company:
                logger.error(f"Could not find company data for ID: {company_id}")
                return []
            
            logger.info(f"Target company: {target_company.name}")
            
            # Step 2: Discover candidate companies using LLM
            discovery_result = self.discovery_service.discover_similar_companies(
                target_company, 
                limit=self.max_candidates
            )
            
            if not discovery_result.suggestions:
                logger.warning(f"No similar companies discovered for {target_company.name}")
                return []
            
            logger.info(f"Discovered {len(discovery_result.suggestions)} candidate companies")
            
            # Step 3: Crawl candidate companies
            candidate_companies = await self._crawl_candidate_companies(discovery_result.suggestions)
            
            if not candidate_companies:
                logger.warning("No candidate companies successfully crawled")
                return []
            
            logger.info(f"Successfully crawled {len(candidate_companies)} candidate companies")
            
            # Step 4: Validate similarities
            validated_similarities = await self._validate_similarities(
                target_company, 
                candidate_companies,
                discovery_result
            )
            
            # Step 5: Store similarity relationships
            if validated_similarities:
                await self._store_similarity_relationships(validated_similarities)
                logger.info(f"Stored {len(validated_similarities)} similarity relationships")
            
            return validated_similarities[:limit]  # Return only requested amount
            
        except Exception as e:
            logger.error(f"Pipeline failed for company {company_id}: {e}")
            return []
    
    async def batch_discover_similarities(self, 
                                        company_ids: List[str],
                                        limit_per_company: int = 5) -> Dict[str, List[CompanySimilarity]]:
        """
        Run similarity discovery for multiple companies in batch
        """
        logger.info(f"Starting batch similarity discovery for {len(company_ids)} companies")
        
        results = {}
        
        for i, company_id in enumerate(company_ids):
            logger.info(f"Processing company {i+1}/{len(company_ids)}: {company_id}")
            
            try:
                similarities = await self.discover_and_validate_similar_companies(
                    company_id, 
                    limit=limit_per_company
                )
                results[company_id] = similarities
                
                # Add small delay to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process company {company_id}: {e}")
                results[company_id] = []
        
        logger.info(f"Batch processing complete. Processed {len(results)} companies")
        return results
    
    async def _get_company_data(self, company_id: str) -> Optional[CompanyData]:
        """
        Retrieve company data from storage
        """
        try:
            # Try to get from Pinecone first
            company_data = self.pinecone_client.get_company_by_id(company_id)
            return company_data
            
        except Exception as e:
            logger.error(f"Could not retrieve company data for {company_id}: {e}")
            return None
    
    async def _crawl_candidate_companies(self, 
                                       suggestions: List[CompanySuggestion]) -> List[CompanyData]:
        """
        Crawl suggested companies to get their detailed data
        """
        logger.info(f"Crawling {len(suggestions)} candidate companies")
        
        crawled_companies = []
        
        for suggestion in suggestions:
            try:
                if not suggestion.website_url:
                    logger.warning(f"No URL for {suggestion.company_name}, skipping crawl")
                    continue
                
                logger.info(f"Crawling: {suggestion.company_name} ({suggestion.website_url})")
                
                # Create minimal CompanyData object for scraper
                temp_company = CompanyData(
                    name=suggestion.company_name,
                    website=suggestion.website_url
                )
                
                # Use existing scraper to crawl the company
                company_data = await self.scraper.scrape_company_comprehensive(temp_company)
                
                if company_data:
                    # Update with suggestion metadata
                    company_data.name = suggestion.company_name  # Use suggested name
                    crawled_companies.append(company_data)
                    logger.info(f"Successfully crawled: {suggestion.company_name}")
                else:
                    logger.warning(f"Failed to crawl: {suggestion.company_name}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling {suggestion.company_name}: {e}")
                continue
        
        return crawled_companies
    
    async def _validate_similarities(self, 
                                   target_company: CompanyData,
                                   candidate_companies: List[CompanyData],
                                   discovery_result: DiscoveryResult) -> List[CompanySimilarity]:
        """
        Validate similarity between target and candidate companies
        """
        logger.info(f"Validating similarities for {len(candidate_companies)} candidates")
        
        validated_similarities = []
        
        for candidate in candidate_companies:
            try:
                # Run similarity validation
                similarity_result = self.similarity_validator.validate_similarity(
                    target_company,
                    candidate,
                    use_llm=True,
                    require_votes=self.require_votes
                )
                
                # Only keep if similarity passes threshold
                if (similarity_result.is_similar and 
                    similarity_result.overall_score >= self.similarity_threshold):
                    
                    # Create similarity relationship
                    similarity = CompanySimilarity(
                        original_company_id=target_company.id,
                        similar_company_id=candidate.id,
                        original_company_name=target_company.name,
                        similar_company_name=candidate.name,
                        similarity_score=similarity_result.overall_score,
                        confidence=similarity_result.confidence,
                        discovery_method="llm_pipeline",
                        validation_methods=similarity_result.methods_used,
                        votes=similarity_result.votes,
                        reasoning=similarity_result.reasoning,
                        
                        # Store method-specific scores
                        structured_score=self._get_method_score(similarity_result, 'structured'),
                        embedding_score=self._get_method_score(similarity_result, 'embedding'),
                        llm_judge_score=self._get_method_score(similarity_result, 'llm_judge'),
                        
                        validation_status="validated"
                    )
                    
                    validated_similarities.append(similarity)
                    logger.info(f"Validated similarity: {candidate.name} (score: {similarity_result.overall_score:.2f})")
                
                else:
                    logger.info(f"Rejected similarity: {candidate.name} (score: {similarity_result.overall_score:.2f})")
                    
            except Exception as e:
                logger.error(f"Error validating similarity for {candidate.name}: {e}")
                continue
        
        return validated_similarities
    
    async def _store_similarity_relationships(self, 
                                            similarities: List[CompanySimilarity]) -> bool:
        """
        Store validated similarity relationships in Pinecone
        """
        try:
            # Store in Pinecone (extend client to support similarity relationships)
            success = self.pinecone_client.store_similarity_relationships(similarities)
            
            if success:
                logger.info(f"Successfully stored {len(similarities)} similarity relationships")
                return True
            else:
                logger.error("Failed to store similarity relationships")
                return False
                
        except Exception as e:
            logger.error(f"Error storing similarity relationships: {e}")
            return False
    
    def _get_method_score(self, similarity_result: SimilarityResult, method: str) -> Optional[float]:
        """
        Extract score for specific method from similarity result
        """
        for method_score in similarity_result.method_scores:
            if method_score.method == method:
                return method_score.score
        return None
    
    async def query_similar_companies(self, 
                                    company_id: str, 
                                    limit: int = 10) -> List[CompanySimilarity]:
        """
        Query existing similar companies for a given company
        """
        try:
            return self.pinecone_client.find_similar_companies(company_id, limit=limit)
        except Exception as e:
            logger.error(f"Error querying similar companies for {company_id}: {e}")
            return []
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline performance statistics
        """
        return {
            "max_candidates": self.max_candidates,
            "similarity_threshold": self.similarity_threshold,
            "require_votes": self.require_votes,
            "services_initialized": {
                "discovery_service": self.discovery_service is not None,
                "similarity_validator": self.similarity_validator is not None,
                "scraper": self.scraper is not None,
                "pinecone_client": self.pinecone_client is not None
            }
        }


async def main():
    """Test the similarity pipeline"""
    pass


if __name__ == "__main__":
    asyncio.run(main())