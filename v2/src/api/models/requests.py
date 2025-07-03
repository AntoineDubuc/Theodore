#!/usr/bin/env python3
"""
Theodore v2 API Request Models

Pydantic models for API request validation and documentation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator

from .common import (
    JobPriority, OutputFormat, BusinessModel, CompanySize,
    TechSophistication, IndustryCategory, CompanyInput
)


class ResearchRequest(BaseModel):
    """Request model for company research"""
    
    company_name: str = Field(
        ..., 
        min_length=1, 
        max_length=200, 
        description="Company name to research"
    )
    website: Optional[str] = Field(
        None, 
        description="Company website URL (optional but improves accuracy)"
    )
    config_overrides: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuration overrides for this research"
    )
    priority: Optional[JobPriority] = Field(
        JobPriority.NORMAL, 
        description="Job priority level"
    )
    webhook_url: Optional[str] = Field(
        None, 
        description="Webhook URL for completion notification"
    )
    tags: Optional[List[str]] = Field(
        None, 
        description="Custom tags for job organization",
        max_items=10
    )
    timeout_seconds: Optional[int] = Field(
        None,
        ge=30,
        le=3600,
        description="Research timeout in seconds"
    )
    deep_analysis: Optional[bool] = Field(
        False,
        description="Enable deep analysis mode (slower but more comprehensive)"
    )
    
    @validator('website')
    def validate_website(cls, v):
        """Ensure website has proper protocol"""
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags"""
        if v:
            # Remove empty tags and duplicates
            cleaned = list(set(tag.strip() for tag in v if tag.strip()))
            return cleaned[:10]  # Limit to 10 tags
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "company_name": "Anthropic",
                "website": "https://anthropic.com",
                "config_overrides": {
                    "max_pages": 20,
                    "include_social_media": True
                },
                "priority": "normal",
                "webhook_url": "https://example.com/webhook",
                "tags": ["ai", "startup", "priority"],
                "timeout_seconds": 300,
                "deep_analysis": False
            }
        }


class DiscoveryFilters(BaseModel):
    """Advanced filtering options for discovery"""
    
    business_model: Optional[List[BusinessModel]] = Field(
        None, 
        description="Filter by business models"
    )
    company_size: Optional[List[CompanySize]] = Field(
        None, 
        description="Filter by company size"
    )
    tech_sophistication: Optional[List[TechSophistication]] = Field(
        None,
        description="Filter by technology sophistication level"
    )
    industry: Optional[List[IndustryCategory]] = Field(
        None, 
        description="Filter by industry categories"
    )
    location: Optional[List[str]] = Field(
        None, 
        description="Filter by location (country, state, city)",
        max_items=20
    )
    founded_after: Optional[int] = Field(
        None, 
        ge=1800, 
        le=2025, 
        description="Founded after year"
    )
    founded_before: Optional[int] = Field(
        None, 
        ge=1800, 
        le=2025, 
        description="Founded before year"
    )
    min_employees: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum number of employees"
    )
    max_employees: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of employees"
    )
    exclude_competitors: Optional[bool] = Field(
        False, 
        description="Exclude direct competitors"
    )
    exclude_companies: Optional[List[str]] = Field(
        None,
        description="List of company names to exclude",
        max_items=50
    )
    include_keywords: Optional[List[str]] = Field(
        None,
        description="Keywords that must be present",
        max_items=20
    )
    exclude_keywords: Optional[List[str]] = Field(
        None,
        description="Keywords to exclude",
        max_items=20
    )
    
    @root_validator
    def validate_date_range(cls, values):
        """Validate founded date range"""
        founded_after = values.get('founded_after')
        founded_before = values.get('founded_before')
        
        if founded_after and founded_before and founded_after >= founded_before:
            raise ValueError('founded_after must be less than founded_before')
        
        return values
    
    @root_validator
    def validate_employee_range(cls, values):
        """Validate employee range"""
        min_employees = values.get('min_employees')
        max_employees = values.get('max_employees')
        
        if min_employees and max_employees and min_employees > max_employees:
            raise ValueError('min_employees must be less than or equal to max_employees')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "business_model": ["b2b", "saas"],
                "company_size": ["medium", "large"],
                "tech_sophistication": ["advanced"],
                "industry": ["technology", "finance"],
                "location": ["United States", "Canada"],
                "founded_after": 2010,
                "founded_before": 2020,
                "min_employees": 50,
                "max_employees": 500,
                "exclude_competitors": True,
                "exclude_companies": ["CompetitorA", "CompetitorB"],
                "include_keywords": ["artificial intelligence", "machine learning"],
                "exclude_keywords": ["consulting", "outsourcing"]
            }
        }


class DiscoveryRequest(BaseModel):
    """Request model for company discovery"""
    
    company_name: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Company name to find similar companies for"
    )
    limit: Optional[int] = Field(
        10, 
        ge=1, 
        le=100, 
        description="Maximum results to return"
    )
    similarity_threshold: Optional[float] = Field(
        0.6, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score (0.0 to 1.0)"
    )
    filters: Optional[DiscoveryFilters] = Field(
        None, 
        description="Advanced filtering options"
    )
    include_research: Optional[bool] = Field(
        False, 
        description="Include full research for discovered companies"
    )
    source_preference: Optional[List[str]] = Field(
        None, 
        description="Preferred discovery sources in priority order",
        max_items=10
    )
    enable_ai_explanations: Optional[bool] = Field(
        True,
        description="Generate AI explanations for similarity matches"
    )
    webhook_url: Optional[str] = Field(
        None, 
        description="Webhook URL for completion notification"
    )
    priority: Optional[JobPriority] = Field(
        JobPriority.NORMAL, 
        description="Job priority level"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "company_name": "Anthropic",
                "limit": 20,
                "similarity_threshold": 0.7,
                "filters": {
                    "business_model": ["b2b", "saas"],
                    "company_size": ["medium", "large"],
                    "industry": ["technology"]
                },
                "include_research": True,
                "source_preference": ["database", "ai_search", "web_search"],
                "enable_ai_explanations": True,
                "webhook_url": "https://example.com/webhook",
                "priority": "normal"
            }
        }


class BatchResearchRequest(BaseModel):
    """Request model for batch company research"""
    
    input_data: Union[List[CompanyInput], str] = Field(
        ..., 
        description="Company list or file reference"
    )
    output_format: Optional[OutputFormat] = Field(
        OutputFormat.JSON, 
        description="Output format preference"
    )
    concurrency: Optional[int] = Field(
        5, 
        ge=1, 
        le=20, 
        description="Concurrent processing limit"
    )
    priority: Optional[JobPriority] = Field(
        JobPriority.NORMAL, 
        description="Batch job priority"
    )
    webhook_url: Optional[str] = Field(
        None, 
        description="Completion webhook URL"
    )
    config_overrides: Optional[Dict[str, Any]] = Field(
        None, 
        description="Processing configuration overrides"
    )
    resume_job_id: Optional[str] = Field(
        None, 
        description="Job ID to resume if applicable"
    )
    retry_failed: Optional[bool] = Field(
        True,
        description="Retry failed companies"
    )
    max_retries: Optional[int] = Field(
        3,
        ge=0,
        le=10,
        description="Maximum retry attempts per company"
    )
    output_location: Optional[str] = Field(
        None,
        description="Output file location (S3, local path, etc.)"
    )
    
    @validator('input_data')
    def validate_input_data(cls, v):
        """Validate input data format"""
        if isinstance(v, str):
            # File reference - validate format/extension
            if not v.endswith(('.json', '.csv', '.xlsx', '.yaml')):
                raise ValueError('File must be JSON, CSV, Excel, or YAML format')
        elif isinstance(v, list):
            # Direct list - validate not empty and reasonable size
            if not v:
                raise ValueError('Company list cannot be empty')
            if len(v) > 10000:
                raise ValueError('Company list too large (max 10,000 companies)')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "input_data": [
                    {
                        "name": "Anthropic",
                        "website": "https://anthropic.com",
                        "custom_id": "ANTH_001"
                    },
                    {
                        "name": "OpenAI", 
                        "website": "https://openai.com",
                        "custom_id": "OPEN_001"
                    }
                ],
                "output_format": "json",
                "concurrency": 8,
                "priority": "normal",
                "webhook_url": "https://example.com/webhook",
                "config_overrides": {
                    "max_pages": 15,
                    "timeout_seconds": 300
                },
                "retry_failed": True,
                "max_retries": 3,
                "output_location": "s3://my-bucket/results/"
            }
        }


class BatchDiscoveryRequest(BaseModel):
    """Request model for batch company discovery"""
    
    input_data: Union[List[CompanyInput], str] = Field(
        ..., 
        description="Company list or file reference"
    )
    discovery_config: DiscoveryRequest = Field(
        ...,
        description="Discovery configuration to apply to all companies"
    )
    output_format: Optional[OutputFormat] = Field(
        OutputFormat.JSON, 
        description="Output format preference"
    )
    concurrency: Optional[int] = Field(
        3, 
        ge=1, 
        le=10, 
        description="Concurrent processing limit"
    )
    priority: Optional[JobPriority] = Field(
        JobPriority.NORMAL, 
        description="Batch job priority"
    )
    webhook_url: Optional[str] = Field(
        None, 
        description="Completion webhook URL"
    )
    deduplicate_results: Optional[bool] = Field(
        True,
        description="Remove duplicate companies from results"
    )
    output_location: Optional[str] = Field(
        None,
        description="Output file location"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "input_data": [
                    {"name": "Anthropic", "website": "https://anthropic.com"},
                    {"name": "OpenAI", "website": "https://openai.com"}
                ],
                "discovery_config": {
                    "company_name": "placeholder",
                    "limit": 10,
                    "similarity_threshold": 0.7,
                    "include_research": False
                },
                "output_format": "json",
                "concurrency": 5,
                "priority": "normal",
                "deduplicate_results": True,
                "output_location": "s3://my-bucket/discovery-results/"
            }
        }