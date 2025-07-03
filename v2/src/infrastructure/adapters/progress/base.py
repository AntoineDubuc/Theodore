"""
Base implementations for progress tracking adapters.

This module provides thread-safe base classes that implement common
functionality for progress tracking, allowing concrete adapters to
focus on their specific display/output logic.
"""

import threading
import logging
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime

from src.core.ports.progress import (
    ProgressTracker, 
    ProgressOperation, 
    ProgressPhase,
    ProgressEvent,
    ProgressEventType
)

logger = logging.getLogger(__name__)


class BaseProgressTracker(ProgressTracker):
    """
    Thread-safe base implementation of ProgressTracker.
    
    Provides common functionality for managing operations, callbacks,
    and thread safety. Concrete adapters inherit from this and implement
    the display-specific logic.
    """
    
    def __init__(self):
        """Initialize base progress tracker."""
        self._operations: Dict[str, ProgressOperation] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._callbacks: List[Callable] = []
        self._next_operation_number = 1
    
    def add_callback(self, callback: Callable) -> None:
        """
        Add a callback for progress updates.
        
        Args:
            callback: Function with signature callback(event_type: str, **data)
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
                logger.debug(f"Added progress callback: {callback}")
    
    def remove_callback(self, callback: Callable) -> None:
        """
        Remove a progress callback.
        
        Args:
            callback: The callback function to remove
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                logger.debug(f"Removed progress callback: {callback}")
    
    def _notify_callbacks(self, event_type: str, **data) -> None:
        """
        Notify all callbacks of progress events.
        
        Args:
            event_type: Type of event
            **data: Event data
        """
        # Create event object
        event = ProgressEvent(
            event_type=event_type,
            operation_id=data.get('operation_id'),
            phase_id=data.get('phase_id'),
            **data
        )
        
        # Notify callbacks (without holding the lock)
        callbacks_to_notify = list(self._callbacks)
        
        for callback in callbacks_to_notify:
            try:
                callback(event_type, **data)
            except Exception as e:
                # Don't let callback errors break progress tracking
                logger.error(f"Progress callback error: {e}")
                # Optionally remove failing callbacks
                self._handle_callback_error(callback, e)
    
    def _handle_callback_error(self, callback: Callable, error: Exception) -> None:
        """
        Handle callback errors by tracking failures and removing persistent failures.
        
        Args:
            callback: The failing callback
            error: The exception that occurred
        """
        # Track error count on the callback function
        if not hasattr(callback, '_error_count'):
            callback._error_count = 0
        callback._error_count += 1
        
        # Remove callbacks that fail too many times
        if callback._error_count > 3:
            logger.warning(f"Removing failing callback after {callback._error_count} errors: {callback}")
            self.remove_callback(callback)
    
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ProgressOperation:
        """
        Start a new operation.
        
        Args:
            operation_id: Unique identifier for the operation
            title: Human-readable operation title
            description: Optional detailed description
            
        Returns:
            ProgressOperation instance
            
        Raises:
            ValueError: If operation_id already exists
        """
        with self._lock:
            if operation_id in self._operations:
                raise ValueError(f"Operation {operation_id} already exists")
            
            # Create operation using factory method
            operation = self._create_operation(operation_id, title, description)
            operation.set_metadata(operation_number=self._next_operation_number)
            self._next_operation_number += 1
            
            # Store operation
            self._operations[operation_id] = operation
            
            # Notify callbacks
            self._notify_callbacks(
                ProgressEventType.OPERATION_STARTED,
                operation_id=operation_id,
                title=title,
                description=description,
                started_at=operation.started_at
            )
            
            logger.info(f"Started operation {operation_id}: {title}")
            return operation
    
    def get_operation(self, operation_id: str) -> Optional[ProgressOperation]:
        """
        Get an existing operation.
        
        Args:
            operation_id: The operation identifier
            
        Returns:
            ProgressOperation if found, None otherwise
        """
        with self._lock:
            return self._operations.get(operation_id)
    
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        """
        Mark operation as complete.
        
        Args:
            operation_id: The operation to finish
            success: Whether the operation completed successfully
        """
        with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                logger.warning(f"Attempted to finish non-existent operation: {operation_id}")
                return
            
            # Mark as complete
            operation.completed_at = datetime.now()
            operation.success = success
            
            # Calculate duration
            duration = operation.duration
            
            # Notify callbacks
            self._notify_callbacks(
                ProgressEventType.OPERATION_FINISHED,
                operation_id=operation_id,
                success=success,
                duration=duration,
                completed_at=operation.completed_at
            )
            
            logger.info(f"Finished operation {operation_id}: {success}, duration: {duration:.1f}s")
    
    def get_all_operations(self) -> List[ProgressOperation]:
        """
        Get all operations (completed and active).
        
        Returns:
            List of all ProgressOperation instances
        """
        with self._lock:
            return list(self._operations.values())
    
    def get_active_operations(self) -> List[ProgressOperation]:
        """
        Get only active (not completed) operations.
        
        Returns:
            List of active ProgressOperation instances
        """
        with self._lock:
            return [op for op in self._operations.values() if not op.is_complete]
    
    def cleanup_completed_operations(self, max_completed: int = 100) -> None:
        """
        Clean up old completed operations to prevent memory leaks.
        
        Args:
            max_completed: Maximum number of completed operations to keep
        """
        with self._lock:
            completed_ops = [
                (op_id, op) for op_id, op in self._operations.items()
                if op.is_complete
            ]
            
            if len(completed_ops) > max_completed:
                # Sort by completion time and remove oldest
                completed_ops.sort(key=lambda x: x[1].completed_at)
                to_remove = completed_ops[:-max_completed]
                
                for op_id, _ in to_remove:
                    del self._operations[op_id]
                
                logger.debug(f"Cleaned up {len(to_remove)} completed operations")
    
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ProgressOperation:
        """
        Create operation instance - implemented by subclasses.
        
        Args:
            operation_id: Unique identifier
            title: Operation title
            description: Optional description
            
        Returns:
            ProgressOperation instance
        """
        return BaseProgressOperation(operation_id, title, description, tracker=self)


class BaseProgressOperation(ProgressOperation):
    """
    Thread-safe base implementation of ProgressOperation.
    
    Manages phases within an operation and handles the communication
    back to the parent tracker for event notifications.
    """
    
    def __init__(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None,
        tracker: Optional[BaseProgressTracker] = None
    ):
        """
        Initialize base progress operation.
        
        Args:
            operation_id: Unique identifier
            title: Operation title
            description: Optional description
            tracker: Parent tracker for notifications
        """
        super().__init__(operation_id, title, description)
        self._tracker = tracker
        self._lock = threading.RLock()
        self._next_phase_number = 1
    
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> ProgressPhase:
        """
        Start a new phase.
        
        Args:
            phase_id: Unique identifier for the phase
            title: Human-readable phase title
            total: Total number of items to process
            description: Optional detailed description
            
        Returns:
            ProgressPhase instance
            
        Raises:
            ValueError: If phase_id already exists
        """
        with self._lock:
            if phase_id in self.phases:
                raise ValueError(f"Phase {phase_id} already exists in operation {self.operation_id}")
            
            # Create phase using factory method
            phase = self._create_phase(phase_id, title, total, description)
            phase.set_metadata(
                phase_number=self._next_phase_number,
                operation_title=self.title
            )
            self._next_phase_number += 1
            
            # Store phase
            self.phases[phase_id] = phase
            self.current_phase = phase_id
            
            # Notify tracker
            if self._tracker:
                self._tracker._notify_callbacks(
                    ProgressEventType.PHASE_STARTED,
                    operation_id=self.operation_id,
                    phase_id=phase_id,
                    title=title,
                    total=total,
                    description=description,
                    started_at=phase.started_at
                )
            
            logger.debug(f"Started phase {phase_id} in operation {self.operation_id}: {title}")
            return phase
    
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        """
        Mark phase as complete.
        
        Args:
            phase_id: The phase to finish
            success: Whether the phase completed successfully
        """
        with self._lock:
            phase = self.phases.get(phase_id)
            if not phase:
                logger.warning(f"Attempted to finish non-existent phase: {phase_id}")
                return
            
            # Mark as complete
            phase.completed_at = datetime.now()
            phase.success = success
            
            # Update current phase if this was it
            if self.current_phase == phase_id:
                # Find next active phase or clear current
                active_phases = [
                    pid for pid, p in self.phases.items() 
                    if not p.is_complete
                ]
                self.current_phase = active_phases[0] if active_phases else None
            
            # Calculate duration
            duration = phase.duration
            
            # Notify tracker
            if self._tracker:
                self._tracker._notify_callbacks(
                    ProgressEventType.PHASE_FINISHED,
                    operation_id=self.operation_id,
                    phase_id=phase_id,
                    success=success,
                    duration=duration,
                    completed_at=phase.completed_at,
                    final_progress=phase.current,
                    total=phase.total,
                    error_count=phase.error_count,
                    warning_count=phase.warning_count
                )
            
            logger.debug(f"Finished phase {phase_id} in operation {self.operation_id}: {success}, duration: {duration:.1f}s")
    
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> ProgressPhase:
        """
        Create phase instance - implemented by subclasses.
        
        Args:
            phase_id: Unique identifier
            title: Phase title
            total: Total items to process
            description: Optional description
            
        Returns:
            ProgressPhase instance
        """
        return BaseProgressPhase(phase_id, title, total, description, operation=self)


class BaseProgressPhase(ProgressPhase):
    """
    Thread-safe base implementation of ProgressPhase.
    
    Handles progress updates and communicates with the parent operation
    for event notifications and coordination.
    """
    
    def __init__(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None,
        operation: Optional[BaseProgressOperation] = None
    ):
        """
        Initialize base progress phase.
        
        Args:
            phase_id: Unique identifier
            title: Phase title
            total: Total items to process
            description: Optional description
            operation: Parent operation for notifications
        """
        super().__init__(phase_id, title, total, description)
        self._operation = operation
        self._lock = threading.RLock()
        self._update_count = 0
    
    def update(
        self, 
        increment: int = 1, 
        message: Optional[str] = None,
        **metadata: Any
    ) -> None:
        """
        Update progress by increment amount.
        
        Args:
            increment: Amount to increment progress by
            message: Optional status message
            **metadata: Custom metadata for this update
        """
        with self._lock:
            # Update internal state
            self.current += increment
            self.last_message = message
            self._update_count += 1
            
            # Auto-complete if we've reached the total
            if self.total and self.current >= self.total and not self.is_complete:
                self.completed_at = datetime.now()
            
            # Store metadata
            if metadata:
                self.set_metadata(**metadata)
            
            # Notify of update
            self._notify_update(message, **metadata)
    
    def set_progress(
        self, 
        current: int, 
        message: Optional[str] = None,
        **metadata: Any
    ) -> None:
        """
        Set absolute progress value.
        
        Args:
            current: Current progress value
            message: Optional status message
            **metadata: Custom metadata for this update
        """
        with self._lock:
            # Update internal state
            self.current = current
            self.last_message = message
            self._update_count += 1
            
            # Auto-complete if we've reached the total
            if self.total and self.current >= self.total and not self.is_complete:
                self.completed_at = datetime.now()
            
            # Store metadata
            if metadata:
                self.set_metadata(**metadata)
            
            # Notify of update
            self._notify_update(message, **metadata)
    
    def _notify_update(self, message: Optional[str] = None, **metadata: Any) -> None:
        """
        Notify tracker of progress update.
        
        Args:
            message: Optional status message
            **metadata: Custom metadata
        """
        if self._operation and self._operation._tracker:
            self._operation._tracker._notify_callbacks(
                ProgressEventType.PHASE_UPDATED,
                operation_id=self._operation.operation_id,
                phase_id=self.phase_id,
                current=self.current,
                total=self.total,
                percentage=self.percentage,
                message=message,
                items_per_second=self.items_per_second,
                estimated_completion=self.estimated_completion.isoformat() if self.estimated_completion else None,
                update_count=self._update_count,
                **metadata
            )


class NoOpProgressTracker(BaseProgressTracker):
    """
    No-operation progress tracker for silent mode.
    
    Implements the full ProgressTracker interface but produces no output.
    Useful for testing or when progress reporting should be disabled.
    """
    
    def __init__(self):
        """Initialize no-op tracker."""
        super().__init__()
    
    def _notify_callbacks(self, event_type: str, **data) -> None:
        """Override to suppress all notifications."""
        pass  # Silent - no notifications
    
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ProgressOperation:
        """Create a no-op operation."""
        return NoOpProgressOperation(operation_id, title, description, tracker=self)


class NoOpProgressOperation(BaseProgressOperation):
    """No-operation progress operation."""
    
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> ProgressPhase:
        """Create a no-op phase."""
        return NoOpProgressPhase(phase_id, title, total, description, operation=self)


class NoOpProgressPhase(BaseProgressPhase):
    """No-operation progress phase."""
    
    def _notify_update(self, message: Optional[str] = None, **metadata: Any) -> None:
        """Override to suppress all notifications."""
        pass  # Silent - no notifications