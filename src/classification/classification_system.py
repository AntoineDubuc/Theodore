"""
Simple SaaS Business Model Classifier for batch processing
Uses Amazon Nova Pro model for classification
"""

import json
import re
from typing import Dict, Any, Optional

class SaaSBusinessModelClassifier:
    """
    Simple classifier for business model analysis using Nova Pro
    """
    
    def __init__(self):
        """Initialize the classifier with basic categories"""
        self.categories = [
            "AdTech", "AI/ML Platform", "Analytics Platform", "API Management",
            "Business Intelligence", "CRM", "Customer Support", "DevOps Platform",
            "E-commerce Platform", "HR Tech", "IT Consulting Services", "Marketing Automation",
            "Project Management", "Security Platform", "Social Media Management",
            "Biopharma R&D", "Retail", "Unclassified"
        ]
        
    def classify_company(self, company_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Classify a company's business model
        
        Args:
            company_data: Dictionary with company information
            
        Returns:
            Classification result with category, confidence, etc.
        """
        try:
            # Import bedrock client
            from src.bedrock_client import BedrockClient
            client = BedrockClient()
            
            # Prepare classification prompt
            prompt = self._build_classification_prompt(company_data)
            
            # Get classification from Nova Pro
            response = client.generate_text(prompt, max_tokens=200)
            
            if response and response.get('content'):
                result = self._parse_classification_response(response['content'])
                if result:
                    result['success'] = True
                    return result
            
            # Fallback classification
            return self._fallback_classification(company_data)
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return self._fallback_classification(company_data)
    
    def _build_classification_prompt(self, company_data: Dict[str, Any]) -> str:
        """Build the classification prompt for Nova Pro"""
        
        name = company_data.get('name', 'Unknown Company')
        website = company_data.get('website', '')
        industry = company_data.get('industry', '')
        description = company_data.get('description', '')
        products = company_data.get('products_services', '')
        
        prompt = f"""Analyze this company and classify its business model:

Company: {name}
Website: {website}
Industry: {industry}
Description: {description}
Products/Services: {products}

Classify as either SaaS or Non-SaaS and select the most appropriate category:

SaaS Categories: AdTech, AI/ML Platform, Analytics Platform, API Management, Business Intelligence, CRM, Customer Support, DevOps Platform, E-commerce Platform, HR Tech, Marketing Automation, Project Management, Security Platform, Social Media Management

Non-SaaS Categories: IT Consulting Services, Biopharma R&D, Retail, Unclassified

Respond with ONLY this JSON format:
{{"is_saas": true/false, "category": "CategoryName", "confidence": 0.85, "justification": "Brief reason"}}"""

        return prompt
    
    def _parse_classification_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the classification response from Nova Pro"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate required fields
                if all(key in result for key in ['is_saas', 'category', 'confidence', 'justification']):
                    # Ensure category is valid
                    if result['category'] in self.categories:
                        return result
            
            return None
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse classification response: {e}")
            return None
    
    def _fallback_classification(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback classification when AI fails"""
        
        # Simple keyword-based classification
        text = ' '.join([
            company_data.get('name', ''),
            company_data.get('description', ''),
            company_data.get('products_services', ''),
            company_data.get('industry', '')
        ]).lower()
        
        # Check for SaaS indicators
        saas_keywords = ['platform', 'software', 'api', 'cloud', 'subscription', 'saas', 'analytics', 'dashboard']
        is_saas = any(keyword in text for keyword in saas_keywords)
        
        # Simple category detection
        if 'advertising' in text or 'ads' in text:
            category = 'AdTech'
        elif 'analytics' in text or 'data' in text:
            category = 'Analytics Platform'
        elif 'consulting' in text:
            category = 'IT Consulting Services'
            is_saas = False
        elif 'biotech' in text or 'pharma' in text or 'clinical' in text:
            category = 'Biopharma R&D'
            is_saas = False
        elif 'retail' in text or 'commerce' in text:
            category = 'E-commerce Platform' if is_saas else 'Retail'
        else:
            category = 'Unclassified'
            is_saas = False
        
        return {
            'success': True,
            'is_saas': is_saas,
            'category': category,
            'confidence': 0.6,  # Lower confidence for fallback
            'justification': f'Fallback classification based on keyword analysis'
        }