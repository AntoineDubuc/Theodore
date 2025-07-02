# TICKET-004: Progress Tracking System (Port)

## Overview
Create a clean port/interface for progress tracking and implement a simple console adapter. This will be used by all long-running operations.

## Acceptance Criteria
- [ ] Define ProgressTracker port/interface
- [ ] Implement ConsoleProgressAdapter with rich progress bars
- [ ] Support nested progress (phases within operations)
- [ ] Thread-safe implementation for concurrent operations
- [ ] Support for both CLI progress bars and structured logging
- [ ] Clean abstraction that allows future SSE/WebSocket adapters

## Technical Details
- Use Rich library for beautiful console progress
- Implement as a port (interface) with adapter pattern
- Support progress callbacks for real-time updates
- Use Python's threading.Lock for thread safety

## Testing
- Unit test the progress tracking logic
- Integration test with a mock long-running operation
- Test concurrent progress tracking
- Manual test with real scraping operation:
  ```python
  # Test progress updates during 4-phase scraping
  progress = ConsoleProgressAdapter()
  progress.start_phase("Link Discovery", total=100)
  for i in range(100):
      progress.update(1, message=f"Found link {i}")
  ```

## Estimated Time: 3-4 hours

## Dependencies
None - this is infrastructure

## Files to Create
- `v2/src/core/ports/progress.py` (port definition)
- `v2/src/infrastructure/adapters/progress/__init__.py`
- `v2/src/infrastructure/adapters/progress/console.py`
- `v2/src/infrastructure/adapters/progress/base.py`
- `v2/tests/unit/adapters/test_console_progress.py`
- `v2/tests/integration/test_progress_tracking.py`

---

# Udemy Tutorial Script: Building Production-Ready Progress Tracking Systems

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Beautiful Progress Tracking with Rich & Clean Architecture"]**

"Welcome to this essential tutorial on building production-ready progress tracking systems! I'm thrilled to show you how to create progress tracking that's not only functional but absolutely beautiful to watch.

By the end of this tutorial, you'll know how to build thread-safe progress systems using the Port/Adapter pattern, create stunning console progress bars with Rich library, and design systems that scale from simple CLI tools to real-time web applications.

This is infrastructure that makes your users love your application!"

## Section 1: Understanding Progress Tracking Challenges (5 minutes)

**[SLIDE 2: The Progress Problem]**

"Let's start by understanding why progress tracking is more complex than it seems. Look at this naive approach:

```python
# ❌ The NAIVE way - print statements everywhere
def scrape_website(url):
    print(f\"Starting scrape of {url}\")
    
    print(\"Phase 1: Finding links...\")
    links = find_links(url)
    print(f\"Found {len(links)} links\")
    
    print(\"Phase 2: Scraping pages...\")
    for i, link in enumerate(links):
        print(f\"Scraping {i+1}/{len(links)}: {link}\")
        scrape_page(link)
    
    print(\"Done!\")
```

What's wrong with this? It's hardcoded, not reusable, and looks terrible!"

**[SLIDE 3: Real-World Progress Requirements]**

"Production applications need progress tracking that handles:

```python
# Real-world complexity:
# 1. Multiple concurrent operations
# 2. Nested progress (phases within operations)
# 3. Different output formats (CLI, web, logs)
# 4. Thread safety for parallel operations
# 5. Error handling and cancellation
# 6. Performance monitoring
```

**[SLIDE 4: The Solution - Port/Adapter Pattern]**

```python
# ✅ The CLEAN way - flexible and reusable
progress = get_progress_tracker()  # Could be console, web, or both!

with progress.operation(\"Website Scraping\") as op:
    with op.phase(\"Link Discovery\", total=100) as phase:
        for i in range(100):
            links = discover_links()
            phase.update(1, message=f\"Found {len(links)} links\")
    
    with op.phase(\"Content Extraction\", total=len(links)) as phase:
        for link in links:
            content = scrape_page(link)
            phase.update(1, message=f\"Scraped {link}\")
```

This is clean, reusable, and beautiful!"

## Section 2: Designing the Progress Port Interface (8 minutes)

**[SLIDE 5: Port-First Design]**

"Let's start with our port interface. This defines the contract that all progress adapters must implement:

```python
# v2/src/core/ports/progress.py

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, Callable
from contextlib import contextmanager
from datetime import datetime
import uuid

class ProgressTracker(ABC):
    \"\"\"Port interface for progress tracking systems\"\"\"
    
    @abstractmethod
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> \"ProgressOperation\":
        \"\"\"Start a new top-level operation\"\"\"
        pass
    
    @abstractmethod
    def get_operation(self, operation_id: str) -> Optional[\"ProgressOperation\"]:
        \"\"\"Retrieve an existing operation\"\"\"
        pass
    
    @abstractmethod
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        \"\"\"Mark an operation as complete\"\"\"
        pass
    
    @contextmanager
    def operation(self, title: str, description: Optional[str] = None):
        \"\"\"Context manager for operations\"\"\"
        operation_id = str(uuid.uuid4())
        op = self.start_operation(operation_id, title, description)
        try:
            yield op
            self.finish_operation(operation_id, success=True)
        except Exception as e:
            self.finish_operation(operation_id, success=False)
            raise


class ProgressOperation(ABC):
    \"\"\"Represents a single operation with multiple phases\"\"\"
    
    def __init__(self, operation_id: str, title: str, description: Optional[str] = None):
        self.operation_id = operation_id
        self.title = title
        self.description = description
        self.started_at = datetime.now()
        self.phases: Dict[str, \"ProgressPhase\"] = {}
        self.current_phase: Optional[str] = None
    
    @abstractmethod
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> \"ProgressPhase\":
        \"\"\"Start a new phase within this operation\"\"\"
        pass
    
    @abstractmethod
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        \"\"\"Mark a phase as complete\"\"\"
        pass
    
    @contextmanager
    def phase(self, title: str, total: Optional[int] = None, description: Optional[str] = None):
        \"\"\"Context manager for phases\"\"\"
        phase_id = str(uuid.uuid4())
        phase = self.start_phase(phase_id, title, total, description)
        try:
            yield phase
            self.finish_phase(phase_id, success=True)
        except Exception as e:
            self.finish_phase(phase_id, success=False)
            raise


class ProgressPhase(ABC):
    \"\"\"Represents a single phase of work\"\"\"
    
    def __init__(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ):
        self.phase_id = phase_id
        self.title = title
        self.total = total
        self.description = description
        self.current = 0
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.last_message: Optional[str] = None
    
    @abstractmethod
    def update(
        self, 
        increment: int = 1, 
        message: Optional[str] = None,
        **metadata: Any
    ) -> None:
        \"\"\"Update progress by increment amount\"\"\"
        pass
    
    @abstractmethod
    def set_progress(
        self, 
        current: int, 
        message: Optional[str] = None,
        **metadata: Any
    ) -> None:
        \"\"\"Set absolute progress value\"\"\"
        pass
    
    @property
    def percentage(self) -> Optional[float]:
        \"\"\"Calculate completion percentage\"\"\"
        if self.total is None or self.total == 0:
            return None
        return min(100.0, (self.current / self.total) * 100.0)
    
    @property
    def is_complete(self) -> bool:
        \"\"\"Check if phase is complete\"\"\"
        return self.completed_at is not None
```

**[SLIDE 6: Why This Design Works]**

"Notice the key design decisions:

1. **Separation of Concerns**: Operation → Phase → Updates
2. **Context Managers**: Automatic cleanup and error handling
3. **Immutable IDs**: Each operation and phase has a unique identifier
4. **Flexible Metadata**: Support for custom progress data
5. **Thread-Safe Interface**: Designed for concurrent access

**[HANDS-ON EXERCISE]** \"Pause the video and create this interface in your project. Make sure you understand each method before continuing!\"

## Section 3: Building the Base Adapter (10 minutes)

**[SLIDE 7: Base Adapter Implementation]**

"Now let's create a base adapter that handles common functionality:

```python
# v2/src/infrastructure/adapters/progress/base.py

import threading
from typing import Dict, Optional, List, Callable
from datetime import datetime
from v2.src.core.ports.progress import (
    ProgressTracker, ProgressOperation, ProgressPhase
)

class BaseProgressTracker(ProgressTracker):
    \"\"\"Base implementation with thread-safe operation management\"\"\"
    
    def __init__(self):
        self._operations: Dict[str, ProgressOperation] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._callbacks: List[Callable] = []
    
    def add_callback(self, callback: Callable) -> None:
        \"\"\"Add a callback for progress updates\"\"\"
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        \"\"\"Remove a progress callback\"\"\"
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, event_type: str, **data) -> None:
        \"\"\"Notify all callbacks of progress events\"\"\"
        for callback in self._callbacks:
            try:
                callback(event_type=event_type, **data)
            except Exception as e:
                # Don't let callback errors break progress tracking
                print(f\"Progress callback error: {e}\")
    
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ProgressOperation:
        \"\"\"Start a new operation\"\"\"
        with self._lock:
            if operation_id in self._operations:
                raise ValueError(f\"Operation {operation_id} already exists\")
            
            operation = self._create_operation(operation_id, title, description)
            self._operations[operation_id] = operation
            
            self._notify_callbacks(
                \"operation_started\",
                operation_id=operation_id,
                title=title,
                description=description
            )
            
            return operation
    
    def get_operation(self, operation_id: str) -> Optional[ProgressOperation]:
        \"\"\"Get an existing operation\"\"\"
        with self._lock:
            return self._operations.get(operation_id)
    
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        \"\"\"Mark operation as complete\"\"\"
        with self._lock:
            if operation_id not in self._operations:
                return
            
            operation = self._operations[operation_id]
            operation.completed_at = datetime.now()
            operation.success = success
            
            self._notify_callbacks(
                \"operation_finished\",
                operation_id=operation_id,
                success=success,
                duration=(operation.completed_at - operation.started_at).total_seconds()
            )
    
    @abstractmethod
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> ProgressOperation:
        \"\"\"Create operation instance - implemented by subclasses\"\"\"
        pass


class BaseProgressOperation(ProgressOperation):
    \"\"\"Base operation implementation\"\"\"
    
    def __init__(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None,
        tracker: BaseProgressTracker = None
    ):
        super().__init__(operation_id, title, description)
        self._tracker = tracker
        self._lock = threading.RLock()
        self.completed_at: Optional[datetime] = None
        self.success: Optional[bool] = None
    
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> ProgressPhase:
        \"\"\"Start a new phase\"\"\"
        with self._lock:
            if phase_id in self.phases:
                raise ValueError(f\"Phase {phase_id} already exists\")
            
            phase = self._create_phase(phase_id, title, total, description)
            self.phases[phase_id] = phase
            self.current_phase = phase_id
            
            if self._tracker:
                self._tracker._notify_callbacks(
                    \"phase_started\",
                    operation_id=self.operation_id,
                    phase_id=phase_id,
                    title=title,
                    total=total
                )
            
            return phase
    
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        \"\"\"Mark phase as complete\"\"\"
        with self._lock:
            if phase_id not in self.phases:
                return
            
            phase = self.phases[phase_id]
            phase.completed_at = datetime.now()
            phase.success = success
            
            if self._tracker:
                self._tracker._notify_callbacks(
                    \"phase_finished\",
                    operation_id=self.operation_id,
                    phase_id=phase_id,
                    success=success,
                    duration=(phase.completed_at - phase.started_at).total_seconds()
                )
    
    @abstractmethod
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> ProgressPhase:
        \"\"\"Create phase instance - implemented by subclasses\"\"\"
        pass


class BaseProgressPhase(ProgressPhase):
    \"\"\"Base phase implementation\"\"\"
    
    def __init__(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None,
        operation: BaseProgressOperation = None
    ):
        super().__init__(phase_id, title, total, description)
        self._operation = operation
        self._lock = threading.RLock()
        self.success: Optional[bool] = None
    
    def update(
        self, 
        increment: int = 1, 
        message: Optional[str] = None,
        **metadata
    ) -> None:
        \"\"\"Update progress by increment\"\"\"
        with self._lock:
            self.current += increment
            self.last_message = message
            
            if self.total and self.current >= self.total:
                self.completed_at = datetime.now()
            
            self._notify_update(message, **metadata)
    
    def set_progress(
        self, 
        current: int, 
        message: Optional[str] = None,
        **metadata
    ) -> None:
        \"\"\"Set absolute progress\"\"\"
        with self._lock:
            self.current = current
            self.last_message = message
            
            if self.total and self.current >= self.total:
                self.completed_at = datetime.now()
            
            self._notify_update(message, **metadata)
    
    def _notify_update(self, message: Optional[str] = None, **metadata) -> None:
        \"\"\"Notify tracker of progress update\"\"\"
        if self._operation and self._operation._tracker:
            self._operation._tracker._notify_callbacks(
                \"progress_update\",
                operation_id=self._operation.operation_id,
                phase_id=self.phase_id,
                current=self.current,
                total=self.total,
                percentage=self.percentage,
                message=message,
                **metadata
            )
```

**[SLIDE 8: Thread Safety Deep Dive]**

"Let me explain the thread safety features:

1. **RLock (Reentrant Lock)**: Allows the same thread to acquire the lock multiple times
2. **Lock Granularity**: Separate locks for operations and phases
3. **Callback Protection**: Errors in callbacks don't break progress tracking
4. **Atomic Updates**: All progress updates are atomic

**[QUIZ TIME]** \"Why do we use RLock instead of regular Lock? Think about nested context managers... That's right! Context managers can call each other, so we need reentrant locks.\"

## Section 4: Creating the Rich Console Adapter (15 minutes)

**[SLIDE 9: Rich Console Magic]**

"Now for the exciting part - building a beautiful console adapter using Rich library:

```python
# v2/src/infrastructure/adapters/progress/console.py

from rich.console import Console
from rich.progress import (
    Progress, TaskID, SpinnerColumn, TextColumn, 
    BarColumn, MofNCompleteColumn, TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from typing import Dict, Optional, Set
import threading

from .base import BaseProgressTracker, BaseProgressOperation, BaseProgressPhase

class ConsoleProgressTracker(BaseProgressTracker):
    \"\"\"Beautiful console progress tracking with Rich\"\"\"
    
    def __init__(self, console: Optional[Console] = None, show_spinner: bool = True):
        super().__init__()
        self.console = console or Console()
        self.show_spinner = show_spinner
        
        # Rich Progress widget
        self.progress = Progress(
            SpinnerColumn() if show_spinner else TextColumn(\"\"),
            TextColumn(\"[bold blue]{task.description}\"),
            BarColumn(bar_width=50),
            MofNCompleteColumn(),
            TextColumn(\"[bright_black]•\"),
            TimeElapsedColumn(),
            TextColumn(\"[bright_black]•\"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        
        # Track Rich task IDs
        self._rich_tasks: Dict[str, TaskID] = {}
        self._active_operations: Set[str] = set()
        
        # Live display for real-time updates
        self._live: Optional[Live] = None
        self._display_lock = threading.Lock()
    
    def _create_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> \"ConsoleProgressOperation\":
        \"\"\"Create a console-specific operation\"\"\"
        return ConsoleProgressOperation(
            operation_id, title, description, tracker=self
        )
    
    def start_operation(
        self, 
        operation_id: str, 
        title: str, 
        description: Optional[str] = None
    ) -> \"ConsoleProgressOperation\":
        \"\"\"Start operation with console display\"\"\"
        operation = super().start_operation(operation_id, title, description)
        
        with self._display_lock:
            self._active_operations.add(operation_id)
            
            # Start live display if this is the first operation
            if len(self._active_operations) == 1:
                self._start_live_display()
            
            # Show operation header
            self.console.print(
                Panel(
                    f\"[bold cyan]{title}[/bold cyan]\\n{description or ''}\",
                    title=\"🚀 Starting Operation\",
                    border_style=\"cyan\"
                )
            )
        
        return operation
    
    def finish_operation(self, operation_id: str, success: bool = True) -> None:
        \"\"\"Finish operation and clean up display\"\"\"
        super().finish_operation(operation_id, success)
        
        with self._display_lock:
            self._active_operations.discard(operation_id)
            
            # Stop live display if no more operations
            if not self._active_operations and self._live:
                self._stop_live_display()
            
            # Show completion message
            operation = self.get_operation(operation_id)
            if operation:
                status = \"✅ Completed\" if success else \"❌ Failed\"
                duration = operation.completed_at - operation.started_at
                
                self.console.print(
                    Panel(
                        f\"[bold green]{status}[/bold green] {operation.title}\\n\"
                        f\"Duration: {duration.total_seconds():.1f}s\",
                        title=\"Operation Complete\",
                        border_style=\"green\" if success else \"red\"
                    )
                )
    
    def _start_live_display(self) -> None:
        \"\"\"Start the live progress display\"\"\"
        if self._live is None:
            layout = Layout()
            layout.split_column(
                Layout(name=\"header\", size=3),
                Layout(self.progress, name=\"progress\")
            )
            
            header = Table.grid()
            header.add_row(
                Text(\"Theodore Progress\", style=\"bold cyan\"),
                Text(\"Real-time Operation Tracking\", style=\"bright_black\"),
                justify=\"left\"
            )
            layout[\"header\"].update(Panel(header, border_style=\"blue\"))
            
            self._live = Live(layout, console=self.console, refresh_per_second=10)
            self._live.start()
    
    def _stop_live_display(self) -> None:
        \"\"\"Stop the live progress display\"\"\"
        if self._live:
            self._live.stop()
            self._live = None


class ConsoleProgressOperation(BaseProgressOperation):
    \"\"\"Console-specific operation implementation\"\"\"
    
    def _create_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> \"ConsoleProgressPhase\":
        \"\"\"Create a console-specific phase\"\"\"
        return ConsoleProgressPhase(
            phase_id, title, total, description, operation=self
        )
    
    def start_phase(
        self, 
        phase_id: str, 
        title: str, 
        total: Optional[int] = None,
        description: Optional[str] = None
    ) -> \"ConsoleProgressPhase\":
        \"\"\"Start phase with Rich progress bar\"\"\"
        phase = super().start_phase(phase_id, title, total, description)
        
        # Add Rich task
        if isinstance(self._tracker, ConsoleProgressTracker):
            task_id = self._tracker.progress.add_task(
                description=title,
                total=total,
                visible=True
            )
            self._tracker._rich_tasks[phase_id] = task_id
        
        return phase
    
    def finish_phase(self, phase_id: str, success: bool = True) -> None:
        \"\"\"Finish phase and update display\"\"\"
        super().finish_phase(phase_id, success)
        
        # Remove Rich task
        if isinstance(self._tracker, ConsoleProgressTracker):
            if phase_id in self._tracker._rich_tasks:
                task_id = self._tracker._rich_tasks[phase_id]
                self._tracker.progress.remove_task(task_id)
                del self._tracker._rich_tasks[phase_id]


class ConsoleProgressPhase(BaseProgressPhase):
    \"\"\"Console-specific phase with Rich integration\"\"\"
    
    def _notify_update(self, message: Optional[str] = None, **metadata) -> None:
        \"\"\"Update Rich progress bar\"\"\"
        super()._notify_update(message, **metadata)
        
        # Update Rich task
        if (self._operation and 
            isinstance(self._operation._tracker, ConsoleProgressTracker) and
            self.phase_id in self._operation._tracker._rich_tasks):
            
            task_id = self._operation._tracker._rich_tasks[self.phase_id]
            
            # Construct description with message
            description = self.title
            if message:
                description += f\" • {message}\"
            
            self._operation._tracker.progress.update(
                task_id,
                completed=self.current,
                description=description
            )
```

**[SLIDE 10: Rich Features Breakdown]**

"Let's understand what makes this console adapter special:

1. **Live Display**: Updates in real-time without scrolling
2. **Multiple Progress Bars**: One per phase, beautifully stacked
3. **Contextual Information**: Shows time elapsed, remaining, and current message
4. **Clean Layout**: Professional panels and borders
5. **Thread-Safe**: Multiple operations can run simultaneously

**[DEMO TIME]** \"Let me show you what this looks like in action:\"

```python
# Example usage that creates beautiful output
progress = ConsoleProgressTracker()

with progress.operation(\"AI Company Research\", \"Analyzing Stripe using 4-phase scraping\") as op:
    
    # Phase 1: Link Discovery
    with op.phase(\"Link Discovery\", total=1000, \"Finding all website pages\") as phase:
        for i in range(1000):
            phase.update(1, f\"Found link #{i+1}\")
            time.sleep(0.001)  # Simulate work
    
    # Phase 2: Page Selection  
    with op.phase(\"LLM Page Selection\", total=50, \"AI selecting best pages\") as phase:
        for i in range(50):
            phase.update(1, f\"Selected page #{i+1}\")
            time.sleep(0.01)
    
    # Phase 3: Content Extraction
    with op.phase(\"Content Extraction\", total=50, \"Parallel page scraping\") as phase:
        for i in range(50):
            phase.update(1, f\"Scraped page #{i+1}\")
            time.sleep(0.02)
    
    # Phase 4: AI Analysis
    with op.phase(\"AI Analysis\", total=1, \"Business intelligence extraction\") as phase:
        phase.update(1, \"Analysis complete\")
        time.sleep(1)
```

**[PRACTICAL TIP]** \"Notice how we use meaningful messages in each update. This gives users insight into what's actually happening!\"

## Section 5: Advanced Features & Testing (12 minutes)

**[SLIDE 11: Concurrent Progress Tracking]**

"Let's test our thread-safety with concurrent operations:

```python
# v2/tests/integration/test_progress_tracking.py

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from v2.src.infrastructure.adapters.progress.console import ConsoleProgressTracker

class TestConcurrentProgress:
    
    def test_concurrent_operations(self):
        \"\"\"Test multiple operations running simultaneously\"\"\"
        tracker = ConsoleProgressTracker()
        results = []
        
        def run_operation(op_name: str, phase_count: int):
            \"\"\"Simulate a multi-phase operation\"\"\"
            with tracker.operation(f\"Operation {op_name}\") as op:
                for phase_num in range(phase_count):
                    phase_name = f\"Phase {phase_num + 1}\"
                    with op.phase(phase_name, total=10) as phase:
                        for i in range(10):
                            phase.update(1, f\"Step {i+1}\")
                            time.sleep(0.01)  # Simulate work
                
                results.append(f\"Completed {op_name}\")
        
        # Run multiple operations in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_operation, \"Alpha\", 3),
                executor.submit(run_operation, \"Beta\", 2),
                executor.submit(run_operation, \"Gamma\", 4)
            ]
            
            # Wait for completion
            for future in futures:
                future.result()
        
        # Verify all operations completed
        assert len(results) == 3
        assert \"Completed Alpha\" in results
        assert \"Completed Beta\" in results
        assert \"Completed Gamma\" in results
    
    def test_nested_progress_context_managers(self):
        \"\"\"Test deeply nested progress contexts\"\"\"
        tracker = ConsoleProgressTracker()
        
        with tracker.operation(\"Main Process\") as main_op:
            
            # Nested sub-operations
            with main_op.phase(\"Initialization\", total=3) as init_phase:
                init_phase.update(1, \"Loading config\")
                init_phase.update(1, \"Connecting to services\")
                init_phase.update(1, \"Validating credentials\")
            
            with main_op.phase(\"Data Processing\", total=100) as data_phase:
                for batch in range(10):
                    for item in range(10):
                        data_phase.update(1, f\"Processing batch {batch+1}, item {item+1}\")
                        time.sleep(0.001)
            
            with main_op.phase(\"Cleanup\", total=2) as cleanup_phase:
                cleanup_phase.update(1, \"Saving results\")
                cleanup_phase.update(1, \"Closing connections\")
        
        # Operation should complete successfully
        operation = tracker.get_operation(main_op.operation_id)
        assert operation.success is True
    
    def test_error_handling_in_progress(self):
        \"\"\"Test progress tracking handles errors gracefully\"\"\"
        tracker = ConsoleProgressTracker()
        
        with pytest.raises(ValueError):
            with tracker.operation(\"Error Test\") as op:
                with op.phase(\"Normal Phase\", total=5) as phase:
                    phase.update(2, \"Processing\")
                    phase.update(2, \"Almost done\")
                    # Simulate error
                    raise ValueError(\"Something went wrong!\")
        
        # Operation should be marked as failed
        operation = tracker.get_operation(op.operation_id)
        assert operation.success is False
    
    def test_progress_callbacks(self):
        \"\"\"Test progress event callbacks\"\"\"
        tracker = ConsoleProgressTracker()
        events = []
        
        def capture_events(event_type: str, **data):
            events.append({\"type\": event_type, \"data\": data})
        
        tracker.add_callback(capture_events)
        
        with tracker.operation(\"Callback Test\") as op:
            with op.phase(\"Test Phase\", total=3) as phase:
                phase.update(1, \"Step 1\")
                phase.update(1, \"Step 2\")
                phase.update(1, \"Step 3\")
        
        # Verify events were captured
        event_types = [event[\"type\"] for event in events]
        assert \"operation_started\" in event_types
        assert \"phase_started\" in event_types
        assert \"progress_update\" in event_types
        assert \"phase_finished\" in event_types
        assert \"operation_finished\" in event_types
        
        # Verify progress updates
        progress_events = [e for e in events if e[\"type\"] == \"progress_update\"]
        assert len(progress_events) == 3
        assert progress_events[-1][\"data\"][\"current\"] == 3
```

**[SLIDE 12: Performance Monitoring Integration]**

"Let's add performance monitoring capabilities:

```python
# Enhanced progress phase with performance tracking

class PerformanceTrackingPhase(BaseProgressPhase):
    \"\"\"Progress phase with built-in performance monitoring\"\"\"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_data = {
            \"items_per_second\": 0.0,
            \"average_time_per_item\": 0.0,
            \"peak_items_per_second\": 0.0,
            \"estimated_completion\": None
        }
        self._last_update_time = time.time()
        self._update_times = []
    
    def update(self, increment: int = 1, message: Optional[str] = None, **metadata):
        \"\"\"Update with performance tracking\"\"\"
        current_time = time.time()
        
        # Calculate performance metrics
        if hasattr(self, '_last_update_time'):
            time_diff = current_time - self._last_update_time
            if time_diff > 0:
                current_rate = increment / time_diff
                self.performance_data[\"items_per_second\"] = current_rate
                
                # Track peak performance
                if current_rate > self.performance_data[\"peak_items_per_second\"]:
                    self.performance_data[\"peak_items_per_second\"] = current_rate
        
        self._last_update_time = current_time
        
        # Estimate completion time
        if self.total and self.current < self.total:
            remaining = self.total - self.current
            if self.performance_data[\"items_per_second\"] > 0:
                seconds_remaining = remaining / self.performance_data[\"items_per_second\"]
                self.performance_data[\"estimated_completion\"] = (
                    datetime.now() + timedelta(seconds=seconds_remaining)
                )
        
        # Enhanced message with performance
        if self.performance_data[\"items_per_second\"] > 0:
            enhanced_message = f\"{message or ''} ({self.performance_data['items_per_second']:.1f}/sec)\"
        else:
            enhanced_message = message
        
        super().update(increment, enhanced_message, 
                      performance=self.performance_data, **metadata)


# Usage example with performance tracking
def scrape_with_performance_tracking():
    progress = ConsoleProgressTracker()
    
    with progress.operation(\"High-Performance Scraping\") as op:
        with op.phase(\"URL Processing\", total=1000) as phase:
            for url in urls:
                start_time = time.time()
                
                # Do the actual work
                result = process_url(url)
                
                # Update with timing information
                processing_time = time.time() - start_time
                phase.update(1, 
                    f\"Processed {url}\",
                    processing_time=processing_time,
                    result_size=len(result)
                )
```

**[SLIDE 13: Web Integration Preparation]**

"Let's prepare our system for future web integration:

```python
# Progress event serialization for web APIs

import json
from datetime import datetime
from typing import Dict, Any

class ProgressEventSerializer:
    \"\"\"Serialize progress events for web consumption\"\"\"
    
    @staticmethod
    def serialize_event(event_type: str, **data) -> str:
        \"\"\"Convert progress event to JSON\"\"\"
        
        # Clean up data for JSON serialization
        cleaned_data = ProgressEventSerializer._clean_data(data)
        
        event = {
            \"type\": event_type,
            \"timestamp\": datetime.now().isoformat(),
            \"data\": cleaned_data
        }
        
        return json.dumps(event)
    
    @staticmethod
    def _clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Clean data for JSON serialization\"\"\"
        cleaned = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (int, float, str, bool, type(None))):
                cleaned[key] = value
            elif isinstance(value, dict):
                cleaned[key] = ProgressEventSerializer._clean_data(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    ProgressEventSerializer._clean_data({\"item\": item})[\"item\"] 
                    if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                cleaned[key] = str(value)
        
        return cleaned


# WebSocket-ready progress adapter
class WebSocketProgressTracker(BaseProgressTracker):
    \"\"\"Progress tracker that emits WebSocket events\"\"\"
    
    def __init__(self, websocket_handler=None):
        super().__init__()
        self.websocket_handler = websocket_handler
        
        # Add serialization callback
        self.add_callback(self._emit_websocket_event)
    
    def _emit_websocket_event(self, event_type: str, **data):
        \"\"\"Emit progress event via WebSocket\"\"\"
        if self.websocket_handler:
            serialized = ProgressEventSerializer.serialize_event(event_type, **data)
            self.websocket_handler.emit(\"progress_update\", serialized)
    
    def _create_operation(self, operation_id: str, title: str, description: Optional[str] = None):
        return WebSocketProgressOperation(operation_id, title, description, tracker=self)


# This prepares us for future web integration!
```

## Section 6: Real-World Integration (8 minutes)

**[SLIDE 14: Integrating with Theodore's Scraping Pipeline]**

"Let's see how to integrate our progress system with Theodore's actual scraping pipeline:

```python
# Modified intelligent scraper with progress integration

class IntelligentCompanyScraperWithProgress:
    \"\"\"Enhanced scraper with beautiful progress tracking\"\"\"
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        # ... other initialization
    
    async def scrape_company(self, company_name: str, website_url: str) -> CompanyData:
        \"\"\"4-phase scraping with real-time progress\"\"\"
        
        with self.progress_tracker.operation(
            f\"Researching {company_name}\",
            f\"4-phase intelligent scraping of {website_url}\"
        ) as operation:
            
            # Phase 1: Link Discovery
            links = await self._phase_1_link_discovery(operation, website_url)
            
            # Phase 2: LLM Page Selection
            selected_pages = await self._phase_2_page_selection(operation, links)
            
            # Phase 3: Content Extraction
            page_contents = await self._phase_3_content_extraction(operation, selected_pages)
            
            # Phase 4: AI Analysis
            company_data = await self._phase_4_ai_analysis(operation, page_contents, company_name)
            
            return company_data
    
    async def _phase_1_link_discovery(self, operation: ProgressOperation, website_url: str):
        \"\"\"Phase 1 with progress tracking\"\"\"
        
        with operation.phase(\"Link Discovery\", total=3, \"Finding all website pages\") as phase:
            
            # Step 1: robots.txt
            phase.update(0, \"Parsing robots.txt\")
            robots_links = await self._parse_robots_txt(website_url)
            phase.update(1, f\"Found {len(robots_links)} links from robots.txt\")
            
            # Step 2: sitemap.xml  
            phase.update(0, \"Parsing sitemap.xml\")
            sitemap_links = await self._parse_sitemap(website_url)
            phase.update(1, f\"Found {len(sitemap_links)} links from sitemap\")
            
            # Step 3: recursive crawling
            phase.update(0, \"Recursive web crawling (3 levels deep)\")
            crawled_links = await self._recursive_crawl(website_url)
            phase.update(1, f\"Discovered {len(crawled_links)} additional links\")
            
            # Combine and deduplicate
            all_links = list(set(robots_links + sitemap_links + crawled_links))
            phase.set_progress(3, f\"Total unique links discovered: {len(all_links)}\")
            
            return all_links
    
    async def _phase_2_page_selection(self, operation: ProgressOperation, links: List[str]):
        \"\"\"Phase 2: LLM-driven page selection\"\"\"
        
        with operation.phase(\"LLM Page Selection\", total=1, \"AI selecting most valuable pages\") as phase:
            
            phase.update(0, f\"Analyzing {len(links)} links with Gemini 2.5 Pro\")
            
            # Use LLM to select best pages
            selected_pages = await self._llm_select_pages(links)
            
            phase.update(1, f\"Selected {len(selected_pages)} high-value pages\")
            
            return selected_pages
    
    async def _phase_3_content_extraction(self, operation: ProgressOperation, pages: List[str]):
        \"\"\"Phase 3: Parallel content extraction\"\"\"
        
        with operation.phase(\"Content Extraction\", total=len(pages), \"Parallel page scraping\") as phase:
            
            contents = {}
            semaphore = asyncio.Semaphore(10)  # Limit concurrency
            
            async def extract_single_page(url: str):
                async with semaphore:
                    try:
                        content = await self._extract_page_content(url)
                        contents[url] = content
                        phase.update(1, f\"✅ Extracted {url}\")
                    except Exception as e:
                        phase.update(1, f\"❌ Failed {url}: {str(e)[:50]}\")
            
            # Run all extractions in parallel
            await asyncio.gather(*[extract_single_page(url) for url in pages])
            
            phase.set_progress(len(pages), f\"Extracted content from {len(contents)} pages\")
            
            return contents
    
    async def _phase_4_ai_analysis(self, operation: ProgressOperation, contents: Dict, company_name: str):
        \"\"\"Phase 4: AI content aggregation\"\"\"
        
        with operation.phase(\"AI Analysis\", total=4, \"Business intelligence extraction\") as phase:
            
            # Step 1: Combine content
            phase.update(1, \"Combining content from all pages\")
            combined_content = self._combine_page_contents(contents)
            
            # Step 2: Generate business analysis
            phase.update(1, \"Generating business intelligence with Gemini 2.5 Pro\")
            business_analysis = await self._analyze_with_gemini(combined_content, company_name)
            
            # Step 3: Extract structured fields
            phase.update(1, \"Extracting structured fields with Nova Pro\")
            structured_data = await self._extract_structured_fields(business_analysis)
            
            # Step 4: Generate embeddings
            phase.update(1, \"Generating embeddings for similarity search\")
            embeddings = await self._generate_embeddings(structured_data)
            
            # Create final company data
            company_data = CompanyData(
                name=company_name,
                **structured_data,
                embedding=embeddings
            )
            
            phase.set_progress(4, \"✅ Analysis complete - company data ready\")
            
            return company_data
```

**[SLIDE 15: CLI Integration]**

"Here's how it works from the command line:

```bash
# Beautiful CLI progress in action
$ theodore research \"Stripe\" \"https://stripe.com\"

🚀 Starting Operation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Researching Stripe
  4-phase intelligent scraping of https://stripe.com

  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ 🔍 Link Discovery • Found 847 unique links          ██████████ 100% ┃
  ┃ 🧠 LLM Page Selection • Selected 43 high-value pages █████████ 100% ┃  
  ┃ 📄 Content Extraction • Extracted from 41 pages     ████████ 95%   ┃
  ┃ 🧠 AI Analysis • Generating embeddings               ███████ 75%    ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  
  ⏱️  Elapsed: 00:23 • Remaining: 00:06 • 2.1 pages/sec
```

**[SLIDE 16: Configuration & Customization]**

"Make progress tracking configurable:

```python
# v2/config/progress.yaml
progress:
  console:
    enabled: true
    show_spinner: true
    show_percentage: true
    show_time_remaining: true
    bar_width: 50
    refresh_rate: 10  # updates per second
    
  websocket:
    enabled: false
    endpoint: \"ws://localhost:8000/progress\"
    
  logging:
    enabled: true
    level: \"INFO\"
    include_performance_metrics: true
    
  performance:
    track_items_per_second: true
    track_memory_usage: false
    estimate_completion_time: true


# Load configuration
from v2.src.infrastructure.config.settings import get_settings

def create_progress_tracker() -> ProgressTracker:
    settings = get_settings()
    
    if settings.progress.console.enabled:
        return ConsoleProgressTracker(
            show_spinner=settings.progress.console.show_spinner,
            refresh_rate=settings.progress.console.refresh_rate
        )
    elif settings.progress.websocket.enabled:
        return WebSocketProgressTracker(
            endpoint=settings.progress.websocket.endpoint
        )
    else:
        return NoOpProgressTracker()  # Silent mode
```

## Section 7: Production Best Practices (5 minutes)

**[SLIDE 17: Production Checklist]**

"Before deploying progress tracking to production:

### 1. **Performance Considerations**
```python
# Limit update frequency to avoid overwhelming the UI
class ThrottledProgressPhase(BaseProgressPhase):
    def __init__(self, *args, min_update_interval=0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_update_interval = min_update_interval
        self._last_ui_update = 0
    
    def update(self, increment: int = 1, message: Optional[str] = None, **metadata):
        # Always update internal state
        super().update(increment, message, **metadata)
        
        # But throttle UI updates
        current_time = time.time()
        if current_time - self._last_ui_update >= self.min_update_interval:
            self._notify_update(message, **metadata)
            self._last_ui_update = current_time
```

### 2. **Memory Management**
```python
# Clean up completed operations to prevent memory leaks
class MemoryEfficientProgressTracker(BaseProgressTracker):
    def __init__(self, max_completed_operations=100):
        super().__init__()
        self.max_completed_operations = max_completed_operations
    
    def finish_operation(self, operation_id: str, success: bool = True):
        super().finish_operation(operation_id, success)
        
        # Clean up old completed operations
        completed_ops = [
            op_id for op_id, op in self._operations.items()
            if hasattr(op, 'completed_at') and op.completed_at is not None
        ]
        
        if len(completed_ops) > self.max_completed_operations:
            # Remove oldest completed operations
            oldest_ops = sorted(
                completed_ops,
                key=lambda op_id: self._operations[op_id].completed_at
            )[:-self.max_completed_operations]
            
            for op_id in oldest_ops:
                del self._operations[op_id]
```

### 3. **Error Recovery**
```python
# Graceful error handling
class ResilientProgressTracker(BaseProgressTracker):
    def _notify_callbacks(self, event_type: str, **data):
        \"\"\"Notify callbacks with error isolation\"\"\"
        for callback in self._callbacks:
            try:
                callback(event_type=event_type, **data)
            except Exception as e:
                # Log error but don't let it break progress tracking
                logger.error(f\"Progress callback failed: {e}\")
                # Optionally remove failing callbacks
                if hasattr(callback, '_error_count'):
                    callback._error_count += 1
                    if callback._error_count > 3:
                        self.remove_callback(callback)
                else:
                    callback._error_count = 1
```

### 4. **Monitoring Integration**
```python
# OpenTelemetry integration
from opentelemetry import trace

class ObservableProgressTracker(BaseProgressTracker):
    def __init__(self):
        super().__init__()
        self.tracer = trace.get_tracer(__name__)
    
    def start_operation(self, operation_id: str, title: str, description: Optional[str] = None):
        with self.tracer.start_as_current_span(\"progress_operation\") as span:
            span.set_attribute(\"operation.id\", operation_id)
            span.set_attribute(\"operation.title\", title)
            return super().start_operation(operation_id, title, description)
```

## Conclusion (3 minutes)

**[SLIDE 18: What We Built]**

"Congratulations! You've built a production-ready progress tracking system that's:

✅ **Thread-Safe**: Handles concurrent operations flawlessly
✅ **Beautiful**: Rich console output that users love
✅ **Extensible**: Port/Adapter pattern for any output format
✅ **Performance-Aware**: Built-in metrics and throttling
✅ **Production-Ready**: Memory management and error recovery

**[SLIDE 19: Next Steps]**

Your homework:
1. Add a WebSocket adapter for real-time web progress
2. Implement progress persistence (resume after crashes)
3. Create a dashboard adapter for monitoring multiple operations
4. Add progress analytics and reporting

**[FINAL THOUGHT]**
"Remember, great progress tracking is about user experience. When users can see what's happening and how long it will take, they trust your application. That's the difference between professional software and amateur tools.

Thank you for joining me in building something that makes software feel alive and responsive!"

---

## Instructor Notes:
- Total runtime: ~60 minutes
- Emphasize the importance of user experience in long-running operations
- Live demo the Rich progress bars - they're visually stunning
- Include downloadable code templates for all adapters
- Consider follow-up video on WebSocket real-time progress for web apps