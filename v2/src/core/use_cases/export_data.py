#!/usr/bin/env python3
"""
Theodore v2 Export Data Use Case

Comprehensive data export use case with advanced analytics and visualization capabilities.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..domain.models.export import (
    ExportDataRequest, ExportDataResponse, ExportResult, Analytics,
    Visualization, ExportAuditEntry, AnalyticsReport, GeneratedReport
)
from ..domain.models.company import CompanyData
from ..ports.repositories.company_repository import CompanyRepository
from ..ports.io.export_engine_port import ExportEnginePort
from ..ports.io.analytics_engine_port import AnalyticsEnginePort
from ..ports.io.visualization_engine_port import VisualizationEnginePort
from ..ports.io.report_engine_port import ReportEnginePort
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ValidationError(Exception):
    """Validation error for export requests"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {', '.join(errors)}")


class ExportError(Exception):
    """Generic export operation error"""
    pass


class ExportDataUseCase:
    """
    Comprehensive data export use case with advanced analytics and visualization
    
    Supports:
    - Advanced filtering with SQL-like queries
    - Multiple export formats (CSV, JSON, Excel, PDF, PowerBI, Tableau)
    - Real-time analytics and visualization generation
    - Streaming exports for large datasets
    - Report template processing
    - Audit trail generation
    """
    
    def __init__(
        self,
        company_repository: CompanyRepository,
        export_engine: ExportEnginePort,
        analytics_engine: Optional[AnalyticsEnginePort] = None,
        visualization_engine: Optional[VisualizationEnginePort] = None,
        report_engine: Optional[ReportEnginePort] = None
    ):
        self.company_repository = company_repository
        self.export_engine = export_engine
        self.analytics_engine = analytics_engine
        self.visualization_engine = visualization_engine
        self.report_engine = report_engine
        
    async def execute(self, request: ExportDataRequest) -> ExportDataResponse:
        """
        Execute comprehensive data export with analytics and visualizations
        
        Args:
            request: Export data request with filters and configuration
            
        Returns:
            Export response with results and metadata
            
        Raises:
            ValidationError: If request validation fails
            ExportError: If export operation fails
        """
        
        start_time = datetime.now(timezone.utc)
        export_id = str(uuid.uuid4())
        
        try:
            # Record export attempt
            metrics.increment_counter(
                "export_attempts_total",
                tags={
                    "format": request.output_config.format.value,
                    "include_analytics": str(request.include_analytics),
                    "include_visualizations": str(request.include_visualizations)
                }
            )
            
            logger.info(
                f"Starting export operation",
                extra={
                    "export_id": export_id,
                    "format": request.output_config.format.value,
                    "include_analytics": request.include_analytics,
                    "requested_by": request.requested_by
                }
            )
            
            # 1. Validate request
            validation_result = await self._validate_request(request)
            if not validation_result.is_valid:
                raise ValidationError(validation_result.errors)
            
            # 2. Fetch and filter companies
            logger.info(f"Fetching companies with filters: {request.filters}")
            companies = await self._fetch_companies(request.filters)
            
            if not companies:
                logger.warning("No companies found matching filters")
                # Still create export with empty data
            
            logger.info(f"Found {len(companies)} companies matching filters")
            
            # 3. Generate analytics if requested
            analytics = None
            if request.include_analytics and self.analytics_engine:
                logger.info("Generating analytics data")
                analytics = await self._generate_analytics(companies, request.analytics_config)
                
                # Enrich companies with analytics data
                companies = await self._enrich_with_analytics(companies, analytics)
            
            # 4. Generate visualizations if requested
            visualizations = None
            if request.include_visualizations and self.visualization_engine:
                logger.info("Generating visualizations")
                visualizations = await self._generate_visualizations(
                    companies, request.visualization_config
                )
            
            # 5. Process template if specified
            if request.template_name and self.report_engine:
                logger.info(f"Processing report template: {request.template_name}")
                return await self._generate_template_report(
                    request, companies, analytics, visualizations, start_time
                )
            
            # 6. Standard export processing
            export_result = await self.export_engine.export(
                companies,
                request.output_config,
                visualizations
            )
            
            # 7. Calculate processing time
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - start_time).total_seconds()
            
            # 8. Generate audit trail if requested
            audit_entry = None
            if request.output_config.include_audit_trail:
                audit_entry = await self._create_audit_entry(
                    export_id, request, export_result, True, None, start_time, end_time
                )
            
            # 9. Record success metrics
            metrics.increment_counter(
                "export_completions_total",
                tags={
                    "format": request.output_config.format.value,
                    "status": "success"
                }
            )
            
            metrics.record_histogram(
                "export_processing_duration_seconds",
                processing_time,
                tags={"format": request.output_config.format.value}
            )
            
            metrics.record_histogram(
                "export_record_count",
                len(companies),
                tags={"format": request.output_config.format.value}
            )
            
            logger.info(
                f"Export completed successfully",
                extra={
                    "export_id": export_id,
                    "record_count": len(companies),
                    "file_path": str(export_result.file_path),
                    "processing_time_seconds": processing_time,
                    "file_size_mb": export_result.file_size_mb
                }
            )
            
            return ExportDataResponse(
                export_result=export_result,
                record_count=len(companies),
                analytics_included=request.include_analytics,
                analytics=analytics,
                visualizations_included=request.include_visualizations,
                visualizations=visualizations,
                audit_entry=audit_entry,
                processing_time_seconds=processing_time,
                total_files_generated=1
            )
            
        except Exception as e:
            # Record failure metrics
            metrics.increment_counter(
                "export_failures_total",
                tags={
                    "format": request.output_config.format.value,
                    "error_type": type(e).__name__
                }
            )
            
            # Generate audit trail for failure
            end_time = datetime.now(timezone.utc)
            if request.output_config.include_audit_trail:
                await self._create_audit_entry(
                    export_id, request, None, False, str(e), start_time, end_time
                )
            
            logger.error(
                f"Export failed",
                extra={
                    "export_id": export_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            raise ExportError(f"Export operation failed: {e}") from e
    
    async def _validate_request(self, request: ExportDataRequest) -> 'ValidationResult':
        """Validate export request"""
        errors = []
        
        # Validate output path
        output_path = request.output_config.file_path
        if not output_path:
            errors.append("Output file path is required")
        else:
            # Check if parent directory exists
            parent_dir = output_path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create output directory: {e}")
            
            # Check file extension matches format
            expected_extensions = {
                'csv': ['.csv'],
                'json': ['.json'],
                'excel': ['.xlsx', '.xls'],
                'pdf': ['.pdf'],
                'parquet': ['.parquet'],
                'powerbi': ['.pbix', '.xlsx'],
                'tableau': ['.twbx', '.hyper', '.csv']
            }
            
            format_name = request.output_config.format.value
            if format_name in expected_extensions:
                valid_extensions = expected_extensions[format_name]
                if not any(str(output_path).lower().endswith(ext) for ext in valid_extensions):
                    errors.append(
                        f"File extension doesn't match format {format_name}. "
                        f"Expected: {', '.join(valid_extensions)}"
                    )
        
        # Validate filters
        filters = request.filters
        if filters.limit and filters.limit <= 0:
            errors.append("Limit must be positive")
        
        if filters.offset < 0:
            errors.append("Offset must be non-negative")
        
        if filters.similarity_threshold < 0 or filters.similarity_threshold > 1:
            errors.append("Similarity threshold must be between 0 and 1")
        
        # Validate date ranges
        if filters.created_after and filters.created_before:
            if filters.created_after >= filters.created_before:
                errors.append("created_after must be before created_before")
        
        if filters.updated_after and filters.updated_before:
            if filters.updated_after >= filters.updated_before:
                errors.append("updated_after must be before updated_before")
        
        # Validate numerical ranges
        if (filters.employee_count_min is not None and 
            filters.employee_count_max is not None):
            if filters.employee_count_min > filters.employee_count_max:
                errors.append("employee_count_min must be <= employee_count_max")
        
        if (filters.revenue_min is not None and 
            filters.revenue_max is not None):
            if filters.revenue_min > filters.revenue_max:
                errors.append("revenue_min must be <= revenue_max")
        
        # Validate analytics requirements
        if request.include_analytics and not self.analytics_engine:
            errors.append("Analytics requested but analytics engine not available")
        
        # Validate visualization requirements  
        if request.include_visualizations and not self.visualization_engine:
            errors.append("Visualizations requested but visualization engine not available")
        
        # Validate template requirements
        if request.template_name and not self.report_engine:
            errors.append("Template specified but report engine not available")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    async def _fetch_companies(self, filters) -> List[CompanyData]:
        """Fetch companies based on filters"""
        try:
            # Use repository to find companies with filters
            companies = await self.company_repository.find_with_filters(
                industries=filters.industries,
                business_models=filters.business_models,
                company_sizes=filters.company_sizes,
                locations=filters.locations,
                created_after=filters.created_after,
                created_before=filters.created_before,
                updated_after=filters.updated_after,
                updated_before=filters.updated_before,
                employee_count_min=filters.employee_count_min,
                employee_count_max=filters.employee_count_max,
                revenue_min=filters.revenue_min,
                revenue_max=filters.revenue_max,
                similarity_threshold=filters.similarity_threshold,
                sql_like_query=filters.sql_like_query,
                include_fields=filters.include_fields,
                exclude_fields=filters.exclude_fields,
                sort_by=filters.sort_by,
                limit=filters.limit,
                offset=filters.offset
            )
            
            return companies
            
        except Exception as e:
            logger.error(f"Failed to fetch companies: {e}", exc_info=True)
            raise ExportError(f"Data retrieval failed: {e}") from e
    
    async def _generate_analytics(
        self, 
        companies: List[CompanyData], 
        config: Optional[Dict[str, Any]]
    ) -> Analytics:
        """Generate analytics for the companies"""
        if not self.analytics_engine:
            raise ExportError("Analytics engine not available")
        
        try:
            analytics = await self.analytics_engine.generate_analytics(companies, config)
            
            logger.info(
                f"Generated analytics",
                extra={
                    "total_companies": analytics.total_companies,
                    "industries_count": analytics.industries_count,
                    "similarity_clusters": len(analytics.similarity_clusters)
                }
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}", exc_info=True)
            raise ExportError(f"Analytics generation failed: {e}") from e
    
    async def _generate_visualizations(
        self, 
        companies: List[CompanyData],
        config: Optional[Dict[str, Any]]
    ) -> List[Visualization]:
        """Generate visualizations for the companies"""
        if not self.visualization_engine:
            raise ExportError("Visualization engine not available")
        
        try:
            visualizations = await self.visualization_engine.create_visualizations(
                companies, config
            )
            
            logger.info(
                f"Generated {len(visualizations)} visualizations",
                extra={"visualization_types": [v.type.value for v in visualizations]}
            )
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}", exc_info=True)
            raise ExportError(f"Visualization generation failed: {e}") from e
    
    async def _enrich_with_analytics(
        self, 
        companies: List[CompanyData], 
        analytics: Analytics
    ) -> List[CompanyData]:
        """Enrich company data with analytics insights"""
        # For now, return companies as-is
        # In future, could add analytics-derived fields
        return companies
    
    async def _generate_template_report(
        self,
        request: ExportDataRequest,
        companies: List[CompanyData],
        analytics: Optional[Analytics],
        visualizations: Optional[List[Visualization]],
        start_time: datetime
    ) -> ExportDataResponse:
        """Generate report using template"""
        if not self.report_engine:
            raise ExportError("Report engine not available")
        
        try:
            report = await self.report_engine.generate_report(
                request.template_name,
                companies,
                request.template_parameters,
                analytics,
                visualizations
            )
            
            # Convert report to export result format
            export_result = ExportResult(
                file_path=report.file_path or request.output_config.file_path,
                format=report.format,
                record_count=report.data_source_count,
                file_size_bytes=report.file_size_bytes or 0,
                processing_time_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
                streaming_used=False,
                columns=[],  # Reports have different structure
                export_timestamp=report.generated_at,
                validation_passed=True
            )
            
            return ExportDataResponse(
                export_result=export_result,
                record_count=len(companies),
                analytics_included=analytics is not None,
                analytics=analytics,
                visualizations_included=visualizations is not None,
                visualizations=visualizations,
                processing_time_seconds=export_result.processing_time_seconds,
                total_files_generated=1
            )
            
        except Exception as e:
            logger.error(f"Template report generation failed: {e}", exc_info=True)
            raise ExportError(f"Template report generation failed: {e}") from e
    
    async def _create_audit_entry(
        self,
        export_id: str,
        request: ExportDataRequest,
        result: Optional[ExportResult],
        success: bool,
        error_message: Optional[str],
        started_at: datetime,
        completed_at: datetime
    ) -> ExportAuditEntry:
        """Create audit trail entry"""
        return ExportAuditEntry(
            export_id=export_id,
            operation_type="export",
            user_id=request.requested_by,
            filters_applied=request.filters,
            output_config=request.output_config,
            result=result,
            success=success,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at
        )


class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid = is_valid
        self.errors = errors