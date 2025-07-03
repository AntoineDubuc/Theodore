#!/usr/bin/env python3
"""
Theodore v2 Batch Processing API Router

FastAPI router for batch research and discovery operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse

from ...infrastructure.container.application import ApplicationContainer
from ...core.use_cases.batch_processing import BatchProcessingUseCase
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.requests import BatchResearchRequest, BatchDiscoveryRequest
from ..models.responses import BatchJobResponse
from ..models.common import BatchJobStatus, OutputFormat

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()


def get_container() -> ApplicationContainer:
    """Get application container dependency"""
    from fastapi import Request
    import inspect
    frame = inspect.currentframe()
    try:
        request = None
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            if 'request' in frame_locals:
                request = frame_locals['request']
                break
        
        if request and hasattr(request.app.state, 'container'):
            return request.app.state.container
        else:
            container = ApplicationContainer()
            return container
    finally:
        del frame


@router.post("/research", response_model=BatchJobResponse, summary="Start Batch Research")
async def start_batch_research(
    request: BatchResearchRequest,
    container: ApplicationContainer = Depends(get_container)
) -> BatchJobResponse:
    """
    Start batch research on multiple companies
    
    This endpoint initiates batch research processing that:
    - Processes multiple companies concurrently
    - Provides job management and progress tracking
    - Supports various input formats (JSON, CSV, Excel)
    - Offers flexible output options and locations
    - Handles retries and error recovery
    
    Batch jobs can process from 10 to 10,000 companies depending on
    your plan and resource limits.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Start batch research job
        job_result = await batch_use_case.start_batch_research(
            input_data=request.input_data,
            output_format=request.output_format,
            concurrency=request.concurrency,
            priority=request.priority.value if request.priority else "normal",
            config_overrides=request.config_overrides or {},
            retry_failed=request.retry_failed,
            max_retries=request.max_retries,
            output_location=request.output_location,
            webhook_url=request.webhook_url,
            resume_job_id=request.resume_job_id
        )
        
        # Record metrics
        metrics.increment_counter(
            "batch_research_jobs_started",
            tags={
                "output_format": request.output_format.value,
                "concurrency": str(request.concurrency),
                "priority": request.priority.value if request.priority else "normal"
            }
        )
        
        logger.info(
            f"Batch research job started",
            extra={
                "job_id": job_result.job_id,
                "total_companies": job_result.total_companies,
                "output_format": request.output_format.value,
                "concurrency": request.concurrency
            }
        )
        
        return BatchJobResponse(
            job_id=job_result.job_id,
            status=BatchJobStatus.PENDING,
            job_type="research",
            total_companies=job_result.total_companies,
            completed=0,
            failed=0,
            pending=job_result.total_companies,
            progress_percentage=0.0,
            created_at=job_result.created_at,
            updated_at=job_result.created_at,
            output_format=request.output_format.value,
            output_location=request.output_location
        )
        
    except Exception as e:
        logger.error(f"Failed to start batch research: {e}", exc_info=True)
        metrics.increment_counter("batch_research_jobs_failed_start")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch research: {str(e)}"
        )


@router.post("/discover", response_model=BatchJobResponse, summary="Start Batch Discovery")
async def start_batch_discovery(
    request: BatchDiscoveryRequest,
    container: ApplicationContainer = Depends(get_container)
) -> BatchJobResponse:
    """
    Start batch discovery for multiple companies
    
    This endpoint initiates batch discovery processing that:
    - Finds similar companies for each input company
    - Applies consistent discovery configuration
    - Handles deduplication across results
    - Provides comprehensive progress tracking
    - Supports various output formats
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Start batch discovery job
        job_result = await batch_use_case.start_batch_discovery(
            input_data=request.input_data,
            discovery_config=request.discovery_config.dict(),
            output_format=request.output_format,
            concurrency=request.concurrency,
            priority=request.priority.value if request.priority else "normal",
            deduplicate_results=request.deduplicate_results,
            output_location=request.output_location,
            webhook_url=request.webhook_url
        )
        
        # Record metrics
        metrics.increment_counter(
            "batch_discovery_jobs_started",
            tags={
                "output_format": request.output_format.value,
                "concurrency": str(request.concurrency),
                "deduplicate": str(request.deduplicate_results)
            }
        )
        
        logger.info(
            f"Batch discovery job started",
            extra={
                "job_id": job_result.job_id,
                "total_companies": job_result.total_companies,
                "discovery_limit": request.discovery_config.limit,
                "deduplicate_results": request.deduplicate_results
            }
        )
        
        return BatchJobResponse(
            job_id=job_result.job_id,
            status=BatchJobStatus.PENDING,
            job_type="discovery",
            total_companies=job_result.total_companies,
            completed=0,
            failed=0,
            pending=job_result.total_companies,
            progress_percentage=0.0,
            created_at=job_result.created_at,
            updated_at=job_result.created_at,
            output_format=request.output_format.value,
            output_location=request.output_location
        )
        
    except Exception as e:
        logger.error(f"Failed to start batch discovery: {e}", exc_info=True)
        metrics.increment_counter("batch_discovery_jobs_failed_start")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch discovery: {str(e)}"
        )


@router.get("/jobs", summary="List Batch Jobs")
async def list_batch_jobs(
    status: Optional[BatchJobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type (research/discovery)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    List batch jobs with filtering and pagination
    
    Returns a paginated list of batch jobs with their current status,
    progress, and metadata. Supports filtering by status and job type.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Get jobs list
        jobs = await batch_use_case.list_jobs(
            status=status.value if status else None,
            job_type=job_type,
            limit=limit,
            offset=offset
        )
        
        return {
            "jobs": [
                BatchJobResponse(
                    job_id=job.job_id,
                    status=BatchJobStatus(job.status),
                    job_type=job.job_type,
                    total_companies=job.total_companies,
                    completed=job.completed,
                    failed=job.failed,
                    pending=job.pending,
                    progress_percentage=job.progress_percentage,
                    estimated_completion=job.estimated_completion,
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    output_location=job.output_location,
                    output_format=job.output_format,
                    error=job.error
                )
                for job in jobs.jobs
            ],
            "total": jobs.total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(jobs.jobs) < jobs.total
        }
        
    except Exception as e:
        logger.error(f"Failed to list batch jobs: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list batch jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=BatchJobResponse, summary="Get Batch Job Details")
async def get_batch_job(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
) -> BatchJobResponse:
    """
    Get detailed information about a specific batch job
    
    Returns comprehensive information including progress, statistics,
    error details, and output location.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Get job details
        job = await batch_use_case.get_job_details(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found: {job_id}"
            )
        
        return BatchJobResponse(
            job_id=job.job_id,
            status=BatchJobStatus(job.status),
            job_type=job.job_type,
            total_companies=job.total_companies,
            completed=job.completed,
            failed=job.failed,
            pending=job.pending,
            progress_percentage=job.progress_percentage,
            estimated_completion=job.estimated_completion,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            output_location=job.output_location,
            output_format=job.output_format,
            error=job.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch job: {str(e)}"
        )


@router.post("/jobs/{job_id}/pause", summary="Pause Batch Job")
async def pause_batch_job(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Pause a running batch job
    
    Pauses job execution while preserving current progress.
    The job can be resumed later from where it left off.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Pause the job
        success = await batch_use_case.pause_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found or cannot be paused: {job_id}"
            )
        
        logger.info(f"Batch job paused: {job_id}")
        metrics.increment_counter("batch_jobs_paused")
        
        return {"message": "Batch job paused successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause job: {str(e)}"
        )


@router.post("/jobs/{job_id}/resume", summary="Resume Batch Job")
async def resume_batch_job(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Resume a paused batch job
    
    Resumes job execution from where it was paused.
    Only paused jobs can be resumed.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Resume the job
        success = await batch_use_case.resume_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found or cannot be resumed: {job_id}"
            )
        
        logger.info(f"Batch job resumed: {job_id}")
        metrics.increment_counter("batch_jobs_resumed")
        
        return {"message": "Batch job resumed successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume job: {str(e)}"
        )


@router.delete("/jobs/{job_id}", summary="Cancel Batch Job")
async def cancel_batch_job(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Cancel a batch job
    
    Cancels job execution and marks it as cancelled.
    Completed jobs cannot be cancelled.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Cancel the job
        success = await batch_use_case.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch job not found or cannot be cancelled: {job_id}"
            )
        
        logger.info(f"Batch job cancelled: {job_id}")
        metrics.increment_counter("batch_jobs_cancelled")
        
        return {"message": "Batch job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/jobs/{job_id}/download", summary="Download Batch Job Results")
async def download_batch_results(
    job_id: str,
    format: Optional[OutputFormat] = Query(None, description="Override output format"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Download batch job results
    
    Downloads the results file for a completed batch job.
    Supports various formats including JSON, CSV, and Excel.
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Get download information
        download_info = await batch_use_case.get_download_info(job_id, format)
        
        if not download_info:
            raise HTTPException(
                status_code=404,
                detail=f"Results not available for job: {job_id}"
            )
        
        # Return file response
        return FileResponse(
            path=download_info["file_path"],
            filename=download_info["filename"],
            media_type=download_info["media_type"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download results for job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download results: {str(e)}"
        )


@router.post("/upload", summary="Upload Companies File")
async def upload_companies_file(
    file: UploadFile = File(..., description="Companies file (CSV, JSON, Excel)"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Upload a companies file for batch processing
    
    Uploads and validates a file containing company information.
    Returns a file reference that can be used in batch processing requests.
    
    Supported formats:
    - CSV: name, website, domain, industry, location columns
    - JSON: Array of company objects
    - Excel: Companies in first sheet
    """
    
    try:
        # Get batch processing use case
        batch_use_case = await container.get(BatchProcessingUseCase)
        
        # Validate file type
        if not file.filename.endswith(('.csv', '.json', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Use CSV, JSON, or Excel files."
            )
        
        # Process uploaded file
        file_info = await batch_use_case.process_uploaded_file(file)
        
        logger.info(
            f"Companies file uploaded: {file.filename}",
            extra={
                "filename": file.filename,
                "file_id": file_info["file_id"],
                "company_count": file_info["company_count"],
                "file_size": file_info["file_size"]
            }
        )
        
        metrics.increment_counter(
            "companies_files_uploaded",
            tags={"file_type": file_info["file_type"]}
        )
        
        return {
            "file_id": file_info["file_id"],
            "filename": file.filename,
            "company_count": file_info["company_count"],
            "file_size": file_info["file_size"],
            "file_type": file_info["file_type"],
            "preview": file_info.get("preview", []),
            "message": "File uploaded and processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file {file.filename}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )