#!/usr/bin/env python3
"""
Theodore v2 Discovery API Router

FastAPI router for company discovery and similarity analysis endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from ...infrastructure.container.application import ApplicationContainer
from ...core.use_cases.discover_similar import DiscoverSimilarUseCase
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.requests import DiscoveryRequest
from ..models.responses import DiscoveryResponse, SimilarityResult
from ..models.common import JobStatus

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


@router.post("", response_model=DiscoveryResponse, summary="Start Company Discovery")
async def start_discovery(
    request: DiscoveryRequest,
    container: ApplicationContainer = Depends(get_container)
) -> DiscoveryResponse:
    """
    Start discovery of similar companies
    
    This endpoint initiates an AI-powered discovery process that:
    - Analyzes the target company's characteristics
    - Searches for similar companies across multiple sources
    - Applies intelligent filtering and ranking
    - Generates AI explanations for similarity matches
    - Returns ranked results with similarity scores
    
    The discovery process typically takes 15-60 seconds depending on
    the search scope and filtering complexity.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Convert request to use case parameters
        job_result = await discovery_use_case.execute(
            company_name=request.company_name,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            filters=request.filters.dict() if request.filters else {},
            include_research=request.include_research,
            source_preference=request.source_preference,
            enable_ai_explanations=request.enable_ai_explanations,
            priority=request.priority.value if request.priority else "normal"
        )
        
        # Record metrics
        metrics.increment_counter(
            "discovery_jobs_started",
            tags={
                "include_research": str(request.include_research),
                "has_filters": str(bool(request.filters)),
                "priority": request.priority.value if request.priority else "normal"
            }
        )
        
        logger.info(
            f"Discovery job started for company: {request.company_name}",
            extra={
                "job_id": job_result.job_id,
                "company_name": request.company_name,
                "limit": request.limit,
                "similarity_threshold": request.similarity_threshold,
                "include_research": request.include_research
            }
        )
        
        return DiscoveryResponse(
            job_id=job_result.job_id,
            status=JobStatus.PENDING,
            query_company=request.company_name,
            created_at=job_result.created_at,
            updated_at=job_result.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to start discovery for {request.company_name}: {e}", exc_info=True)
        metrics.increment_counter("discovery_jobs_failed_start")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery: {str(e)}"
        )


@router.get("/{job_id}", response_model=DiscoveryResponse, summary="Get Discovery Results")
async def get_discovery_results(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
) -> DiscoveryResponse:
    """
    Get discovery results for a specific job
    
    Returns the current status and results (if completed) for a discovery job.
    Results include similar companies with similarity scores and AI explanations.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Get job status and results
        job_result = await discovery_use_case.get_job_status(job_id)
        
        if not job_result:
            raise HTTPException(
                status_code=404,
                detail=f"Discovery job not found: {job_id}"
            )
        
        # Convert to response model
        response = DiscoveryResponse(
            job_id=job_result.job_id,
            status=JobStatus(job_result.status),
            query_company=job_result.query_company,
            created_at=job_result.created_at,
            updated_at=job_result.updated_at,
            completed_at=job_result.completed_at,
            progress=job_result.progress,
            total_found=job_result.total_found,
            filters_applied=job_result.filters_applied,
            error=job_result.error
        )
        
        # Add results if completed
        if job_result.status == "completed" and job_result.results:
            response.results = [
                SimilarityResult(**result.dict()) 
                for result in job_result.results
            ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery results for job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get discovery results: {str(e)}"
        )


@router.get("/{job_id}/progress", summary="Get Discovery Progress")
async def get_discovery_progress(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get detailed progress information for a discovery job
    
    Returns detailed progress including current step, companies found,
    and estimated time remaining.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Get progress information
        progress = await discovery_use_case.get_job_progress(job_id)
        
        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Discovery job not found: {job_id}"
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


@router.delete("/{job_id}", summary="Cancel Discovery Job")
async def cancel_discovery(
    job_id: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Cancel a running discovery job
    
    Cancels a discovery job that is currently running or queued.
    Completed jobs cannot be cancelled.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Cancel the job
        success = await discovery_use_case.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Discovery job not found or cannot be cancelled: {job_id}"
            )
        
        logger.info(f"Discovery job cancelled: {job_id}")
        metrics.increment_counter("discovery_jobs_cancelled")
        
        return {"message": "Discovery job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/quick", summary="Quick Company Discovery")
async def quick_discovery(
    company_name: str = Query(..., description="Company name to find similar companies for"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    similarity_threshold: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity score"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Quick discovery for simple use cases
    
    Performs a fast, synchronous discovery for simple queries.
    Use this for real-time suggestions or when you need immediate results.
    
    Note: This endpoint has lower limits and shorter timeouts than the full discovery API.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Perform quick discovery (synchronous)
        results = await discovery_use_case.quick_discover(
            company_name=company_name,
            limit=min(limit, 20),  # Cap at 20 for quick discovery
            similarity_threshold=similarity_threshold,
            timeout_seconds=30  # 30 second timeout for quick discovery
        )
        
        # Record metrics
        metrics.increment_counter(
            "quick_discovery_requests",
            tags={"limit": str(limit)}
        )
        
        logger.info(
            f"Quick discovery completed for: {company_name}",
            extra={
                "company_name": company_name,
                "results_count": len(results),
                "limit": limit,
                "similarity_threshold": similarity_threshold
            }
        )
        
        return {
            "query_company": company_name,
            "results": results,
            "total_found": len(results),
            "similarity_threshold": similarity_threshold,
            "execution_type": "quick_discovery"
        }
        
    except Exception as e:
        logger.error(f"Quick discovery failed for {company_name}: {e}", exc_info=True)
        metrics.increment_counter("quick_discovery_failed")
        
        raise HTTPException(
            status_code=500,
            detail=f"Quick discovery failed: {str(e)}"
        )


@router.get("/suggestions", summary="Get Company Name Suggestions")
async def get_company_suggestions(
    query: str = Query(..., min_length=2, description="Partial company name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions to return"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get company name suggestions for autocomplete
    
    Returns company names that match the partial query.
    Useful for implementing autocomplete functionality in UIs.
    """
    
    try:
        # Get discovery use case
        discovery_use_case = await container.get(DiscoverSimilarUseCase)
        
        # Get suggestions
        suggestions = await discovery_use_case.get_company_suggestions(
            query=query,
            limit=limit
        )
        
        # Record metrics
        metrics.increment_counter("company_suggestions_requests")
        
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions for query '{query}': {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {str(e)}"
        )