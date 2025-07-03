"""
Beautiful console progress tracking using Rich library.

This module provides a stunning console progress adapter that displays
real-time progress with Rich's beautiful progress bars, panels, and
live displays.
"""

from rich.console import Console
from rich.progress import (
    Progress, TaskID, SpinnerColumn, TextColumn, 
    BarColumn, MofNCompleteColumn, TimeElapsedColumn,
    TimeRemainingColumn, TransferSpeedColumn
)
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.align import Align
from typing import Dict, Optional, Set, Any
import threading
import time

from .base import BaseProgressTracker, BaseProgressOperation, BaseProgressPhase


class ConsoleProgressTracker(BaseProgressTracker):
    """
    Beautiful console progress tracking with Rich library.
    
    Features:
    - Real-time live display with progress bars
    - Nested operation and phase tracking
    - Beautiful panels and formatting
    - Thread-safe concurrent operations
    - Performance metrics display
    """
    
    def __init__(
        self, 
        console: Optional[Console] = None, 
        show_spinner: bool = True,
        show_speed: bool = True,
        refresh_per_second: int = 10
    ):
        """
        Initialize console progress tracker.
        
        Args:
            console: Rich Console instance (creates new if None)
            show_spinner: Whether to show spinning indicators
            show_speed: Whether to show processing speed
            refresh_per_second: Live display refresh rate
        """
        super().__init__()
        self.console = console or Console()
        self.show_spinner = show_spinner
        self.show_speed = show_speed
        self.refresh_per_second = refresh_per_second
        
        # Create Rich Progress widget
        columns = []
        if show_spinner:
            columns.append(SpinnerColumn())
        
        columns.extend([
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("[bright_black]•"),
            TimeElapsedColumn(),
        ])
        
        if show_speed:
            columns.extend([
                TextColumn("[bright_black]•"),
                TransferSpeedColumn(),
            ])
        
        columns.extend([
            TextColumn("[bright_black]•"),
            TimeRemainingColumn(),
        ])
        
        self.progress = Progress(
            *columns,
            console=self.console,
            expand=True
        )
        
        # Track Rich task IDs and display state
        self._rich_tasks: Dict[str, TaskID] = {}
        self._active_operations: Set[str] = set()
        self._live: Optional[Live] = None
        self._display_lock = threading.Lock()
        self._start_time = time.time()
    
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> "ConsoleProgressOperation":
        """Create a console-specific operation."""
        return ConsoleProgressOperation(
            operation_id, title, description, tracker=self
        )
    
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> "ConsoleProgressOperation":
        """Start operation with beautiful console display."""
        operation = super().start_operation(operation_id, title, description)
        
        with self._display_lock:
            self._active_operations.add(operation_id)
            
            # Start live display if this is the first operation
            if len(self._active_operations) == 1:
                self._start_live_display()
            
            # Show operation header
            self._show_operation_header(title, description)
        
        return operation
    
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        """Finish operation and update display."""
        # Get operation before finishing (for display info)
        operation = self.get_operation(operation_id)
        
        # Call parent to handle the actual finishing
        super().finish_operation(operation_id, success)
        
        with self._display_lock:
            self._active_operations.discard(operation_id)
            
            # Show completion message
            if operation:
                self._show_operation_completion(operation, success)
            
            # Stop live display if no more operations
            if not self._active_operations and self._live:
                self._stop_live_display()
    
    def _start_live_display(self) -> None:
        """Start the live progress display."""
        if self._live is None:
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(self.progress, name="progress")
            )
            
            # Create header
            header_table = Table.grid(expand=True)
            header_table.add_column(justify="left")
            header_table.add_column(justify="right")
            
            header_table.add_row(
                Text("🔥 Theodore Progress Tracker", style="bold cyan"),
                Text("Real-time Operation Tracking", style="bright_black")
            )
            
            layout["header"].update(
                Panel(
                    Align.center(header_table),
                    border_style="blue",
                    padding=(0, 1)
                )
            )
            
            # Start live display
            self._live = Live(
                layout, 
                console=self.console, 
                refresh_per_second=self.refresh_per_second
            )
            self._live.start()
    
    def _stop_live_display(self) -> None:
        """Stop the live progress display."""
        if self._live:
            self._live.stop()
            self._live = None
    
    def _show_operation_header(self, title: str, description: Optional[str]) -> None:
        """Show operation start header."""
        content = f"[bold cyan]{title}[/bold cyan]"
        if description:
            content += f"\n[bright_black]{description}[/bright_black]"
        
        elapsed = time.time() - self._start_time
        content += f"\n[dim]Session time: {elapsed:.1f}s[/dim]"
        
        panel = Panel(
            content,
            title="🚀 Starting Operation",
            border_style="cyan",
            padding=(0, 1)
        )
        
        self.console.print(panel)
    
    def _show_operation_completion(
        self, 
        operation: "ConsoleProgressOperation", 
        success: bool
    ) -> None:
        """Show operation completion summary."""
        # Determine status
        status_emoji = "✅" if success else "❌"
        status_text = "Completed" if success else "Failed"
        status_color = "green" if success else "red"
        
        # Calculate stats
        duration = operation.duration or 0
        phase_count = len(operation.phases)
        total_errors = sum(phase.error_count for phase in operation.phases.values())
        total_warnings = sum(phase.warning_count for phase in operation.phases.values())
        
        # Build content
        content = f"[bold {status_color}]{status_emoji} {status_text}[/bold {status_color}] {operation.title}\n"
        content += f"[bright_black]Duration: {duration:.1f}s • Phases: {phase_count}"
        
        if total_errors > 0:
            content += f" • Errors: {total_errors}"
        if total_warnings > 0:
            content += f" • Warnings: {total_warnings}"
        
        content += "[/bright_black]"
        
        panel = Panel(
            content,
            title="Operation Complete",
            border_style=status_color,
            padding=(0, 1)
        )
        
        self.console.print(panel)


class ConsoleProgressOperation(BaseProgressOperation):
    """Console-specific operation with Rich integration."""
    
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> "ConsoleProgressPhase":
        """Create a console-specific phase."""
        return ConsoleProgressPhase(
            phase_id, title, total, description, operation=self
        )
    
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> "ConsoleProgressPhase":
        """Start phase with Rich progress bar."""
        phase = super().start_phase(phase_id, title, total, description)
        
        # Add Rich task
        if isinstance(self._tracker, ConsoleProgressTracker):
            # Create descriptive title with emoji
            display_title = self._format_phase_title(title)
            
            task_id = self._tracker.progress.add_task(
                description=display_title,
                total=total,
                visible=True
            )
            self._tracker._rich_tasks[phase_id] = task_id
        
        return phase
    
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        """Finish phase and update display."""
        super().finish_phase(phase_id, success)
        
        # Remove Rich task
        if isinstance(self._tracker, ConsoleProgressTracker):
            if phase_id in self._tracker._rich_tasks:
                task_id = self._tracker._rich_tasks[phase_id]
                
                # Mark as complete before removing
                phase = self.phases.get(phase_id)
                if phase and phase.total:
                    self._tracker.progress.update(
                        task_id,
                        completed=phase.total,
                        description=self._format_phase_completion(phase, success)
                    )
                
                # Remove after a brief display
                self._tracker.progress.remove_task(task_id)
                del self._tracker._rich_tasks[phase_id]
    
    def _format_phase_title(self, title: str) -> str:
        """Format phase title with appropriate emoji."""
        title_lower = title.lower()
        
        if "discover" in title_lower or "link" in title_lower:
            return f"🔍 {title}"
        elif "select" in title_lower or "llm" in title_lower or "ai" in title_lower:
            return f"🧠 {title}"
        elif "extract" in title_lower or "scrape" in title_lower:
            return f"📄 {title}"
        elif "analyz" in title_lower or "process" in title_lower:
            return f"⚙️  {title}"
        elif "embed" in title_lower or "vector" in title_lower:
            return f"🔗 {title}"
        else:
            return f"📊 {title}"
    
    def _format_phase_completion(self, phase: "ConsoleProgressPhase", success: bool) -> str:
        """Format phase completion message."""
        emoji = "✅" if success else "❌"
        base_title = self._format_phase_title(phase.title)
        
        if success and phase.last_message:
            return f"{emoji} {base_title} • {phase.last_message}"
        else:
            return f"{emoji} {base_title}"


class ConsoleProgressPhase(BaseProgressPhase):
    """Console-specific phase with Rich progress bar integration."""
    
    def __init__(self, *args, **kwargs):
        """Initialize console progress phase."""
        super().__init__(*args, **kwargs)
        self._last_ui_update = 0
        self._min_update_interval = 0.1  # Throttle updates to 10 FPS
    
    def _notify_update(self, message: Optional[str] = None, **metadata: Any) -> None:
        """Update Rich progress bar with throttling."""
        # Always call parent for callbacks
        super()._notify_update(message, **metadata)
        
        # Throttle UI updates for performance
        current_time = time.time()
        if current_time - self._last_ui_update < self._min_update_interval:
            return
        
        self._last_ui_update = current_time
        
        # Update Rich task
        if (self._operation and 
            isinstance(self._operation._tracker, ConsoleProgressTracker) and
            self.phase_id in self._operation._tracker._rich_tasks):
            
            task_id = self._operation._tracker._rich_tasks[self.phase_id]
            
            # Create enhanced description
            base_description = self._operation._format_phase_title(self.title)
            
            if message:
                # Truncate long messages
                display_message = message[:50] + "..." if len(message) > 50 else message
                description = f"{base_description} • {display_message}"
            else:
                description = base_description
            
            # Add performance info if available
            if self.items_per_second > 0:
                description += f" ({self.items_per_second:.1f}/sec)"
            
            # Update progress
            self._operation._tracker.progress.update(
                task_id,
                completed=self.current,
                description=description
            )


class LoggingProgressTracker(BaseProgressTracker):
    """
    Progress tracker that outputs to Python logging.
    
    Useful for server environments or when Rich console output
    is not appropriate.
    """
    
    def __init__(self, logger_name: str = "theodore.progress", level: int = 20):
        """
        Initialize logging progress tracker.
        
        Args:
            logger_name: Logger name to use
            level: Logging level (default: INFO)
        """
        super().__init__()
        self.logger = logging.getLogger(logger_name)
        self.level = level
    
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> "LoggingProgressOperation":
        """Create a logging-specific operation."""
        return LoggingProgressOperation(
            operation_id, title, description, tracker=self
        )
    
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> "LoggingProgressOperation":
        """Start operation with logging."""
        operation = super().start_operation(operation_id, title, description)
        
        log_msg = f"🚀 Started operation: {title}"
        if description:
            log_msg += f" ({description})"
        
        self.logger.log(self.level, log_msg)
        return operation
    
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        """Finish operation with logging."""
        operation = self.get_operation(operation_id)
        super().finish_operation(operation_id, success)
        
        if operation:
            status = "✅ Completed" if success else "❌ Failed"
            duration = operation.duration or 0
            self.logger.log(
                self.level,
                f"{status} operation: {operation.title} (duration: {duration:.1f}s)"
            )


class LoggingProgressOperation(BaseProgressOperation):
    """Logging-specific operation."""
    
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> "LoggingProgressPhase":
        """Create a logging-specific phase."""
        return LoggingProgressPhase(
            phase_id, title, total, description, operation=self
        )
    
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> "LoggingProgressPhase":
        """Start phase with logging."""
        phase = super().start_phase(phase_id, title, total, description)
        
        if isinstance(self._tracker, LoggingProgressTracker):
            log_msg = f"  📊 Started phase: {title}"
            if total:
                log_msg += f" (0/{total})"
            
            self._tracker.logger.log(self._tracker.level, log_msg)
        
        return phase
    
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        """Finish phase with logging."""
        phase = self.phases.get(phase_id)
        super().finish_phase(phase_id, success)
        
        if isinstance(self._tracker, LoggingProgressTracker) and phase:
            status = "✅" if success else "❌"
            duration = phase.duration or 0
            final_progress = f"{phase.current}"
            if phase.total:
                final_progress += f"/{phase.total}"
            
            log_msg = f"  {status} Finished phase: {phase.title} ({final_progress}, {duration:.1f}s)"
            if phase.error_count > 0:
                log_msg += f", {phase.error_count} errors"
            if phase.warning_count > 0:
                log_msg += f", {phase.warning_count} warnings"
            
            self._tracker.logger.log(self._tracker.level, log_msg)


class LoggingProgressPhase(BaseProgressPhase):
    """Logging-specific phase with periodic progress logging."""
    
    def __init__(self, *args, **kwargs):
        """Initialize logging progress phase."""
        super().__init__(*args, **kwargs)
        self._last_log_time = 0
        self._log_interval = 5.0  # Log progress every 5 seconds
        self._last_logged_progress = 0
    
    def _notify_update(self, message: Optional[str] = None, **metadata: Any) -> None:
        """Log progress updates periodically."""
        super()._notify_update(message, **metadata)
        
        # Log significant progress or time-based updates
        current_time = time.time()
        progress_change = abs(self.current - self._last_logged_progress)
        time_elapsed = current_time - self._last_log_time
        
        should_log = (
            time_elapsed >= self._log_interval or  # Time-based
            (self.total and progress_change >= self.total * 0.1) or  # 10% progress change
            message and any(keyword in message.lower() for keyword in ['error', 'fail', 'complete'])  # Important messages
        )
        
        if should_log and isinstance(self._operation._tracker, LoggingProgressTracker):
            progress_str = f"{self.current}"
            if self.total:
                progress_str += f"/{self.total} ({self.percentage:.1f}%)"
            
            log_msg = f"    📈 {self.title}: {progress_str}"
            if message:
                log_msg += f" - {message}"
            if self.items_per_second > 0:
                log_msg += f" ({self.items_per_second:.1f}/sec)"
            
            self._operation._tracker.logger.log(self._operation._tracker.level, log_msg)
            self._last_log_time = current_time
            self._last_logged_progress = self.current