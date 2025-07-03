#!/usr/bin/env python3
"""
Theodore v2 API Response Models

Pydantic models for API response serialization and documentation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

from .common import (
    JobStatus, BatchJobStatus, ProgressInfo, PaginationInfo,
    FilterInfo, SortInfo, ErrorDetail, BusinessModel, CompanySize,
    TechSophistication, IndustryCategory
)


class CompanyIntelligence(BaseModel):
    """Comprehensive company intelligence response"""
    
    # Basic Information
    name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Primary domain")
    website: Optional[str] = Field(None, description="Primary website URL")
    description: Optional[str] = Field(None, description="Company description")
    
    # Business Information
    business_model: Optional[BusinessModel] = Field(None, description="Business model classification")
    company_size: Optional[CompanySize] = Field(None, description="Company size category")
    industry: Optional[IndustryCategory] = Field(None, description="Primary industry")
    tech_sophistication: Optional[TechSophistication] = Field(None, description="Technology sophistication")
    
    # Location Information
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    locations: Optional[List[str]] = Field(None, description="All office locations")
    
    # Company Details
    founded_year: Optional[int] = Field(None, description="Year founded")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    revenue_range: Optional[str] = Field(None, description="Revenue range estimate")
    
    # Products & Services
    products: Optional[List[str]] = Field(None, description="Main products/services")
    target_market: Optional[str] = Field(None, description="Target market description")
    value_proposition: Optional[str] = Field(None, description="Value proposition")
    
    # Technology & Innovation
    technologies: Optional[List[str]] = Field(None, description="Technologies used")
    competitive_advantages: Optional[List[str]] = Field(None, description="Competitive advantages")
    
    # Market & Competitive Analysis
    competitors: Optional[List[str]] = Field(None, description="Known competitors")
    market_position: Optional[str] = Field(None, description="Market position analysis")
    
    # Contact & Social
    contact_email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Phone number")
    social_media: Optional[Dict[str, str]] = Field(None, description="Social media profiles")
    
    # Leadership
    key_personnel: Optional[List[Dict[str, str]]] = Field(None, description="Key personnel information")
    
    # Financial & Investment
    funding_stage: Optional[str] = Field(None, description="Current funding stage")
    total_funding: Optional[str] = Field(None, description="Total funding raised")
    investors: Optional[List[str]] = Field(None, description="Known investors")
    
    # AI Analysis
    ai_summary: Optional[str] = Field(None, description="AI-generated company summary")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data confidence score")
    
    # Metadata
    data_sources: Optional[List[str]] = Field(None, description="Data sources used")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    research_depth: Optional[str] = Field(None, description="Research depth level")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Anthropic",
                "domain": "anthropic.com",
                "website": "https://anthropic.com",
                "description": "AI safety company developing reliable, interpretable, and steerable AI systems",
                "business_model": "b2b",
                "company_size": "medium",
                "industry": "technology",
                "tech_sophistication": "cutting_edge",
                "headquarters": "San Francisco, CA",
                "locations": ["San Francisco, CA", "London, UK"],
                "founded_year": 2021,
                "employee_count": 150,
                "revenue_range": "$10M-$50M",
                "products": ["Claude AI", "Constitutional AI", "AI Safety Research"],
                "target_market": "Enterprise AI users, developers, researchers",
                "value_proposition": "Safe, beneficial AI that helps humans",
                "technologies": ["Machine Learning", "Natural Language Processing", "Constitutional AI"],
                "competitive_advantages": ["AI Safety Focus", "Constitutional AI", "Research Excellence"],
                "competitors": ["OpenAI", "Google DeepMind", "Cohere"],
                "market_position": "Leading AI safety company",
                "social_media": {
                    "twitter": "@AnthropicAI",
                    "linkedin": "/company/anthropic"
                },
                "key_personnel": [
                    {"name": "Dario Amodei", "role": "CEO"},
                    {"name": "Daniela Amodei", "role": "President"}
                ],
                "funding_stage": "Series B",
                "total_funding": "$750M",
                "investors": ["Google", "Spark Capital", "Salesforce"],
                "ai_summary": "Anthropic is a leading AI safety company...",
                "confidence_score": 0.92,
                "data_sources": ["website", "crunchbase", "linkedin"],
                "last_updated": "2025-01-02T10:30:00Z",
                "research_depth": "comprehensive"
            }
        }


class SimilarityResult(BaseModel):
    """Company similarity result"""
    
    company: CompanyIntelligence = Field(..., description="Similar company information")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    similarity_explanation: Optional[str] = Field(None, description="AI explanation of similarity")
    similarity_factors: Optional[Dict[str, float]] = Field(None, description="Breakdown of similarity factors")
    match_reasons: Optional[List[str]] = Field(None, description="Key reasons for the match")
    
    class Config:
        schema_extra = {
            "example": {
                "company": {
                    "name": "OpenAI",
                    "domain": "openai.com",
                    "description": "AI research and deployment company"
                },
                "similarity_score": 0.87,
                "similarity_explanation": "Both companies are AI safety-focused with similar business models",
                "similarity_factors": {
                    "industry": 0.95,
                    "business_model": 0.85,
                    "company_size": 0.80,
                    "technology": 0.90
                },
                "match_reasons": [
                    "Both focus on AI safety and research",
                    "Similar B2B SaaS business model",
                    "Comparable company size and funding"
                ]
            }
        }


class ResearchResponse(BaseModel):
    """Response model for company research"""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    company_name: str = Field(..., description="Company name being researched")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    progress: Optional[ProgressInfo] = Field(None, description="Current progress information")
    result: Optional[CompanyIntelligence] = Field(None, description="Research results if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    retry_count: Optional[int] = Field(None, description="Number of retry attempts")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "research_123456",
                "status": "completed",
                "company_name": "Anthropic",
                "created_at": "2025-01-02T10:30:00Z",
                "updated_at": "2025-01-02T10:35:00Z",
                "started_at": "2025-01-02T10:30:05Z",
                "completed_at": "2025-01-02T10:35:00Z",
                "estimated_completion": "2025-01-02T10:35:00Z",
                "progress": {
                    "current_step": "Completed",
                    "step_number": 5,
                    "total_steps": 5,
                    "percentage": 100.0
                },
                "result": {
                    "name": "Anthropic",
                    "description": "AI safety company"
                },
                "retry_count": 0
            }
        }


class DiscoveryResponse(BaseModel):
    """Response model for company discovery"""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    query_company: str = Field(..., description="Company used for similarity search")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    progress: Optional[ProgressInfo] = Field(None, description="Current progress information")
    results: Optional[List[SimilarityResult]] = Field(None, description="Discovery results if completed")
    total_found: Optional[int] = Field(None, description="Total companies found")
    filters_applied: Optional[List[FilterInfo]] = Field(None, description="Filters that were applied")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "discovery_789012",
                "status": "completed",
                "query_company": "Anthropic",
                "created_at": "2025-01-02T10:30:00Z",
                "updated_at": "2025-01-02T10:35:00Z",
                "completed_at": "2025-01-02T10:35:00Z",
                "results": [
                    {
                        "company": {"name": "OpenAI"},
                        "similarity_score": 0.87,
                        "similarity_explanation": "Both AI companies"
                    }
                ],
                "total_found": 15,
                "filters_applied": [
                    {
                        "field": "industry",
                        "operator": "in",
                        "value": ["technology"],
                        "applied": True
                    }
                ]
            }
        }


class BatchJobResponse(BaseModel):
    """Response model for batch job operations"""
    
    job_id: str = Field(..., description="Unique batch job identifier")
    status: BatchJobStatus = Field(..., description="Current batch job status")
    job_type: str = Field(..., description="Type of batch job (research/discovery)")
    total_companies: int = Field(..., description="Total companies to process")
    completed: int = Field(..., description="Companies completed successfully")
    failed: int = Field(..., description="Companies failed")
    pending: int = Field(..., description="Companies pending processing")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    output_location: Optional[str] = Field(None, description="Output file location")
    output_format: Optional[str] = Field(None, description="Output format used")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "batch_345678",
                "status": "running",
                "job_type": "research",
                "total_companies": 100,
                "completed": 45,
                "failed": 2,
                "pending": 53,
                "progress_percentage": 45.0,
                "estimated_completion": "2025-01-02T12:00:00Z",
                "created_at": "2025-01-02T10:00:00Z",
                "updated_at": "2025-01-02T10:30:00Z",
                "started_at": "2025-01-02T10:01:00Z",
                "output_location": "s3://bucket/results/batch_345678.json",
                "output_format": "json"
            }
        }


class HealthResponse(BaseModel):
    """System health response"""
    
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    
    # Component health
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    
    # System metrics
    metrics: Dict[str, Union[int, float, str]] = Field(..., description="System metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-02T10:30:00Z",
                "version": "2.0.0",
                "uptime_seconds": 3600.5,
                "components": {
                    "database": {"status": "healthy", "response_time_ms": 12},
                    "ai_services": {"status": "healthy", "response_time_ms": 245},
                    "vector_storage": {"status": "healthy", "response_time_ms": 34}
                },
                "metrics": {
                    "active_jobs": 5,
                    "completed_jobs_today": 127,
                    "error_rate_percent": 0.8,
                    "avg_response_time_ms": 450
                }
            }
        }


class MetricsResponse(BaseModel):
    """System metrics response"""
    
    timestamp: datetime = Field(..., description="Metrics collection timestamp")
    period_seconds: int = Field(..., description="Metrics collection period")
    
    # Request metrics
    requests: Dict[str, int] = Field(..., description="Request counts by endpoint")
    response_times: Dict[str, float] = Field(..., description="Average response times")
    error_rates: Dict[str, float] = Field(..., description="Error rates by endpoint")
    
    # Job metrics
    jobs: Dict[str, int] = Field(..., description="Job counts by type and status")
    
    # System metrics
    system: Dict[str, Union[int, float]] = Field(..., description="System resource usage")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-01-02T10:30:00Z",
                "period_seconds": 300,
                "requests": {
                    "/api/v2/research": 45,
                    "/api/v2/discover": 23,
                    "/api/v2/health": 120
                },
                "response_times": {
                    "/api/v2/research": 2.4,
                    "/api/v2/discover": 1.8,
                    "/api/v2/health": 0.1
                },
                "error_rates": {
                    "/api/v2/research": 0.02,
                    "/api/v2/discover": 0.01,
                    "/api/v2/health": 0.0
                },
                "jobs": {
                    "research_completed": 42,
                    "research_running": 3,
                    "discovery_completed": 18
                },
                "system": {
                    "cpu_percent": 45.2,
                    "memory_percent": 67.8,
                    "disk_percent": 23.1
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format"""
    
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Union[str, List[ErrorDetail], Dict[str, Any]]] = Field(
        None, 
        description="Additional error details"
    )
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(..., description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused error")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "code": "VALUE_ERROR",
                        "message": "Company name is required",
                        "field": "company_name"
                    }
                ],
                "status_code": 422,
                "timestamp": "2025-01-02T10:30:00Z",
                "path": "/api/v2/research",
                "request_id": "req_123456789"
            }
        }