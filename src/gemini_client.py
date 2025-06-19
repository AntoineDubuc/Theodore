"""
Gemini AI integration for company intelligence analysis
Replaces Claude Sonnet 4 with Gemini 2.5 Flash Preview
"""

import json
import logging
import os
from typing import List, Optional, Dict, Any
from src.models import CompanyData, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiClient:
    """Gemini AI client for analysis and similarity discovery"""
    
    def __init__(self, config: CompanyIntelligenceConfig):
        self.config = config
        self.model_name = "gemini-2.5-flash"
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        # Initialize Gemini client
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key or not gemini_api_key.startswith("AIza"):
            raise ValueError("Valid GEMINI_API_KEY not found in environment variables")
        
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini {self.model_name} client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate text using Gemini for general purpose prompts"""
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response.text:
                logger.debug(f"Gemini response generated: {len(response.text)} characters")
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return ""
                
        except Exception as e:
            logger.error(f"Gemini text generation error: {e}")
            return ""

    def generate_text_with_usage(self, prompt: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """Generate text and return both response and usage statistics"""
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract usage information
            usage_data = self._extract_usage_from_response(response)
            
            response_text = ""
            if response.text:
                response_text = response.text
                logger.debug(f"Gemini response generated: {len(response_text)} characters")
            else:
                logger.warning("Gemini returned empty response")
            
            return {
                "text": response_text,
                "usage": usage_data
            }
                
        except Exception as e:
            logger.error(f"Gemini text generation with usage error: {e}")
            return {
                "text": "",
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "model": self.model_name,
                    "error": str(e)
                }
            }

    def _extract_usage_from_response(self, response) -> Dict[str, Any]:
        """Extract token usage and calculate cost from Gemini response"""
        input_tokens = 0
        output_tokens = 0
        
        # Extract usage from Gemini response
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', 0)
            output_tokens = getattr(usage, 'candidates_token_count', 0)
        
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost based on Gemini pricing
        cost_usd = self._calculate_cost(input_tokens, output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "model": self.model_name
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on Gemini pricing"""
        
        # Gemini 2.5 Flash pricing (per 1M tokens as of Dec 2024)
        # Input: $0.075 per 1M tokens
        # Output: $0.30 per 1M tokens
        input_rate_per_1m = 0.075
        output_rate_per_1m = 0.30
        
        input_cost = (input_tokens / 1000000.0) * input_rate_per_1m
        output_cost = (output_tokens / 1000000.0) * output_rate_per_1m
        
        return round(input_cost + output_cost, 6)  # Round to 6 decimal places
    
    def analyze_content(self, content: str) -> str:
        """
        Wrapper for generate_text() - used by similarity discovery
        
        Args:
            content: Content/prompt to analyze
            
        Returns:
            Generated analysis text
        """
        return self.generate_text(content)
    
    def analyze_company_content(self, company_data: CompanyData) -> Dict[str, Any]:
        """Analyze company content and extract structured intelligence"""
        
        prompt = self._build_analysis_prompt(company_data)
        
        try:
            analysis_text = self.generate_text(prompt, max_tokens=1500)
            
            if not analysis_text:
                return {"error": "No response from Gemini"}
            
            # Parse the structured response
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Gemini analysis error for {company_data.name}: {e}")
            return {"error": str(e)}
    
    def generate_sector_summary(self, companies: List[CompanyData], sector_name: str) -> str:
        """Generate sector-level insights from multiple companies"""
        
        company_summaries = []
        for company in companies[:10]:  # Limit to first 10 to avoid token limits
            summary = f"- {company.name}: {company.ai_summary or 'No summary'}"
            company_summaries.append(summary)
        
        prompt = f"""
        Analyze this sector: {sector_name}
        
        Companies in this sector:
        {chr(10).join(company_summaries)}
        
        Provide sector-level insights in this JSON format:
        {{
            "sector_overview": "Brief description of this sector",
            "common_pain_points": ["pain1", "pain2", "pain3"],
            "common_technologies": ["tech1", "tech2", "tech3"],
            "market_opportunities": "Key opportunities for sales teams",
            "recommended_approach": "How to approach companies in this sector"
        }}
        
        Focus on actionable insights for sales teams.
        """
        
        return self.generate_text(prompt)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings - placeholder for compatibility
        Note: Gemini doesn't provide embeddings API, so this returns empty
        In production, you'd use a dedicated embedding service
        """
        logger.warning("Gemini client doesn't support embeddings - returning empty list")
        return []
    
    def _build_analysis_prompt(self, company_data: CompanyData) -> str:
        """Build analysis prompt for company data"""
        
        prompt = f"""
        Analyze this company and provide structured business intelligence:
        
        Company: {company_data.name}
        Website: {company_data.website}
        Industry: {company_data.industry or 'Unknown'}
        
        Raw Content:
        {company_data.raw_content[:3000] if company_data.raw_content else 'No content available'}
        
        Provide analysis in this JSON format:
        {{
            "business_model": "Brief description of how they make money",
            "target_market": "Who are their customers",
            "value_proposition": "What unique value they provide",
            "key_technologies": ["tech1", "tech2", "tech3"],
            "pain_points": ["potential pain point 1", "potential pain point 2"],
            "competitive_advantages": "What makes them unique",
            "sales_approach": "Recommended approach for sales teams"
        }}
        
        Focus on actionable insights for business development.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse analysis response into structured data"""
        try:
            # Try to extract JSON from the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback to plain text response
                return {"analysis": response_text}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {"analysis": response_text}
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return {"error": str(e)}
    
    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean text for embedding generation (compatibility method)"""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        # Limit length 
        if len(cleaned) > 8000:
            cleaned = cleaned[:8000] + "..."
        
        return cleaned