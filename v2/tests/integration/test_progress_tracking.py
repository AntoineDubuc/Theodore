"""
Integration tests for progress tracking system.

These tests verify that the progress tracking system works correctly
in realistic scenarios with actual timing, concurrency, and complex
operation hierarchies.
"""

import pytest
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from src.infrastructure.adapters.progress import create_progress_tracker
from src.core.ports.progress import ProgressEventType


class TestProgressTrackingIntegration:
    """Integration tests for complete progress tracking workflows"""
    
    def test_simulated_company_research_workflow(self):
        """Test progress tracking for a simulated company research workflow"""
        tracker = create_progress_tracker("console", show_spinner=True)
        events = []
        
        def capture_events(event_type, **data):
            events.append({
                "type": event_type,
                "timestamp": time.time(),
                "data": data
            })
        
        tracker.add_callback(capture_events)
        
        # Simulate Theodore's 4-phase company research
        with tracker.operation(
            "Researching Stripe Inc.", 
            "4-phase intelligent scraping of https://stripe.com"
        ) as operation:
            
            # Phase 1: Link Discovery
            with operation.phase("Link Discovery", total=1000, "Finding all website pages") as phase:
                # Simulate discovering links
                for i in range(100):  # Reduced for testing
                    phase.update(10, f"Found {(i+1)*10} links")
                    time.sleep(0.001)  # Simulate I/O
            
            # Phase 2: LLM Page Selection
            with operation.phase("LLM Page Selection", total=50, "AI selecting most valuable pages") as phase:
                # Simulate LLM processing
                phase.update(0, "Analyzing discovered links with Gemini 2.5 Pro")
                time.sleep(0.1)  # Simulate AI processing
                
                for i in range(50):
                    phase.update(1, f"Selected page {i+1}/50")
                    time.sleep(0.002)  # Simulate selection
            
            # Phase 3: Content Extraction  
            with operation.phase("Content Extraction", total=50, "Parallel page scraping") as phase:
                # Simulate parallel extraction
                for i in range(50):
                    page_url = f"https://stripe.com/page-{i+1}"
                    phase.update(1, f"✅ Extracted {page_url}")
                    time.sleep(0.005)  # Simulate network I/O
            
            # Phase 4: AI Analysis
            with operation.phase("AI Analysis", total=4, "Business intelligence extraction") as phase:
                phase.update(1, "Combining content from all pages")
                time.sleep(0.05)
                
                phase.update(1, "Generating business intelligence with Gemini 2.5 Pro")
                time.sleep(0.1)
                
                phase.update(1, "Extracting structured fields with Nova Pro")
                time.sleep(0.05)
                
                phase.update(1, "Generating embeddings for similarity search")
                time.sleep(0.03)
        
        # Verify the workflow completed successfully
        operation_finished_events = [
            e for e in events if e["type"] == ProgressEventType.OPERATION_FINISHED
        ]
        assert len(operation_finished_events) == 1
        assert operation_finished_events[0]["data"]["success"] is True
        
        # Verify all phases completed
        phase_finished_events = [
            e for e in events if e["type"] == ProgressEventType.PHASE_FINISHED
        ]
        assert len(phase_finished_events) == 4
        
        # Verify performance metrics
        assert operation.duration > 0
        for phase in operation.phases.values():
            assert phase.items_per_second >= 0
            assert phase.is_complete
    
    def test_concurrent_company_research(self):
        """Test multiple concurrent company research operations"""
        tracker = create_progress_tracker("console")
        results = []
        errors = []
        
        companies = [
            ("Stripe", "https://stripe.com"),
            ("Square", "https://squareup.com"),
            ("PayPal", "https://paypal.com"),
            ("Shopify", "https://shopify.com"),
            ("Twilio", "https://twilio.com")
        ]
        
        def research_company(company_name: str, website_url: str):
            """Simulate researching a single company"""
            try:
                with tracker.operation(
                    f"Researching {company_name}",
                    f"AI analysis of {website_url}"
                ) as op:
                    
                    # Quick discovery phase
                    with op.phase("Discovery", total=100) as phase:
                        for i in range(100):
                            phase.update(1, f"Found link {i+1}")
                            time.sleep(0.001)
                    
                    # Analysis phase
                    with op.phase("Analysis", total=1) as phase:
                        phase.update(1, "Business intelligence extracted")
                        time.sleep(0.05)
                
                results.append(company_name)
                
            except Exception as e:
                errors.append((company_name, str(e)))
        
        # Run concurrent research
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(research_company, name, url): name
                for name, url in companies
            }
            
            for future in as_completed(futures):
                company_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    errors.append((company_name, str(e)))
        
        # Verify results
        assert len(results) == 5
        assert len(errors) == 0
        assert set(results) == {name for name, _ in companies}
        
        # Verify no active operations remain
        assert len(tracker.get_active_operations()) == 0
    
    def test_error_recovery_and_reporting(self):
        """Test progress tracking handles errors gracefully"""
        tracker = create_progress_tracker("console")
        events = []
        
        def capture_events(event_type, **data):
            events.append({"type": event_type, "data": data})
        
        tracker.add_callback(capture_events)
        
        # Test operation that fails
        with pytest.raises(ValueError):
            with tracker.operation("Error Test Operation") as op:
                with op.phase("Normal Phase", total=5) as phase:
                    phase.update(2, "Processing normally")
                    phase.update(1, "Still working")
                    
                    # Add some errors and warnings
                    phase.add_error("Connection timeout to server")
                    phase.add_warning("Slow response from API")
                    
                    # Simulate failure
                    raise ValueError("Critical system error")
        
        # Verify operation was marked as failed
        operation_finished_events = [
            e for e in events if e["type"] == ProgressEventType.OPERATION_FINISHED
        ]
        assert len(operation_finished_events) == 1
        assert operation_finished_events[0]["data"]["success"] is False
        
        # Test operation that recovers from errors
        with tracker.operation("Recovery Test Operation") as op:
            with op.phase("Error-Prone Phase", total=10) as phase:
                for i in range(10):
                    if i == 3:
                        phase.add_error("Temporary network error")
                    elif i == 7:
                        phase.add_warning("Rate limit approaching")
                    else:
                        phase.update(1, f"Successfully processed item {i+1}")
        
        # Verify recovery operation succeeded
        recovery_events = [
            e for e in events if e["type"] == ProgressEventType.OPERATION_FINISHED
        ][-1]  # Get the last finished operation
        assert recovery_events["data"]["success"] is True
    
    def test_nested_operation_hierarchy(self):
        """Test deeply nested progress operations"""
        tracker = create_progress_tracker("console")
        
        with tracker.operation("Batch Processing") as main_op:
            
            # Initialization phase
            with main_op.phase("Initialization", total=3) as init_phase:
                init_phase.update(1, "Loading configuration")
                time.sleep(0.01)
                
                init_phase.update(1, "Connecting to services")
                time.sleep(0.01)
                
                init_phase.update(1, "Validating credentials")
                time.sleep(0.01)
            
            # Main processing phase with sub-batches
            with main_op.phase("Batch Processing", total=100) as batch_phase:
                batch_size = 10
                for batch_num in range(10):
                    batch_start = batch_num * batch_size
                    
                    for item_num in range(batch_size):
                        global_item = batch_start + item_num + 1
                        batch_phase.update(
                            1, 
                            f"Processing batch {batch_num+1}/10, item {item_num+1}/{batch_size}"
                        )
                        time.sleep(0.001)
            
            # Finalization phase
            with main_op.phase("Finalization", total=2) as final_phase:
                final_phase.update(1, "Saving results")
                time.sleep(0.02)
                
                final_phase.update(1, "Cleanup and close connections")
                time.sleep(0.01)
        
        # Verify all phases completed
        assert len(main_op.phases) == 3
        for phase in main_op.phases.values():
            assert phase.is_complete
            assert phase.success is True
    
    def test_progress_performance_monitoring(self):
        """Test progress tracking performance under load"""
        tracker = create_progress_tracker("console")
        
        # Track performance metrics
        start_time = time.time()
        update_count = 0
        
        def count_updates(event_type, **data):
            nonlocal update_count
            if event_type == ProgressEventType.PHASE_UPDATED:
                update_count += 1
        
        tracker.add_callback(count_updates)
        
        # High-frequency updates test
        with tracker.operation("Performance Test") as op:
            with op.phase("High-Frequency Updates", total=1000) as phase:
                for i in range(1000):
                    phase.update(1, f"High-speed item {i+1}")
                    # No sleep - test maximum update rate
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance
        assert duration < 2.0  # Should complete quickly
        assert update_count > 0  # Should have captured updates
        
        # Verify progress metrics
        for phase in op.phases.values():
            assert phase.items_per_second > 0
            assert phase.duration is not None
    
    @pytest.mark.asyncio
    async def test_async_operation_simulation(self):
        """Test progress tracking with async operations"""
        tracker = create_progress_tracker("console")
        
        async def async_work_simulation():
            """Simulate async work with progress tracking"""
            
            with tracker.operation("Async Data Processing") as op:
                
                # Simulate async I/O operations
                with op.phase("Data Fetching", total=5) as phase:
                    for i in range(5):
                        # Simulate async network call
                        await asyncio.sleep(0.01)
                        phase.update(1, f"Fetched data chunk {i+1}")
                
                # Simulate async processing
                with op.phase("Data Processing", total=10) as phase:
                    for i in range(10):
                        # Simulate async computation
                        await asyncio.sleep(0.005)
                        phase.update(1, f"Processed record {i+1}")
                
                # Simulate async storage
                with op.phase("Data Storage", total=3) as phase:
                    for i in range(3):
                        # Simulate async database write
                        await asyncio.sleep(0.02)
                        phase.update(1, f"Saved batch {i+1}")
            
            return "async_completed"
        
        # Run the async operation
        result = await async_work_simulation()
        assert result == "async_completed"
    
    def test_memory_efficiency_with_cleanup(self):
        """Test that progress tracking doesn't leak memory"""
        tracker = create_progress_tracker("console")
        
        # Run many operations to test memory management
        for i in range(50):
            with tracker.operation(f"Operation {i+1}") as op:
                with op.phase(f"Phase {i+1}", total=10) as phase:
                    for j in range(10):
                        phase.update(1, f"Item {j+1}")
        
        # Verify operations accumulated
        all_operations = tracker.get_all_operations()
        assert len(all_operations) == 50
        
        # Test cleanup
        tracker.cleanup_completed_operations(max_completed=10)
        
        # Should only keep 10 most recent completed operations
        remaining_operations = tracker.get_all_operations()
        assert len(remaining_operations) == 10
        
        # Verify we kept the most recent ones
        for op in remaining_operations:
            assert int(op.title.split()[-1]) > 40  # Should be operations 41-50
    
    def test_callback_chain_and_event_flow(self):
        """Test complex callback chains and event flow"""
        tracker = create_progress_tracker("console")
        
        # Create multiple callbacks that transform/log events
        event_log = []
        error_log = []
        performance_log = []
        
        def general_logger(event_type, **data):
            event_log.append({
                "type": event_type,
                "operation_id": data.get("operation_id"),
                "phase_id": data.get("phase_id")
            })
        
        def error_logger(event_type, **data):
            if event_type == ProgressEventType.OPERATION_FINISHED and not data.get("success"):
                error_log.append(data)
        
        def performance_logger(event_type, **data):
            if event_type == ProgressEventType.PHASE_FINISHED:
                performance_log.append({
                    "phase_id": data.get("phase_id"),
                    "duration": data.get("duration"),
                    "final_progress": data.get("final_progress")
                })
        
        # Add all callbacks
        tracker.add_callback(general_logger)
        tracker.add_callback(error_logger)
        tracker.add_callback(performance_logger)
        
        # Run operations with different outcomes
        with tracker.operation("Success Operation") as op:
            with op.phase("Success Phase", total=3) as phase:
                phase.update(1, "Step 1")
                phase.update(1, "Step 2")
                phase.update(1, "Step 3")
        
        # Run failing operation
        try:
            with tracker.operation("Failure Operation") as op:
                with op.phase("Failure Phase", total=2) as phase:
                    phase.update(1, "Step 1")
                    raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass  # Expected
        
        # Verify event logs
        assert len(event_log) > 0
        assert len(performance_log) == 2  # Two phases completed
        assert len(error_log) == 1  # One failed operation
        
        # Verify event structure
        operation_events = [e for e in event_log if e["type"] == ProgressEventType.OPERATION_STARTED]
        assert len(operation_events) == 2
        
        phase_events = [e for e in event_log if e["type"] == ProgressEventType.PHASE_STARTED]
        assert len(phase_events) == 2


class TestProgressTrackingRealWorld:
    """Real-world scenario tests"""
    
    def test_theodore_scraping_pipeline_simulation(self):
        """Simulate the complete Theodore scraping pipeline with realistic timing"""
        tracker = create_progress_tracker("console", show_spinner=True, show_speed=True)
        
        companies = ["Stripe", "Square", "Shopify"]
        results = {}
        
        def research_company_realistic(company_name: str):
            """Realistic company research simulation"""
            with tracker.operation(
                f"Researching {company_name}",
                f"AI-powered analysis of {company_name} using 4-phase scraping"
            ) as op:
                
                # Phase 1: Link Discovery (1-3 seconds)
                with op.phase("🔍 Link Discovery", total=random_links := 500 + (hash(company_name) % 500)) as phase:
                    for i in range(0, random_links, 50):
                        batch_size = min(50, random_links - i)
                        phase.update(batch_size, f"Discovered {i + batch_size} links")
                        time.sleep(0.02)  # Simulate I/O
                
                # Phase 2: LLM Page Selection (0.5-1 second)
                selected_pages = min(50, random_links // 10)
                with op.phase("🧠 LLM Page Selection", total=selected_pages) as phase:
                    phase.update(0, "Analyzing links with Gemini 2.5 Pro")
                    time.sleep(0.1)  # Simulate LLM processing
                    
                    for i in range(selected_pages):
                        phase.update(1, f"Selected high-value page {i+1}")
                        time.sleep(0.01)
                
                # Phase 3: Content Extraction (2-5 seconds)
                with op.phase("📄 Content Extraction", total=selected_pages) as phase:
                    for i in range(selected_pages):
                        page_type = ["about", "contact", "careers", "products"][i % 4]
                        phase.update(1, f"✅ Extracted /{page_type} page")
                        time.sleep(0.03 + (hash(f"{company_name}{i}") % 20) / 1000)  # Variable timing
                
                # Phase 4: AI Analysis (1-2 seconds)
                with op.phase("🧠 AI Analysis", total=4) as phase:
                    steps = [
                        ("Combining content from all pages", 0.05),
                        ("Business intelligence with Gemini 2.5 Pro", 0.15),
                        ("Structured field extraction with Nova Pro", 0.08),
                        ("Generating embeddings for similarity", 0.04)
                    ]
                    
                    for step_name, duration in steps:
                        phase.update(1, step_name)
                        time.sleep(duration)
                
                # Store results
                results[company_name] = {
                    "links_discovered": random_links,
                    "pages_selected": selected_pages,
                    "duration": op.duration,
                    "success": True
                }
        
        # Process companies sequentially (like real usage)
        for company in companies:
            research_company_realistic(company)
        
        # Verify results
        assert len(results) == 3
        for company, result in results.items():
            assert result["success"] is True
            assert result["duration"] > 0
            assert result["links_discovered"] > 0
            assert result["pages_selected"] > 0
            
        # Verify performance characteristics
        total_duration = sum(r["duration"] for r in results.values())
        assert total_duration < 30  # Should complete all companies in reasonable time
        
        print(f"\n📊 Research Summary:")
        print(f"Companies processed: {len(results)}")
        print(f"Total duration: {total_duration:.1f}s")
        print(f"Average per company: {total_duration/len(results):.1f}s")
        
        for company, result in results.items():
            print(f"  {company}: {result['links_discovered']} links → {result['pages_selected']} pages ({result['duration']:.1f}s)")


if __name__ == "__main__":
    # Allow running integration tests directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))  