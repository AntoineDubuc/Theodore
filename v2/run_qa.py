"""
Comprehensive QA test runner for Theodore v2.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED ({duration:.2f}s)")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print(f"Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 ERROR ({duration:.2f}s): {e}")
        return False


def main():
    """Run comprehensive QA suite"""
    print("🚀 Theodore v2 - Comprehensive QA Suite")
    print("=" * 50)
    
    qa_results = []
    
    # 1. Basic Import Tests
    qa_results.append(run_command(
        [sys.executable, "-c", "from src.core.domain.entities.company import Company; print('✅ Domain imports work')"],
        "Testing domain model imports"
    ))
    
    qa_results.append(run_command(
        [sys.executable, "-c", "from src.cli.main import cli; print('✅ CLI imports work')"],
        "Testing CLI imports"
    ))
    
    # 2. Domain Model Validation
    qa_results.append(run_command(
        [sys.executable, "-c", """
from src.core.domain.entities.company import Company, BusinessModel
c = Company(name='Test', website='test.com', business_model=BusinessModel.SAAS)
assert c.name == 'Test'
assert c.website == 'https://test.com'
print('✅ Domain model creation and validation works')
"""],
        "Testing domain model creation and validation"
    ))
    
    # 3. CLI Command Testing
    qa_results.append(run_command(
        [sys.executable, "-m", "src.cli.main", "--help"],
        "Testing CLI help command"
    ))
    
    qa_results.append(run_command(
        [sys.executable, "-m", "src.cli.main", "--version"],
        "Testing CLI version command"
    ))
    
    qa_results.append(run_command(
        [sys.executable, "-m", "src.cli.main", "research", "company", "Test Corp", "--output", "json"],
        "Testing CLI research command"
    ))
    
    # 4. Architecture Compliance (if available)
    try:
        qa_results.append(run_command(
            [sys.executable, "-c", """
import ast
from pathlib import Path

# Check domain independence
domain_path = Path('src/core/domain/entities')
forbidden = ['requests', 'boto3', 'click']
violations = []

for py_file in domain_path.glob('*.py'):
    if py_file.name == '__init__.py':
        continue
    with open(py_file, 'r') as f:
        content = f.read()
    for forbidden_import in forbidden:
        if forbidden_import in content:
            violations.append(f'{py_file.name}: {forbidden_import}')

assert not violations, f'Architecture violations: {violations}'
print('✅ Domain layer architecture compliance verified')
"""],
            "Testing architecture compliance"
        ))
    except:
        qa_results.append(False)
        print("⚠️  Architecture compliance test skipped")
    
    # 5. Performance Basic Check
    qa_results.append(run_command(
        [sys.executable, "-c", """
import time
from src.core.domain.entities.company import Company, BusinessModel

start = time.time()
companies = []
for i in range(100):
    c = Company(name=f'Perf Test {i}', website=f'https://test{i}.com', business_model=BusinessModel.SAAS)
    companies.append(c)

duration = time.time() - start
assert duration < 1.0, f'Performance too slow: {duration:.2f}s for 100 companies'
print(f'✅ Performance acceptable: {100/duration:.0f} companies/sec')
"""],
            "Testing basic performance"
    ))
    
    # 6. Data Quality Tests
    qa_results.append(run_command(
        [sys.executable, "-c", """
from src.core.domain.entities.company import Company, BusinessModel, TechSophistication

# Test data quality calculation
company = Company(
    name='Quality Test Corp',
    website='https://quality.com',
    industry='Technology',
    business_model=BusinessModel.SAAS,
    description='Test company',
    value_proposition='Test value',
    target_market='Test market',
    founding_year=2020,
    headquarters_location='San Francisco',
    employee_count=100,
    products_services=['Product A'],
    tech_stack=['Python'],
    leadership_team={'CEO': 'John Doe'},
    certifications=['ISO 9001']
)

score = company.calculate_data_quality_score()
assert score == 1.0, f'Expected perfect score, got {score}'

tech_check = company.is_tech_company()
assert tech_check, 'Should detect as tech company'

embedding_text = company.to_embedding_text()
assert len(embedding_text) > 100, 'Embedding text too short'

print('✅ Data quality methods work correctly')
"""],
            "Testing data quality methods"
    ))
    
    # 7. Research Lifecycle Test
    qa_results.append(run_command(
        [sys.executable, "-c", """
from src.core.domain.entities.research import Research, ResearchSource, ResearchPhase, ResearchStatus

research = Research(
    company_name='Lifecycle Test Corp',
    source=ResearchSource.CLI
)

assert research.status == ResearchStatus.QUEUED

research.start()
assert research.status == ResearchStatus.RUNNING

# Test phase progression
research.start_phase(ResearchPhase.DOMAIN_DISCOVERY)
research.complete_phase(ResearchPhase.DOMAIN_DISCOVERY, pages_found=100)

research.start_phase(ResearchPhase.AI_ANALYSIS)
research.complete_phase(ResearchPhase.AI_ANALYSIS, tokens_used=1000, cost_usd=2.50)

research.complete()
assert research.status == ResearchStatus.COMPLETED
assert research.total_tokens_used == 1000
assert research.total_cost_usd == 2.50

print('✅ Research lifecycle works correctly')
"""],
            "Testing research lifecycle"
    ))
    
    # 8. Similarity Analysis Test
    qa_results.append(run_command(
        [sys.executable, "-c", """
from src.core.domain.entities.similarity import SimilarityResult, SimilarCompany, SimilarityMethod, RelationshipType

result = SimilarityResult(
    source_company_name='Similarity Test Corp',
    primary_method=SimilarityMethod.HYBRID
)

# Add similar company
similar = SimilarCompany(
    name='Similar Corp',
    website='https://similar.com',
    discovery_method=SimilarityMethod.VECTOR_SEARCH
)

result.add_company(similar, RelationshipType.COMPETITOR, 0.85)
assert result.total_found == 1

# Add dimensions
result.add_dimension('industry', 0.9, ['Same industry'])
result.add_dimension('business_model', 0.8, ['Similar model'])

assert len(result.similarity_dimensions) == 2
assert result.overall_confidence > 0.8

summary = result.to_summary()
assert summary['source_company'] == 'Similarity Test Corp'
assert summary['total_found'] == 1

print('✅ Similarity analysis works correctly')
"""],
            "Testing similarity analysis"
    ))
    
    # Results Summary
    print("\n" + "=" * 50)
    print("🏁 QA RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(qa_results)
    total = len(qa_results)
    
    print(f"✅ Passed: {passed}/{total} tests")
    print(f"❌ Failed: {total - passed}/{total} tests")
    print(f"📊 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Theodore v2 is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())