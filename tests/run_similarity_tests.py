#!/usr/bin/env python3
"""
Test runner for similarity discovery features
"""

import pytest
import sys
import os

# Add src directory to path so tests can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_similarity_tests():
    """Run all similarity discovery tests"""
    test_files = [
        "tests/test_company_discovery.py",
        "tests/test_similarity_validator.py", 
        "tests/test_similarity_pipeline.py",
        "tests/test_pinecone_similarity.py"
    ]
    
    print("🧪 Running Theodore Similarity Discovery Tests")
    print("=" * 50)
    
    # Run tests with verbose output
    args = ["-v", "--tb=short"] + test_files
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All similarity tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code

def run_specific_test(test_name):
    """Run a specific test file"""
    test_files = {
        "discovery": "tests/test_company_discovery.py",
        "similarity": "tests/test_similarity_validator.py",
        "pipeline": "tests/test_similarity_pipeline.py", 
        "pinecone": "tests/test_pinecone_similarity.py"
    }
    
    if test_name not in test_files:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_files.keys())}")
        return 1
    
    print(f"🧪 Running {test_name} tests")
    print("=" * 30)
    
    args = ["-v", "--tb=short", test_files[test_name]]
    return pytest.main(args)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_similarity_tests()
    
    sys.exit(exit_code)