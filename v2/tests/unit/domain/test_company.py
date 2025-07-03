"""
Unit tests for Company domain entity.
"""

import pytest
from datetime import datetime
from v2.src.core.domain.entities.company import (
    Company, CompanyStage, TechSophistication, BusinessModel, CompanySize
)


class TestCompanyEntity:
    """Test suite for Company entity"""
    
    def test_create_minimal_company(self):
        """Test creating company with minimal required fields"""
        company = Company(
            name="Acme Corp",
            website="https://acme.com"
        )
        
        assert company.name == "Acme Corp"
        assert company.website == "https://acme.com"
        assert company.id is not None
        assert isinstance(company.created_at, datetime)
        
    def test_website_normalization(self):
        """Test website URL normalization"""
        # Add https if missing
        company = Company(name="Test", website="acme.com")
        assert company.website == "https://acme.com"
        
        # Lowercase
        company = Company(name="Test", website="HTTPS://ACME.COM")
        assert company.website == "https://acme.com"
    
    def test_website_validation(self):
        """Test website validation rules"""
        with pytest.raises(ValueError, match="Website cannot be empty"):
            Company(name="Test", website="")
        
        with pytest.raises(ValueError, match="Invalid website URL"):
            Company(name="Test", website="not a url")
        
        with pytest.raises(ValueError, match="Invalid website URL"):
            Company(name="Test", website="https://no-dot")
    
    def test_email_validation(self):
        """Test email validation"""
        company = Company(
            name="Test",
            website="test.com",
            contact_email="info@test.com"
        )
        assert company.contact_email == "info@test.com"
        
        # Invalid email
        with pytest.raises(ValueError, match="Invalid email format"):
            Company(
                name="Test",
                website="test.com", 
                contact_email="not-an-email"
            )
    
    def test_founding_year_validation(self):
        """Test founding year validation"""
        current_year = datetime.now().year
        
        # Valid year
        company = Company(
            name="Test",
            website="test.com",
            founding_year=2020
        )
        assert company.founding_year == 2020
        
        # Future year
        with pytest.raises(ValueError, match="Founding year cannot be in the future"):
            Company(
                name="Test",
                website="test.com",
                founding_year=current_year + 1
            )
        
        # Too old
        with pytest.raises(ValueError):
            Company(
                name="Test",
                website="test.com",
                founding_year=1799
            )
    
    def test_enum_fields(self):
        """Test enum field assignments"""
        company = Company(
            name="Test",
            website="test.com",
            business_model=BusinessModel.SAAS,
            company_stage=CompanyStage.GROWTH,
            tech_sophistication=TechSophistication.HIGH,
            company_size=CompanySize.MEDIUM
        )
        
        assert company.business_model == BusinessModel.SAAS
        assert company.company_stage == CompanyStage.GROWTH
        assert company.tech_sophistication == TechSophistication.HIGH
        assert company.company_size == CompanySize.MEDIUM
    
    def test_list_field_limits(self):
        """Test list field maximum items"""
        # Create list with too many items
        too_many_products = [f"Product {i}" for i in range(101)]
        
        with pytest.raises(ValueError):
            Company(
                name="Test",
                website="test.com",
                products_services=too_many_products
            )
    
    def test_data_quality_score(self):
        """Test data quality score calculation"""
        # Minimal company
        company = Company(name="Test", website="test.com")
        score = company.calculate_data_quality_score()
        assert score < 0.2
        
        # Complete company
        company = Company(
            name="Test Corp",
            website="test.com",
            industry="Software",
            business_model=BusinessModel.SAAS,
            description="Test company",
            value_proposition="Test value",
            target_market="Enterprises",
            founding_year=2020,
            headquarters_location="San Francisco",
            employee_count=100,
            products_services=["Product A"],
            tech_stack=["Python"],
            leadership_team={"CEO": "John Doe"},
            certifications=["ISO 9001"]
        )
        score = company.calculate_data_quality_score()
        assert score == 1.0
    
    def test_is_tech_company(self):
        """Test tech company detection"""
        # Non-tech company
        company = Company(
            name="Bakery",
            website="bakery.com",
            industry="Food Service"
        )
        assert not company.is_tech_company()
        
        # Tech company
        company = Company(
            name="TechCorp",
            website="tech.com",
            industry="Software",
            business_model=BusinessModel.SAAS,
            tech_sophistication=TechSophistication.HIGH,
            tech_stack=["Python", "React", "AWS", "Docker", "K8s", "Redis"]
        )
        assert company.is_tech_company()
    
    def test_embedding_text_generation(self):
        """Test embedding text generation"""
        company = Company(
            name="Acme Corp",
            website="acme.com",
            industry="Software",
            business_model=BusinessModel.SAAS,
            description="Leading SaaS provider",
            value_proposition="10x faster deployments",
            target_market="DevOps teams",
            products_services=["CI/CD Platform", "Monitoring"],
            tech_stack=["Python", "Go", "Kubernetes"]
        )
        
        embedding_text = company.to_embedding_text()
        
        assert "Company: Acme Corp" in embedding_text
        assert "Industry: Software" in embedding_text
        assert "Business Model: saas" in embedding_text
        assert "CI/CD Platform" in embedding_text
        assert "Python" in embedding_text
    
    def test_serialization(self):
        """Test model serialization"""
        company = Company(
            name="Test Corp",
            website="test.com",
            industry="Technology",
            tech_stack=["Python", "React"],
            social_media={"twitter": "https://twitter.com/test"}
        )
        
        # To dict
        data = company.model_dump()
        assert data["name"] == "Test Corp"
        assert data["tech_stack"] == ["Python", "React"]
        
        # To JSON
        json_str = company.model_dump_json()
        assert "Test Corp" in json_str
        
        # From dict
        company2 = Company(**data)
        assert company2.name == company.name
        assert company2.id == company.id
    
    def test_real_company_example(self):
        """Test with real company data from v1"""
        stripe_data = {
            "name": "Stripe",
            "website": "https://stripe.com",
            "industry": "Financial Technology",
            "business_model": BusinessModel.SAAS,
            "company_size": CompanySize.LARGE,
            "description": "Online payment processing for internet businesses",
            "value_proposition": "Payments infrastructure for the internet",
            "target_market": "Online businesses and platforms",
            "products_services": [
                "Payments API",
                "Stripe Connect",
                "Stripe Billing",
                "Stripe Radar"
            ],
            "tech_stack": [
                "Ruby", "Go", "JavaScript", "React", "AWS", 
                "PostgreSQL", "Redis", "Kafka"
            ],
            "founding_year": 2010,
            "headquarters_location": "San Francisco, CA",
            "tech_sophistication": TechSophistication.HIGH,
            "has_api": True,
            "certifications": ["PCI DSS Level 1", "SOC 2"],
            "social_media": {
                "twitter": "https://twitter.com/stripe",
                "linkedin": "https://linkedin.com/company/stripe"
            }
        }
        
        stripe = Company(**stripe_data)
        
        assert stripe.is_tech_company()
        assert stripe.calculate_data_quality_score() > 0.8
        assert "Financial Technology" in stripe.to_embedding_text()