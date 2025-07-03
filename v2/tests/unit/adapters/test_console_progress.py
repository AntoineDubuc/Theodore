"""
Unit tests for console progress tracking adapters.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.adapters.progress.console import (
    ConsoleProgressTracker,
    LoggingProgressTracker
)
from src.infrastructure.adapters.progress.base import (
    NoOpProgressTracker
)
from src.core.ports.progress import ProgressEventType


class TestConsoleProgressTracker:
    """Test ConsoleProgressTracker functionality"""
    
    def test_initialization(self):
        """Test tracker initialization"""
        tracker = ConsoleProgressTracker()
        
        assert tracker.console is not None
        assert tracker.show_spinner is True
        assert tracker.show_speed is True
        assert tracker.refresh_per_second == 10
        assert len(tracker._active_operations) == 0
        assert len(tracker._rich_tasks) == 0
    
    def test_initialization_with_custom_params(self):
        """Test tracker initialization with custom parameters"""
        console = Mock()
        tracker = ConsoleProgressTracker(
            console=console,
            show_spinner=False,
            show_speed=False,
            refresh_per_second=5
        )
        
        assert tracker.console is console
        assert tracker.show_spinner is False
        assert tracker.show_speed is False
        assert tracker.refresh_per_second == 5
    
    @patch('src.infrastructure.adapters.progress.console.Live')
    def test_operation_lifecycle(self, mock_live_class):
        """Test complete operation lifecycle"""
        mock_live = Mock()
        mock_live_class.return_value = mock_live
        
        tracker = ConsoleProgressTracker()
        
        # Start operation
        operation = tracker.start_operation("test-op", "Test Operation", "Testing")
        
        assert operation.operation_id == "test-op"
        assert operation.title == "Test Operation"
        assert operation.description == "Testing"
        assert "test-op" in tracker._active_operations
        
        # Verify live display started
        mock_live_class.assert_called_once()
        mock_live.start.assert_called_once()
        
        # Get operation
        retrieved = tracker.get_operation("test-op")
        assert retrieved is operation
        
        # Finish operation
        tracker.finish_operation("test-op", success=True)
        
        assert operation.is_complete
        assert operation.success is True
        assert "test-op" not in tracker._active_operations
        
        # Verify live display stopped
        mock_live.stop.assert_called_once()
    
    def test_multiple_concurrent_operations(self):
        """Test multiple operations running concurrently"""
        tracker = ConsoleProgressTracker()
        
        # Start multiple operations
        op1 = tracker.start_operation("op1", "Operation 1")
        op2 = tracker.start_operation("op2", "Operation 2") 
        op3 = tracker.start_operation("op3", "Operation 3")
        
        assert len(tracker._active_operations) == 3
        assert tracker.get_operation("op1") is op1
        assert tracker.get_operation("op2") is op2
        assert tracker.get_operation("op3") is op3
        
        # Finish operations out of order
        tracker.finish_operation("op2", success=True)
        assert len(tracker._active_operations) == 2
        
        tracker.finish_operation("op1", success=False)
        assert len(tracker._active_operations) == 1
        
        tracker.finish_operation("op3", success=True)
        assert len(tracker._active_operations) == 0
    
    def test_phase_lifecycle_with_rich_tasks(self):
        """Test phase lifecycle with Rich task management"""
        tracker = ConsoleProgressTracker()
        
        with tracker.operation("Test Operation") as op:
            # Start phase
            phase = op.start_phase("phase1", "Test Phase", total=100)
            
            assert "phase1" in tracker._rich_tasks
            task_id = tracker._rich_tasks["phase1"]
            
            # Update progress
            phase.update(10, "Processing...")
            assert phase.current == 10
            
            phase.update(20, "Still processing...")
            assert phase.current == 30
            
            # Set absolute progress
            phase.set_progress(50, "Halfway done")
            assert phase.current == 50
            
            # Finish phase
            op.finish_phase("phase1", success=True)
            
            # Rich task should be removed
            assert "phase1" not in tracker._rich_tasks
    
    def test_context_manager_success(self):
        """Test successful operation using context manager"""
        tracker = ConsoleProgressTracker()
        events = []
        
        def capture_events(event_type, **data):
            events.append({"type": event_type, "data": data})
        
        tracker.add_callback(capture_events)
        
        with tracker.operation("Context Test") as op:
            with op.phase("Phase 1", total=3) as phase:
                phase.update(1, "Step 1")
                phase.update(1, "Step 2") 
                phase.update(1, "Step 3")
        
        # Verify events
        event_types = [e["type"] for e in events]
        assert ProgressEventType.OPERATION_STARTED in event_types
        assert ProgressEventType.PHASE_STARTED in event_types
        assert ProgressEventType.PHASE_UPDATED in event_types
        assert ProgressEventType.PHASE_FINISHED in event_types
        assert ProgressEventType.OPERATION_FINISHED in event_types
        
        # Check final states
        operation_finished_events = [
            e for e in events 
            if e["type"] == ProgressEventType.OPERATION_FINISHED
        ]
        assert len(operation_finished_events) == 1
        assert operation_finished_events[0]["data"]["success"] is True
    
    def test_context_manager_with_error(self):
        """Test operation context manager with error handling"""
        tracker = ConsoleProgressTracker()
        events = []
        
        def capture_events(event_type, **data):
            events.append({"type": event_type, "data": data})
        
        tracker.add_callback(capture_events)
        
        with pytest.raises(ValueError):
            with tracker.operation("Error Test") as op:
                with op.phase("Phase 1", total=2) as phase:
                    phase.update(1, "Step 1")
                    raise ValueError("Test error")
        
        # Check that operation was marked as failed
        operation_finished_events = [
            e for e in events 
            if e["type"] == ProgressEventType.OPERATION_FINISHED
        ]
        assert len(operation_finished_events) == 1
        assert operation_finished_events[0]["data"]["success"] is False
    
    def test_callback_management(self):
        """Test callback addition and removal"""
        tracker = ConsoleProgressTracker()
        
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        tracker.add_callback(callback1)
        tracker.add_callback(callback2)
        
        # Start operation to trigger callbacks
        tracker.start_operation("test", "Test")
        
        callback1.assert_called_once()
        callback2.assert_called_once()
        
        # Remove one callback
        tracker.remove_callback(callback1)
        callback1.reset_mock()
        callback2.reset_mock()
        
        # Finish operation
        tracker.finish_operation("test", success=True)
        
        callback1.assert_not_called()
        callback2.assert_called_once()
    
    def test_callback_error_handling(self):
        """Test that callback errors don't break progress tracking"""
        tracker = ConsoleProgressTracker()
        
        # Create callbacks - one that works, one that fails
        good_callback = Mock()
        bad_callback = Mock(side_effect=Exception("Callback error"))
        
        tracker.add_callback(good_callback)
        tracker.add_callback(bad_callback)
        
        # Should not raise exception despite bad callback
        tracker.start_operation("test", "Test")
        
        # Good callback should still be called
        good_callback.assert_called_once()
        bad_callback.assert_called_once()
        
        # Bad callback should be removed after multiple failures
        for i in range(3):
            tracker.start_operation(f"test{i}", f"Test {i}")
        
        # Bad callback should be removed from the list
        assert bad_callback not in tracker._callbacks
        assert good_callback in tracker._callbacks
    
    def test_thread_safety(self):
        """Test thread safety with concurrent operations"""
        tracker = ConsoleProgressTracker()
        results = []
        errors = []
        
        def run_operation(op_id: str):
            """Run a simple operation"""
            try:
                with tracker.operation(f"Operation {op_id}") as op:
                    with op.phase(f"Phase {op_id}", total=10) as phase:
                        for i in range(10):
                            phase.update(1, f"Step {i+1}")
                            time.sleep(0.001)  # Simulate work
                
                results.append(op_id)
            except Exception as e:
                errors.append((op_id, e))
        
        # Run multiple operations concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(run_operation, f"op{i}")
                for i in range(10)
            ]
            
            # Wait for completion
            for future in futures:
                future.result()
        
        # Verify all operations completed successfully
        assert len(results) == 10
        assert len(errors) == 0
        assert len(tracker._active_operations) == 0
    
    def test_performance_tracking(self):
        """Test performance metrics calculation"""
        tracker = ConsoleProgressTracker()
        
        with tracker.operation("Performance Test") as op:
            with op.phase("Fast Phase", total=100) as phase:
                start_time = time.time()
                
                for i in range(100):
                    phase.update(1, f"Item {i+1}")
                    if i % 10 == 0:  # Check performance occasionally
                        time.sleep(0.001)  # Small delay
                
                end_time = time.time()
                
                # Verify performance metrics
                assert phase.items_per_second > 0
                assert phase.duration is not None
                assert phase.duration <= (end_time - start_time) + 0.1  # Small tolerance


class TestLoggingProgressTracker:
    """Test LoggingProgressTracker functionality"""
    
    @patch('src.infrastructure.adapters.progress.console.logging.getLogger')
    def test_logging_initialization(self, mock_get_logger):
        """Test logging tracker initialization"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        tracker = LoggingProgressTracker("test.logger", level=30)
        
        assert tracker.level == 30
        mock_get_logger.assert_called_once_with("test.logger")
    
    @patch('src.infrastructure.adapters.progress.console.logging.getLogger')
    def test_logging_operation_lifecycle(self, mock_get_logger):
        """Test operation lifecycle with logging"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        tracker = LoggingProgressTracker()
        
        with tracker.operation("Log Test", "Test operation") as op:
            with op.phase("Log Phase", total=3) as phase:
                phase.update(1, "Step 1")
                phase.update(1, "Step 2")
                phase.update(1, "Step 3")
        
        # Verify logging calls
        assert mock_logger.log.call_count >= 4  # Start op, start phase, finish phase, finish op
        
        # Check some specific log messages
        log_calls = [call[0] for call in mock_logger.log.call_args_list]
        log_messages = [call[1] for call in log_calls]
        
        # Should have logged operation start and completion
        assert any("Started operation: Log Test" in msg for msg in log_messages)
        assert any("Completed operation: Log Test" in msg for msg in log_messages)


class TestNoOpProgressTracker:
    """Test NoOpProgressTracker functionality"""
    
    def test_no_op_tracker_silent(self):
        """Test that no-op tracker produces no output"""
        tracker = NoOpProgressTracker()
        
        # Should work normally but produce no output
        with tracker.operation("Silent Test") as op:
            with op.phase("Silent Phase", total=100) as phase:
                for i in range(100):
                    phase.update(1, f"Item {i+1}")
        
        # No way to test silence directly, but should not crash
        assert True
    
    def test_no_op_tracker_functionality(self):
        """Test that no-op tracker maintains functionality"""
        tracker = NoOpProgressTracker()
        
        # Test basic functionality still works
        operation = tracker.start_operation("test", "Test")
        assert operation.operation_id == "test"
        assert operation.title == "Test"
        
        phase = operation.start_phase("phase1", "Phase", total=10)
        assert phase.phase_id == "phase1"
        assert phase.title == "Phase"
        assert phase.total == 10
        
        phase.update(5, "Halfway")
        assert phase.current == 5
        assert phase.percentage == 50.0
        
        operation.finish_phase("phase1", success=True)
        tracker.finish_operation("test", success=True)
        
        assert operation.is_complete
        assert operation.success is True
        assert phase.is_complete
        assert phase.success is True


class TestProgressAdapterIntegration:
    """Test integration between different progress adapters"""
    
    def test_adapter_switching(self):
        """Test switching between different progress adapters"""
        from src.infrastructure.adapters.progress import create_progress_tracker
        
        # Test console tracker creation
        console_tracker = create_progress_tracker("console", show_spinner=False)
        assert isinstance(console_tracker, ConsoleProgressTracker)
        assert console_tracker.show_spinner is False
        
        # Test logging tracker creation
        logging_tracker = create_progress_tracker("logging", level=10)
        assert isinstance(logging_tracker, LoggingProgressTracker)
        assert logging_tracker.level == 10
        
        # Test silent tracker creation
        silent_tracker = create_progress_tracker("silent")
        assert isinstance(silent_tracker, NoOpProgressTracker)
        
        # Test invalid mode
        with pytest.raises(ValueError):
            create_progress_tracker("invalid_mode")
    
    def test_adapter_polymorphism(self):
        """Test that all adapters implement the same interface"""
        from src.infrastructure.adapters.progress import create_progress_tracker
        
        adapters = [
            create_progress_tracker("console"),
            create_progress_tracker("logging"),
            create_progress_tracker("silent")
        ]
        
        # All should implement the same basic interface
        for adapter in adapters:
            # Test operation creation
            with adapter.operation("Polymorphism Test") as op:
                with op.phase("Test Phase", total=5) as phase:
                    for i in range(5):
                        phase.update(1, f"Step {i+1}")
            
            # Should all complete successfully
            assert True  # No exceptions means success