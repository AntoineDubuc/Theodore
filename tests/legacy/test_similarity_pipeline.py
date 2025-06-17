"""
Tests for SimilarityDiscoveryPipeline
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.similarity_pipeline import SimilarityDiscoveryPipeline
from src.company_discovery import DiscoveryResult, CompanySuggestion
from src.similarity_validator import SimilarityResult, SimilarityScore
from src.models import CompanyData, CompanySimilarity, CompanyIntelligenceConfig


class TestSimilarityDiscoveryPipeline:
    """Test the SimilarityDiscoveryPipeline class"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        return CompanyIntelligenceConfig()
    
    @pytest.fixture
    def mock_services(self):
        """Mock all service dependencies"""
        mocks = {
            'bedrock_client': Mock(),
            'discovery_service': Mock(),
            'similarity_validator': Mock(),
            'scraper': AsyncMock(),
            'pinecone_client': Mock()
        }
        return mocks
    
    @pytest.fixture
    def pipeline(self, mock_config, mock_services):
        """Create pipeline with mocked dependencies"""
        pipeline = SimilarityDiscoveryPipeline(mock_config)
        
        # Replace with mocks
        pipeline.bedrock_client = mock_services['bedrock_client']
        pipeline.discovery_service = mock_services['discovery_service']
        pipeline.similarity_validator = mock_services['similarity_validator']
        pipeline.scraper = mock_services['scraper']
        pipeline.pinecone_client = mock_services['pinecone_client']
        
        return pipeline
    
    @pytest.fixture
    def sample_target_company(self):
        """Sample target company for testing"""
        return CompanyData(
            id="target-123",
            name="Target Corp",
            website="https://target.com",
            industry="Software",
            business_model="B2B SaaS"
        )
    
    @pytest.fixture
    def sample_discovery_result(self):
        """Sample discovery result"""
        suggestions = [
            CompanySuggestion(
                company_name="Similar Corp A",
                website_url="https://similar-a.com",
                suggested_reason="Same industry"
            ),
            CompanySuggestion(
                company_name="Similar Corp B", 
                website_url="https://similar-b.com",
                suggested_reason="Same business model"
            )
        ]
        
        return DiscoveryResult(
            target_company="Target Corp",
            suggestions=suggestions,
            total_suggestions=2
        )
    
    @pytest.fixture
    def sample_crawled_companies(self):
        """Sample crawled company data"""
        return [
            CompanyData(
                id="similar-a-123",
                name="Similar Corp A",
                website="https://similar-a.com",
                industry="Software",
                business_model="B2B SaaS"
            ),
            CompanyData(
                id="similar-b-123", 
                name="Similar Corp B",
                website="https://similar-b.com",
                industry="Software",
                business_model="B2B SaaS"
            )
        ]
    
    @pytest.fixture
    def sample_similarity_results(self):
        """Sample similarity validation results"""
        return [
            SimilarityResult(
                company_a_name="Target Corp",
                company_b_name="Similar Corp A",
                is_similar=True,
                confidence=0.8,
                overall_score=0.75,
                methods_used=["structured", "embedding"],
                method_scores=[
                    SimilarityScore(method="structured", score=0.7, is_similar=True, details={}),
                    SimilarityScore(method="embedding", score=0.8, is_similar=True, details={})
                ],
                votes=["structured", "embedding"],
                reasoning=["High industry match", "Strong embedding similarity"]
            ),
            SimilarityResult(
                company_a_name="Target Corp",
                company_b_name="Similar Corp B",
                is_similar=False,
                confidence=0.3,
                overall_score=0.4,
                methods_used=["structured", "embedding"],
                method_scores=[
                    SimilarityScore(method="structured", score=0.4, is_similar=False, details={}),
                    SimilarityScore(method="embedding", score=0.4, is_similar=False, details={})
                ],
                votes=[],
                reasoning=["Low overall similarity"]
            )
        ]
    
    @pytest.mark.asyncio
    async def test_discover_and_validate_similar_companies_success(
        self, 
        pipeline, 
        mock_services,
        sample_target_company,
        sample_discovery_result,
        sample_crawled_companies,
        sample_similarity_results
    ):
        """Test successful end-to-end similarity discovery"""
        
        # Mock pipeline steps
        mock_services['pinecone_client'].get_company_by_id.return_value = sample_target_company
        mock_services['discovery_service'].discover_similar_companies.return_value = sample_discovery_result
        mock_services['scraper'].scrape_company_comprehensive.side_effect = sample_crawled_companies
        mock_services['similarity_validator'].validate_similarity.side_effect = sample_similarity_results
        mock_services['pinecone_client'].store_similarity_relationships.return_value = True
        
        # Execute pipeline
        result = await pipeline.discover_and_validate_similar_companies("target-123", limit=5)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1  # Only one similarity passed validation
        
        similarity = result[0]
        assert isinstance(similarity, CompanySimilarity)
        assert similarity.original_company_name == "Target Corp"
        assert similarity.similar_company_name == "Similar Corp A"
        assert similarity.similarity_score == 0.75
        assert similarity.confidence == 0.8
        assert similarity.validation_status == "validated"
        
        # Verify service calls
        mock_services['pinecone_client'].get_company_by_id.assert_called_once_with("target-123")
        mock_services['discovery_service'].discover_similar_companies.assert_called_once()
        assert mock_services['scraper'].scrape_company_comprehensive.call_count == 2
        assert mock_services['similarity_validator'].validate_similarity.call_count == 2
        mock_services['pinecone_client'].store_similarity_relationships.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_and_validate_company_not_found(self, pipeline, mock_services):
        """Test pipeline when target company not found"""
        mock_services['pinecone_client'].get_company_by_id.return_value = None
        
        result = await pipeline.discover_and_validate_similar_companies("nonexistent-123")
        
        assert result == []
        mock_services['discovery_service'].discover_similar_companies.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_discover_and_validate_no_discovery_results(
        self, 
        pipeline, 
        mock_services,
        sample_target_company
    ):
        """Test pipeline when no similar companies discovered"""
        mock_services['pinecone_client'].get_company_by_id.return_value = sample_target_company
        mock_services['discovery_service'].discover_similar_companies.return_value = DiscoveryResult(
            target_company="Target Corp",
            suggestions=[],
            total_suggestions=0
        )
        
        result = await pipeline.discover_and_validate_similar_companies("target-123")
        
        assert result == []
        mock_services['scraper'].scrape_company_comprehensive.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_crawl_candidate_companies_success(
        self, 
        pipeline, 
        mock_services,
        sample_discovery_result,
        sample_crawled_companies
    ):
        """Test successful crawling of candidate companies"""
        mock_services['scraper'].scrape_company_comprehensive.side_effect = sample_crawled_companies
        
        result = await pipeline._crawl_candidate_companies(sample_discovery_result.suggestions)
        
        assert len(result) == 2
        assert all(isinstance(company, CompanyData) for company in result)
        assert result[0].name == "Similar Corp A"
        assert result[1].name == "Similar Corp B"
        
        # Verify scraper was called with proper CompanyData objects
        assert mock_services['scraper'].scrape_company_comprehensive.call_count == 2
    
    @pytest.mark.asyncio
    async def test_crawl_candidate_companies_with_failures(
        self, 
        pipeline, 
        mock_services,
        sample_discovery_result,
        sample_crawled_companies
    ):
        """Test crawling with some failures"""
        # First crawl succeeds, second fails
        mock_services['scraper'].scrape_company_comprehensive.side_effect = [
            sample_crawled_companies[0],
            None  # Scraping failed
        ]
        
        result = await pipeline._crawl_candidate_companies(sample_discovery_result.suggestions)
        
        assert len(result) == 1  # Only successful crawl
        assert result[0].name == "Similar Corp A"
    
    @pytest.mark.asyncio
    async def test_crawl_candidate_companies_no_urls(self, pipeline, mock_services):
        """Test crawling when suggestions have no URLs"""
        suggestions = [
            CompanySuggestion(
                company_name="No URL Company",
                website_url=None,
                suggested_reason="Test"
            )
        ]
        
        result = await pipeline._crawl_candidate_companies(suggestions)
        
        assert result == []
        mock_services['scraper'].scrape_company_comprehensive.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_validate_similarities_filtering(
        self,
        pipeline,
        mock_services,
        sample_target_company,
        sample_crawled_companies,
        sample_similarity_results
    ):
        """Test similarity validation with filtering"""
        # Mock discovery result (not used in this method but needed for type)
        discovery_result = DiscoveryResult(target_company="Target Corp", suggestions=[], total_suggestions=0)
        
        mock_services['similarity_validator'].validate_similarity.side_effect = sample_similarity_results
        
        result = await pipeline._validate_similarities(
            sample_target_company,
            sample_crawled_companies,
            discovery_result
        )
        
        # Should only return the one that passed validation
        assert len(result) == 1
        assert result[0].similar_company_name == "Similar Corp A"
        assert result[0].similarity_score == 0.75
    
    @pytest.mark.asyncio
    async def test_validate_similarities_all_rejected(
        self,
        pipeline,
        mock_services,
        sample_target_company,
        sample_crawled_companies
    ):
        """Test similarity validation when all candidates rejected"""
        # Mock all similarities as rejected
        rejected_results = [
            SimilarityResult(
                company_a_name="Target Corp",
                company_b_name="Similar Corp A",
                is_similar=False,
                confidence=0.3,
                overall_score=0.3,
                methods_used=["structured"],
                method_scores=[],
                votes=[],
                reasoning=["Too different"]
            ),
            SimilarityResult(
                company_a_name="Target Corp", 
                company_b_name="Similar Corp B",
                is_similar=False,
                confidence=0.2,
                overall_score=0.2,
                methods_used=["structured"],
                method_scores=[],
                votes=[],
                reasoning=["Too different"]
            )
        ]
        
        discovery_result = DiscoveryResult(target_company="Target Corp", suggestions=[], total_suggestions=0)
        mock_services['similarity_validator'].validate_similarity.side_effect = rejected_results
        
        result = await pipeline._validate_similarities(
            sample_target_company,
            sample_crawled_companies,
            discovery_result
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_store_similarity_relationships_success(self, pipeline, mock_services):
        """Test successful storage of similarity relationships"""
        similarities = [
            CompanySimilarity(
                original_company_id="target-123",
                similar_company_id="similar-123", 
                original_company_name="Target Corp",
                similar_company_name="Similar Corp",
                similarity_score=0.8,
                confidence=0.9
            )
        ]
        
        mock_services['pinecone_client'].store_similarity_relationships.return_value = True
        
        result = await pipeline._store_similarity_relationships(similarities)
        
        assert result == True
        mock_services['pinecone_client'].store_similarity_relationships.assert_called_once_with(similarities)
    
    @pytest.mark.asyncio
    async def test_store_similarity_relationships_failure(self, pipeline, mock_services):
        """Test failed storage of similarity relationships"""
        similarities = [
            CompanySimilarity(
                original_company_id="target-123",
                similar_company_id="similar-123",
                original_company_name="Target Corp", 
                similar_company_name="Similar Corp",
                similarity_score=0.8,
                confidence=0.9
            )
        ]
        
        mock_services['pinecone_client'].store_similarity_relationships.return_value = False
        
        result = await pipeline._store_similarity_relationships(similarities)
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_batch_discover_similarities(
        self,
        pipeline,
        mock_services,
        sample_target_company
    ):
        """Test batch discovery of similarities"""
        company_ids = ["company1", "company2", "company3"]
        
        # Mock successful discovery for all companies
        mock_similarities = [
            CompanySimilarity(
                original_company_id=f"company{i}",
                similar_company_id=f"similar{i}",
                original_company_name=f"Company {i}",
                similar_company_name=f"Similar {i}",
                similarity_score=0.8,
                confidence=0.9
            )
            for i in range(1, 4)
        ]
        
        # Mock the discover_and_validate method to return different results for each company
        async def mock_discover(company_id, limit=5):
            index = int(company_id[-1]) - 1  # Extract index from company_id
            return [mock_similarities[index]]
        
        with patch.object(pipeline, 'discover_and_validate_similar_companies', side_effect=mock_discover):
            results = await pipeline.batch_discover_similarities(company_ids, limit_per_company=3)
        
        assert len(results) == 3
        assert all(company_id in results for company_id in company_ids)
        assert all(len(similarities) == 1 for similarities in results.values())
    
    @pytest.mark.asyncio
    async def test_batch_discover_similarities_with_failures(self, pipeline):
        """Test batch discovery with some failures"""
        company_ids = ["company1", "company2", "company3"]
        
        # Mock mixed success/failure
        async def mock_discover(company_id, limit=5):
            if company_id == "company2":
                raise Exception("Discovery failed")
            return [
                CompanySimilarity(
                    original_company_id=company_id,
                    similar_company_id=f"similar-{company_id}",
                    original_company_name=f"Company {company_id}",
                    similar_company_name=f"Similar {company_id}",
                    similarity_score=0.8,
                    confidence=0.9
                )
            ]
        
        with patch.object(pipeline, 'discover_and_validate_similar_companies', side_effect=mock_discover):
            results = await pipeline.batch_discover_similarities(company_ids)
        
        assert len(results) == 3
        assert len(results["company1"]) == 1  # Success
        assert len(results["company2"]) == 0  # Failed
        assert len(results["company3"]) == 1  # Success
    
    @pytest.mark.asyncio
    async def test_query_similar_companies(self, pipeline, mock_services):
        """Test querying existing similar companies"""
        mock_similarities = [
            CompanySimilarity(
                original_company_id="target-123",
                similar_company_id="similar1",
                original_company_name="Target Corp",
                similar_company_name="Similar 1",
                similarity_score=0.8,
                confidence=0.9
            )
        ]
        
        mock_services['pinecone_client'].find_similar_companies.return_value = mock_similarities
        
        result = await pipeline.query_similar_companies("target-123", limit=10)
        
        assert result == mock_similarities
        mock_services['pinecone_client'].find_similar_companies.assert_called_once_with("target-123", limit=10)
    
    def test_get_method_score(self, pipeline):
        """Test extraction of method-specific scores"""
        similarity_result = SimilarityResult(
            company_a_name="A",
            company_b_name="B",
            is_similar=True,
            confidence=0.8,
            overall_score=0.75,
            methods_used=["structured", "embedding"],
            method_scores=[
                SimilarityScore(method="structured", score=0.7, is_similar=True, details={}),
                SimilarityScore(method="embedding", score=0.8, is_similar=True, details={})
            ],
            votes=[],
            reasoning=[]
        )
        
        structured_score = pipeline._get_method_score(similarity_result, "structured")
        embedding_score = pipeline._get_method_score(similarity_result, "embedding")
        missing_score = pipeline._get_method_score(similarity_result, "llm_judge")
        
        assert structured_score == 0.7
        assert embedding_score == 0.8
        assert missing_score is None
    
    def test_get_pipeline_stats(self, pipeline):
        """Test pipeline statistics reporting"""
        stats = pipeline.get_pipeline_stats()
        
        assert "max_candidates" in stats
        assert "similarity_threshold" in stats
        assert "require_votes" in stats
        assert "services_initialized" in stats
        
        services = stats["services_initialized"]
        assert all(services.values())  # All services should be initialized


if __name__ == "__main__":
    pytest.main([__file__])