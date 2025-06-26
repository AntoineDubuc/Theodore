"""
Pydantic models for Theodore company intelligence system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum
import uuid


class SaaSCategory(str, Enum):
    """59-category SaaS business model taxonomy"""
    
    # SaaS Verticals (26 categories - corrected count)
    ADTECH = "AdTech"
    ASSET_MANAGEMENT = "AssetManagement"
    BILLING = "Billing"
    BIO_LS = "Bio/LS"
    COLLAB_TECH = "CollabTech"
    DATA_BI_ANALYTICS = "Data/BI/Analytics"
    DEVOPS_CLOUD_INFRA = "DevOps/CloudInfra"
    ECOMMERCE_RETAIL = "E-commerce & Retail"
    EDTECH = "EdTech"
    ENERTECH = "Enertech"
    FINTECH = "FinTech"
    GOVTECH = "GovTech"
    HRTECH = "HRTech"
    HEALTHTECH = "HealthTech"
    IAM = "Identity & Access Management (IAM)"
    INSURETECH = "InsureTech"
    LAWTECH = "LawTech"
    LEISURETECH = "LeisureTech"
    MANUFACTURING_AGTECH_IOT = "Manufacturing/AgTech/IoT"
    MARTECH_CRM = "Martech & CRM"
    MEDIATECH = "MediaTech"
    PROPTECH = "PropTech"
    RISK_AUDIT_GOVERNANCE = "Risk/Audit/Governance"
    SOCIAL_COMMUNITY_NONPROFIT = "Social / Community / Non Profit"
    SUPPLY_CHAIN_LOGISTICS = "Supply Chain & Logistics"
    TRANSPOTECH = "TranspoTech"
    
    # Non-SaaS Categories (17 categories - corrected count)
    ADVERTISING_MEDIA_SERVICES = "Advertising & Media Services"
    BIOPHARMA_RD = "Biopharma R&D"
    COMBO_HW_SW = "Combo HW & SW"
    EDUCATION = "Education"
    ENERGY = "Energy"
    FINANCIAL_SERVICES = "Financial Services"
    HEALTHCARE_SERVICES = "Healthcare Services"
    INDUSTRY_CONSULTING = "Industry Consulting Services"
    INSURANCE = "Insurance"
    IT_CONSULTING = "IT Consulting Services"
    LOGISTICS_SERVICES = "Logistics Services"
    MANUFACTURING = "Manufacturing"
    NONPROFIT = "Non-Profit"
    RETAIL = "Retail"
    SPORTS = "Sports"
    TRAVEL_LEISURE = "Travel & Leisure"
    WHOLESALE_DISTRIBUTION = "Wholesale Distribution & Supply"
    
    # Special category
    UNCLASSIFIED = "Unclassified"


class ClassificationResult(BaseModel):
    """Result of business model classification"""
    category: SaaSCategory
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    justification: str = Field(..., min_length=10, description="One-sentence explanation")
    model_version: str = Field(default="v1.0", description="Classification model version")
    timestamp: datetime = Field(default_factory=datetime.now)
    is_saas: bool = Field(..., description="True if SaaS, False if Non-SaaS")


class CompanyData(BaseModel):
    """Company intelligence data model"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Company name")
    website: str = Field(..., description="Company website URL")
    
    # Basic company info
    industry: Optional[str] = Field(None, description="Detected industry/sector")
    business_model: Optional[str] = Field(None, description="B2B, B2C, marketplace, etc.")
    company_size: Optional[str] = Field(None, description="startup, SMB, enterprise")
    
    # Technology insights
    tech_stack: List[str] = Field(default_factory=list, description="Detected technologies")
    has_chat_widget: bool = Field(False, description="Has customer support chat")
    has_forms: bool = Field(False, description="Has lead capture forms")
    
    # Business intelligence
    pain_points: List[str] = Field(default_factory=list, description="Inferred business challenges")
    key_services: List[str] = Field(default_factory=list, description="Main offerings")
    competitive_advantages: List[str] = Field(default_factory=list, description="Company competitive advantages")
    target_market: Optional[str] = Field(None, description="Who they serve")
    business_model_framework: Optional[str] = Field(None, description="David's Business Model Framework classification")
    
    # Extended metadata from Crawl4AI
    company_description: Optional[str] = Field(None, description="About/description from website")
    value_proposition: Optional[str] = Field(None, description="Main value proposition")
    founding_year: Optional[int] = Field(None, description="Year company was founded")
    location: Optional[str] = Field(None, description="Company headquarters location")
    employee_count_range: Optional[str] = Field(None, description="Estimated employee count")
    company_culture: Optional[str] = Field(None, description="Company culture and values")
    funding_status: Optional[str] = Field(None, description="Funding stage/status")
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media links")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    leadership_team: List[str] = Field(default_factory=list, description="Key leadership names")
    recent_news: List[str] = Field(default_factory=list, description="Recent company news/updates")
    certifications: List[str] = Field(default_factory=list, description="Industry certifications")
    partnerships: List[str] = Field(default_factory=list, description="Key partnerships")
    awards: List[str] = Field(default_factory=list, description="Awards and recognition")
    
    # Multi-page crawling results
    pages_crawled: List[str] = Field(default_factory=list, description="URLs successfully crawled")
    crawl_depth: int = Field(default=1, description="Number of pages deep crawled")
    crawl_duration: Optional[float] = Field(None, description="Time taken to crawl in seconds")
    
    # SaaS Classification fields (Phase 5 of pipeline)
    saas_classification: Optional[str] = Field(None, description="Business model classification category")
    classification_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Classification confidence score")
    classification_justification: Optional[str] = Field(None, description="One-sentence explanation for classification")
    classification_timestamp: Optional[datetime] = Field(None, description="When classification was performed")
    classification_model_version: Optional[str] = Field(default="v1.0", description="Version of classification model used")
    is_saas: Optional[bool] = Field(None, description="Quick boolean: True for SaaS, False for Non-SaaS")
    
    # Similarity metrics for sales intelligence
    company_stage: Optional[str] = Field(None, description="startup, growth, enterprise")
    tech_sophistication: Optional[str] = Field(None, description="low, medium, high")
    geographic_scope: Optional[str] = Field(None, description="local, regional, global")
    business_model_type: Optional[str] = Field(None, description="saas, services, marketplace, ecommerce, other")
    decision_maker_type: Optional[str] = Field(None, description="technical, business, hybrid")
    sales_complexity: Optional[str] = Field(None, description="simple, moderate, complex")
    
    # Confidence scores for similarity metrics
    stage_confidence: Optional[float] = Field(None, description="Confidence in company stage classification (0-1)")
    tech_confidence: Optional[float] = Field(None, description="Confidence in tech sophistication (0-1)")
    industry_confidence: Optional[float] = Field(None, description="Confidence in industry classification (0-1)")
    
    # Batch Research Intelligence (from BATCH_RESEARCH.md requirements)
    has_job_listings: Optional[bool] = Field(None, description="Does this company have open job listings?")
    job_listings_count: Optional[int] = Field(None, description="Number of current job openings")
    job_listings: Optional[str] = Field(None, description="Job listings summary or status")
    job_listings_details: List[str] = Field(default_factory=list, description="Job titles and departments")
    products_services_offered: List[str] = Field(default_factory=list, description="What products/services does this company offer?")
    key_decision_makers: Dict[str, str] = Field(default_factory=dict, description="Key decision makers (CEO, CMO, Head of Product, etc.)")
    funding_stage_detailed: Optional[str] = Field(None, description="Detailed funding stage (bootstrap, seed, series_a, etc.)")
    sales_marketing_tools: List[str] = Field(default_factory=list, description="What sales/marketing tools does the company use?")
    recent_news_events: List[Dict[str, str]] = Field(default_factory=list, description="Recent news/events with date and description")
    
    # AI analysis
    raw_content: Optional[str] = Field(None, description="Scraped website content")
    ai_summary: Optional[str] = Field(None, description="Bedrock-generated summary")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
    # Scraping details
    scraped_urls: List[str] = Field(default_factory=list, description="URLs that were successfully scraped")
    scraped_content_details: Dict[str, str] = Field(default_factory=dict, description="URL -> content mapping")
    
    # LLM interaction details
    llm_prompts_sent: List[Dict[str, str]] = Field(default_factory=list, description="Prompts sent to LLM with responses")
    page_selection_prompt: Optional[str] = Field(None, description="Prompt used for page selection")
    content_analysis_prompt: Optional[str] = Field(None, description="Prompt used for content analysis")
    
    # Token usage and cost tracking
    total_input_tokens: int = Field(default=0, description="Total input tokens used across all LLM calls")
    total_output_tokens: int = Field(default=0, description="Total output tokens generated across all LLM calls")
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD for all LLM calls")
    llm_calls_breakdown: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed breakdown of each LLM call with tokens and cost")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    scrape_status: str = Field(default="pending", description="pending, success, failed")
    scrape_error: Optional[str] = Field(None, description="Error message if scraping failed")


class SectorCluster(BaseModel):
    """Sector clustering results"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Sector name (e.g., 'Healthcare Tech')")
    companies: List[str] = Field(..., description="List of company IDs in this sector")
    
    # Sector insights
    common_pain_points: List[str] = Field(default_factory=list)
    common_technologies: List[str] = Field(default_factory=list)
    average_company_size: Optional[str] = Field(None)
    
    # Cluster metadata
    centroid_embedding: Optional[List[float]] = Field(None, description="Sector centroid vector")
    similarity_threshold: float = Field(0.7, description="Similarity threshold used")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SimilarityRelation(BaseModel):
    """Company-to-company similarity relationship"""
    
    company_a_id: str = Field(..., description="First company ID")
    company_b_id: str = Field(..., description="Second company ID")
    similarity_score: float = Field(..., description="Cosine similarity score")
    relationship_type: str = Field(..., description="similar, competitor, complementary")
    
    # Relationship metadata
    shared_technologies: List[str] = Field(default_factory=list)
    shared_pain_points: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SurveyResponse(BaseModel):
    """Input survey response data"""
    
    company_name: str = Field(..., description="Company name from survey")
    website: Optional[str] = Field(None, description="Company website if provided")
    contact_email: Optional[str] = Field(None, description="Contact email")
    pain_points: Optional[str] = Field(None, description="Self-reported pain points")
    
    # Survey-specific fields
    survey_date: Optional[datetime] = Field(None)
    survey_source: Optional[str] = Field(None, description="Survey campaign source")
    
    
class ProcessingJob(BaseModel):
    """Batch processing job tracking"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = Field(default="pending", description="pending, running, completed, failed")
    
    # Job configuration
    total_companies: int = Field(..., description="Total companies to process")
    processed_companies: int = Field(default=0)
    failed_companies: int = Field(default=0)
    
    # Results
    sectors_discovered: int = Field(default=0)
    similarity_relations: int = Field(default=0)
    
    # Timing
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate job progress percentage"""
        if self.total_companies == 0:
            return 0.0
        return (self.processed_companies / self.total_companies) * 100


class CompanySimilarity(BaseModel):
    """Company similarity relationship data"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_company_id: str = Field(..., description="ID of the original company")
    similar_company_id: str = Field(..., description="ID of the similar company")
    original_company_name: str = Field(..., description="Name of original company")
    similar_company_name: str = Field(..., description="Name of similar company")
    
    # Similarity metrics
    similarity_score: float = Field(..., description="Overall similarity score (0-1)")
    confidence: float = Field(..., description="Confidence in similarity assessment (0-1)")
    
    # Discovery metadata
    discovery_method: str = Field(default="llm", description="How similarity was discovered")
    validation_methods: List[str] = Field(default_factory=list, description="Methods used to validate similarity")
    votes: List[str] = Field(default_factory=list, description="Validation methods that agreed")
    
    # Method-specific scores
    structured_score: Optional[float] = Field(None, description="Structured comparison score")
    embedding_score: Optional[float] = Field(None, description="Embedding similarity score")
    llm_judge_score: Optional[float] = Field(None, description="LLM judge score")
    
    # Reasoning and details
    reasoning: List[str] = Field(default_factory=list, description="Human-readable similarity reasons")
    similarity_aspects: List[str] = Field(default_factory=list, description="Specific aspects that are similar")
    
    # Relationship direction
    is_bidirectional: bool = Field(default=True, description="Whether similarity works both ways")
    relationship_type: str = Field(default="competitor", description="Type of relationship: competitor, adjacent, aspirational")
    
    # Status and validation
    validation_status: str = Field(default="pending", description="pending, validated, rejected")
    validated_by: Optional[str] = Field(None, description="Who/what validated this similarity")
    validated_at: Optional[datetime] = Field(None, description="When validation occurred")
    
    # Timestamps
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SimilarityCluster(BaseModel):
    """Group of similar companies forming a cluster"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cluster_name: str = Field(..., description="Human-readable cluster name")
    company_ids: List[str] = Field(default_factory=list, description="Company IDs in this cluster")
    company_names: List[str] = Field(default_factory=list, description="Company names for quick reference")
    
    # Cluster characteristics
    primary_industry: Optional[str] = Field(None, description="Main industry of cluster")
    business_model: Optional[str] = Field(None, description="Common business model")
    average_company_size: Optional[str] = Field(None, description="Typical company size in cluster")
    common_technologies: List[str] = Field(default_factory=list, description="Technologies used by multiple companies")
    
    # Cluster metrics
    cohesion_score: float = Field(default=0.0, description="How similar companies in cluster are (0-1)")
    cluster_size: int = Field(default=0, description="Number of companies in cluster")
    
    # Discovery metadata
    clustering_method: str = Field(default="similarity_graph", description="How cluster was formed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FieldExtractionResult(BaseModel):
    """Result of extracting a specific field from company data"""
    
    field_name: str = Field(..., description="Name of the field (e.g., 'founding_year', 'location')")
    success: bool = Field(..., description="Whether extraction was successful")
    value: Optional[str] = Field(None, description="Extracted value if successful")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in extraction (0-1)")
    method: str = Field(..., description="Extraction method: regex, ai_analysis, manual, etc.")
    source_page: Optional[str] = Field(None, description="URL where field was found")
    extraction_time: float = Field(default=0.0, description="Time taken to extract this field")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FieldExtractionMetrics(BaseModel):
    """Aggregated field extraction metrics for analytics"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str = Field(..., description="Name of the field being tracked")
    
    # Success metrics
    total_attempts: int = Field(default=0, description="Total extraction attempts")
    successful_extractions: int = Field(default=0, description="Number of successful extractions")
    failed_extractions: int = Field(default=0, description="Number of failed extractions")
    
    # Success rate calculations
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0-1)")
    
    # Performance metrics
    avg_extraction_time: float = Field(default=0.0, description="Average time per extraction")
    avg_confidence: float = Field(default=0.0, description="Average confidence score")
    
    # Method breakdown
    method_performance: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Performance by extraction method (regex, ai_analysis, etc.)"
    )
    
    # Recent performance trends
    last_24h_success_rate: Optional[float] = Field(None, description="Success rate in last 24 hours")
    last_week_success_rate: Optional[float] = Field(None, description="Success rate in last week")
    
    # Data quality insights
    common_failure_reasons: List[str] = Field(default_factory=list, description="Most common failure reasons")
    improvement_suggestions: List[str] = Field(default_factory=list, description="AI-generated improvement suggestions")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_success_rate(self):
        """Calculate and update success rate"""
        if self.total_attempts > 0:
            self.success_rate = self.successful_extractions / self.total_attempts
        else:
            self.success_rate = 0.0
    
    def add_extraction_result(self, result: FieldExtractionResult):
        """Add a new extraction result and update metrics"""
        self.total_attempts += 1
        
        if result.success:
            self.successful_extractions += 1
        else:
            self.failed_extractions += 1
            if result.error_message:
                self.common_failure_reasons.append(result.error_message)
        
        # Update method performance
        method = result.method
        if method not in self.method_performance:
            self.method_performance[method] = {
                "attempts": 0,
                "successes": 0,
                "avg_time": 0.0,
                "avg_confidence": 0.0
            }
        
        method_data = self.method_performance[method]
        method_data["attempts"] += 1
        if result.success:
            method_data["successes"] += 1
        
        # Update averages
        method_data["avg_time"] = (
            (method_data["avg_time"] * (method_data["attempts"] - 1) + result.extraction_time) / 
            method_data["attempts"]
        )
        
        if result.confidence is not None:
            method_data["avg_confidence"] = (
                (method_data["avg_confidence"] * (method_data["attempts"] - 1) + result.confidence) / 
                method_data["attempts"]
            )
        
        # Recalculate overall metrics
        self.calculate_success_rate()
        self.last_updated = datetime.utcnow()


class CompanyFieldExtractionSession(BaseModel):
    """Track field extraction for a specific company processing session"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = Field(..., description="Company being processed")
    company_name: str = Field(..., description="Company name for reference")
    
    # Session details
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = Field(None)
    total_processing_time: float = Field(default=0.0, description="Total session time in seconds")
    
    # Field extraction results
    field_results: List[FieldExtractionResult] = Field(default_factory=list, description="Results for each field")
    
    # Session summary
    fields_attempted: int = Field(default=0)
    fields_successful: int = Field(default=0)
    fields_failed: int = Field(default=0)
    session_success_rate: float = Field(default=0.0)
    
    # Processing details
    pages_scraped: int = Field(default=0)
    ai_calls_made: int = Field(default=0)
    total_tokens_used: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    
    def add_field_result(self, result: FieldExtractionResult):
        """Add a field extraction result to this session"""
        self.field_results.append(result)
        self.fields_attempted += 1
        
        if result.success:
            self.fields_successful += 1
        else:
            self.fields_failed += 1
        
        # Update session success rate
        self.session_success_rate = self.fields_successful / self.fields_attempted if self.fields_attempted > 0 else 0.0
    
    def complete_session(self):
        """Mark session as complete and calculate final metrics"""
        self.session_end = datetime.utcnow()
        if self.session_start:
            self.total_processing_time = (self.session_end - self.session_start).total_seconds()


class UserPrompt(BaseModel):
    """User-specific prompt configuration stored in Pinecone"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID who owns this prompt")
    prompt_type: str = Field(..., description="Type of prompt: analysis, page_selection, extraction, custom")
    prompt_name: str = Field(..., description="User-friendly name for the prompt")
    prompt_content: str = Field(..., description="The actual prompt text")
    
    # Metadata
    description: Optional[str] = Field(None, description="User description of what this prompt does")
    is_active: bool = Field(default=True, description="Whether this prompt is currently active")
    is_default: bool = Field(default=False, description="Whether this is the user's default for this type")
    
    # Usage tracking
    usage_count: int = Field(default=0, description="How many times this prompt has been used")
    last_used: Optional[datetime] = Field(None, description="When this prompt was last used")
    
    # Performance tracking
    avg_success_rate: Optional[float] = Field(None, description="Average success rate when using this prompt")
    avg_processing_time: Optional[float] = Field(None, description="Average processing time")
    avg_cost_per_use: Optional[float] = Field(None, description="Average cost per use")
    
    # Versioning
    version: int = Field(default=1, description="Version number for this prompt")
    parent_prompt_id: Optional[str] = Field(None, description="ID of the prompt this was based on")
    
    # Sharing
    is_public: bool = Field(default=False, description="Whether other users can see/use this prompt")
    shared_with: List[str] = Field(default_factory=list, description="User IDs this prompt is shared with")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def update_usage_stats(self, success_rate: float, processing_time: float, cost: float):
        """Update prompt usage statistics"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        
        # Calculate running averages
        if self.avg_success_rate is None:
            self.avg_success_rate = success_rate
        else:
            self.avg_success_rate = (self.avg_success_rate * (self.usage_count - 1) + success_rate) / self.usage_count
        
        if self.avg_processing_time is None:
            self.avg_processing_time = processing_time
        else:
            self.avg_processing_time = (self.avg_processing_time * (self.usage_count - 1) + processing_time) / self.usage_count
        
        if self.avg_cost_per_use is None:
            self.avg_cost_per_use = cost
        else:
            self.avg_cost_per_use = (self.avg_cost_per_use * (self.usage_count - 1) + cost) / self.usage_count


class UserPromptLibrary(BaseModel):
    """Collection of prompts for a specific user"""
    
    user_id: str = Field(..., description="User ID who owns this library")
    prompts: List[UserPrompt] = Field(default_factory=list, description="User's prompts")
    
    # Library metadata
    total_prompts: int = Field(default=0, description="Total number of prompts")
    total_usage: int = Field(default=0, description="Total usage across all prompts")
    avg_library_success_rate: Optional[float] = Field(None, description="Average success rate across all prompts")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    def add_prompt(self, prompt: UserPrompt):
        """Add a new prompt to the library"""
        self.prompts.append(prompt)
        self.total_prompts = len(self.prompts)
        self.last_accessed = datetime.utcnow()
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[UserPrompt]:
        """Get a specific prompt by ID"""
        return next((p for p in self.prompts if p.id == prompt_id), None)
    
    def get_prompts_by_type(self, prompt_type: str) -> List[UserPrompt]:
        """Get all prompts of a specific type"""
        return [p for p in self.prompts if p.prompt_type == prompt_type and p.is_active]
    
    def get_default_prompt(self, prompt_type: str) -> Optional[UserPrompt]:
        """Get the default prompt for a specific type"""
        return next((p for p in self.prompts if p.prompt_type == prompt_type and p.is_default and p.is_active), None)
    
    def set_default_prompt(self, prompt_id: str):
        """Set a prompt as default for its type"""
        prompt = self.get_prompt_by_id(prompt_id)
        if prompt:
            # Unset other defaults for this type
            for p in self.prompts:
                if p.prompt_type == prompt.prompt_type:
                    p.is_default = False
            # Set new default
            prompt.is_default = True


class CompanyIntelligenceConfig(BaseModel):
    """Configuration for the intelligence extraction system"""
    
    # Scraping configuration
    max_content_length: int = Field(default=50000, description="Max content to analyze")
    request_timeout: int = Field(default=10, description="HTTP request timeout")
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        description="User agent for web requests"
    )
    
    # AI analysis configuration
    bedrock_embedding_model: str = Field(default="amazon.titan-embed-text-v1")
    bedrock_analysis_model: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0")
    bedrock_region: str = Field(default="us-west-2")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load from environment variables if available
        import os
        if os.getenv('BEDROCK_ANALYSIS_MODEL'):
            self.bedrock_analysis_model = os.getenv('BEDROCK_ANALYSIS_MODEL').strip('"')
        if os.getenv('BEDROCK_REGION'):
            self.bedrock_region = os.getenv('BEDROCK_REGION')
        if os.getenv('BEDROCK_EMBEDDING_MODEL'):
            self.bedrock_embedding_model = os.getenv('BEDROCK_EMBEDDING_MODEL')
    
    # Clustering configuration
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity for clustering")
    min_cluster_size: int = Field(default=3, description="Minimum companies per sector")
    
    # Pinecone configuration
    pinecone_dimension: int = Field(default=1536, description="Embedding dimension")
    pinecone_metric: str = Field(default="cosine", description="Distance metric")
    
    # Rate limiting
    requests_per_second: float = Field(default=2.0, description="Max requests per second")
    batch_size: int = Field(default=10, description="Companies to process per batch")