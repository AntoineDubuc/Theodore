"""
Research job tracking and results domain entity.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid
from enum import Enum


class ResearchStatus(str, Enum):
    """Research job status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchPhase(str, Enum):
    """Research pipeline phases"""
    DOMAIN_DISCOVERY = "domain_discovery"
    LINK_DISCOVERY = "link_discovery" 
    PAGE_SELECTION = "page_selection"
    CONTENT_EXTRACTION = "content_extraction"
    AI_ANALYSIS = "ai_analysis"
    CLASSIFICATION = "classification"
    EMBEDDING_GENERATION = "embedding_generation"
    STORAGE = "storage"


class ResearchSource(str, Enum):
    """How research was initiated"""
    WEB_UI = "web_ui"
    CLI = "cli"
    API = "api"
    BATCH = "batch"
    SCHEDULED = "scheduled"


class PhaseResult(BaseModel):
    """Result from a research phase"""
    phase: ResearchPhase
    status: ResearchStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Phase-specific data
    pages_found: Optional[int] = None
    pages_selected: Optional[int] = None
    pages_scraped: Optional[int] = None
    content_length: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    
    error_message: Optional[str] = None
    
    def complete(self, error: Optional[str] = None):
        """Mark phase as complete"""
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        if error:
            self.status = ResearchStatus.FAILED
            self.error_message = error
        else:
            self.status = ResearchStatus.COMPLETED


class Research(BaseModel):
    """
    Research job entity tracking the complete research process for a company.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = Field(None, description="ID of company being researched")
    company_name: str = Field(..., description="Company name for reference")
    website: Optional[str] = Field(None, description="Website being researched")
    
    # Job tracking
    status: ResearchStatus = Field(default=ResearchStatus.QUEUED)
    source: ResearchSource = Field(..., description="How research was initiated")
    priority: int = Field(default=5, ge=1, le=10, description="1=highest, 10=lowest")
    
    # Progress tracking
    phases: List[PhaseResult] = Field(default_factory=list)
    current_phase: Optional[ResearchPhase] = None
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Research configuration")
    skip_domain_discovery: bool = Field(False)
    max_pages_to_scrape: int = Field(default=50, ge=1, le=100)
    
    # Results summary
    pages_discovered: int = Field(default=0)
    pages_scraped: int = Field(default=0)
    total_content_length: int = Field(default=0)
    
    # AI processing
    total_tokens_used: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    ai_model_versions: Dict[str, str] = Field(default_factory=dict)
    
    # Timing
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    
    # Error tracking
    error_message: Optional[str] = None
    failed_phase: Optional[ResearchPhase] = None
    retry_count: int = Field(default=0)
    
    # User context
    user_id: Optional[str] = Field(None, description="User who initiated research")
    batch_id: Optional[str] = Field(None, description="Batch job ID if part of batch")
    
    def start(self):
        """Mark research as started"""
        self.status = ResearchStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def start_phase(self, phase: ResearchPhase) -> PhaseResult:
        """Start a new research phase"""
        phase_result = PhaseResult(
            phase=phase,
            status=ResearchStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        self.phases.append(phase_result)
        self.current_phase = phase
        self._update_progress()
        return phase_result
    
    def complete_phase(self, phase: ResearchPhase, **kwargs):
        """Complete a research phase with results"""
        phase_result = next((p for p in self.phases if p.phase == phase), None)
        if phase_result:
            phase_result.complete()
            # Update with phase-specific data
            for key, value in kwargs.items():
                if hasattr(phase_result, key):
                    setattr(phase_result, key, value)
        self._update_progress()
    
    def fail(self, error: str, phase: Optional[ResearchPhase] = None):
        """Mark research as failed"""
        self.status = ResearchStatus.FAILED
        self.error_message = error
        self.failed_phase = phase or self.current_phase
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def complete(self):
        """Mark research as completed successfully"""
        self.status = ResearchStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.progress_percentage = 100.0
        
        # Sum up totals from phases
        for phase in self.phases:
            if phase.tokens_used:
                self.total_tokens_used += phase.tokens_used
            if phase.cost_usd:
                self.total_cost_usd += phase.cost_usd
    
    def cancel(self):
        """Mark research as cancelled"""
        self.status = ResearchStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def _update_progress(self):
        """Update progress percentage based on completed phases"""
        total_phases = 8  # Total possible phases
        completed = len([p for p in self.phases if p.status == ResearchStatus.COMPLETED])
        self.progress_percentage = (completed / total_phases) * 100
    
    def get_phase_duration(self, phase: ResearchPhase) -> Optional[float]:
        """Get duration of a specific phase"""
        phase_result = next((p for p in self.phases if p.phase == phase), None)
        return phase_result.duration_seconds if phase_result else None
    
    def is_complete(self) -> bool:
        """Check if research is in a terminal state"""
        return self.status in [ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED]