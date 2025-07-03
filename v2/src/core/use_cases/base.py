#!/usr/bin/env python3
"""
Base Use Case Foundation for Theodore v2
=======================================

This module provides the foundational classes and interfaces for implementing
use cases following Clean Architecture principles.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

# Generic types for request/response
TRequest = TypeVar('TRequest', bound=BaseModel)
TResult = TypeVar('TResult', bound=BaseModel)


class UseCaseStatus(str, Enum):
    """Status of use case execution"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UseCaseError(Exception):
    """Base exception for use case errors"""
    
    def __init__(self, message: str, phase: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.phase = phase
        self.cause = cause
        self.timestamp = datetime.utcnow()


class BaseUseCaseResult(BaseModel):
    """Base result for all use cases"""
    status: UseCaseStatus
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    
    # Error information
    error_message: Optional[str] = None
    error_phase: Optional[str] = None
    
    # Progress tracking
    progress_percentage: float = 0.0
    current_phase: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def mark_completed(self) -> None:
        """Mark the result as completed"""
        self.status = UseCaseStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.total_duration_ms = duration * 1000
    
    def mark_failed(self, error: UseCaseError) -> None:
        """Mark the result as failed"""
        self.status = UseCaseStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = str(error)
        self.error_phase = error.phase
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.total_duration_ms = duration * 1000


class BaseUseCase(ABC, Generic[TRequest, TResult]):
    """Base class for all use cases"""
    
    def __init__(self, progress_tracker=None):
        self.progress_tracker = progress_tracker
    
    @abstractmethod
    async def execute(self, request: TRequest) -> TResult:
        """Execute the use case with the given request"""
        pass
    
    async def _emit_progress(
        self, 
        execution_id: str, 
        phase: str, 
        percentage: float, 
        message: Optional[str] = None
    ) -> None:
        """Emit progress event"""
        if self.progress_tracker:
            try:
                # Use the progress tracking system we built in TICKET-004
                with self.progress_tracker.operation(f"UseCase {execution_id}") as op:
                    with op.phase(phase, description=message) as phase_tracker:
                        phase_tracker.set_progress(int(percentage), message)
            except (AttributeError, TypeError):
                # Handle case where progress_tracker is a mock or doesn't support context manager
                pass
    
    async def _start_phase(
        self, 
        execution_id: str, 
        phase: str, 
        description: str
    ) -> None:
        """Start a new phase"""
        await self._emit_progress(execution_id, phase, 0, f"Starting {description}")
    
    async def _complete_phase(
        self, 
        execution_id: str, 
        phase: str, 
        success: bool = True
    ) -> None:
        """Complete a phase"""
        status = "completed" if success else "failed"
        await self._emit_progress(execution_id, phase, 100 if success else 0, f"Phase {status}")