#!/usr/bin/env python3
"""
Research Result Value Objects
============================

Value objects for company research use case requests and results.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.core.use_cases.base import BaseUseCaseResult
from src.core.domain.entities.company import Company
from enum import Enum


class ResearchCompanyRequest(BaseModel):
    """Request for company research"""
    company_name: str = Field(..., description="Company name to research")
    company_url: Optional[str] = Field(None, description="Known company URL")
    
    # Research options
    force_refresh: bool = Field(False, description="Force refresh even if data exists")
    include_embeddings: bool = Field(True, description="Generate embeddings")
    store_in_vector_db: bool = Field(True, description="Store in vector database")
    
    # Progress tracking
    execution_id: Optional[str] = Field(None, description="Execution ID for progress tracking")
    
    # Configuration overrides
    scraping_config: Optional[Dict[str, Any]] = Field(None, description="Custom scraping configuration")
    ai_config: Optional[Dict[str, Any]] = Field(None, description="Custom AI configuration")


class PhaseResult(BaseModel):
    """Result from a single research phase"""
    phase_name: str = Field(..., description="Name of the phase")
    success: bool = Field(..., description="Whether phase succeeded")
    duration_ms: float = Field(..., description="Phase duration in milliseconds")
    
    # Phase-specific data
    output_data: Optional[Dict[str, Any]] = Field(None, description="Phase output data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Progress info
    started_at: datetime = Field(..., description="Phase start time")
    completed_at: Optional[datetime] = Field(None, description="Phase completion time")


class AnalysisResult(BaseModel):
    """AI Analysis result"""
    content: str = Field(..., description="Analysis content")
    status: str = Field(..., description="Analysis status")
    model_used: str = Field(..., description="AI model used")
    confidence_score: float = Field(..., description="Confidence score")
    token_usage: Dict[str, int] = Field(..., description="Token usage statistics")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")


class EmbeddingResult(BaseModel):
    """Embedding generation result"""
    embedding: List[float] = Field(..., description="Generated embedding vector")
    dimensions: int = Field(..., description="Embedding dimensions")
    model_used: str = Field(..., description="Embedding model used")
    token_count: int = Field(..., description="Tokens processed")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")


class ResearchCompanyResult(BaseUseCaseResult):
    """Result from company research use case"""
    
    # Request info
    company_name: str = Field(..., description="Company that was researched")
    discovered_url: Optional[str] = Field(None, description="URL discovered/used for research")
    
    # Research outputs
    company_data: Optional[Company] = Field(None, description="Extracted company data")
    ai_analysis: Optional[AnalysisResult] = Field(None, description="AI analysis result")
    embeddings: Optional[EmbeddingResult] = Field(None, description="Generated embeddings")
    
    # Phase tracking
    phase_results: List[PhaseResult] = Field(default_factory=list, description="Results from each phase")
    
    # Storage info
    stored_in_vector_db: bool = Field(False, description="Whether data was stored in vector DB")
    vector_id: Optional[str] = Field(None, description="Vector database ID")
    
    # Performance metrics
    total_pages_scraped: int = Field(0, description="Number of pages scraped")
    total_content_length: int = Field(0, description="Total content length processed")
    ai_tokens_used: int = Field(0, description="AI tokens consumed")
    estimated_cost: float = Field(0.0, description="Estimated cost in USD")
    
    def add_phase_result(self, phase_result: PhaseResult) -> None:
        """Add a phase result"""
        self.phase_results.append(phase_result)
        
        # Update current phase
        self.current_phase = phase_result.phase_name
        
        # Update metadata
        if phase_result.output_data:
            self.metadata.update(phase_result.output_data)
    
    def get_phase_result(self, phase_name: str) -> Optional[PhaseResult]:
        """Get result for a specific phase"""
        for phase_result in self.phase_results:
            if phase_result.phase_name == phase_name:
                return phase_result
        return None
    
    def get_successful_phases(self) -> List[PhaseResult]:
        """Get all successful phases"""
        return [pr for pr in self.phase_results if pr.success]
    
    def get_failed_phases(self) -> List[PhaseResult]:
        """Get all failed phases"""
        return [pr for pr in self.phase_results if not pr.success]
    
    def calculate_success_rate(self) -> float:
        """Calculate percentage of successful phases"""
        if not self.phase_results:
            return 0.0
        successful = len(self.get_successful_phases())
        return (successful / len(self.phase_results)) * 100.0