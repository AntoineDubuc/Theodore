"""
Company domain entity representing core business data.
Clean domain model following DDD principles.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid
from enum import Enum


class CompanyStage(str, Enum):
    """Company lifecycle stage"""
    STARTUP = "startup"
    GROWTH = "growth"
    SCALE = "scale"
    ENTERPRISE = "enterprise"
    UNKNOWN = "unknown"


class TechSophistication(str, Enum):
    """Technology sophistication level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class BusinessModel(str, Enum):
    """Primary business model types"""
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    MARKETPLACE = "marketplace"
    SAAS = "saas"
    SERVICES = "services"
    ECOMMERCE = "ecommerce"
    PLATFORM = "platform"
    OTHER = "other"
    UNKNOWN = "unknown"


class CompanySize(str, Enum):
    """Company size categories"""
    MICRO = "1-10"
    SMALL = "11-50"
    MEDIUM = "51-200"
    LARGE = "201-1000"
    ENTERPRISE = "1000+"
    UNKNOWN = "unknown"


class Company(BaseModel):
    """
    Core company entity representing all business-relevant data.
    This is a clean domain model with no infrastructure concerns.
    """
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=500, description="Company legal or brand name")
    website: str = Field(..., description="Primary company website URL")
    
    # Core Business Information
    industry: Optional[str] = Field(None, max_length=200, description="Primary industry/sector")
    business_model: Optional[BusinessModel] = Field(None, description="Primary business model")
    company_size: Optional[CompanySize] = Field(None, description="Employee count range")
    company_stage: Optional[CompanyStage] = Field(None, description="Lifecycle stage")
    
    # Business Intelligence
    description: Optional[str] = Field(None, max_length=5000, description="Company overview")
    value_proposition: Optional[str] = Field(None, max_length=1000, description="Core value prop")
    target_market: Optional[str] = Field(None, max_length=500, description="Primary target market")
    products_services: List[str] = Field(default_factory=list, max_items=100, description="Main offerings")
    competitive_advantages: List[str] = Field(default_factory=list, max_items=50)
    pain_points: List[str] = Field(default_factory=list, max_items=50, description="Customer challenges solved")
    
    # Technology Profile
    tech_stack: List[str] = Field(default_factory=list, max_items=200, description="Technologies used")
    tech_sophistication: Optional[TechSophistication] = Field(None)
    has_api: bool = Field(False, description="Offers API to customers")
    has_mobile_app: bool = Field(False, description="Has mobile application")
    
    # Company Details
    founding_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year founded")
    headquarters_location: Optional[str] = Field(None, max_length=200)
    geographic_scope: Optional[str] = Field(None, description="local, regional, national, global")
    employee_count: Optional[int] = Field(None, ge=1, le=10000000)
    
    # Leadership & Culture
    leadership_team: Dict[str, str] = Field(default_factory=dict, description="Role -> Name mapping")
    company_culture: Optional[str] = Field(None, max_length=1000)
    
    # Financial & Growth
    funding_stage: Optional[str] = Field(None, description="bootstrap, seed, series_a, etc")
    total_funding: Optional[float] = Field(None, ge=0, description="Total funding in USD")
    is_profitable: Optional[bool] = Field(None)
    growth_rate: Optional[float] = Field(None, description="YoY growth percentage")
    
    # Online Presence
    social_media: Dict[str, str] = Field(default_factory=dict, description="Platform -> URL mapping")
    contact_email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None)
    
    # Sales Intelligence
    sales_complexity: Optional[str] = Field(None, description="simple, moderate, complex")
    decision_maker_titles: List[str] = Field(default_factory=list, max_items=20)
    sales_cycle_days: Optional[int] = Field(None, ge=1, le=1000)
    average_deal_size: Optional[float] = Field(None, ge=0)
    
    # Certifications & Compliance
    certifications: List[str] = Field(default_factory=list, max_items=50)
    compliance_standards: List[str] = Field(default_factory=list, max_items=50)
    
    # Partnerships & Integrations
    key_partnerships: List[str] = Field(default_factory=list, max_items=100)
    integrations: List[str] = Field(default_factory=list, max_items=200)
    
    # Market Position
    competitors: List[str] = Field(default_factory=list, max_items=50)
    market_share: Optional[float] = Field(None, ge=0, le=100, description="Percentage")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Completeness score")
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v: str) -> str:
        """Ensure website has valid format"""
        if not v:
            raise ValueError("Website cannot be empty")
        # Add http if missing
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        # Basic URL validation
        if ' ' in v or not '.' in v:
            raise ValueError(f"Invalid website URL: {v}")
        return v.lower()
    
    @field_validator('contact_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation"""
        if v and '@' not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v.lower() if v else None
    
    @field_validator('founding_year')
    @classmethod
    def validate_founding_year(cls, v: Optional[int]) -> Optional[int]:
        """Ensure founding year is reasonable"""
        if v:
            current_year = datetime.now().year
            if v > current_year:
                raise ValueError(f"Founding year cannot be in the future: {v}")
        return v
    
    def calculate_data_quality_score(self) -> float:
        """Calculate how complete the company profile is"""
        fields = [
            self.industry, self.business_model, self.description,
            self.value_proposition, self.target_market, self.founding_year,
            self.headquarters_location, self.employee_count
        ]
        filled = sum(1 for f in fields if f is not None)
        
        # Lists with content
        if self.products_services: filled += 1
        if self.tech_stack: filled += 1
        if self.leadership_team: filled += 1
        if self.certifications: filled += 1
        
        total_fields = 12
        self.data_quality_score = filled / total_fields
        return self.data_quality_score
    
    def is_tech_company(self) -> bool:
        """Determine if this is primarily a technology company"""
        tech_indicators = [
            self.tech_sophistication == TechSophistication.HIGH,
            self.business_model in [BusinessModel.SAAS, BusinessModel.PLATFORM],
            len(self.tech_stack) > 5,
            self.has_api,
            any(term in (self.industry or '').lower() 
                for term in ['tech', 'software', 'saas', 'cloud', 'ai', 'data'])
        ]
        return sum(tech_indicators) >= 2
    
    def to_embedding_text(self) -> str:
        """Generate text representation for embedding generation"""
        parts = [
            f"Company: {self.name}",
            f"Industry: {self.industry or 'Unknown'}",
            f"Business Model: {self.business_model or 'Unknown'}",
            f"Description: {self.description or 'No description'}",
            f"Value Proposition: {self.value_proposition or 'Not specified'}",
            f"Target Market: {self.target_market or 'Not specified'}",
        ]
        
        if self.products_services:
            parts.append(f"Products/Services: {', '.join(self.products_services[:10])}")
        
        if self.tech_stack:
            parts.append(f"Technologies: {', '.join(self.tech_stack[:20])}")
            
        return '\n'.join(parts)
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        json_schema_extra={
            "example": {
                "name": "Acme Corp",
                "website": "https://acme.com",
                "industry": "Software",
                "business_model": "saas",
                "description": "Leading provider of widget automation",
                "value_proposition": "Automate widget production 10x faster",
                "target_market": "Manufacturing companies",
                "products_services": ["Widget Automation Platform", "Widget Analytics"],
                "tech_stack": ["Python", "React", "PostgreSQL", "AWS"],
                "founding_year": 2015,
                "company_size": "51-200"
            }
        }
    )