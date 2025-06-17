#!/usr/bin/env python3
"""
Unit tests for SaaS Classification System
Test-driven development approach - tests written first
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import CompanyData, SaaSCategory, ClassificationResult
from classification.saas_classifier import SaaSBusinessModelClassifier


class TestSaaSCategory:
    """Test the SaaSCategory enum"""
    
    def test_saas_categories_exist(self):
        """Test that SaaS categories are properly defined"""
        # SaaS Verticals
        assert SaaSCategory.ADTECH == "AdTech"
        assert SaaSCategory.FINTECH == "FinTech"
        assert SaaSCategory.MARTECH_CRM == "Martech & CRM"
        
        # Non-SaaS Categories
        assert SaaSCategory.FINANCIAL_SERVICES == "Financial Services"
        assert SaaSCategory.MANUFACTURING == "Manufacturing"
        
        # Special category
        assert SaaSCategory.UNCLASSIFIED == "Unclassified"
    
    def test_category_count(self):
        """Test that we have all 59 categories plus unclassified"""
        categories = list(SaaSCategory)
        # 33 SaaS + 25 Non-SaaS + 1 Unclassified = 59 total categories
        assert len(categories) == 60  # Including Unclassified


class TestClassificationResult:
    """Test the ClassificationResult model"""
    
    def test_classification_result_creation(self):
        """Test creating a classification result"""
        result = ClassificationResult(
            category=SaaSCategory.ADTECH,
            confidence=0.85,
            justification="Company provides advertising technology platforms with subscription pricing.",
            model_version="v1.0",
            timestamp=datetime.now(),
            is_saas=True
        )
        
        assert result.category == SaaSCategory.ADTECH
        assert result.confidence == 0.85
        assert result.is_saas == True
        assert "advertising technology" in result.justification
    
    def test_confidence_validation(self):
        """Test confidence score validation"""
        # Valid confidence scores
        for confidence in [0.0, 0.5, 1.0]:
            result = ClassificationResult(
                category=SaaSCategory.FINTECH,
                confidence=confidence,
                justification="Test justification",
                model_version="v1.0",
                timestamp=datetime.now(),
                is_saas=True
            )
            assert result.confidence == confidence


class TestSaaSBusinessModelClassifier:
    """Test the main classifier class"""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for testing"""
        client = Mock()
        client.generate_response.return_value = """
        Classification: AdTech
        Confidence: 0.85
        Justification: Company provides advertising optimization platforms with SaaS pricing model.
        Is_SaaS: true
        """
        return client
    
    @pytest.fixture
    def classifier(self, mock_ai_client):
        """Create classifier instance with mocked AI client"""
        return SaaSBusinessModelClassifier(mock_ai_client)
    
    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing"""
        return CompanyData(
            name="TestCorp",
            website="https://testcorp.com",
            business_intelligence="TestCorp provides advertising technology solutions for digital marketers. Our SaaS platform helps optimize ad campaigns across multiple channels with real-time analytics and automated bidding.",
            value_proposition="Increase ad ROI by 40% with our AI-powered optimization platform",
            products_services_offered=["Ad optimization platform", "Campaign analytics", "Automated bidding"],
            industry="Advertising Technology"
        )
    
    def test_classifier_initialization(self, mock_ai_client):
        """Test classifier initializes properly"""
        classifier = SaaSBusinessModelClassifier(mock_ai_client)
        assert classifier.ai_client == mock_ai_client
        assert classifier.model_version == "v1.0"
        assert len(classifier.taxonomy) > 0
    
    def test_classify_company_saas(self, classifier, sample_company_data):
        """Test classifying a SaaS company"""
        result = classifier.classify_company(sample_company_data)
        
        assert isinstance(result, ClassificationResult)
        assert result.category == SaaSCategory.ADTECH
        assert result.confidence == 0.85
        assert result.is_saas == True
        assert "advertising" in result.justification.lower()
    
    def test_classify_company_non_saas(self, classifier, mock_ai_client):
        """Test classifying a Non-SaaS company"""
        # Update mock for non-SaaS response
        mock_ai_client.generate_response.return_value = """
        Classification: Manufacturing
        Confidence: 0.92
        Justification: Company manufactures and sells physical automotive parts.
        Is_SaaS: false
        """
        
        non_saas_company = CompanyData(
            name="AutoParts Inc",
            website="https://autoparts.com",
            business_intelligence="AutoParts Inc manufactures high-quality automotive components for the automotive industry. We produce brake pads, filters, and engine parts sold through distributors.",
            value_proposition="Premium automotive parts with 5-year warranty",
            products_services_offered=["Brake pads", "Air filters", "Engine components"],
            industry="Automotive Manufacturing"
        )
        
        result = classifier.classify_company(non_saas_company)
        
        assert result.category == SaaSCategory.MANUFACTURING
        assert result.confidence == 0.92
        assert result.is_saas == False
    
    def test_prepare_classification_input(self, classifier, sample_company_data):
        """Test input preparation for classification"""
        input_text = classifier._prepare_classification_input(sample_company_data)
        
        assert "TestCorp" in input_text
        assert "advertising technology" in input_text.lower()
        assert "testcorp.com" in input_text
        assert "Ad optimization platform" in input_text
    
    def test_parse_classification_response(self, classifier):
        """Test parsing LLM response"""
        response = """
        Classification: FinTech
        Confidence: 0.78
        Justification: Company provides digital payment processing with subscription model.
        Is_SaaS: true
        """
        
        result = classifier._parse_classification_response(response)
        
        assert result.category == SaaSCategory.FINTECH
        assert result.confidence == 0.78
        assert result.is_saas == True
        assert "payment processing" in result.justification
    
    def test_invalid_response_handling(self, classifier):
        """Test handling of invalid LLM responses"""
        invalid_response = "This is not a valid classification response"
        
        result = classifier._parse_classification_response(invalid_response)
        
        assert result.category == SaaSCategory.UNCLASSIFIED
        assert result.confidence == 0.0
        assert "parsing failed" in result.justification.lower()
    
    def test_validate_classification(self, classifier):
        """Test classification validation"""
        # Valid classification
        valid_result = ClassificationResult(
            category=SaaSCategory.ADTECH,
            confidence=0.85,
            justification="Valid justification with sufficient detail.",
            model_version="v1.0",
            timestamp=datetime.now(),
            is_saas=True
        )
        assert classifier._validate_classification(valid_result) == True
        
        # Invalid classification - low confidence with insufficient justification
        invalid_result = ClassificationResult(
            category=SaaSCategory.UNCLASSIFIED,
            confidence=0.3,
            justification="No info",
            model_version="v1.0",
            timestamp=datetime.now(),
            is_saas=False
        )
        assert classifier._validate_classification(invalid_result) == False


class TestCompanyDataExtensions:
    """Test the extended CompanyData model with classification fields"""
    
    def test_company_data_with_classification(self):
        """Test CompanyData with classification fields"""
        company = CompanyData(
            name="TestCorp",
            website="https://testcorp.com",
            saas_classification="AdTech",
            classification_confidence=0.85,
            classification_justification="Company provides SaaS advertising platform",
            classification_timestamp=datetime.now(),
            is_saas=True
        )
        
        assert company.saas_classification == "AdTech"
        assert company.classification_confidence == 0.85
        assert company.is_saas == True
        assert company.classification_justification is not None
    
    def test_company_data_without_classification(self):
        """Test CompanyData without classification (backwards compatibility)"""
        company = CompanyData(
            name="TestCorp",
            website="https://testcorp.com"
        )
        
        assert company.saas_classification is None
        assert company.classification_confidence is None
        assert company.is_saas is None


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])