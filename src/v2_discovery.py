"""
Theodore V2 Discovery Engine
Fast company discovery with URL detection and LLM-based similar company finding
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from src.models import CompanyData
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class V2DiscoveryEngine:
    """V2 Discovery Engine - Fast company discovery with URL detection"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def is_url(self, input_text: str) -> bool:
        """
        Detect if input is a URL using native JavaScript-like validation
        More reliable than regex patterns
        """
        try:
            # Clean up the input
            text = input_text.strip()
            
            # Add protocol if missing but looks like URL
            if not text.startswith(('http://', 'https://')):
                if '.' in text and not ' ' in text:
                    text = f"https://{text}"
                else:
                    return False
            
            # Use urlparse to validate
            parsed = urlparse(text)
             
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Must be http/https
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # Basic domain validation
            if '.' not in parsed.netloc:
                return False
                
            self.logger.info(f"✅ Detected valid URL: {text}")
            return True
            
        except Exception as e:
            self.logger.debug(f"URL validation failed for '{input_text}': {e}")
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if needed"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        return url
    
    def discover_similar_companies(self, input_text: str, limit: int = 5) -> Dict[str, Any]:
        """
        Main V2 discovery method
        
        Args:
            input_text: Either company name or website URL
            limit: Number of similar companies to find
            
        Returns:
            Dict with discovery results and metadata
        """
        self.logger.info(f"🚀 V2 Discovery starting for: '{input_text}' (limit: {limit})")
        
        try:
            # Step 1: Detect if input is URL or company name
            is_url_input = self.is_url(input_text)
            
            if is_url_input:
                self.logger.info("📍 Input detected as URL - will use for LLM discovery")
                website_url = self.normalize_url(input_text)
                company_name = self._extract_domain_name(website_url)
                input_type = "url"
            else:
                self.logger.info("📍 Input detected as company name - will use for LLM discovery")
                company_name = input_text.strip()
                website_url = None
                input_type = "company_name"
            
            # Step 2: Use LLM to find similar companies
            similar_companies = self._llm_find_similar_companies(
                company_name=company_name,
                website_url=website_url,
                limit=limit
            )
            
            # Step 3: Format results
            discovery_result = {
                "success": True,
                "input_type": input_type,
                "input_text": input_text,
                "primary_company": {
                    "name": company_name,
                    "website": website_url
                },
                "similar_companies": similar_companies,
                "total_found": len(similar_companies),
                "discovery_method": "V2_LLM_Discovery"
            }
            
            self.logger.info(f"✅ V2 Discovery completed: {len(similar_companies)} companies found")
            return discovery_result
            
        except Exception as e:
            self.logger.error(f"❌ V2 Discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_text": input_text,
                "similar_companies": [],
                "total_found": 0
            }
    
    def _extract_domain_name(self, url: str) -> str:
        """Extract a reasonable company name from domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Take first part before first dot
            company_name = domain.split('.')[0]
            
            # Capitalize first letter
            company_name = company_name.capitalize()
            
            self.logger.info(f"📝 Extracted company name '{company_name}' from URL '{url}'")
            return company_name
            
        except Exception as e:
            self.logger.warning(f"Failed to extract company name from URL '{url}': {e}")
            return "Unknown Company"
    
    def _llm_find_similar_companies(
        self, 
        company_name: str, 
        website_url: Optional[str], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Use LLM to find similar companies"""
        
        self.logger.info(f"🧠 Using LLM to find {limit} companies similar to '{company_name}'")
        
        # Build context for LLM
        context = f"Company: {company_name}"
        if website_url:
            context += f"\nWebsite: {website_url}"
        
        prompt = f"""Find {limit} real companies that are similar to the following company for business development and competitive analysis purposes.

TARGET COMPANY:
{context}

Requirements:
- Find REAL companies with actual websites (not fictional)
- Focus on companies in similar industries, markets, or business models
- Provide diverse examples (different sizes, stages, approaches)
- Include both direct competitors and adjacent/complementary companies

Respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Real Company Name",
      "website": "https://realcompany.com",
      "similarity_score": 0.85,
      "relationship_type": "competitor",
      "reasoning": "Brief explanation of why similar",
      "business_context": "What makes them relevant for comparison"
    }}
  ]
}}

Focus on accuracy and real companies only. Ensure all suggested companies actually exist."""

        try:
            response = self.ai_client.analyze_content(prompt)
            
            if response:
                self.logger.info(f"📥 LLM Response received: {len(response)} characters")
                companies = self._parse_llm_response(response)
                self.logger.info(f"✅ Parsed {len(companies)} companies from LLM response")
                return companies[:limit]  # Ensure we don't exceed limit
            else:
                self.logger.warning("❌ Empty response from LLM")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ LLM discovery failed: {e}")
            return []
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM JSON response for similar companies"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                companies = data.get('similar_companies', [])
                
                # Validate and clean up company data
                validated_companies = []
                for comp in companies:
                    if self._validate_company_data(comp):
                        validated_companies.append(comp)
                    else:
                        self.logger.warning(f"❌ Invalid company data: {comp}")
                
                return validated_companies
            else:
                self.logger.error("❌ No JSON found in LLM response")
                return []
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse LLM JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error parsing LLM response: {e}")
            return []
    
    def _validate_company_data(self, company: Dict[str, Any]) -> bool:
        """Validate company data from LLM response"""
        required_fields = ['name', 'website']
        
        # Check required fields
        for field in required_fields:
            if not company.get(field):
                return False
        
        # Validate website URL
        website = company.get('website', '')
        if not self.is_url(website):
            return False
        
        # Ensure similarity_score is reasonable
        score = company.get('similarity_score', 0)
        if not isinstance(score, (int, float)) or score < 0 or score > 1:
            company['similarity_score'] = 0.8  # Default reasonable score
        
        # Ensure required fields have defaults
        company.setdefault('relationship_type', 'similar')
        company.setdefault('reasoning', 'Similar business model')
        company.setdefault('business_context', 'Relevant for comparison')
        
        return True