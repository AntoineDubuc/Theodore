"""
Batch Job domain entity for Theodore v2.

Represents a complete batch processing job with state management,
progress tracking, and comprehensive job lifecycle support.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class BatchJobType(str, Enum):
    """Types of batch operations supported"""
    RESEARCH = "research"
    DISCOVER = "discover"
    EXPORT = "export"
    ANALYSIS = "analysis"


class BatchJobStatus(str, Enum):
    """Batch job lifecycle status"""
    PENDING = "pending"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESUMING = "resuming"


class BatchJobPriority(str, Enum):
    """Job priority levels for scheduling"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class InputSourceType(str, Enum):
    """Types of batch input sources"""
    CSV_FILE = "csv_file"
    GOOGLE_SHEETS = "google_sheets"
    EXCEL_FILE = "excel_file"
    JSON_FILE = "json_file"
    MANUAL_LIST = "manual_list"


class OutputDestinationType(str, Enum):
    """Types of batch output destinations"""
    CSV_FILE = "csv_file"
    JSON_FILE = "json_file"
    EXCEL_FILE = "excel_file"
    GOOGLE_SHEETS = "google_sheets"
    DATABASE = "database"


@dataclass
class BatchInputSource:
    """Configuration for batch input source"""
    type: InputSourceType
    path: Optional[str] = None
    sheet_id: Optional[str] = None
    range_spec: Optional[str] = None
    schema_config: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class BatchOutputDestination:
    """Configuration for batch output destination"""
    type: OutputDestinationType
    path: Optional[str] = None
    sheet_id: Optional[str] = None
    range_spec: Optional[str] = None
    format_config: Dict[str, Any] = field(default_factory=dict)
    include_metadata: bool = True


@dataclass
class BatchProgress:
    """Comprehensive batch progress tracking"""
    total_companies: int
    completed_companies: int = 0
    failed_companies: int = 0
    skipped_companies: int = 0
    processing_companies: int = 0
    
    # Current operation details
    current_company: Optional[str] = None
    current_stage: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    
    # Performance metrics
    processing_rate: float = 0.0  # companies per minute
    average_processing_time: float = 0.0  # seconds per company
    cost_accumulated: float = 0.0
    
    # Error tracking
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_company: Dict[str, str] = field(default_factory=dict)
    
    # Checkpointing
    last_checkpoint: Optional[datetime] = None
    checkpoint_interval: int = 10
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_companies == 0:
            return 0.0
        return (self.completed_companies / self.total_companies) * 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of processed companies"""
        processed = self.completed_companies + self.failed_companies
        if processed == 0:
            return 0.0
        return (self.completed_companies / processed) * 100.0
    
    @property
    def is_completed(self) -> bool:
        """Check if batch is completed"""
        return (self.completed_companies + self.failed_companies + self.skipped_companies) >= self.total_companies


@dataclass
class BatchConfiguration:
    """Comprehensive batch processing configuration"""
    # Concurrency settings
    max_concurrent: int = 5
    rate_limit_per_minute: int = 60
    timeout_per_company: int = 120
    
    # Retry and recovery
    max_retries: int = 2
    retry_delay: int = 30
    enable_failure_recovery: bool = True
    
    # Progress and checkpointing
    checkpoint_interval: int = 10
    enable_progress_tracking: bool = True
    progress_update_interval: int = 5
    
    # Resource management
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80
    enable_adaptive_scaling: bool = True
    
    # Output and formatting
    include_metadata: bool = True
    include_error_details: bool = True
    preserve_input_columns: bool = True
    
    # Cost and optimization
    enable_cost_tracking: bool = True
    cost_limit: Optional[float] = None
    enable_cost_estimation: bool = True
    
    # Notification settings
    notification_email: Optional[str] = None
    webhook_url: Optional[str] = None
    
    # Custom configuration
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResultSummary:
    """Summary of batch processing results"""
    total_processed: int
    successful_results: int
    failed_results: int
    skipped_results: int
    
    # Performance metrics
    total_processing_time: float
    average_processing_time: float
    peak_processing_rate: float
    
    # Cost information
    total_cost: float
    cost_per_company: float
    
    # Quality metrics
    data_quality_score: float
    completeness_score: float
    
    # Error analysis
    error_categories: Dict[str, int]
    most_common_errors: List[str]
    
    # Output information
    output_file_size: Optional[int] = None
    output_record_count: Optional[int] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_processed == 0:
            return 0.0
        return (self.successful_results / self.total_processed) * 100.0


class BatchJob(BaseModel):
    """
    Core batch job entity with comprehensive lifecycle management.
    
    Represents a complete batch processing operation with state management,
    progress tracking, error handling, and result aggregation.
    """
    
    # Identity and metadata
    job_id: str = Field(default_factory=lambda: f"batch_{uuid.uuid4().hex[:8]}")
    job_name: Optional[str] = Field(None, description="Human-readable job name")
    job_type: BatchJobType = Field(..., description="Type of batch operation")
    priority: BatchJobPriority = Field(BatchJobPriority.MEDIUM, description="Job priority level")
    
    # Status and lifecycle
    status: BatchJobStatus = Field(BatchJobStatus.PENDING, description="Current job status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    # Configuration
    input_source: BatchInputSource = Field(..., description="Input data source configuration")
    output_destination: BatchOutputDestination = Field(..., description="Output destination configuration")
    configuration: BatchConfiguration = Field(default_factory=BatchConfiguration)
    
    # Progress and state
    progress: BatchProgress = Field(..., description="Current progress tracking")
    error_summary: Optional[str] = Field(None, description="Summary of errors encountered")
    result_summary: Optional[BatchResultSummary] = Field(None, description="Final results summary")
    
    # Job persistence
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict, description="Checkpoint state for resuming")
    processed_companies: List[str] = Field(default_factory=list, description="List of processed company names")
    failed_companies: List[str] = Field(default_factory=list, description="List of failed company names")
    
    # Metadata
    created_by: Optional[str] = Field(None, description="User who created the job")
    tags: List[str] = Field(default_factory=list, description="Job tags for organization")
    notes: Optional[str] = Field(None, description="Additional job notes")
    
    def start_job(self) -> None:
        """Mark job as started and update timestamps"""
        self.status = BatchJobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = self.started_at
    
    def pause_job(self) -> None:
        """Pause the job execution"""
        if self.status == BatchJobStatus.RUNNING:
            self.status = BatchJobStatus.PAUSED
            self.updated_at = datetime.now(timezone.utc)
    
    def resume_job(self) -> None:
        """Resume paused job execution"""
        if self.status == BatchJobStatus.PAUSED:
            self.status = BatchJobStatus.RESUMING
            self.updated_at = datetime.now(timezone.utc)
    
    def complete_job(self, result_summary: BatchResultSummary) -> None:
        """Mark job as completed with results"""
        self.status = BatchJobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at
        self.result_summary = result_summary
    
    def fail_job(self, error_summary: str) -> None:
        """Mark job as failed with error details"""
        self.status = BatchJobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at
        self.error_summary = error_summary
    
    def cancel_job(self) -> None:
        """Cancel job execution"""
        if self.status in [BatchJobStatus.PENDING, BatchJobStatus.RUNNING, BatchJobStatus.PAUSED]:
            self.status = BatchJobStatus.CANCELLED
            self.completed_at = datetime.now(timezone.utc)
            self.updated_at = self.completed_at
    
    def update_progress(self, **kwargs) -> None:
        """Update job progress with new metrics"""
        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_processed_company(self, company_name: str, success: bool = True) -> None:
        """Record a processed company"""
        if company_name not in self.processed_companies:
            self.processed_companies.append(company_name)
        
        if success:
            self.progress.completed_companies += 1
        else:
            self.progress.failed_companies += 1
            if company_name not in self.failed_companies:
                self.failed_companies.append(company_name)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_error(self, company_name: str, error_type: str, error_message: str) -> None:
        """Record an error for a specific company"""
        self.progress.errors_by_company[company_name] = error_message
        
        if error_type in self.progress.errors_by_type:
            self.progress.errors_by_type[error_type] += 1
        else:
            self.progress.errors_by_type[error_type] = 1
    
    def should_checkpoint(self) -> bool:
        """Check if job should create a checkpoint"""
        if not self.progress.last_checkpoint:
            return self.progress.completed_companies > 0
        
        companies_since_checkpoint = (
            self.progress.completed_companies + self.progress.failed_companies
        ) % self.progress.checkpoint_interval
        
        return companies_since_checkpoint == 0
    
    def create_checkpoint(self) -> Dict[str, Any]:
        """Create checkpoint data for job state"""
        checkpoint = {
            "job_id": self.job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "progress": {
                "completed_companies": self.progress.completed_companies,
                "failed_companies": self.progress.failed_companies,
                "skipped_companies": self.progress.skipped_companies,
                "cost_accumulated": self.progress.cost_accumulated,
                "errors_by_type": self.progress.errors_by_type.copy(),
                "errors_by_company": self.progress.errors_by_company.copy()
            },
            "processed_companies": self.processed_companies.copy(),
            "failed_companies": self.failed_companies.copy(),
            "custom_state": self.checkpoint_data.copy()
        }
        
        self.progress.last_checkpoint = datetime.now(timezone.utc)
        return checkpoint
    
    def restore_from_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """Restore job state from checkpoint data"""
        if "progress" in checkpoint_data:
            progress_data = checkpoint_data["progress"]
            for key, value in progress_data.items():
                if hasattr(self.progress, key):
                    setattr(self.progress, key, value)
        
        if "processed_companies" in checkpoint_data:
            self.processed_companies = checkpoint_data["processed_companies"]
        
        if "failed_companies" in checkpoint_data:
            self.failed_companies = checkpoint_data["failed_companies"]
        
        if "custom_state" in checkpoint_data:
            self.checkpoint_data = checkpoint_data["custom_state"]
    
    @property
    def execution_time(self) -> Optional[float]:
        """Calculate total execution time in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_active(self) -> bool:
        """Check if job is currently active"""
        return self.status in [BatchJobStatus.RUNNING, BatchJobStatus.RESUMING]
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state"""
        return self.status in [BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED]
    
    @property
    def can_resume(self) -> bool:
        """Check if job can be resumed"""
        return self.status in [BatchJobStatus.PAUSED, BatchJobStatus.FAILED] and len(self.processed_companies) > 0
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert job to summary dictionary for display"""
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "progress": {
                "completion_percentage": self.progress.completion_percentage,
                "completed": self.progress.completed_companies,
                "failed": self.progress.failed_companies,
                "total": self.progress.total_companies,
                "success_rate": self.progress.success_rate
            },
            "execution_time": self.execution_time,
            "cost_accumulated": self.progress.cost_accumulated,
            "input_source": f"{self.input_source.type.value}: {self.input_source.path or self.input_source.sheet_id}",
            "output_destination": f"{self.output_destination.type.value}: {self.output_destination.path or self.output_destination.sheet_id}"
        }
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }