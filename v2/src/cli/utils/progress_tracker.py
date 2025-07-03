"""
CLI Progress Tracker for Theodore v2.

Provides real-time progress tracking for CLI operations.
"""

import threading
import time
from typing import Optional, Callable, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn


class CLIProgressTracker:
    """
    CLI-specific progress tracker with Rich integration.
    """
    
    def __init__(self):
        self.console = Console()
        self._active_tasks: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def create_progress_callback(self, task_name: str = "Processing") -> Callable:
        """
        Create a progress callback function for use with async operations.
        
        Args:
            task_name: Name of the task for display
            
        Returns:
            Progress callback function
        """
        
        def progress_callback(description: str, percentage: float, error: Optional[str] = None):
            """
            Progress callback function.
            
            Args:
                description: Current operation description
                percentage: Progress percentage (0.0 to 1.0)
                error: Error message if any
            """
            
            with self._lock:
                # Store progress information
                task_id = f"{task_name}_{threading.get_ident()}"
                
                self._active_tasks[task_id] = {
                    'description': description,
                    'percentage': percentage * 100,  # Convert to 0-100
                    'error': error,
                    'timestamp': time.time()
                }
                
                # For CLI, we can display immediate feedback
                if error:
                    self.console.print(f"⚠️ [yellow]{error}[/yellow]")
                else:
                    # Update progress display (simplified for CLI)
                    progress_bar = self._create_simple_progress_bar(percentage)
                    self.console.print(f"\r{description} {progress_bar} {percentage*100:.0f}%", end="")
        
        return progress_callback
    
    def _create_simple_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a simple text progress bar."""
        filled = int(percentage * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get currently active tasks."""
        with self._lock:
            return self._active_tasks.copy()
    
    def clear_completed_tasks(self) -> None:
        """Clear completed tasks from tracking."""
        with self._lock:
            # Remove tasks that are 100% complete or have errors
            completed_tasks = [
                task_id for task_id, task_data in self._active_tasks.items()
                if task_data['percentage'] >= 100 or task_data['error']
            ]
            
            for task_id in completed_tasks:
                del self._active_tasks[task_id]
    
    def display_task_summary(self) -> None:
        """Display summary of active tasks."""
        with self._lock:
            if not self._active_tasks:
                return
            
            self.console.print("\n📊 [bold]Active Tasks:[/bold]")
            
            for task_id, task_data in self._active_tasks.items():
                description = task_data['description']
                percentage = task_data['percentage']
                
                if task_data['error']:
                    status = f"[red]Error: {task_data['error']}[/red]"
                elif percentage >= 100:
                    status = "[green]Completed[/green]"
                else:
                    progress_bar = self._create_simple_progress_bar(percentage / 100)
                    status = f"{progress_bar} {percentage:.0f}%"
                
                self.console.print(f"  • {description}: {status}")


class ProgressContext:
    """Context manager for CLI progress tracking."""
    
    def __init__(self, description: str, console: Optional[Console] = None):
        self.description = description
        self.console = console or Console()
        self.progress = None
        self.task = None
    
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        )
        
        self.progress.start()
        self.task = self.progress.add_task(self.description, total=100)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()
    
    def update(self, description: str, percentage: float):
        """Update progress."""
        if self.progress and self.task is not None:
            self.progress.update(
                self.task,
                description=description,
                completed=percentage
            )
    
    def complete(self, description: str = "Completed"):
        """Mark as complete."""
        if self.progress and self.task is not None:
            self.progress.update(
                self.task,
                description=description,
                completed=100
            )