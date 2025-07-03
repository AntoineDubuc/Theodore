"""
Unit tests for Research domain entity.
"""

import pytest
from datetime import datetime, timedelta
from v2.src.core.domain.entities.research import (
    Research, ResearchStatus, ResearchPhase, ResearchSource
)


class TestResearchEntity:
    """Test suite for Research entity"""
    
    def test_create_research_job(self):
        """Test creating a research job"""
        research = Research(
            company_name="Acme Corp",
            website="https://acme.com",
            source=ResearchSource.WEB_UI
        )
        
        assert research.company_name == "Acme Corp"
        assert research.status == ResearchStatus.QUEUED
        assert research.source == ResearchSource.WEB_UI
        assert research.priority == 5
        assert research.progress_percentage == 0.0
    
    def test_research_lifecycle(self):
        """Test research job lifecycle"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.CLI
        )
        
        # Start research
        research.start()
        assert research.status == ResearchStatus.RUNNING
        assert research.started_at is not None
        
        # Start phases
        phase1 = research.start_phase(ResearchPhase.DOMAIN_DISCOVERY)
        assert phase1.status == ResearchStatus.RUNNING
        assert research.current_phase == ResearchPhase.DOMAIN_DISCOVERY
        
        # Complete phase
        research.complete_phase(
            ResearchPhase.DOMAIN_DISCOVERY,
            pages_found=150
        )
        assert phase1.status == ResearchStatus.COMPLETED
        assert phase1.pages_found == 150
        assert phase1.duration_seconds > 0
        
        # Complete research
        research.complete()
        assert research.status == ResearchStatus.COMPLETED
        assert research.completed_at is not None
        assert research.total_duration_seconds > 0
        assert research.progress_percentage == 100.0
    
    def test_research_failure(self):
        """Test research failure handling"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.API
        )
        
        research.start()
        research.start_phase(ResearchPhase.LINK_DISCOVERY)
        
        # Fail during phase
        research.fail("Network error", ResearchPhase.LINK_DISCOVERY)
        
        assert research.status == ResearchStatus.FAILED
        assert research.error_message == "Network error"
        assert research.failed_phase == ResearchPhase.LINK_DISCOVERY
        assert research.completed_at is not None
    
    def test_phase_tracking(self):
        """Test phase progress tracking"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.BATCH
        )
        
        research.start()
        
        # Run through multiple phases
        phases_data = [
            (ResearchPhase.DOMAIN_DISCOVERY, {"pages_found": 1}),
            (ResearchPhase.LINK_DISCOVERY, {"pages_found": 120}),
            (ResearchPhase.PAGE_SELECTION, {"pages_selected": 50}),
            (ResearchPhase.CONTENT_EXTRACTION, {"pages_scraped": 45, "content_length": 500000}),
            (ResearchPhase.AI_ANALYSIS, {"tokens_used": 150000, "cost_usd": 2.50}),
        ]
        
        for phase, data in phases_data:
            research.start_phase(phase)
            research.complete_phase(phase, **data)
        
        assert len(research.phases) == 5
        assert research.progress_percentage > 60.0
        
        # Check phase duration retrieval
        link_duration = research.get_phase_duration(ResearchPhase.LINK_DISCOVERY)
        assert link_duration is not None
        assert link_duration >= 0
    
    def test_cost_tracking(self):
        """Test AI cost tracking across phases"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.CLI
        )
        
        research.start()
        
        # Phase with token usage
        research.start_phase(ResearchPhase.AI_ANALYSIS)
        research.complete_phase(
            ResearchPhase.AI_ANALYSIS,
            tokens_used=100000,
            cost_usd=1.50
        )
        
        research.start_phase(ResearchPhase.CLASSIFICATION)
        research.complete_phase(
            ResearchPhase.CLASSIFICATION,
            tokens_used=5000,
            cost_usd=0.10
        )
        
        research.complete()
        
        assert research.total_tokens_used == 105000
        assert research.total_cost_usd == 1.60
    
    def test_research_cancellation(self):
        """Test research cancellation"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.WEB_UI
        )
        
        research.start()
        research.start_phase(ResearchPhase.CONTENT_EXTRACTION)
        
        # Cancel mid-process
        research.cancel()
        
        assert research.status == ResearchStatus.CANCELLED
        assert research.completed_at is not None
        assert research.is_complete()
    
    def test_research_configuration(self):
        """Test research configuration options"""
        research = Research(
            company_name="Test Corp",
            website="test.com",
            source=ResearchSource.API,
            skip_domain_discovery=True,
            max_pages_to_scrape=25,
            config={
                "use_javascript": True,
                "timeout_seconds": 30
            }
        )
        
        assert research.skip_domain_discovery is True
        assert research.max_pages_to_scrape == 25
        assert research.config["use_javascript"] is True
    
    def test_batch_research_tracking(self):
        """Test research as part of batch"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.BATCH,
            batch_id="batch_123",
            user_id="user_456",
            priority=3
        )
        
        assert research.batch_id == "batch_123"
        assert research.user_id == "user_456"
        assert research.priority == 3
    
    def test_retry_tracking(self):
        """Test retry count tracking"""
        research = Research(
            company_name="Test Corp",
            source=ResearchSource.CLI
        )
        
        assert research.retry_count == 0
        
        research.retry_count += 1
        assert research.retry_count == 1
    
    def test_serialization(self):
        """Test research serialization"""
        research = Research(
            company_name="Test Corp",
            website="test.com",
            source=ResearchSource.API,
            ai_model_versions={
                "analysis": "gpt-4",
                "embedding": "text-embedding-3"
            }
        )
        
        research.start()
        research.start_phase(ResearchPhase.LINK_DISCOVERY)
        research.complete_phase(ResearchPhase.LINK_DISCOVERY, pages_found=100)
        
        # Serialize
        data = research.model_dump()
        assert data["company_name"] == "Test Corp"
        assert len(data["phases"]) == 1
        
        # Deserialize
        research2 = Research(**data)
        assert research2.company_name == research.company_name
        assert len(research2.phases) == 1
        assert research2.phases[0].pages_found == 100