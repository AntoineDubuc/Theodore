#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Company Intelligence Field Extraction System
============================================

Extracts structured company intelligence fields from aggregated crawled content
using Amazon Nova Pro LLM via OpenRouter API. Takes raw website content and
maps it to the comprehensive Target Information Profile.

This is the final step in the pipeline:
1. Critter discovers paths
2. Nova Pro selects valuable paths  
3. Crawler extracts content with fallback
4. THIS MODULE extracts structured fields from aggregated content

Usage:
    from distill_out_fields import extract_company_fields
    
    result = extract_company_fields(batch_crawl_result, company_name)
    
    if result.success:
        print(f"Extracted {len(result.extracted_fields)} fields")
        print(f"Cost: ${result.cost_usd:.4f}")
        print(f"Confidence: {result.overall_confidence:.2f}")
    else:
        print(f"Failed: {result.error}")
"""

import json
import logging
import os
import time
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass, field
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f" Loaded environment variables from {env_path}")
    else:
        print("� No .env file found, using system environment variables")
except ImportError:
    print("� python-dotenv not available, using system environment variables")

# Import crawler data structures
try:
    from crawler import BatchCrawlResult, PageCrawlResult
    CRAWLER_AVAILABLE = True
    print(" Crawler module imported successfully")
except ImportError:
    print("� Crawler module not available, using basic data structures")
    CRAWLER_AVAILABLE = False
    
    # Define basic data structures if crawler not available
    @dataclass
    class PageCrawlResult:
        url: str
        success: bool
        content: str = ""
        title: str = ""
        content_length: int = 0
        crawl_time: float = 0.0
        extraction_method: str = ""
        error: str = ""

    @dataclass
    class BatchCrawlResult:
        base_url: str
        total_pages: int
        successful_pages: int
        failed_pages: int
        total_content_length: int
        total_crawl_time: float
        aggregated_content: str = ""
        page_results: List[PageCrawlResult] = None
        errors: List[str] = None

logger = logging.getLogger(__name__)


@dataclass
class FieldExtractionResult:
    """Result from extracting structured fields from company content"""
    success: bool
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    field_confidence_scores: Dict[str, float] = field(default_factory=dict)
    overall_confidence: float = 0.0
    source_attribution: Dict[str, List[str]] = field(default_factory=dict)  # field -> list of source URLs
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    tokens_used: int = 0
    processing_time: float = 0.0
    model_used: str = ""
    company_name: str = ""
    extraction_timestamp: str = ""
    error: str = ""
    
    def __post_init__(self):
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.now().isoformat()


@dataclass
class OpenRouterResponse:
    """Response from OpenRouter API call"""
    success: bool
    content: str
    model_used: str
    tokens_used: int
    cost_usd: float
    processing_time: float
    error: str = ""


class OpenRouterClient:
    """OpenRouter API client for Nova Pro field extraction"""
    
    def __init__(self, api_key: str, model: str = "amazon/nova-pro-v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        
    def call_llm(self, prompt: str, timeout: int = 120) -> OpenRouterResponse:
        """Call Nova Pro LLM via OpenRouter for field extraction"""
        
        print(f"🧠 Calling Nova Pro for field extraction...")
        print(f"📊 Model: {self.model}")
        print(f"📝 Prompt length: {len(prompt):,} characters")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://theodore-ai.com",
                    "X-Title": "Theodore AI Company Intelligence"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistent field extraction
                    "max_tokens": 4000   # Enough for comprehensive field extraction
                },
                timeout=timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code != 200:
                return OpenRouterResponse(
                    success=False,
                    content="",
                    model_used="",
                    tokens_used=0,
                    cost_usd=0.0,
                    processing_time=processing_time,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract model and usage information
            model_used = result.get("model", self.model)
            
            # Get usage from response or estimate
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", len(prompt) // 4)  # Rough estimate
            
            # Calculate cost (Nova Pro is ~$0.0008/1K tokens)
            cost_usd = (tokens_used / 1000) * 0.0008
            
            print(f"✅ Nova Pro extraction completed")
            print(f"🔢 Tokens used: {tokens_used:,}")
            print(f"💰 Cost: ${cost_usd:.4f}")
            print(f"⏱️ Processing time: {processing_time:.2f}s")
            
            return OpenRouterResponse(
                success=True,
                content=content,
                model_used=model_used,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                processing_time=processing_time
            )
            
        except requests.exceptions.Timeout:
            return OpenRouterResponse(
                success=False,
                content="",
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                processing_time=time.time() - start_time,
                error=f"Request timed out after {timeout} seconds"
            )
            
        except Exception as e:
            return OpenRouterResponse(
                success=False,
                content="",
                model_used="",
                tokens_used=0,
                cost_usd=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )


def create_openrouter_client() -> OpenRouterClient:
    """Create OpenRouter client with environment variables"""
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_API_KEY environment variable is required")
    
    return OpenRouterClient(api_key, "amazon/nova-pro-v1")


def create_field_extraction_prompt(company_name: str, aggregated_content: str, page_sources: List[str]) -> str:
    """Create comprehensive field extraction prompt using Target Information Profile"""
    
    # Truncate content if too long (keep within Nova Pro context limits)
    max_content_length = 80000  # Conservative limit for Nova Pro
    if len(aggregated_content) > max_content_length:
        aggregated_content = aggregated_content[:max_content_length] + "\n\n[CONTENT TRUNCATED FOR LENGTH]"
    
    prompt = f"""System: You are an expert AI business intelligence analyst. Your task is to extract structured company information from website content and map it to specific data fields.

User: I will provide you with aggregated content from a company's website. Your job is to extract as many specific fields as possible and return them in a structured JSON format.

COMPANY: {company_name}
SOURCE PAGES: {len(page_sources)} pages crawled
CONTENT LENGTH: {len(aggregated_content):,} characters

TARGET INFORMATION PROFILE:
Extract these specific fields from the content below:

Core Company Information:
- company_name: Official company name
- website: Primary website URL
- company_description: Brief description of what the company does
- value_proposition: Main value proposition or unique selling points
- industry: Primary industry/sector
- location: Headquarters location (city, state/country)
- founding_year: Year the company was founded
- company_size: Size category (startup, small, medium, large, enterprise)
- employee_count_range: Estimated employee count or range

Business Model & Classification:
- business_model_type: B2B, B2C, B2B2C, marketplace, etc.
- business_model: Description of how the company makes money
- saas_classification: SaaS, PaaS, IaaS, or not applicable
- is_saas: True/false if it's a SaaS company
- classification_confidence: Your confidence in the classification (0.0-1.0)
- classification_justification: Brief reasoning for classification

Products & Services:
- products_services_offered: List of main products/services
- key_services: Top 3-5 most important services
- target_market: Description of target customers/market
- pain_points: Customer pain points the company addresses
- competitive_advantages: Key competitive differentiators
- tech_stack: Technologies, platforms, or tools mentioned

Company Stage & Metrics:
- company_stage: Early-stage, growth, mature, established
- detailed_funding_stage: Seed, Series A/B/C, IPO, private, etc.
- funding_status: Recent funding information if available
- stage_confidence: Confidence in stage assessment (0.0-1.0)
- tech_sophistication: Low, moderate, high based on technical complexity
- tech_confidence: Confidence in tech sophistication (0.0-1.0)
- industry_confidence: Confidence in industry classification (0.0-1.0)
- geographic_scope: Local, regional, national, international
- sales_complexity: Simple, moderate, complex based on sales process

People & Leadership:
- key_decision_makers: Names and roles of key executives
- leadership_team: Leadership team information
- decision_maker_type: Technical, business, mixed decision makers

Growth & Activity Indicators:
- has_job_listings: True/false if hiring information found
- job_listings_count: Number of open positions if mentioned
- job_listings_details: Types of roles being hired
- recent_news_events: Recent news, press releases, or events
- recent_news: Latest company developments

Technology & Digital Presence:
- sales_marketing_tools: Tools and platforms used for sales/marketing
- has_chat_widget: True/false if live chat found on website
- has_forms: True/false if contact/lead forms found
- social_media: Social media presence and platforms
- contact_info: Contact information found

Recognition & Partnerships:
- company_culture: Company culture and values mentioned
- awards: Awards, recognitions, or certifications
- certifications: Professional certifications or compliance
- partnerships: Key partnerships or integrations mentioned

Operational Metadata:
- ai_summary: AI-generated summary of the company's core business and value proposition
- ai_summary_tokens: Number of tokens used for AI summary generation (if applicable)
- field_extraction_tokens: Number of tokens used for field extraction
- total_tokens: Total tokens used across all AI operations
- llm_model_used: Primary LLM model used for analysis
- total_cost_usd: Total cost in USD for complete analysis
- scrape_duration_seconds: Total time taken for complete scraping process
- field_extraction_duration_seconds: Time taken for field extraction phase

INSTRUCTIONS:
1. Read through ALL the content carefully
2. Extract as many fields as possible from the available content
3. If a field cannot be determined from the content, set it to null
4. Provide confidence scores for uncertain extractions
5. Use the exact field names listed above
6. Return ONLY valid JSON - no explanations or extra text

CONTENT TO ANALYZE:
{aggregated_content}

Return the extracted fields as a JSON object with the structure above. Include confidence scores for uncertain fields and set unavailable fields to null."""

    return prompt


def parse_extraction_response(response_content: str) -> Dict[str, Any]:
    """Parse Nova Pro response and extract structured fields"""
    
    try:
        # Try to extract JSON from the response
        content = response_content.strip()
        
        # Handle cases where response is wrapped in markdown code blocks
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```
            
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        
        # Parse JSON
        extracted_data = json.loads(content.strip())
        
        print(f" Successfully parsed {len(extracted_data)} fields from Nova Pro response")
        
        return extracted_data
        
    except json.JSONDecodeError as e:
        print(f"L Failed to parse JSON from Nova Pro response: {e}")
        print(f"=� Response content preview: {response_content[:500]}...")
        
        # Try to extract partial data using fallback parsing
        return parse_fallback_extraction(response_content)
    
    except Exception as e:
        print(f"L Unexpected error parsing extraction response: {e}")
        return {}


def parse_fallback_extraction(response_content: str) -> Dict[str, Any]:
    """Fallback parsing for cases where JSON extraction fails"""
    
    print("= Attempting fallback extraction parsing...")
    
    # Try to find JSON-like content in the response
    import re
    
    # Look for JSON object patterns
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response_content, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict) and len(parsed) > 5:  # Reasonable number of fields
                print(f" Fallback parsing successful with {len(parsed)} fields")
                return parsed
        except:
            continue
    
    print("L Fallback parsing failed - returning empty dict")
    return {}


def calculate_field_confidence_scores(extracted_fields: Dict[str, Any]) -> Dict[str, float]:
    """Calculate confidence scores for extracted fields"""
    
    confidence_scores = {}
    
    for field_name, field_value in extracted_fields.items():
        if field_value is None or field_value == "":
            confidence_scores[field_name] = 0.0
        elif field_name.endswith("_confidence"):
            # Already a confidence score
            continue
        elif isinstance(field_value, str):
            if len(field_value.strip()) > 10:
                confidence_scores[field_name] = 0.8  # Good confidence for substantial text
            elif len(field_value.strip()) > 3:
                confidence_scores[field_name] = 0.6  # Moderate confidence
            else:
                confidence_scores[field_name] = 0.3  # Low confidence for short values
        elif isinstance(field_value, (list, dict)):
            if len(field_value) > 0:
                confidence_scores[field_name] = 0.7  # Good confidence for non-empty collections
            else:
                confidence_scores[field_name] = 0.1  # Low confidence for empty collections
        elif isinstance(field_value, bool):
            confidence_scores[field_name] = 0.9  # High confidence for boolean values
        elif isinstance(field_value, (int, float)):
            confidence_scores[field_name] = 0.8  # Good confidence for numeric values
        else:
            confidence_scores[field_name] = 0.5  # Default moderate confidence
    
    return confidence_scores


def create_source_attribution(extracted_fields: Dict[str, Any], page_results: List[PageCrawlResult]) -> Dict[str, List[str]]:
    """Create source attribution mapping fields to source URLs"""
    
    # For now, attribute all fields to all successful pages
    # In a more sophisticated implementation, this could analyze which pages
    # likely contributed to which fields based on content analysis
    
    source_attribution = {}
    successful_urls = [page.url for page in page_results if page.success]
    
    for field_name in extracted_fields.keys():
        if extracted_fields[field_name] is not None:
            source_attribution[field_name] = successful_urls
    
    return source_attribution


def extract_company_fields(
    batch_crawl_result: BatchCrawlResult,
    company_name: Optional[str] = None,
    timeout_seconds: int = 120,
    pipeline_metadata: Optional[Dict[str, Any]] = None
) -> FieldExtractionResult:
    """
    Extract structured company intelligence fields from aggregated crawled content.
    
    This is the final step in the pipeline that transforms raw website content
    into structured company intelligence using Nova Pro LLM.
    
    Args:
        batch_crawl_result: Result from crawler with aggregated content
        company_name: Company name (extracted from URL if not provided)
        timeout_seconds: Timeout for LLM call
        
    Returns:
        FieldExtractionResult with extracted fields and metadata
    """
    
    start_time = time.time()
    
    # Extract company name from base URL if not provided
    if not company_name:
        try:
            parsed = urlparse(batch_crawl_result.base_url)
            domain = parsed.netloc.lower().replace('www.', '')
            company_name = domain.split('.')[0].capitalize()
        except:
            company_name = "Unknown Company"
    
    print(f"=� STARTING FIELD EXTRACTION FOR {company_name.upper()}")
    print(f"=� Content: {batch_crawl_result.total_content_length:,} characters from {batch_crawl_result.successful_pages} pages")
    print(f"< Base URL: {batch_crawl_result.base_url}")
    
    # Check if we have sufficient content
    if not batch_crawl_result.aggregated_content.strip():
        return FieldExtractionResult(
            success=False,
            company_name=company_name,
            error="No aggregated content available for field extraction"
        )
    
    if batch_crawl_result.total_content_length < 500:
        return FieldExtractionResult(
            success=False,
            company_name=company_name,
            error=f"Insufficient content for field extraction ({batch_crawl_result.total_content_length} chars < 500 minimum)"
        )
    
    try:
        # Create OpenRouter client
        client = create_openrouter_client()
        
        # Get source page URLs
        page_sources = [page.url for page in batch_crawl_result.page_results if page.success]
        
        # Create field extraction prompt
        prompt = create_field_extraction_prompt(
            company_name, 
            batch_crawl_result.aggregated_content,
            page_sources
        )
        
        print(f"=� Generated extraction prompt: {len(prompt):,} characters")
        
        # Call Nova Pro for field extraction
        llm_response = client.call_llm(prompt, timeout_seconds)
        
        if not llm_response.success:
            return FieldExtractionResult(
                success=False,
                company_name=company_name,
                cost_usd=llm_response.cost_usd,
                tokens_used=llm_response.tokens_used,
                processing_time=time.time() - start_time,
                error=f"Nova Pro call failed: {llm_response.error}"
            )
        
        # Parse extracted fields
        extracted_fields = parse_extraction_response(llm_response.content)
        
        if not extracted_fields:
            return FieldExtractionResult(
                success=False,
                company_name=company_name,
                cost_usd=llm_response.cost_usd,
                tokens_used=llm_response.tokens_used,
                processing_time=time.time() - start_time,
                error="Failed to parse any fields from Nova Pro response"
            )
        
        # Add operational metadata to extracted fields
        if pipeline_metadata:
            # Calculate total tokens across all phases
            total_tokens = llm_response.tokens_used
            ai_summary_tokens = 0
            total_cost = llm_response.cost_usd
            scrape_duration = batch_crawl_result.total_crawl_time
            
            # Extract metadata from pipeline phases if available
            if 'phase2_selection' in pipeline_metadata:
                phase2 = pipeline_metadata['phase2_selection']
                if phase2.get('success'):
                    total_tokens += phase2.get('tokens_used', 0)
                    total_cost += phase2.get('cost_usd', 0.0)
            
            if 'phase3_extraction' in pipeline_metadata:
                phase3 = pipeline_metadata['phase3_extraction']
                if phase3.get('success'):
                    scrape_duration = phase3.get('processing_time', scrape_duration)
            
            # Add operational metadata fields
            extracted_fields.update({
                'ai_summary': extracted_fields.get('company_description', '') or extracted_fields.get('value_proposition', ''),
                'ai_summary_tokens': ai_summary_tokens,  # Not tracked separately in current pipeline
                'field_extraction_tokens': llm_response.tokens_used,
                'total_tokens': total_tokens,
                'llm_model_used': llm_response.model_used,
                'total_cost_usd': total_cost,
                'scrape_duration_seconds': scrape_duration,
                'field_extraction_duration_seconds': time.time() - start_time
            })
        
        # Calculate confidence scores
        field_confidence_scores = calculate_field_confidence_scores(extracted_fields)
        
        # Calculate overall confidence (average of non-zero confidence scores)
        valid_confidences = [score for score in field_confidence_scores.values() if score > 0]
        overall_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0
        
        # Create source attribution
        source_attribution = create_source_attribution(extracted_fields, batch_crawl_result.page_results)
        
        # Create processing metadata
        processing_metadata = {
            "source_pages": len(page_sources),
            "content_length_processed": len(batch_crawl_result.aggregated_content),
            "fields_extracted": len(extracted_fields),
            "non_null_fields": len([v for v in extracted_fields.values() if v is not None]),
            "extraction_method": "nova_pro_llm",
            "prompt_length": len(prompt)
        }
        
        total_time = time.time() - start_time
        
        print(f" FIELD EXTRACTION COMPLETED FOR {company_name.upper()}")
        print(f"=� Extracted {len(extracted_fields)} total fields")
        print(f"( Non-null fields: {processing_metadata['non_null_fields']}")
        print(f"<� Overall confidence: {overall_confidence:.2f}")
        print(f"=� Total cost: ${llm_response.cost_usd:.4f}")
        print(f"� Total time: {total_time:.2f}s")
        
        return FieldExtractionResult(
            success=True,
            extracted_fields=extracted_fields,
            field_confidence_scores=field_confidence_scores,
            overall_confidence=overall_confidence,
            source_attribution=source_attribution,
            processing_metadata=processing_metadata,
            cost_usd=llm_response.cost_usd,
            tokens_used=llm_response.tokens_used,
            processing_time=total_time,
            model_used=llm_response.model_used,
            company_name=company_name
        )
        
    except Exception as e:
        return FieldExtractionResult(
            success=False,
            company_name=company_name,
            processing_time=time.time() - start_time,
            error=f"Unexpected error during field extraction: {str(e)}"
        )


# Sync wrapper functions
def extract_company_fields_sync(
    batch_crawl_result: BatchCrawlResult,
    company_name: Optional[str] = None,
    timeout_seconds: int = 120,
    pipeline_metadata: Optional[Dict[str, Any]] = None
) -> FieldExtractionResult:
    """Synchronous wrapper for field extraction"""
    return extract_company_fields(batch_crawl_result, company_name, timeout_seconds, pipeline_metadata)


if __name__ == "__main__":
    print(">� Company Intelligence Field Extraction System")
    print("=" * 60)
    print("This module extracts structured company intelligence fields")
    print("from aggregated website content using Nova Pro LLM.")
    print()
    print("Usage:")
    print("  from distill_out_fields import extract_company_fields")
    print("  result = extract_company_fields(batch_crawl_result, 'Company Name')")
    print()
    print("For testing, use the test scripts in the test/ folder.")