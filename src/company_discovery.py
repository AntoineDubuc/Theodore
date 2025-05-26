"""
LLM-powered company discovery service for finding similar companies
"""

import logging
import re
import json
import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

from src.bedrock_client import BedrockClient
from src.models import CompanyData

logger = logging.getLogger(__name__)


class CompanySuggestion(BaseModel):
    """Single company suggestion from LLM discovery"""
    company_name: str = Field(..., description="Name of the suggested company")
    website_url: Optional[str] = Field(None, description="Company website URL if found")
    suggested_reason: str = Field(..., description="Why this company is similar")
    confidence_score: float = Field(default=0.8, description="LLM confidence in suggestion (0-1)")


class DiscoveryResult(BaseModel):
    """Result of company discovery process"""
    target_company: str = Field(..., description="Original company we're finding similarities for")
    suggestions: List[CompanySuggestion] = Field(default_factory=list)
    discovery_method: str = Field(default="llm", description="Method used for discovery")
    discovered_at: datetime = Field(default_factory=datetime.now)
    total_suggestions: int = Field(default=0, description="Number of suggestions found")
    

class CompanyDiscoveryService:
    """Service for discovering similar companies using LLM intelligence"""
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        self.bedrock_client = bedrock_client or BedrockClient()
        
    def discover_similar_companies(self, target_company: CompanyData, limit: int = 10) -> DiscoveryResult:
        """
        Discover companies similar to the target company using LLM analysis
        
        Args:
            target_company: Company to find similarities for
            limit: Maximum number of similar companies to discover
            
        Returns:
            DiscoveryResult with list of suggested similar companies
        """
        logger.info(f"Starting company discovery for: {target_company.name}")
        
        try:
            # Create discovery prompt
            prompt = self._create_discovery_prompt(target_company, limit)
            
            # Get LLM suggestions
            llm_response = self.bedrock_client.analyze_content(prompt)
            
            # Parse suggestions
            raw_suggestions = self._parse_llm_suggestions(llm_response)
            
            # Validate suggestions
            validated_suggestions = []
            for suggestion in raw_suggestions:
                if self._validate_suggestion(suggestion):
                    validated_suggestions.append(suggestion)
                else:
                    logger.warning(f"Filtered out invalid suggestion: {suggestion.company_name}")
            
            # Create result
            result = DiscoveryResult(
                target_company=target_company.name,
                suggestions=validated_suggestions[:limit],  # Ensure we don't exceed limit
                total_suggestions=len(validated_suggestions)
            )
            
            logger.info(f"Discovered {len(validated_suggestions)} similar companies for {target_company.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error discovering similar companies for {target_company.name}: {e}")
            return DiscoveryResult(
                target_company=target_company.name,
                suggestions=[],
                total_suggestions=0
            )
    
    def _create_discovery_prompt(self, company: CompanyData, limit: int = 10) -> str:
        """
        Create a structured prompt for LLM to discover similar companies
        """
        
        # Build company context
        company_context = f"""
Company: {company.name}
Website: {company.website}
Industry: {company.industry or 'Not specified'}
Business Model: {company.business_model or 'Not specified'}
Description: {company.company_description or 'Not available'}
Key Services: {', '.join(company.key_services) if company.key_services else 'Not specified'}
Target Market: {company.target_market or 'Not specified'}
Location: {company.location or 'Not specified'}
Tech Stack: {', '.join(company.tech_stack) if company.tech_stack else 'Not specified'}
Company Size: {company.company_size or 'Not specified'}
"""

        prompt = f"""You are a business intelligence analyst tasked with finding companies similar to the target company below.

TARGET COMPANY:
{company_context}

Find {limit} companies that are similar to this target company. Focus on:
1. Direct competitors (same industry, similar services)
2. Adjacent companies (different approach, similar customers)
3. Companies in similar business models or market segments

For each similar company, provide:
- Company name (exact, official name)
- Website URL (if known, format: https://companyname.com)
- Brief reason why they're similar (1-2 sentences)

IMPORTANT GUIDELINES:
- Only suggest real, existing companies
- Provide accurate website URLs when possible
- Focus on companies that would be meaningful comparisons
- Avoid suggesting companies that are too large/small compared to target
- Include a mix of direct competitors and adjacent players

Respond in this EXACT JSON format:
{{
  "similar_companies": [
    {{
      "company_name": "Company Name",
      "website_url": "https://example.com",
      "reason": "Brief explanation of similarity"
    }}
  ]
}}

Provide exactly {limit} suggestions in valid JSON format:"""

        return prompt
    
    def _parse_llm_suggestions(self, llm_response: str) -> List[CompanySuggestion]:
        """
        Parse LLM response to extract company suggestions
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            List of CompanySuggestion objects
        """
        suggestions = []
        
        try:
            # Try to parse as JSON first
            json_match = re.search(r'\\{.*\\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if 'similar_companies' in data:
                    for item in data['similar_companies']:
                        suggestion = CompanySuggestion(
                            company_name=item.get('company_name', '').strip(),
                            website_url=self._clean_url(item.get('website_url', '')),
                            suggested_reason=item.get('reason', '').strip(),
                            confidence_score=0.8  # Default confidence for LLM suggestions
                        )
                        
                        # Only add if we have a valid company name
                        if suggestion.company_name:
                            suggestions.append(suggestion)
            
            # Fallback: try to parse unstructured response
            if not suggestions:
                suggestions = self._parse_unstructured_response(llm_response)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response, trying fallback parsing: {e}")
            suggestions = self._parse_unstructured_response(llm_response)
        except Exception as e:
            logger.error(f"Error parsing LLM suggestions: {e}")
            
        return suggestions
    
    def _parse_unstructured_response(self, response: str) -> List[CompanySuggestion]:
        """
        Fallback parser for unstructured LLM responses
        """
        suggestions = []
        
        # Look for company names and URLs in text
        lines = response.split('\\n')
        current_company = None
        current_url = None
        current_reason = None
        
        for line in lines:
            line = line.strip()
            
            # Look for company names (often numbered or bulleted)
            company_match = re.search(r'(?:^\\d+\\.\\s*|^-\\s*|^\\*\\s*)(.+?)(?:\\s*-|\\s*:|$)', line)
            if company_match:
                current_company = company_match.group(1).strip()
                
            # Look for URLs
            url_match = re.search(r'(https?://[^\\s]+)', line)
            if url_match:
                current_url = url_match.group(1)
                
            # Look for reasoning
            if current_company and ('similar' in line.lower() or 'because' in line.lower() or 'competitor' in line.lower()):
                current_reason = line
                
            # If we have enough info, create suggestion
            if current_company and len(current_company) > 2:
                suggestion = CompanySuggestion(
                    company_name=current_company,
                    website_url=self._clean_url(current_url) if current_url else None,
                    suggested_reason=current_reason or f"Similar company in related market",
                    confidence_score=0.6  # Lower confidence for unstructured parsing
                )
                suggestions.append(suggestion)
                
                # Reset for next company
                current_company = None
                current_url = None
                current_reason = None
                
        return suggestions[:10]  # Limit to 10 suggestions
    
    def _validate_suggestion(self, suggestion: CompanySuggestion) -> bool:
        """
        Validate that a company suggestion is legitimate and accessible
        """
        # Check company name isn't empty or generic
        if not suggestion.company_name or len(suggestion.company_name.strip()) < 3:
            return False
            
        # Filter out generic/invalid company names
        invalid_names = ['company', 'corp', 'llc', 'inc', 'ltd', 'example', 'test', 'sample']
        name_lower = suggestion.company_name.lower().strip()
        if name_lower in invalid_names or any(invalid in name_lower for invalid in invalid_names):
            return False
        
        # Check URL if provided
        if suggestion.website_url:
            if not self._check_url_accessible(suggestion.website_url):
                # Don't reject completely, just clear the URL
                suggestion.website_url = None
                suggestion.confidence_score *= 0.8  # Reduce confidence
        
        return True
    
    def _check_url_accessible(self, url: str) -> bool:
        """
        Quick check if URL is accessible (basic validation)
        """
        try:
            # Basic URL format validation
            if not url.startswith(('http://', 'https://')):
                return False
                
            # Quick HEAD request with short timeout
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400
            
        except Exception:
            return False
    
    def _clean_url(self, url: Optional[str]) -> Optional[str]:
        """
        Clean and validate URL format
        """
        if not url:
            return None
            
        url = url.strip()
        
        # Remove common markdown formatting
        url = re.sub(r'[\\[\\]\\(\\)]', '', url)
        
        # Ensure proper protocol
        if url and not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        # Basic URL validation
        if url and '.' in url and len(url) > 7:
            return url
            
        return None


def main():
    """Test the discovery service"""
    # This would be used for testing
    pass


if __name__ == "__main__":
    main()