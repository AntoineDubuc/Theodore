"""
Test cases for similarity engine functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import unittest
from src.models import CompanyData
from src.similarity_engine import SimilarityEngine

class TestSimilarityEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test companies"""
        self.similarity_engine = SimilarityEngine()
        
        # Create test companies
        self.stripe = CompanyData(
            name="Stripe",
            website="https://stripe.com",
            industry="fintech",
            company_stage="enterprise",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global"
        )
        
        self.square = CompanyData(
            name="Square", 
            website="https://squareup.com",
            industry="fintech",
            company_stage="enterprise",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global"
        )
        
        self.visterra = CompanyData(
            name="Visterra",
            website="https://visterra.com",
            industry="biotechnology",
            company_stage="startup",
            tech_sophistication="medium",
            business_model_type="services",
            geographic_scope="regional"
        )
        
        self.openai = CompanyData(
            name="OpenAI",
            website="https://openai.com",
            industry="artificial intelligence",
            company_stage="growth",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global"
        )
        
        self.anthropic = CompanyData(
            name="Anthropic",
            website="https://anthropic.com",
            industry="artificial intelligence",
            company_stage="growth",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global"
        )
    
    def test_high_similarity_fintech(self):
        """Test that Stripe and Square are highly similar"""
        result = self.similarity_engine.calculate_similarity(self.stripe, self.square)
        
        self.assertGreater(result['overall_similarity'], 0.8)
        self.assertIn("similar", result['explanation'].lower())
        print(f"✅ Stripe-Square similarity: {result['overall_similarity']:.3f}")
    
    def test_high_similarity_ai(self):
        """Test that OpenAI and Anthropic are highly similar"""
        result = self.similarity_engine.calculate_similarity(self.openai, self.anthropic)
        
        self.assertGreater(result['overall_similarity'], 0.8)
        self.assertEqual(result['dimension_similarities']['company_stage'], 1.0)
        self.assertEqual(result['dimension_similarities']['tech_sophistication'], 1.0)
        print(f"✅ OpenAI-Anthropic similarity: {result['overall_similarity']:.3f}")
    
    def test_low_similarity_different_domains(self):
        """Test that Stripe and Visterra are not similar"""
        result = self.similarity_engine.calculate_similarity(self.stripe, self.visterra)
        
        self.assertLess(result['overall_similarity'], 0.4)
        self.assertIn("different", result['explanation'].lower())
        print(f"✅ Stripe-Visterra dissimilarity: {result['overall_similarity']:.3f}")
    
    def test_dimension_scores(self):
        """Test individual dimension scoring"""
        result = self.similarity_engine.calculate_similarity(self.stripe, self.square)
        
        # Both are enterprise fintech companies
        self.assertEqual(result['dimension_similarities']['company_stage'], 1.0)
        self.assertGreater(result['dimension_similarities']['industry'], 0.8)
        self.assertEqual(result['dimension_similarities']['tech_sophistication'], 1.0)
        print(f"✅ Dimension scores working correctly")
    
    def test_find_similar_companies(self):
        """Test finding similar companies from a list"""
        companies = [self.square, self.visterra, self.openai, self.anthropic]
        
        similar = self.similarity_engine.find_similar_companies(
            self.stripe, 
            companies, 
            threshold=0.7,
            limit=5
        )
        
        # Should find Square as similar, not others
        self.assertGreater(len(similar), 0)
        self.assertEqual(similar[0][0].name, "Square")
        self.assertGreater(similar[0][1]['overall_similarity'], 0.7)
        print(f"✅ Found {len(similar)} similar companies to Stripe")
    
    def test_confidence_scoring(self):
        """Test confidence score calculation"""
        # Set confidence scores
        self.stripe.stage_confidence = 0.9
        self.stripe.tech_confidence = 0.8
        self.stripe.industry_confidence = 0.95
        
        self.square.stage_confidence = 0.85
        self.square.tech_confidence = 0.9
        self.square.industry_confidence = 0.9
        
        result = self.similarity_engine.calculate_similarity(self.stripe, self.square)
        
        # Should have reasonable overall confidence
        self.assertGreater(result['overall_confidence'], 0.7)
        self.assertIn('dimension_confidences', result)
        print(f"✅ Confidence scoring: {result['overall_confidence']:.3f}")
    
    def test_explanation_generation(self):
        """Test that explanations are generated correctly"""
        result = self.similarity_engine.calculate_similarity(self.openai, self.anthropic)
        
        explanation = result['explanation']
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)
        print(f"✅ Explanation: {explanation}")

if __name__ == '__main__':
    print("🧪 Testing Theodore Similarity Engine...")
    print("=" * 50)
    unittest.main(verbosity=2)