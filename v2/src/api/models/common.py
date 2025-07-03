#!/usr/bin/env python3
"""
Theodore v2 API Common Models

Shared models and enums used across the API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobPriority(str, Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BatchJobStatus(str, Enum):
    """Batch job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class OutputFormat(str, Enum):
    """Output format options"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"
    YAML = "yaml"


class BusinessModel(str, Enum):
    """Business model categories"""
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    MARKETPLACE = "marketplace"
    SaaS = "saas"
    ECOMMERCE = "ecommerce"
    SUBSCRIPTION = "subscription"
    FREEMIUM = "freemium"
    ADVERTISING = "advertising"
    UNKNOWN = "unknown"


class CompanySize(str, Enum):
    """Company size categories"""
    STARTUP = "startup"  # 1-10 employees
    SMALL = "small"      # 11-50 employees
    MEDIUM = "medium"    # 51-200 employees
    LARGE = "large"      # 201-1000 employees
    ENTERPRISE = "enterprise"  # 1000+ employees
    UNKNOWN = "unknown"


class TechSophistication(str, Enum):
    """Technology sophistication levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    CUTTING_EDGE = "cutting_edge"
    UNKNOWN = "unknown"


class IndustryCategory(str, Enum):
    """Industry categories"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    MEDIA = "media"
    REAL_ESTATE = "real_estate"
    ENERGY = "energy"
    TRANSPORTATION = "transportation"
    AGRICULTURE = "agriculture"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    OTHER = "other"
    UNKNOWN = "unknown"


class ProgressInfo(BaseModel):
    """Progress information for long-running operations"""
    
    current_step: str = Field(..., description="Current processing step")
    step_number: int = Field(..., ge=0, description="Current step number")
    total_steps: int = Field(..., ge=1, description="Total number of steps")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Completion percentage")
    message: Optional[str] = Field(None, description="Progress message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional progress details")
    started_at: datetime = Field(..., description="Process start time")
    updated_at: datetime = Field(..., description="Last update time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    class Config:
        schema_extra = {
            "example": {
                "current_step": "AI Analysis",
                "step_number": 3,
                "total_steps": 5,
                "percentage": 60.0,
                "message": "Analyzing company data with AI models",
                "details": {
                    "pages_processed": 12,
                    "ai_tokens_used": 15432
                },
                "started_at": "2025-01-02T10:30:00Z",
                "updated_at": "2025-01-02T10:32:15Z",
                "estimated_completion": "2025-01-02T10:35:00Z"
            }
        }


class CompanyInput(BaseModel):
    """Input model for company information"""
    
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    website: Optional[str] = Field(None, description="Company website URL")
    domain: Optional[str] = Field(None, description="Company domain")
    industry: Optional[str] = Field(None, description="Company industry")
    location: Optional[str] = Field(None, description="Company location")
    custom_id: Optional[str] = Field(None, description="Custom identifier for tracking")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('website')
    def validate_website(cls, v):
        """Ensure website has proper protocol"""
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        """Clean domain format"""
        if v:
            # Remove protocol and www
            v = v.replace('http://', '').replace('https://', '').replace('www.', '')
            # Remove trailing slash
            v = v.rstrip('/')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "website": "https://acme.com",
                "domain": "acme.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "custom_id": "ACME_001",
                "metadata": {
                    "source": "crunchbase",
                    "priority": "high"
                }
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information"""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class PaginationInfo(BaseModel):
    """Pagination information for list responses"""
    
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, le=100, description="Page size")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class FilterInfo(BaseModel):
    """Applied filter information"""
    
    field: str = Field(..., description="Filtered field name")
    operator: str = Field(..., description="Filter operator")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Filter value")
    applied: bool = Field(..., description="Whether filter was successfully applied")


class SortInfo(BaseModel):
    """Sort information"""
    
    field: str = Field(..., description="Sort field")
    direction: str = Field(..., regex="^(asc|desc)$", description="Sort direction")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "similarity_score",
                "direction": "desc"
            }
        }