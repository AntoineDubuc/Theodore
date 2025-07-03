#!/usr/bin/env python3
"""
AI Content Aggregator - Phase 4 of Intelligent Scraping
=======================================================

Business intelligence generation using advanced AI analysis to combine content
from multiple pages into comprehensive company intelligence summaries.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ...core.interfaces.ai_provider import AIProviderPort
from .content_extractor import ExtractionResult
import logging
import json


@dataclass
class CompanyIntelligence:
    """Structured company intelligence result"""
    company_name: str
    description: str = ""
    industry: str = ""
    business_model: str = ""
    target_market: str = ""
    value_proposition: str = ""
    company_stage: str = ""
    tech_sophistication: str = ""
    funding_stage: str = ""
    employee_count_estimate: str = ""
    founding_year: Optional[int] = None
    headquarters: str = ""
    key_products: List[str] = None
    leadership_team: List[str] = None
    recent_news: List[str] = None
    competitive_advantages: List[str] = None
    raw_content_summary: str = ""
    confidence_score: float = 0.0
    extraction_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.key_products is None:
            self.key_products = []
        if self.leadership_team is None:
            self.leadership_team = []
        if self.recent_news is None:
            self.recent_news = []
        if self.competitive_advantages is None:
            self.competitive_advantages = []
        if self.extraction_metadata is None:
            self.extraction_metadata = {}


class AIContentAggregator:
    """Service for aggregating extracted content into business intelligence"""
    
    def __init__(self, ai_provider: AIProviderPort):
        self.ai_provider = ai_provider
        self.logger = logging.getLogger(__name__)
    
    async def aggregate_company_intelligence(
        self, 
        company_name: str,
        extraction_results: List[ExtractionResult],
        progress_callback: Optional = None
    ) -> CompanyIntelligence:
        """Aggregate content from multiple pages into comprehensive company intelligence."""
        
        if progress_callback:
            from ...interfaces.web_scraper import ScrapingProgress, ScrapingPhase
            progress_callback(ScrapingProgress(
                ScrapingPhase.AI_AGGREGATION, 1, 3,
                f"Preparing content aggregation for {company_name}",
                {"pages_to_analyze": len([r for r in extraction_results if r.success])}
            ))
        
        # Filter successful extractions
        successful_results = [r for r in extraction_results if r.success and r.content.strip()]
        
        if not successful_results:
            self.logger.warning(f"No successful content extractions for {company_name}")
            return CompanyIntelligence(
                company_name=company_name,
                description="No content available for analysis",
                confidence_score=0.0,
                extraction_metadata={"error": "no_content", "total_pages_attempted": len(extraction_results)}
            )
        
        self.logger.info(f"Aggregating intelligence from {len(successful_results)} pages for {company_name}")
        
        # Prepare content for AI analysis
        if progress_callback:
            progress_callback(ScrapingProgress(
                ScrapingPhase.AI_AGGREGATION, 2, 3,
                f"Analyzing content from {len(successful_results)} pages",
                {"content_length": sum(len(r.content) for r in successful_results)}
            ))
        
        combined_content = self._prepare_content_for_analysis(successful_results)
        
        # Generate AI analysis
        analysis_prompt = self._create_intelligence_prompt(company_name, combined_content, successful_results)
        
        try:
            # Use high-context AI model for comprehensive analysis
            ai_response = await self.ai_provider.analyze_text(
                text=analysis_prompt,
                config={
                    "max_tokens": 4000,
                    "temperature": 0.2,  # Lower temperature for factual analysis
                    "response_format": "json"  # Request structured response
                }
            )
            
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.AI_AGGREGATION, 3, 3,
                    "Structuring and validating intelligence results"
                ))
            
            # Parse and structure the AI response
            intelligence = self._parse_ai_response(company_name, ai_response.content, successful_results)
            
            self.logger.info(f"Intelligence generation completed for {company_name} (confidence: {intelligence.confidence_score:.2f})")
            return intelligence
            
        except Exception as e:
            self.logger.error(f"AI aggregation failed for {company_name}: {e}")
            
            # Fallback to basic content summary
            return self._create_fallback_intelligence(company_name, successful_results)
    
    def _prepare_content_for_analysis(self, results: List[ExtractionResult]) -> str:
        """Prepare and optimize content for AI analysis."""
        
        # Organize content by page value
        organized_content = []
        
        for result in results:
            # Prioritize content based on URL patterns
            priority = self._calculate_content_priority(result.url)
            
            # Format content with context
            page_content = f"""
PAGE: {result.url} (Priority: {priority})
TITLE: {result.title}
CONTENT: {result.content[:5000]}  # Limit per page to manage token usage
---
"""
            organized_content.append((priority, page_content))
        
        # Sort by priority and combine
        organized_content.sort(reverse=True, key=lambda x: x[0])
        combined = "".join([content for priority, content in organized_content])
        
        # Ensure total content fits within context limits (aim for ~50K chars max)
        if len(combined) > 50000:
            combined = combined[:50000] + "\n... [Additional content truncated for analysis efficiency]"
        
        return combined
    
    def _calculate_content_priority(self, url: str) -> float:
        """Calculate priority score for content based on URL patterns."""
        url_lower = url.lower()
        
        high_priority_patterns = {
            '/about': 10.0, '/contact': 9.0, '/team': 8.0, '/company': 8.0,
            '/leadership': 7.0, '/careers': 6.0, '/investors': 5.0
        }
        
        for pattern, score in high_priority_patterns.items():
            if pattern in url_lower:
                return score
        
        return 3.0  # Default priority
    
    def _create_intelligence_prompt(self, company_name: str, content: str, results: List[ExtractionResult]) -> str:
        """Create comprehensive prompt for AI intelligence extraction."""
        
        pages_analyzed = [f"- {r.url} ({len(r.content)} chars)" for r in results]
        pages_summary = "\n".join(pages_analyzed)
        
        return f"""You are an expert business intelligence analyst. Analyze the following website content for {company_name} and extract comprehensive company intelligence.

CONTENT TO ANALYZE:
{content}

PAGES ANALYZED:
{pages_summary}

Extract the following information and return as a JSON object:

{{
  "company_name": "{company_name}",
  "description": "2-3 sentence company overview focusing on what they do and their value proposition",
  "industry": "Primary industry/sector (e.g., 'SaaS', 'E-commerce', 'Healthcare Tech', 'Manufacturing')",
  "business_model": "How they make money (e.g., 'B2B SaaS', 'B2C Marketplace', 'Professional Services')",
  "target_market": "Who are their primary customers (e.g., 'SMB retailers', 'Enterprise healthcare', 'Individual consumers')",
  "value_proposition": "Key benefits/advantages they offer customers",
  "company_stage": "Business maturity (e.g., 'Startup', 'Growth', 'Established', 'Enterprise')",
  "tech_sophistication": "Technical complexity (e.g., 'Low-tech', 'Moderate', 'High-tech', 'Deep-tech')",
  "funding_stage": "If mentioned (e.g., 'Bootstrapped', 'Seed', 'Series A', 'Public', 'Unknown')",
  "employee_count_estimate": "If mentioned or inferrable (e.g., '10-50', '100-500', '1000+', 'Unknown')",
  "founding_year": null or year as integer if mentioned,
  "headquarters": "City, State/Country if mentioned, otherwise empty string",
  "key_products": ["List", "of", "main", "products", "or", "services"],
  "leadership_team": ["Names of key executives/founders if mentioned"],
  "recent_news": ["Notable recent developments, partnerships, or announcements"],
  "competitive_advantages": ["Key", "differentiators", "or", "strengths"],
  "raw_content_summary": "Brief summary of the key information found across all pages",
  "confidence_score": 0.85
}}

GUIDELINES:
- Focus on factual information explicitly stated in the content
- Use "Unknown" for missing information rather than guessing
- Base confidence_score on data quality and completeness (0.0-1.0)
- Prioritize business intelligence over marketing content
- Extract specific, actionable business insights
- Keep descriptions concise but informative

Return only the JSON object, no additional text."""
    
    def _parse_ai_response(self, company_name: str, response: str, results: List[ExtractionResult]) -> CompanyIntelligence:
        """Parse AI response into structured intelligence object."""
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                intelligence_data = json.loads(json_str)
                
                # Create structured intelligence object
                intelligence = CompanyIntelligence(
                    company_name=intelligence_data.get("company_name", company_name),
                    description=intelligence_data.get("description", ""),
                    industry=intelligence_data.get("industry", ""),
                    business_model=intelligence_data.get("business_model", ""),
                    target_market=intelligence_data.get("target_market", ""),
                    value_proposition=intelligence_data.get("value_proposition", ""),
                    company_stage=intelligence_data.get("company_stage", ""),
                    tech_sophistication=intelligence_data.get("tech_sophistication", ""),
                    funding_stage=intelligence_data.get("funding_stage", ""),
                    employee_count_estimate=intelligence_data.get("employee_count_estimate", ""),
                    founding_year=intelligence_data.get("founding_year"),
                    headquarters=intelligence_data.get("headquarters", ""),
                    key_products=intelligence_data.get("key_products", []),
                    leadership_team=intelligence_data.get("leadership_team", []),
                    recent_news=intelligence_data.get("recent_news", []),
                    competitive_advantages=intelligence_data.get("competitive_advantages", []),
                    raw_content_summary=intelligence_data.get("raw_content_summary", ""),
                    confidence_score=float(intelligence_data.get("confidence_score", 0.5)),
                    extraction_metadata={
                        "pages_analyzed": len(results),
                        "successful_extractions": len([r for r in results if r.success]),
                        "total_content_length": sum(len(r.content) for r in results if r.success),
                        "ai_model": "structured_analysis",
                        "analysis_method": "llm_aggregation"
                    }
                )
                
                return intelligence
            else:
                raise ValueError("No valid JSON found in AI response")
        
        except Exception as e:
            self.logger.warning(f"Failed to parse AI response for {company_name}: {e}")
            return self._create_fallback_intelligence(company_name, results)
    
    def _create_fallback_intelligence(self, company_name: str, results: List[ExtractionResult]) -> CompanyIntelligence:
        """Create basic intelligence when AI analysis fails."""
        
        # Combine all content for basic summary
        all_content = " ".join([r.content[:1000] for r in results if r.success])
        basic_summary = all_content[:500] + "..." if len(all_content) > 500 else all_content
        
        return CompanyIntelligence(
            company_name=company_name,
            description=f"Company information extracted from {len(results)} pages",
            raw_content_summary=basic_summary,
            confidence_score=0.3,  # Low confidence for fallback
            extraction_metadata={
                "pages_analyzed": len(results),
                "successful_extractions": len([r for r in results if r.success]),
                "analysis_method": "fallback_summary",
                "error": "ai_analysis_failed"
            }
        )