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
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f" Loaded environment variables from {env_path}")
    else:
        print("� No .env file found, using system environment variables")
except ImportError:
    print("� python-dotenv not available, using system environment variables")

# Import crawler data structures
try:
    from src.antoine_crawler import BatchCrawlResult, PageCrawlResult
    CRAWLER_AVAILABLE = True
    print(" Crawler module imported successfully")
except ImportError:
    print("� Crawler module not available, using basic data structures")
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
    error: str = ""
    company_data: Optional[Any] = None  # CompanyData object if available


@dataclass 
class OpenRouterResponse:
    """Response from OpenRouter API"""
    success: bool
    content: str = ""
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    response_time: float = 0.0
    error: str = ""


class OpenRouterClient:
    """Client for interacting with OpenRouter API"""
    
    def __init__(self, api_key: str, model: str = "amazon/nova-pro-v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://theodore-ai.com",
            "X-Title": "Theodore AI Intelligence",
            "Content-Type": "application/json"
        }
    
    def call_llm(self, prompt: str, timeout: int = 120) -> OpenRouterResponse:
        """Make a request to OpenRouter API"""
        
        start_time = time.time()
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Low temperature for consistency
                "max_tokens": 8000,  # Sufficient for JSON response
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "response_format": {"type": "json_object"}  # Request JSON format
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract content
                content = ""
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                
                # Extract usage data
                usage = data.get("usage", {})
                
                # Calculate cost (Nova Pro pricing)
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                
                # Nova Pro pricing: $0.80 per million input, $3.20 per million output
                input_cost = (input_tokens / 1_000_000) * 0.80
                output_cost = (output_tokens / 1_000_000) * 3.20
                total_cost = input_cost + output_cost
                
                return OpenRouterResponse(
                    success=True,
                    content=content,
                    model=data.get("model", self.model),
                    usage=usage,
                    cost_usd=total_cost,
                    response_time=response_time
                )
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                return OpenRouterResponse(
                    success=False,
                    error=error_msg,
                    response_time=response_time
                )
                
        except requests.exceptions.Timeout:
            return OpenRouterResponse(
                success=False,
                error=f"Request timed out after {timeout} seconds",
                response_time=time.time() - start_time
            )
        except Exception as e:
            return OpenRouterResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                response_time=time.time() - start_time
            )


def get_openrouter_client() -> Optional[OpenRouterClient]:
    """Initialize OpenRouter client with API key"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        print("💡 Please set: export OPENROUTER_API_KEY='your-api-key'")
        return None
    
    if not api_key.startswith("sk-or-"):
        print("❌ Invalid OpenRouter API key format (should start with 'sk-or-')")
        return None
    
    return OpenRouterClient(api_key, "amazon/nova-pro-v1")


def create_field_extraction_prompt(company_name: str, aggregated_content: str, page_sources: List[str]) -> str:
    """Create comprehensive field extraction prompt using Target Information Profile"""
    
    # Get the prompt template from storage
    try:
        from src.prompt_storage import get_prompt_storage
        storage = get_prompt_storage()
        prompt_template = storage.get_prompt('extraction')
    except Exception as e:
        # Fallback to default if storage not available
        print(f"❌ Failed to load extraction prompt from storage: {e}")
        from src.theodore_prompts import get_field_extraction_prompt
        prompt_template = get_field_extraction_prompt()
    
    # Truncate content if too long (keep within Nova Pro context limits)
    max_content_length = 80000  # Conservative limit for Nova Pro
    if len(aggregated_content) > max_content_length:
        aggregated_content = aggregated_content[:max_content_length] + "\n\n[CONTENT TRUNCATED FOR LENGTH]"
    
    # Fill in the placeholders
    prompt = prompt_template.format(
        company_name=company_name,
        source_pages_count=len(page_sources),
        content_length=len(aggregated_content),
        aggregated_content=aggregated_content
    )
    
    return prompt


def parse_extraction_response(response_content: str) -> Dict[str, Any]:
    """Parse Nova Pro response and extract structured fields"""
    
    try:
        # Try to extract JSON from the response
        content = response_content.strip()
        
        # Find JSON object boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx+1]
            
            # Parse JSON
            extracted_data = json.loads(json_str)
            
            # Ensure it's a flat dictionary (not nested)
            if isinstance(extracted_data, dict):
                return extracted_data
            else:
                print(f"❌ Response is not a dictionary: {type(extracted_data)}")
                return {}
        else:
            print("❌ No JSON object found in response")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response preview: {response_content[:200]}...")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error parsing response: {e}")
        return {}


def validate_and_enrich_fields(extracted_fields: Dict[str, Any], company_name: str) -> Dict[str, Any]:
    """Validate extracted fields and add metadata"""
    
    # Ensure required fields exist
    if "company_name" not in extracted_fields or not extracted_fields["company_name"]:
        extracted_fields["company_name"] = company_name
    
    if "name" not in extracted_fields or not extracted_fields["name"]:
        extracted_fields["name"] = extracted_fields.get("company_name", company_name)
    
    # Convert string booleans to actual booleans
    bool_fields = ["is_saas", "has_job_listings", "has_chat_widget", "has_forms"]
    for field in bool_fields:
        if field in extracted_fields:
            value = extracted_fields[field]
            if isinstance(value, str):
                extracted_fields[field] = value.lower() in ["true", "yes", "1"]
    
    # Convert string numbers to integers
    int_fields = ["founding_year", "job_listings_count"]
    for field in int_fields:
        if field in extracted_fields and extracted_fields[field]:
            try:
                extracted_fields[field] = int(extracted_fields[field])
            except (ValueError, TypeError):
                pass
    
    # Convert string floats to floats
    float_fields = ["classification_confidence", "stage_confidence", "tech_confidence", "industry_confidence", "overall_confidence"]
    for field in float_fields:
        if field in extracted_fields and extracted_fields[field]:
            try:
                extracted_fields[field] = float(extracted_fields[field])
            except (ValueError, TypeError):
                pass
    
    # Add metadata fields
    extracted_fields["field_extraction_timestamp"] = datetime.utcnow().isoformat()
    extracted_fields["field_extraction_model"] = "amazon/nova-pro-v1"
    
    return extracted_fields


def calculate_confidence_score(extracted_fields: Dict[str, Any]) -> float:
    """Calculate overall confidence score based on field completeness"""
    
    # High-value fields and their weights
    field_weights = {
        "company_description": 0.15,
        "value_proposition": 0.10,
        "industry": 0.10,
        "business_model": 0.08,
        "target_market": 0.08,
        "products_services_offered": 0.07,
        "key_services": 0.06,
        "company_stage": 0.05,
        "tech_stack": 0.05,
        "location": 0.04,
        "founding_year": 0.04,
        "employee_count_range": 0.04,
        "contact_info": 0.03,
        "social_media": 0.03,
        "leadership_team": 0.03,
        "competitive_advantages": 0.03,
        "funding_status": 0.02
    }
    
    total_weight = sum(field_weights.values())
    achieved_weight = 0.0
    
    for field, weight in field_weights.items():
        if field in extracted_fields and extracted_fields[field]:
            # Check if field has meaningful content
            value = extracted_fields[field]
            if isinstance(value, str) and len(value.strip()) > 3:
                achieved_weight += weight
            elif isinstance(value, (list, dict)) and len(value) > 0:
                achieved_weight += weight
            elif isinstance(value, (int, float)) and value > 0:
                achieved_weight += weight
    
    # Calculate confidence as percentage of achieved weight
    confidence = achieved_weight / total_weight if total_weight > 0 else 0.0
    
    return round(confidence, 2)


def extract_company_fields(
    batch_result: BatchCrawlResult,
    company_name: str,
    llm_client: Optional[OpenRouterClient] = None,
    debug: bool = False
) -> FieldExtractionResult:
    """
    Extract structured fields from aggregated company content
    
    Args:
        batch_result: Result from batch crawling containing aggregated content
        company_name: Name of the company
        llm_client: Optional pre-initialized OpenRouter client
        debug: Enable debug logging
        
    Returns:
        FieldExtractionResult with extracted fields and metadata
    """
    
    start_time = time.time()
    
    # Validate input
    if not batch_result or not batch_result.aggregated_content:
        return FieldExtractionResult(
            success=False,
            error="No content provided for extraction"
        )
    
    # Initialize LLM client if not provided
    if not llm_client:
        llm_client = get_openrouter_client()
        if not llm_client:
            return FieldExtractionResult(
                success=False,
                error="Failed to initialize LLM client"
            )
    
    # Get page sources for attribution
    page_sources = []
    if batch_result.page_results:
        page_sources = [r.url for r in batch_result.page_results if r.success]
    
    # Create extraction prompt
    prompt = create_field_extraction_prompt(
        company_name=company_name,
        aggregated_content=batch_result.aggregated_content,
        page_sources=page_sources
    )
    
    if debug:
        print(f"\n📝 Prompt length: {len(prompt):,} characters")
    
    # Call LLM for extraction
    print(f"\n🤖 Calling Nova Pro for field extraction...")
    llm_response = llm_client.call_llm(prompt)
    
    if not llm_response.success:
        return FieldExtractionResult(
            success=False,
            error=f"LLM call failed: {llm_response.error}",
            processing_time=time.time() - start_time
        )
    
    # Parse response
    extracted_fields = parse_extraction_response(llm_response.content)
    
    if not extracted_fields:
        return FieldExtractionResult(
            success=False,
            error="Failed to parse LLM response into structured fields",
            processing_time=time.time() - start_time,
            cost_usd=llm_response.cost_usd,
            tokens_used=llm_response.usage.get("total_tokens", 0)
        )
    
    # Validate and enrich fields
    extracted_fields = validate_and_enrich_fields(extracted_fields, company_name)
    
    # Add extraction metadata
    extracted_fields["field_extraction_tokens"] = llm_response.usage.get("total_tokens", 0)
    extracted_fields["field_extraction_duration_seconds"] = round(time.time() - start_time, 2)
    extracted_fields["llm_model_used"] = llm_response.model
    extracted_fields["total_cost_usd"] = round(llm_response.cost_usd, 4)
    
    # Calculate confidence scores
    overall_confidence = calculate_confidence_score(extracted_fields)
    
    # Build field confidence scores (simplified version)
    field_confidence = {}
    for field, value in extracted_fields.items():
        if value and field not in ["field_extraction_timestamp", "field_extraction_model", "field_extraction_tokens", "field_extraction_duration_seconds"]:
            # Assign confidence based on field completeness
            if isinstance(value, str) and len(value.strip()) > 10:
                field_confidence[field] = 0.9
            elif isinstance(value, (list, dict)) and len(value) > 0:
                field_confidence[field] = 0.85
            elif value:
                field_confidence[field] = 0.8
    
    # Build source attribution
    source_attribution = {}
    for field in extracted_fields:
        if extracted_fields[field]:
            # Simple attribution - all fields come from the aggregated content
            source_attribution[field] = page_sources[:3]  # Top 3 pages
    
    # Create comprehensive company data object if available
    company_data = None
    try:
        from src.models import CompanyData
        company_data = CompanyData(**extracted_fields)
    except Exception as e:
        if debug:
            print(f"⚠️  Could not create CompanyData object: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ Extracted {len(extracted_fields)} fields in {processing_time:.1f}s")
    print(f"💰 Cost: ${llm_response.cost_usd:.4f}")
    print(f"🎯 Confidence: {overall_confidence:.0%}")
    
    return FieldExtractionResult(
        success=True,
        extracted_fields=extracted_fields,
        field_confidence_scores=field_confidence,
        overall_confidence=overall_confidence,
        source_attribution=source_attribution,
        processing_metadata={
            "total_pages_processed": batch_result.total_pages,
            "successful_pages": batch_result.successful_pages,
            "total_content_length": batch_result.total_content_length,
            "aggregation_time": batch_result.total_crawl_time
        },
        cost_usd=llm_response.cost_usd,
        tokens_used=llm_response.usage.get("total_tokens", 0),
        processing_time=processing_time,
        model_used=llm_response.model,
        company_data=company_data
    )


def main():
    """Test the field extraction with sample data"""
    
    # Sample batch crawl result for testing
    sample_result = BatchCrawlResult(
        base_url="https://example.com",
        total_pages=5,
        successful_pages=5,
        failed_pages=0,
        total_content_length=50000,
        total_crawl_time=12.5,
        aggregated_content="""
        Example Corp - Leading Technology Solutions Provider
        
        About Us:
        Founded in 2015, Example Corp is a B2B SaaS company based in San Francisco, CA.
        We provide cloud-based analytics solutions for enterprise customers.
        
        Our Products:
        - Analytics Dashboard Pro: Real-time business intelligence platform
        - DataSync Enterprise: Automated data integration solution
        - ML Insights: Machine learning powered predictive analytics
        
        Contact:
        Headquarters: 123 Market St, San Francisco, CA 94105
        Email: contact@example.com
        Phone: (555) 123-4567
        
        Leadership Team:
        - Jane Smith, CEO & Co-founder
        - John Doe, CTO & Co-founder
        - Sarah Johnson, VP of Sales
        
        We're Hiring!
        Join our team of 150+ employees. Currently hiring for:
        - Senior Software Engineers
        - Data Scientists
        - Account Executives
        
        Our Technology Stack:
        Python, React, AWS, PostgreSQL, Kubernetes, TensorFlow
        
        Awards & Recognition:
        - 2023 Best B2B SaaS Startup - TechCrunch
        - SOC 2 Type II Certified
        - ISO 27001 Compliant
        """,
        page_results=[
            PageCrawlResult(
                url="https://example.com/about",
                success=True,
                content="About content...",
                content_length=5000,
                crawl_time=2.1
            ),
            PageCrawlResult(
                url="https://example.com/products",
                success=True,
                content="Products content...",
                content_length=8000,
                crawl_time=2.5
            )
        ]
    )
    
    # Initialize client
    client = get_openrouter_client()
    if not client:
        print("❌ Failed to initialize client")
        return
    
    # Extract fields
    print("\n🚀 Starting field extraction for Example Corp...")
    result = extract_company_fields(
        batch_result=sample_result,
        company_name="Example Corp",
        llm_client=client,
        debug=True
    )
    
    if result.success:
        print("\n✅ Field Extraction Successful!")
        print(f"\n📊 Extracted {len(result.extracted_fields)} fields:")
        
        # Display key fields
        key_fields = [
            "company_name", "industry", "business_model", "location",
            "founding_year", "employee_count_range", "is_saas",
            "products_services_offered", "tech_stack", "leadership_team"
        ]
        
        for field in key_fields:
            if field in result.extracted_fields:
                value = result.extracted_fields[field]
                if isinstance(value, list):
                    print(f"  - {field}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"  - {field}: {value}")
        
        print(f"\n💰 Total cost: ${result.cost_usd:.4f}")
        print(f"📊 Tokens used: {result.tokens_used:,}")
        print(f"⏱️  Processing time: {result.processing_time:.1f}s")
        print(f"🎯 Overall confidence: {result.overall_confidence:.0%}")
    else:
        print(f"\n❌ Extraction failed: {result.error}")


if __name__ == "__main__":
    main()