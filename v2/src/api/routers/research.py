#!/usr/bin/env python3
"""
Theodore v2 Research API Router

FastAPI router for company research endpoints with streaming progress.
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse

from ...infrastructure.container.application import ApplicationContainer
from ...core.use_cases.research_company import ResearchCompanyUseCase
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.requests import ResearchRequest
from ..models.responses import ResearchResponse, CompanyIntelligence
from ..models.common import JobStatus

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()


def get_container() -> ApplicationContainer:
    """Get application container dependency"""
    # This would be injected from the app state
    from fastapi import Request
    import inspect
    frame = inspect.currentframe()
    try:
        # Get request from calling context
        request = None
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            if 'request' in frame_locals:
                request = frame_locals['request']
                break
        
        if request and hasattr(request.app.state, 'container'):
            return request.app.state.container
        else:
            # Fallback - create container
            container = ApplicationContainer()
            return container
    finally:
        del frame


@router.post("", response_model=ResearchResponse, summary="Start Company Research")
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    container: ApplicationContainer = Depends(get_container)
) -> ResearchResponse:
    """
    Start comprehensive research on a company
    
    This endpoint initiates an AI-powered research process that:
    - Discovers and crawls relevant company web pages
    - Extracts structured business intelligence using AI
    - Generates comprehensive company profiles
    - Provides real-time progress updates via WebSocket
    
    The research process typically takes 30-120 seconds depending on
    company website complexity and analysis depth.
    """
    
    try:
        # Get research use case
        research_use_case = await container.get(ResearchCompanyUseCase)
        
        # Start research job
        job_result = await research_use_case.execute(
            company_name=request.company_name,
            website=request.website,
            config_overrides=request.config_overrides or {},
            priority=request.priority.value if request.priority else "normal",
            deep_analysis=request.deep_analysis or False,
            timeout_seconds=request.timeout_seconds
        )
        
        # Record metrics
        metrics.increment_counter(
            "research_jobs_started",
            tags={
                "priority": request.priority.value if request.priority else "normal",
                "deep_analysis": str(request.deep_analysis or False)
            }
        )
        
        logger.info(
            f"Research job started for company: {request.company_name}",
            extra={
                "job_id": job_result.job_id,
                "company_name": request.company_name,
                "website": request.website,
                "priority": request.priority.value if request.priority else "normal"
            }
        )
        
        # Return job information
        return ResearchResponse(
            job_id=job_result.job_id,
            status=JobStatus.PENDING,
            company_name=request.company_name,
            created_at=job_result.created_at,
            updated_at=job_result.created_at,
            estimated_completion=job_result.estimated_completion
        )
        
    except Exception as e:
        logger.error(f"Failed to start research for {request.company_name}: {e}", exc_info=True)
        metrics.increment_counter("research_jobs_failed_start")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start research: {str(e)}"
        )


@router.get("/{job_id}", response_model=ResearchResponse, summary="Get Research Results")
async def get_research_results(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
) -> ResearchResponse:
    """
    Get research results for a specific job
    
    Returns the current status and results (if completed) for a research job.
    Use this endpoint to poll for completion or get final results.
    
    For real-time updates, use the WebSocket endpoint at `/api/v2/ws/progress/{job_id}`.
    """
    
    try:
        # Get research use case
        research_use_case = await container.get(ResearchCompanyUseCase)
        
        # Get job status and results
        job_result = await research_use_case.get_job_status(job_id)
        
        if not job_result:
            raise HTTPException(
                status_code=404,
                detail=f"Research job not found: {job_id}"
            )
        
        # Convert to response model
        response = ResearchResponse(
            job_id=job_result.job_id,
            status=JobStatus(job_result.status),
            company_name=job_result.company_name,
            created_at=job_result.created_at,
            updated_at=job_result.updated_at,
            started_at=job_result.started_at,
            completed_at=job_result.completed_at,
            estimated_completion=job_result.estimated_completion,
            progress=job_result.progress,
            error=job_result.error,
            retry_count=job_result.retry_count
        )
        
        # Add results if completed
        if job_result.status == "completed" and job_result.result:
            response.result = CompanyIntelligence(**job_result.result.dict())
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research results for job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get research results: {str(e)}"
        )


@router.get("/{job_id}/progress", summary="Get Research Progress")
async def get_research_progress(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get detailed progress information for a research job
    
    Returns detailed progress including current step, percentage completion,
    and estimated time remaining.
    """
    
    try:
        # Get research use case
        research_use_case = await container.get(ResearchCompanyUseCase)
        
        # Get progress information
        progress = await research_use_case.get_job_progress(job_id)
        
        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Research job not found: {job_id}"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress for job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get progress: {str(e)}"
        )


@router.delete("/{job_id}", summary="Cancel Research Job")
async def cancel_research(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Cancel a running research job
    
    Cancels a research job that is currently running or queued.
    Completed jobs cannot be cancelled.
    """
    
    try:
        # Get research use case
        research_use_case = await container.get(ResearchCompanyUseCase)
        
        # Cancel the job
        success = await research_use_case.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Research job not found or cannot be cancelled: {job_id}"
            )
        
        logger.info(f"Research job cancelled: {job_id}")
        metrics.increment_counter("research_jobs_cancelled")
        
        return {"message": "Research job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/{job_id}/stream", summary="Stream Research Progress")
async def stream_research_progress(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Stream real-time progress updates for a research job
    
    Returns a Server-Sent Events (SSE) stream with real-time progress updates.
    Each event contains the current progress information in JSON format.
    
    This is an alternative to WebSocket for clients that prefer HTTP streaming.
    """
    
    async def generate_progress_stream():
        """Generate SSE stream of progress updates"""
        
        try:
            research_use_case = await container.get(ResearchCompanyUseCase)
            
            # Check if job exists
            job_result = await research_use_case.get_job_status(job_id)
            if not job_result:
                yield f"event: error\ndata: {{\"error\": \"Job not found: {job_id}\"}}\n\n"
                return
            
            # Stream progress updates
            last_progress = None
            
            while True:
                try:
                    # Get current progress
                    current_progress = await research_use_case.get_job_progress(job_id)
                    
                    if current_progress != last_progress:
                        # Progress changed, send update
                        yield f"event: progress\ndata: {current_progress.json()}\n\n"
                        last_progress = current_progress
                        
                        # Check if job is complete
                        if current_progress.status in ["completed", "failed", "cancelled"]:
                            yield f"event: complete\ndata: {{\"status\": \"{current_progress.status}\"}}\n\n"
                            break
                    
                    # Wait before next check
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error streaming progress for job {job_id}: {e}")
                    yield f"event: error\ndata: {{\"error\": \"Stream error: {str(e)}\"}}\n\n"
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start progress stream for job {job_id}: {e}")
            yield f"event: error\ndata: {{\"error\": \"Failed to start stream: {str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )