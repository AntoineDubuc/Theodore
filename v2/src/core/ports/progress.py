"""
Progress tracking interfaces for Theodore.

This module provides interfaces for tracking progress of long-running
operations across different providers and components.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class ProgressStatus(str, Enum):
    """Status of progress tracking operation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressTracker(ABC):
    """
    Interface for tracking progress of operations.
    
    Provides methods for updating progress, reporting status,
    and handling completion or errors.
    """
    
    @abstractmethod
    def start(self, operation_name: str, total_steps: Optional[int] = None) -> str:
        """
        Start tracking progress for an operation.
        
        Args:
            operation_name: Name/description of the operation
            total_steps: Total number of steps (if known)
            
        Returns:
            Operation ID for tracking
        """
        pass
    
    @abstractmethod
    def update(
        self, 
        operation_id: str, 
        current_step: int, 
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update progress for an operation.
        
        Args:
            operation_id: ID of the operation to update
            current_step: Current step number
            message: Optional progress message
            details: Optional additional details
        """
        pass
    
    @abstractmethod
    def complete(
        self, 
        operation_id: str, 
        message: Optional[str] = None,
        result: Optional[Any] = None
    ) -> None:
        """
        Mark operation as completed.
        
        Args:
            operation_id: ID of the operation
            message: Optional completion message
            result: Optional operation result
        """
        pass
    
    @abstractmethod
    def fail(
        self, 
        operation_id: str, 
        error: Exception,
        message: Optional[str] = None
    ) -> None:
        """
        Mark operation as failed.
        
        Args:
            operation_id: ID of the operation
            error: The error that occurred
            message: Optional error message
        """
        pass
    
    @abstractmethod
    def get_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get current status of an operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Dictionary with operation status and progress
        """
        pass


# Type alias for progress callback functions
ProgressCallback = Callable[[str, float, Optional[str]], None]