"""
Performance tests for Theodore v2 components.
"""

import pytest
import time
import psutil
import os
from memory_profiler import profile
from src.core.domain.entities.company import Company, BusinessModel
from src.core.domain.entities.research import Research, ResearchSource
from src.core.domain.entities.similarity import SimilarityResult, SimilarCompany, SimilarityMethod


class TestPerformance:
    """Performance benchmarks for core components"""
    
    def test_company_creation_performance(self):
        """Test company creation performance"""
        start_time = time.time()
        companies = []
        
        # Create 1000 companies
        for i in range(1000):
            company = Company(
                name=f"Company {i}",
                website=f"https://company{i}.com",
                industry="Technology",
                business_model=BusinessModel.SAAS,
                description=f"Company {i} description with some longer text to simulate real data",
                products_services=[f"Product {j}" for j in range(5)],
                tech_stack=["Python", "React", "PostgreSQL", "AWS", "Docker"]
            )
            companies.append(company)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 2.0, f"Company creation too slow: {duration:.2f}s for 1000 companies"
        assert len(companies) == 1000
        
        # Memory usage check
        company_size = len(companies[0].model_dump_json())
        assert company_size < 5000, f"Company JSON too large: {company_size} bytes"
        
        print(f"✅ Created 1000 companies in {duration:.3f}s ({1000/duration:.0f} companies/sec)")
    
    def test_research_lifecycle_performance(self):
        """Test research lifecycle performance"""
        start_time = time.time()
        
        # Create and run multiple research jobs
        research_jobs = []
        for i in range(100):
            research = Research(
                company_name=f"Research Company {i}",
                website=f"https://research{i}.com",
                source=ResearchSource.BATCH
            )
            
            # Simulate research phases
            research.start()
            for phase_num in range(5):
                phase_name = list(research.ResearchPhase)[phase_num]
                research.start_phase(phase_name)
                research.complete_phase(phase_name, pages_found=100, tokens_used=1000)
            
            research.complete()
            research_jobs.append(research)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 1.0, f"Research lifecycle too slow: {duration:.2f}s for 100 jobs"
        assert all(r.status.value == "completed" for r in research_jobs)
        
        print(f"✅ Completed 100 research lifecycles in {duration:.3f}s")
    
    def test_similarity_calculation_performance(self):
        """Test similarity calculation performance"""
        start_time = time.time()
        
        # Create large similarity results
        similarity_results = []
        for i in range(50):
            result = SimilarityResult(
                source_company_name=f"Source Company {i}",
                primary_method=SimilarityMethod.HYBRID
            )
            
            # Add many similar companies
            for j in range(100):
                similar = SimilarCompany(
                    name=f"Similar Company {j}",
                    website=f"https://similar{j}.com",
                    discovery_method=SimilarityMethod.VECTOR_SEARCH
                )
                result.add_company(similar, confidence=0.5 + (j % 50) / 100)
            
            # Add similarity dimensions
            for k in range(10):
                result.add_dimension(f"dimension_{k}", 0.7 + (k % 3) / 10, [f"evidence_{k}"])
            
            similarity_results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 3.0, f"Similarity calculation too slow: {duration:.2f}s"
        assert all(len(r.similar_companies) == 100 for r in similarity_results)
        assert all(len(r.similarity_dimensions) == 10 for r in similarity_results)
        
        print(f"✅ Created 50 similarity results (5000 companies) in {duration:.3f}s")
    
    def test_serialization_performance(self):
        """Test JSON serialization performance"""
        # Create complex company
        company = Company(
            name="Performance Test Corp",
            website="https://perftest.com",
            industry="Technology",
            business_model=BusinessModel.SAAS,
            description="A" * 1000,  # Large description
            products_services=[f"Product {i}" for i in range(50)],
            tech_stack=[f"Tech {i}" for i in range(100)],
            leadership_team={f"Role {i}": f"Person {i}" for i in range(20)},
            certifications=[f"Cert {i}" for i in range(30)]
        )
        
        # Test serialization speed
        start_time = time.time()
        for _ in range(1000):
            json_data = company.model_dump_json()
            assert len(json_data) > 1000
        
        serialization_time = time.time() - start_time
        
        # Test deserialization speed
        company_dict = company.model_dump()
        start_time = time.time()
        for _ in range(1000):
            Company(**company_dict)
        
        deserialization_time = time.time() - start_time
        
        # Performance assertions
        assert serialization_time < 1.0, f"Serialization too slow: {serialization_time:.2f}s"
        assert deserialization_time < 2.0, f"Deserialization too slow: {deserialization_time:.2f}s"
        
        print(f"✅ Serialization: {1000/serialization_time:.0f} ops/sec")
        print(f"✅ Deserialization: {1000/deserialization_time:.0f} ops/sec")
    
    def test_memory_usage(self):
        """Test memory usage patterns"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        companies = []
        for i in range(1000):
            company = Company(
                name=f"Memory Test Company {i}",
                website=f"https://memtest{i}.com",
                description="A" * 500,  # 500 char description
                products_services=[f"Product {j}" for j in range(10)],
                tech_stack=[f"Tech {j}" for j in range(20)]
            )
            companies.append(company)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_per_company = (peak_memory - initial_memory) / 1000
        
        # Clean up
        companies.clear()
        
        # Memory assertions
        assert memory_per_company < 0.1, f"Too much memory per company: {memory_per_company:.3f} MB"
        assert peak_memory - initial_memory < 100, f"Total memory usage too high: {peak_memory - initial_memory:.1f} MB"
        
        print(f"✅ Memory usage: {memory_per_company:.3f} MB per company")
    
    def test_validation_performance(self):
        """Test validation performance"""
        # Create company with all validation rules
        company_data = {
            "name": "Validation Test Corp",
            "website": "https://validation-test.com",
            "industry": "Technology",
            "business_model": "saas",
            "contact_email": "contact@validation-test.com",
            "founding_year": 2020,
            "employee_count": 150,
            "products_services": [f"Product {i}" for i in range(50)],
            "tech_stack": [f"Tech {i}" for i in range(100)]
        }
        
        start_time = time.time()
        
        # Test validation speed
        for _ in range(1000):
            company = Company(**company_data)
            company.calculate_data_quality_score()
            company.is_tech_company()
            company.to_embedding_text()
        
        validation_time = time.time() - start_time
        
        # Performance assertion
        assert validation_time < 2.0, f"Validation too slow: {validation_time:.2f}s for 1000 validations"
        
        print(f"✅ Validation: {1000/validation_time:.0f} validations/sec")
    
    def test_concurrent_access_performance(self):
        """Test concurrent access patterns"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker():
            """Worker function for concurrent testing"""
            start = time.time()
            for i in range(100):
                company = Company(
                    name=f"Concurrent Company {threading.current_thread().ident}_{i}",
                    website=f"https://concurrent{i}.com"
                )
                company.calculate_data_quality_score()
            
            duration = time.time() - start
            results_queue.put(duration)
        
        # Run 10 concurrent workers
        start_time = time.time()
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect worker results
        worker_times = []
        while not results_queue.empty():
            worker_times.append(results_queue.get())
        
        # Performance assertions
        assert total_time < 5.0, f"Concurrent processing too slow: {total_time:.2f}s"
        assert len(worker_times) == 10
        assert max(worker_times) < 3.0, f"Slowest worker too slow: {max(worker_times):.2f}s"
        
        print(f"✅ Concurrent processing: 10 workers, {total_time:.3f}s total")
        print(f"✅ Worker times: min={min(worker_times):.3f}s, max={max(worker_times):.3f}s")
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create large similarity result
        result = SimilarityResult(
            source_company_name="Large Dataset Test",
            primary_method=SimilarityMethod.HYBRID
        )
        
        start_time = time.time()
        
        # Add 10,000 similar companies
        for i in range(10000):
            similar = SimilarCompany(
                name=f"Large Dataset Company {i}",
                website=f"https://large{i}.com",
                discovery_method=SimilarityMethod.VECTOR_SEARCH
            )
            result.add_company(similar, confidence=0.5)
        
        creation_time = time.time() - start_time
        
        # Test filtering performance
        start_time = time.time()
        high_confidence = result.get_high_confidence_companies(0.7)
        filtering_time = time.time() - start_time
        
        # Test summary generation
        start_time = time.time()
        summary = result.to_summary()
        summary_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 5.0, f"Large dataset creation too slow: {creation_time:.2f}s"
        assert filtering_time < 1.0, f"Filtering too slow: {filtering_time:.2f}s"
        assert summary_time < 0.1, f"Summary generation too slow: {summary_time:.2f}s"
        
        print(f"✅ Large dataset (10K items): creation={creation_time:.3f}s, filtering={filtering_time:.3f}s")


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance regression detection"""
    
    def test_company_creation_benchmark(self, benchmark):
        """Benchmark company creation"""
        def create_company():
            return Company(
                name="Benchmark Corp",
                website="https://benchmark.com",
                industry="Technology",
                business_model=BusinessModel.SAAS
            )
        
        result = benchmark(create_company)
        assert result.name == "Benchmark Corp"
    
    def test_research_phase_benchmark(self, benchmark):
        """Benchmark research phase operations"""
        research = Research(
            company_name="Benchmark Corp",
            source=ResearchSource.CLI
        )
        research.start()
        
        def phase_operation():
            phase = research.start_phase(research.ResearchPhase.AI_ANALYSIS)
            research.complete_phase(research.ResearchPhase.AI_ANALYSIS, tokens_used=1000)
            return phase
        
        result = benchmark(phase_operation)
        assert result.status.value == "completed"