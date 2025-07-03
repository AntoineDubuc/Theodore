"""
Integration tests for domain model interactions.
"""

import pytest
from datetime import datetime, timedelta
from src.core.domain.entities.company import Company, BusinessModel, TechSophistication
from src.core.domain.entities.research import Research, ResearchSource, ResearchPhase
from src.core.domain.entities.similarity import SimilarityResult, SimilarCompany, SimilarityMethod


class TestDomainModelIntegration:
    """Test interactions between domain entities"""
    
    def test_company_research_lifecycle(self):
        """Test complete research lifecycle for a company"""
        # Create company
        company = Company(
            name="Test Corp",
            website="https://test.com",
            industry="Technology",
            business_model=BusinessModel.SAAS
        )
        
        # Create research job for company
        research = Research(
            company_id=company.id,
            company_name=company.name,
            website=company.website,
            source=ResearchSource.CLI
        )
        
        # Verify relationships
        assert research.company_name == company.name
        assert research.website == company.website
        assert research.company_id == company.id
        
        # Run research phases
        research.start()
        
        phase_results = [
            (ResearchPhase.DOMAIN_DISCOVERY, {"pages_found": 1}),
            (ResearchPhase.LINK_DISCOVERY, {"pages_found": 120}),
            (ResearchPhase.PAGE_SELECTION, {"pages_selected": 45}),
            (ResearchPhase.CONTENT_EXTRACTION, {"pages_scraped": 40, "content_length": 500000}),
            (ResearchPhase.AI_ANALYSIS, {"tokens_used": 150000, "cost_usd": 2.25})
        ]
        
        for phase, data in phase_results:
            research.start_phase(phase)
            research.complete_phase(phase, **data)
        
        research.complete()
        
        # Verify research completion
        assert research.status.value == "completed"
        assert research.total_tokens_used == 150000
        assert research.total_cost_usd == 2.25
        assert research.progress_percentage == 100.0
        
        # Update company with research results
        company.description = "Technology company specializing in SaaS solutions"
        company.tech_sophistication = TechSophistication.HIGH
        company.calculate_data_quality_score()
        
        assert company.data_quality_score > 0.5
        assert company.is_tech_company()
    
    def test_similarity_discovery_integration(self):
        """Test similarity discovery with real company data"""
        # Source company
        source_company = Company(
            name="Stripe",
            website="https://stripe.com",
            industry="Financial Technology",
            business_model=BusinessModel.SAAS,
            description="Online payment processing platform"
        )
        
        # Create similarity result
        similarity_result = SimilarityResult(
            source_company_id=source_company.id,
            source_company_name=source_company.name,
            primary_method=SimilarityMethod.HYBRID
        )
        
        # Add similar companies
        similar_companies = [
            {
                "name": "Square",
                "website": "https://square.com",
                "industry": "Financial Technology",
                "business_model": "saas"
            },
            {
                "name": "PayPal",
                "website": "https://paypal.com", 
                "industry": "Financial Technology",
                "business_model": "platform"
            }
        ]
        
        for comp_data in similar_companies:
            similar_company = SimilarCompany(
                name=comp_data["name"],
                website=comp_data["website"],
                industry=comp_data["industry"],
                business_model=comp_data["business_model"],
                discovery_method=SimilarityMethod.VECTOR_SEARCH
            )
            
            similarity_result.add_company(similar_company, confidence=0.85)
        
        # Add similarity dimensions
        similarity_result.add_dimension("industry", 0.95, ["Both in FinTech", "Payment processing"])
        similarity_result.add_dimension("business_model", 0.8, ["SaaS platforms", "API-first"])
        similarity_result.add_dimension("target_market", 0.75, ["Online businesses", "Developers"])
        
        # Verify similarity analysis
        assert similarity_result.total_found == 2
        assert similarity_result.overall_confidence > 0.8
        assert len(similarity_result.similarity_dimensions) == 3
        
        # Test filtering
        high_confidence = similarity_result.get_high_confidence_companies(0.8)
        assert len(high_confidence) == 2
        
        # Generate summary
        summary = similarity_result.to_summary()
        assert summary["source_company"] == "Stripe"
        assert summary["total_found"] == 2
        assert "Square" in [c["name"] for c in summary["top_companies"]]
    
    def test_cross_entity_serialization(self):
        """Test serialization consistency across entities"""
        # Create entities
        company = Company(name="Test Corp", website="test.com")
        research = Research(
            company_id=company.id,
            company_name=company.name,
            source=ResearchSource.API
        )
        similarity = SimilarityResult(
            source_company_id=company.id,
            source_company_name=company.name,
            primary_method=SimilarityMethod.VECTOR_SEARCH
        )
        
        # Test serialization
        company_data = company.model_dump()
        research_data = research.model_dump()
        similarity_data = similarity.model_dump()
        
        # Verify ID consistency
        assert company_data["id"] == research_data["company_id"]
        assert company_data["id"] == similarity_data["source_company_id"]
        assert company_data["name"] == research_data["company_name"]
        assert company_data["name"] == similarity_data["source_company_name"]
        
        # Test deserialization
        company2 = Company(**company_data)
        research2 = Research(**research_data)
        similarity2 = SimilarityResult(**similarity_data)
        
        # Verify relationships maintained
        assert company2.id == research2.company_id
        assert company2.id == similarity2.source_company_id
        assert company2.name == research2.company_name
        assert company2.name == similarity2.source_company_name
    
    def test_research_cost_tracking_integration(self):
        """Test cost tracking across research phases"""
        research = Research(
            company_name="Cost Test Corp",
            source=ResearchSource.BATCH
        )
        
        research.start()
        
        # Simulate expensive research phases
        expensive_phases = [
            (ResearchPhase.AI_ANALYSIS, {"tokens_used": 200000, "cost_usd": 4.50}),
            (ResearchPhase.CLASSIFICATION, {"tokens_used": 50000, "cost_usd": 1.25}),
            (ResearchPhase.EMBEDDING_GENERATION, {"tokens_used": 10000, "cost_usd": 0.25})
        ]
        
        total_expected_tokens = 0
        total_expected_cost = 0.0
        
        for phase, data in expensive_phases:
            research.start_phase(phase)
            research.complete_phase(phase, **data)
            total_expected_tokens += data["tokens_used"]
            total_expected_cost += data["cost_usd"]
        
        research.complete()
        
        # Verify cost aggregation
        assert research.total_tokens_used == total_expected_tokens
        assert research.total_cost_usd == total_expected_cost
        assert research.total_cost_usd == 6.0
        
        # Verify individual phase tracking
        ai_phase_duration = research.get_phase_duration(ResearchPhase.AI_ANALYSIS)
        assert ai_phase_duration is not None
        assert ai_phase_duration >= 0
    
    def test_data_quality_evolution(self):
        """Test how data quality evolves through research"""
        # Start with minimal company
        company = Company(name="Evolving Corp", website="evolving.com")
        initial_score = company.calculate_data_quality_score()
        assert initial_score < 0.3
        
        # Simulate research discoveries
        research_updates = [
            {"industry": "Software"},
            {"business_model": BusinessModel.SAAS},
            {"description": "AI-powered analytics platform"},
            {"value_proposition": "10x faster data insights"},
            {"target_market": "Enterprise data teams"},
            {"founding_year": 2020},
            {"headquarters_location": "San Francisco, CA"},
            {"employee_count": 150}
        ]
        
        # Apply updates and track quality improvement
        scores = [initial_score]
        
        for update in research_updates:
            for key, value in update.items():
                setattr(company, key, value)
            score = company.calculate_data_quality_score()
            scores.append(score)
        
        # Add enriched data
        company.products_services = ["Analytics Platform", "Data Visualization"]
        company.tech_stack = ["Python", "React", "PostgreSQL", "AWS"]
        company.leadership_team = {"CEO": "Jane Smith", "CTO": "John Doe"}
        company.certifications = ["SOC 2", "ISO 27001"]
        
        final_score = company.calculate_data_quality_score()
        scores.append(final_score)
        
        # Verify quality improvement
        assert final_score > initial_score
        assert final_score >= 0.9  # Should be nearly complete
        assert all(scores[i] <= scores[i+1] for i in range(len(scores)-1))  # Monotonically increasing