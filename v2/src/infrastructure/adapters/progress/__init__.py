"""
Progress tracking adapters for Theodore.

This module provides different implementations of the ProgressTracker port:
- ConsoleProgressTracker: Beautiful Rich-based console progress
- LoggingProgressTracker: Standard Python logging output
- NoOpProgressTracker: Silent mode for testing/batch operations
"""

from .base import (
    BaseProgressTracker,
    BaseProgressOperation, 
    BaseProgressPhase,
    NoOpProgressTracker
)

from .console import (
    ConsoleProgressTracker,
    LoggingProgressTracker
)

# Default tracker for different environments
def create_progress_tracker(
    mode: str = "console",
    **kwargs
) -> BaseProgressTracker:
    """
    Factory function to create appropriate progress tracker.
    
    Args:
        mode: Type of tracker ("console", "logging", "silent")
        **kwargs: Arguments passed to tracker constructor
        
    Returns:
        ProgressTracker instance
        
    Example:
        # Beautiful console progress
        tracker = create_progress_tracker("console", show_spinner=True)
        
        # Logging-based progress
        tracker = create_progress_tracker("logging", level=logging.INFO)
        
        # Silent mode
        tracker = create_progress_tracker("silent")
    """
    if mode == "console":
        return ConsoleProgressTracker(**kwargs)
    elif mode == "logging":
        return LoggingProgressTracker(**kwargs)
    elif mode == "silent":
        return NoOpProgressTracker(**kwargs)
    else:
        raise ValueError(f"Unknown progress tracker mode: {mode}")


__all__ = [
    'BaseProgressTracker',
    'BaseProgressOperation',
    'BaseProgressPhase', 
    'NoOpProgressTracker',
    'ConsoleProgressTracker',
    'LoggingProgressTracker',
    'create_progress_tracker'
]