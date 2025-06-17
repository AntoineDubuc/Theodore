#!/usr/bin/env python3
"""
Manual test script for SaaS Classification System
Tests basic functionality without external dependencies
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from models import CompanyData, SaaSCategory, ClassificationResult
from classification.saas_classifier import SaaSBusinessModelClassifier
from classification.classification_prompts import get_classification_prompt
from datetime import datetime


class MockAIClient:
    """Mock AI client for testing"""
    
    def __init__(self, response=None):
        self.response = response or """
        Classification: AdTech
        Confidence: 0.85
        Justification: Company provides advertising technology platforms with subscription pricing.
        Is_SaaS: true
        """
    
    def generate_response(self, prompt):
        return self.response


def test_saas_category_enum():
    """Test SaaSCategory enum"""
    print("🧪 Testing SaaSCategory enum...")
    
    # Test basic categories
    assert SaaSCategory.ADTECH == "AdTech"
    assert SaaSCategory.FINTECH == "FinTech"
    assert SaaSCategory.MANUFACTURING == "Manufacturing"
    assert SaaSCategory.UNCLASSIFIED == "Unclassified"
    
    # Test category count (26 SaaS + 17 Non-SaaS + 1 Unclassified = 44)
    categories = list(SaaSCategory)
    print(f"   Total categories: {len(categories)}")
    assert len(categories) == 44
    
    print("   ✅ SaaSCategory enum tests passed")


def test_classification_result():
    """Test ClassificationResult model"""
    print("🧪 Testing ClassificationResult model...")
    
    result = ClassificationResult(
        category=SaaSCategory.ADTECH,
        confidence=0.85,
        justification="Company provides advertising technology platforms",
        model_version="v1.0",
        timestamp=datetime.now(),
        is_saas=True
    )
    
    assert result.category == SaaSCategory.ADTECH
    assert result.confidence == 0.85
    assert result.is_saas == True
    
    print("   ✅ ClassificationResult model tests passed")


def test_company_data_with_classification():
    """Test CompanyData with new classification fields"""
    print("🧪 Testing CompanyData with classification fields...")
    
    company = CompanyData(
        name="TestCorp",
        website="https://testcorp.com",
        saas_classification="AdTech",
        classification_confidence=0.85,
        is_saas=True
    )
    
    assert company.saas_classification == "AdTech"
    assert company.classification_confidence == 0.85
    assert company.is_saas == True
    
    print("   ✅ CompanyData classification fields tests passed")


def test_classification_prompt():
    """Test classification prompt generation"""
    print("🧪 Testing classification prompt generation...")
    
    company = CompanyData(
        name="TestCorp",
        website="https://testcorp.com",
        ai_summary="TestCorp provides advertising technology solutions",
        value_proposition="Optimize ad campaigns with AI",
        products_services_offered=["Ad optimization", "Analytics"]
    )
    
    prompt = get_classification_prompt(company)
    
    assert "TestCorp" in prompt
    assert "advertising technology" in prompt
    assert "CLASSIFICATION TAXONOMY:" in prompt
    assert "AdTech" in prompt
    
    print("   ✅ Classification prompt tests passed")


def test_classifier_initialization():
    """Test classifier initialization"""
    print("🧪 Testing classifier initialization...")
    
    mock_client = MockAIClient()
    classifier = SaaSBusinessModelClassifier(mock_client)
    
    assert classifier.ai_client == mock_client
    assert classifier.model_version == "v1.0"
    assert len(classifier.taxonomy) > 0
    
    print("   ✅ Classifier initialization tests passed")


def test_parse_classification_response():
    """Test parsing LLM responses"""
    print("🧪 Testing classification response parsing...")
    
    mock_client = MockAIClient()
    classifier = SaaSBusinessModelClassifier(mock_client)
    
    # Test valid response
    valid_response = """
    Classification: FinTech
    Confidence: 0.78
    Justification: Company provides digital payment processing with subscription model.
    Is_SaaS: true
    """
    
    result = classifier._parse_classification_response(valid_response)
    
    assert result.category == SaaSCategory.FINTECH
    assert result.confidence == 0.78
    assert result.is_saas == True
    assert "payment processing" in result.justification
    
    # Test invalid response
    invalid_response = "This is not a valid response"
    result = classifier._parse_classification_response(invalid_response)
    
    assert result.category == SaaSCategory.UNCLASSIFIED
    assert result.confidence == 0.0
    
    print("   ✅ Response parsing tests passed")


def test_full_classification_flow():
    """Test complete classification workflow"""
    print("🧪 Testing full classification workflow...")
    
    # Create mock AI client with SaaS response
    mock_client = MockAIClient()
    classifier = SaaSBusinessModelClassifier(mock_client)
    
    # Create sample company
    company = CompanyData(
        name="AdTech Corp",
        website="https://adtech-corp.com",
        ai_summary="AdTech Corp provides advertising optimization platforms for digital marketers. Our SaaS platform helps optimize ad campaigns.",
        value_proposition="Increase ad ROI by 40%",
        products_services_offered=["Ad optimization", "Campaign analytics"],
        industry="Advertising Technology"
    )
    
    # Classify
    result = classifier.classify_company(company)
    
    assert isinstance(result, ClassificationResult)
    assert result.category == SaaSCategory.ADTECH
    assert result.confidence == 0.85
    assert result.is_saas == True
    
    print("   ✅ Full classification workflow tests passed")


def test_non_saas_classification():
    """Test Non-SaaS classification"""
    print("🧪 Testing Non-SaaS classification...")
    
    # Mock response for manufacturing company
    manufacturing_response = """
    Classification: Manufacturing
    Confidence: 0.92
    Justification: Company manufactures and sells physical automotive parts.
    Is_SaaS: false
    """
    
    mock_client = MockAIClient(manufacturing_response)
    classifier = SaaSBusinessModelClassifier(mock_client)
    
    company = CompanyData(
        name="AutoParts Inc",
        website="https://autoparts.com",
        ai_summary="AutoParts Inc manufactures automotive components",
        industry="Manufacturing"
    )
    
    result = classifier.classify_company(company)
    
    assert result.category == SaaSCategory.MANUFACTURING
    assert result.is_saas == False
    assert result.confidence == 0.92
    
    print("   ✅ Non-SaaS classification tests passed")


def run_all_tests():
    """Run all manual tests"""
    print("🚀 Starting SaaS Classification Manual Tests\n")
    
    try:
        test_saas_category_enum()
        test_classification_result()
        test_company_data_with_classification()
        test_classification_prompt()
        test_classifier_initialization()
        test_parse_classification_response()
        test_full_classification_flow()
        test_non_saas_classification()
        
        print("\n🎉 All tests passed successfully!")
        print("✅ SaaS Classification System is working correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)