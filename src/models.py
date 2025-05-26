"""
Pydantic models for Theodore company intelligence system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
import uuid


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
    target_market: Optional[str] = Field(None, description="Who they serve")
    
    # Extended metadata from Crawl4AI
    company_description: Optional[str] = Field(None, description="About/description from website")
    founding_year: Optional[int] = Field(None, description="Year company was founded")
    location: Optional[str] = Field(None, description="Company headquarters location")
    employee_count_range: Optional[str] = Field(None, description="Estimated employee count")
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
    
    # AI analysis
    raw_content: Optional[str] = Field(None, description="Scraped website content")
    ai_summary: Optional[str] = Field(None, description="Bedrock-generated summary")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
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
    bedrock_analysis_model: str = Field(default="amazon.nova-premier-v1:0")
    bedrock_region: str = Field(default="us-east-1")
    
    # Clustering configuration
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity for clustering")
    min_cluster_size: int = Field(default=3, description="Minimum companies per sector")
    
    # Pinecone configuration
    pinecone_dimension: int = Field(default=1536, description="Embedding dimension")
    pinecone_metric: str = Field(default="cosine", description="Distance metric")
    
    # Rate limiting
    requests_per_second: float = Field(default=2.0, description="Max requests per second")
    batch_size: int = Field(default=10, description="Companies to process per batch")