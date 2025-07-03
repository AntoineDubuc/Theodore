#!/usr/bin/env python3
"""
Theodore v2 Export Domain Models

Comprehensive domain models for data export, analytics, and reporting functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator

from .company import CompanyData


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    PARQUET = "parquet"
    POWERBI = "powerbi"
    TABLEAU = "tableau"


class AggregationFunction(str, Enum):
    """Supported aggregation functions"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"


class SortDirection(str, Enum):
    """Sort direction options"""
    ASC = "asc"
    DESC = "desc"


class AnalysisType(str, Enum):
    """Types of analytics analysis"""
    SUMMARY = "summary"
    TRENDS = "trends"
    COMPARISON = "comparison"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    MARKET_TRENDS = "market_trends"
    GROWTH_PATTERNS = "growth_patterns"
    SIMILARITY_CLUSTERS = "similarity_clusters"


class VisualizationType(str, Enum):
    """Types of visualizations"""
    CHARTS = "charts"
    TABLES = "tables"
    HEATMAPS = "heatmaps"
    NETWORK = "network"
    DASHBOARD = "dashboard"


class DashboardType(str, Enum):
    """Types of interactive dashboards"""
    MARKET_ANALYSIS = "market_analysis"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    TREND_ANALYSIS = "trend_analysis"
    COMPANY_OVERVIEW = "company_overview"


class SortField(BaseModel):
    """Field sorting specification"""
    field: str
    direction: SortDirection = SortDirection.ASC


class ExportFilters(BaseModel):
    """Advanced filtering system for data export"""
    
    # Basic Filters
    industries: List[str] = Field(default_factory=list)
    business_models: List[str] = Field(default_factory=list)
    company_sizes: List[str] = Field(default_factory=list)
    growth_stages: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    
    # Date Range Filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    
    # Numerical Filters
    employee_count_min: Optional[int] = None
    employee_count_max: Optional[int] = None
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Advanced Query Filters
    sql_like_query: Optional[str] = None
    custom_expressions: List[str] = Field(default_factory=list)
    
    # Field Selection
    include_fields: List[str] = Field(default_factory=list)
    exclude_fields: List[str] = Field(default_factory=list)
    custom_columns: Dict[str, str] = Field(default_factory=dict)
    
    # Aggregation Options
    group_by: List[str] = Field(default_factory=list)
    aggregations: Dict[str, AggregationFunction] = Field(default_factory=dict)
    
    # Sorting and Pagination
    sort_by: List[SortField] = Field(default_factory=list)
    limit: Optional[int] = None
    offset: int = Field(default=0, ge=0)


class OutputConfig(BaseModel):
    """Export output configuration"""
    
    format: ExportFormat
    file_path: Path
    
    # Streaming options
    stream_large_datasets: bool = False
    streaming_threshold: int = Field(default=1000, gt=0)
    chunk_size: int = Field(default=1000, gt=0)
    
    # Compression and optimization
    compress: bool = False
    optimize_memory: bool = True
    
    # Validation options
    validate_data: bool = False
    include_audit_trail: bool = False
    
    # Format-specific options
    format_options: Dict[str, Any] = Field(default_factory=dict)


class VisualizationConfig(BaseModel):
    """Configuration for visualizations"""
    
    types: List[VisualizationType] = Field(default_factory=list)
    include_charts: bool = True
    include_tables: bool = False
    include_heatmaps: bool = False
    include_network_graphs: bool = False
    
    # Chart-specific options
    chart_theme: str = "default"
    color_scheme: str = "professional"
    interactive: bool = True
    
    # Dashboard options
    dashboard_type: Optional[DashboardType] = None
    real_time_updates: bool = False


class ExportResult(BaseModel):
    """Result of export operation"""
    
    file_path: Path
    format: ExportFormat
    record_count: int
    file_size_bytes: int
    
    # Processing details
    processing_time_seconds: float
    streaming_used: bool = False
    chunks_processed: Optional[int] = None
    
    # Content details
    columns: List[str] = Field(default_factory=list)
    sheets: Optional[List[str]] = None  # For Excel/multi-sheet formats
    
    # Validation results
    validation_passed: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    
    # Audit information
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    exported_by: Optional[str] = None
    
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes"""
        return self.file_size_bytes / (1024 * 1024)


class Analytics(BaseModel):
    """Analytics data container"""
    
    # Basic statistics
    total_companies: int
    industries_count: int
    average_company_size: Optional[float] = None
    
    # Distribution analytics
    industry_distribution: Dict[str, int] = Field(default_factory=dict)
    size_distribution: Dict[str, int] = Field(default_factory=dict)
    location_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Similarity analytics
    similarity_clusters: List[Dict[str, Any]] = Field(default_factory=list)
    average_similarity: Optional[float] = None
    
    # Market analytics
    market_concentration: Optional[float] = None
    competitive_density: Optional[float] = None
    
    # Trend data
    growth_trends: Dict[str, List[float]] = Field(default_factory=dict)
    temporal_patterns: Dict[str, Any] = Field(default_factory=dict)


class Visualization(BaseModel):
    """Visualization data container"""
    
    type: VisualizationType
    title: str
    data: Dict[str, Any]
    
    # Chart configuration
    chart_type: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    
    # Styling
    theme: str = "default"
    color_scheme: str = "professional"
    interactive: bool = True
    
    # Metadata
    description: Optional[str] = None
    data_source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportTemplate(BaseModel):
    """Report template definition"""
    
    name: str
    title: str
    description: str
    
    # Template structure
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    output_format: ExportFormat
    
    # Template parameters
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    default_values: Dict[str, Any] = Field(default_factory=dict)
    
    # Styling
    theme: str = "professional"
    styling: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    version: str = "1.0"
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedReport(BaseModel):
    """Generated report result"""
    
    template_name: str
    title: str
    content: Union[str, bytes, Dict[str, Any]]
    format: ExportFormat
    
    # Generation details
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_source_count: int
    parameters_used: Dict[str, Any] = Field(default_factory=dict)
    
    # Content metadata
    sections_count: int = 0
    visualizations_count: int = 0
    
    # File information
    file_path: Optional[Path] = None
    file_size_bytes: Optional[int] = None


class ScheduleConfig(BaseModel):
    """Configuration for scheduled report generation"""
    
    job_id: str
    name: str
    template_name: str
    
    # Schedule settings
    frequency: str  # cron expression or predefined (daily, weekly, monthly)
    timezone: str = "UTC"
    enabled: bool = True
    
    # Report configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    data_filters: ExportFilters
    output_format: ExportFormat
    
    # Distribution settings
    recipients: List[str] = Field(default_factory=list)
    distribution_method: str = "email"  # email, slack, webhook, etc.
    
    # Notification settings
    notify_on_success: bool = True
    notify_on_failure: bool = True
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class ScheduledJob(BaseModel):
    """Scheduled job status"""
    
    job_id: str
    name: str
    schedule: str
    status: str  # active, paused, completed, failed
    
    # Execution details
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    
    # Statistics
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0


class ExportAuditEntry(BaseModel):
    """Audit trail entry for export operations"""
    
    export_id: str
    operation_type: str  # export, analytics, report_generation
    
    # Request details
    user_id: Optional[str] = None
    filters_applied: ExportFilters
    output_config: OutputConfig
    
    # Result details
    result: ExportResult
    success: bool
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: datetime
    completed_at: datetime
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ExportDataRequest(BaseModel):
    """Request for data export operation"""
    
    filters: ExportFilters
    output_config: OutputConfig
    
    # Optional analytics
    include_analytics: bool = False
    analytics_config: Optional[Dict[str, Any]] = None
    
    # Optional visualizations
    include_visualizations: bool = False
    visualization_config: Optional[VisualizationConfig] = None
    
    # Optional template
    template_name: Optional[str] = None
    template_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Request metadata
    requested_by: Optional[str] = None
    request_id: Optional[str] = None


class ExportDataResponse(BaseModel):
    """Response from data export operation"""
    
    export_result: ExportResult
    record_count: int
    
    # Optional analytics
    analytics_included: bool
    analytics: Optional[Analytics] = None
    
    # Optional visualizations
    visualizations_included: bool
    visualizations: Optional[List[Visualization]] = None
    
    # Optional audit
    audit_entry: Optional[ExportAuditEntry] = None
    
    # Processing details
    processing_time_seconds: float
    total_files_generated: int = 1


class CompetitiveLandscapeReport(BaseModel):
    """Competitive landscape analysis report"""
    
    market_segments: Dict[str, List[CompanyData]]
    competitive_positioning: Dict[str, Any]
    market_concentration: Dict[str, float]
    opportunities: List[Dict[str, Any]]
    visualizations: List[Visualization]
    
    # Analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    companies_analyzed: int
    market_coverage: float  # Percentage of market covered


class AnalyticsReport(BaseModel):
    """Generic analytics report"""
    
    report_type: AnalysisType
    title: str
    summary: str
    
    # Data content
    analytics: Analytics
    visualizations: List[Visualization]
    key_insights: List[str]
    
    # Report metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_period: Optional[str] = None
    confidence_score: Optional[float] = None


class InteractiveDashboard(BaseModel):
    """Interactive dashboard definition"""
    
    dashboard_type: DashboardType
    title: str
    
    # Dashboard components
    kpis: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[Visualization] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    data_tables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Configuration
    layout: Dict[str, Any] = Field(default_factory=dict)
    styling: Dict[str, Any] = Field(default_factory=dict)
    real_time_updates: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    data_source_count: int = 0
    
    @property
    def has_kpi_section(self) -> bool:
        return len(self.kpis) > 0
    
    @property
    def has_filtering_controls(self) -> bool:
        return len(self.filters) > 0


class QueryBuilder(BaseModel):
    """SQL-like query builder for complex filtering"""
    
    filters: List[str] = Field(default_factory=list)
    joins: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)
    sort_conditions: List[str] = Field(default_factory=list)
    
    def where(self, condition: str) -> 'QueryBuilder':
        """Add WHERE clause condition"""
        self.filters.append(condition)
        return self
    
    def join(self, table: str, condition: str) -> 'QueryBuilder':
        """Add JOIN operation"""
        self.joins.append(f"JOIN {table} ON {condition}")
        return self
    
    def group_by(self, *fields: str) -> 'QueryBuilder':
        """Add GROUP BY clause"""
        self.aggregations.extend(fields)
        return self
    
    def order_by(self, field: str, direction: SortDirection = SortDirection.ASC) -> 'QueryBuilder':
        """Add ORDER BY clause"""
        self.sort_conditions.append(f"{field} {direction.value.upper()}")
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build final query configuration"""
        return {
            'filters': self.filters,
            'joins': self.joins,
            'aggregations': self.aggregations,
            'sort_conditions': self.sort_conditions
        }