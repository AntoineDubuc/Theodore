"""
Unit tests for SimilarityResult domain entity.
"""

import pytest
from datetime import datetime
from v2.src.core.domain.entities.similarity import (
    SimilarityResult, SimilarCompany, SimilarityMethod,
    RelationshipType, ConfidenceLevel, SimilarityDimension
)


class TestSimilarityResultEntity:
    """Test suite for SimilarityResult entity"""
    
    def test_create_similarity_result(self):
        """Test creating similarity result"""
        result = SimilarityResult(
            source_company_name="Stripe",
            primary_method=SimilarityMethod.VECTOR_SEARCH
        )
        
        assert result.source_company_name == "Stripe"
        assert result.primary_method == SimilarityMethod.VECTOR_SEARCH
        assert result.total_found == 0
        assert result.similar_companies == []
    
    def test_add_similar_company(self):
        """Test adding similar companies"""
        result = SimilarityResult(
            source_company_name="Stripe",
            primary_method=SimilarityMethod.VECTOR_SEARCH
        )
        
        # Add company
        similar = SimilarCompany(
            name="Square",
            website="https://square.com",
            industry="Payments",
            discovery_method=SimilarityMethod.VECTOR_SEARCH
        )
        
        result.add_company(
            similar,
            relationship=RelationshipType.COMPETITOR,
            confidence=0.85,
            reasoning=["Both are payment processors", "Similar target market"]
        )
        
        assert result.total_found == 1
        assert len(result.similar_companies) == 1
        
        company = result.similar_companies[0]
        assert company.name == "Square"
        assert hasattr(company, 'relationship_type')
        assert hasattr(company, 'confidence')
        assert company.confidence == 0.85
    
    def test_similarity_dimensions(self):
        """Test similarity dimension tracking"""
        result = SimilarityResult(
            source_company_name="Salesforce",
            primary_method=SimilarityMethod.HYBRID
        )
        
        # Add dimensions
        result.add_dimension(
            "industry",
            0.9,
            ["Both in CRM", "Enterprise software"]
        )
        
        result.add_dimension(
            "business_model",
            0.85,
            ["SaaS", "Subscription-based"]
        )
        
        result.add_dimension(
            "target_market",
            0.7,
            ["Enterprise customers", "Sales teams"]
        )
        
        assert len(result.similarity_dimensions) == 3
        assert result.overall_confidence == pytest.approx(0.816, rel=0.01)
        assert result.confidence_level == ConfidenceLevel.HIGH
    
    def test_confidence_levels(self):
        """Test confidence level categorization"""
        result = SimilarityResult(
            source_company_name="Test",
            primary_method=SimilarityMethod.LLM_SUGGESTION
        )
        
        # Test different confidence scores
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.8, ConfidenceLevel.HIGH),
            (0.6, ConfidenceLevel.MEDIUM),
            (0.4, ConfidenceLevel.LOW),
            (0.2, ConfidenceLevel.VERY_LOW)
        ]
        
        for score, expected_level in test_cases:
            result.overall_confidence = score
            assert result.confidence_level == expected_level
    
    def test_company_filtering(self):
        """Test filtering companies by criteria"""
        result = SimilarityResult(
            source_company_name="Uber",
            primary_method=SimilarityMethod.GOOGLE_SEARCH
        )
        
        # Add various companies
        companies_data = [
            ("Lyft", RelationshipType.COMPETITOR, 0.9),
            ("DoorDash", RelationshipType.SIMILAR, 0.7),
            ("Airbnb", RelationshipType.SIMILAR, 0.6),
            ("GrubHub", RelationshipType.SIMILAR, 0.8),
            ("Instacart", RelationshipType.COMPLEMENTARY, 0.5)
        ]
        
        for name, rel_type, confidence in companies_data:
            company = SimilarCompany(
                name=name,
                website=f"https://{name.lower()}.com",
                discovery_method=SimilarityMethod.GOOGLE_SEARCH
            )
            result.add_company(company, rel_type, confidence)
        
        # Filter high confidence
        high_conf = result.get_high_confidence_companies(0.7)
        assert len(high_conf) == 3
        
        # Filter by relationship
        competitors = result.get_companies_by_relationship(RelationshipType.COMPETITOR)
        assert len(competitors) == 1
        assert competitors[0].name == "Lyft"
    
    def test_enrichment_tracking(self):
        """Test tracking companies needing enrichment"""
        result = SimilarityResult(
            source_company_name="Netflix",
            primary_method=SimilarityMethod.HYBRID
        )
        
        # Company in database
        company1 = SimilarCompany(
            id="123",
            name="Hulu",
            website="https://hulu.com",
            discovery_method=SimilarityMethod.VECTOR_SEARCH,
            requires_research=False
        )
        
        # Company not in database
        company2 = SimilarCompany(
            name="Disney+",
            website="https://disneyplus.com",
            discovery_method=SimilarityMethod.GOOGLE_SEARCH,
            requires_research=True
        )
        
        result.similar_companies = [company1, company2]
        result.total_found = 2
        
        assert result.needs_enrichment_count() == 1
        assert company1.needs_enrichment() is False
        assert company2.needs_enrichment() is True
    
    def test_search_metadata(self):
        """Test search metadata tracking"""
        result = SimilarityResult(
            source_company_name="Shopify",
            primary_method=SimilarityMethod.GOOGLE_SEARCH,
            requested_limit=20
        )
        
        result.search_queries = [
            "e-commerce platforms like Shopify",
            "Shopify competitors",
            "online store builders"
        ]
        
        result.filters_applied = {
            "business_model": "saas",
            "min_company_size": 50
        }
        
        result.search_api_calls = 3
        result.ai_tokens_used = 5000
        result.discovery_duration_seconds = 12.5
        
        assert len(result.search_queries) == 3
        assert result.filters_applied["business_model"] == "saas"
        assert result.search_api_calls == 3
    
    def test_result_summary(self):
        """Test result summary generation"""
        result = SimilarityResult(
            source_company_name="Slack",
            primary_method=SimilarityMethod.HYBRID,
            overall_confidence=0.82
        )
        
        # Add some companies
        companies = [
            ("Microsoft Teams", 0.9),
            ("Discord", 0.8),
            ("Zoom", 0.7),
            ("Mattermost", 0.6)
        ]
        
        for name, confidence in companies:
            company = SimilarCompany(
                name=name,
                website=f"https://{name.lower().replace(' ', '')}.com",
                discovery_method=SimilarityMethod.HYBRID
            )
            result.add_company(company, RelationshipType.COMPETITOR, confidence)
        
        summary = result.to_summary()
        
        assert summary["source_company"] == "Slack"
        assert summary["total_found"] == 4
        assert summary["confidence_level"] == "high"
        assert summary["primary_method"] == "hybrid"
        assert len(summary["top_companies"]) == 4
        assert summary["top_companies"][0]["name"] == "Microsoft Teams"
    
    def test_multiple_discovery_methods(self):
        """Test tracking multiple discovery methods"""
        result = SimilarityResult(
            source_company_name="Airbnb",
            primary_method=SimilarityMethod.HYBRID
        )
        
        result.methods_used = [
            SimilarityMethod.VECTOR_SEARCH,
            SimilarityMethod.GOOGLE_SEARCH,
            SimilarityMethod.LLM_SUGGESTION
        ]
        
        assert len(result.methods_used) == 3
        assert SimilarityMethod.VECTOR_SEARCH in result.methods_used
    
    def test_serialization(self):
        """Test similarity result serialization"""
        result = SimilarityResult(
            source_company_name="GitHub",
            source_company_id="gh123",
            primary_method=SimilarityMethod.VECTOR_SEARCH
        )
        
        # Add company and dimension
        company = SimilarCompany(
            name="GitLab",
            website="https://gitlab.com",
            discovery_method=SimilarityMethod.VECTOR_SEARCH
        )
        result.add_company(company, RelationshipType.COMPETITOR, 0.88)
        result.add_dimension("features", 0.9, ["Version control", "CI/CD"])
        
        # Serialize
        data = result.model_dump()
        assert data["source_company_name"] == "GitHub"
        assert len(data["similar_companies"]) == 1
        assert len(data["similarity_dimensions"]) == 1
        
        # Deserialize
        result2 = SimilarityResult(**data)
        assert result2.source_company_name == result.source_company_name
        assert len(result2.similar_companies) == 1
        assert result2.overall_confidence == result.overall_confidence