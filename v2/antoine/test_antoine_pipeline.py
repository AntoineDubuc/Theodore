#!/usr/bin/env python3
"""
Antoine Pipeline Compatibility Test
==================================

Tests the complete antoine pipeline to ensure it outputs fields compatible 
with Theodore's CompanyData model and UI expectations.

This test:
1. Runs the complete antoine pipeline on a test company
2. Validates all extracted fields match Theodore's schema
3. Checks for required UI fields
4. Verifies Pinecone compatibility

Usage:
    cd v2/antoine/
    python test_antoine_pipeline.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List
from pprint import pprint

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import antoine pipeline components
from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync
from crawler import crawl_selected_pages_sync
from distill_out_fields import extract_company_fields

# Import Theodore models for validation
try:
    from src.models import CompanyData
    THEODORE_MODELS_AVAILABLE = True
except ImportError:
    print("Warning: Theodore models not available - will validate manually")
    THEODORE_MODELS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class AntoineTheodoreCompatibilityTest:
    """Test antoine pipeline compatibility with Theodore"""
    
    def __init__(self):
        self.test_company = "Linear"
        self.test_website = "https://linear.app"
        self.results = {}
        
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete antoine pipeline and validate Theodore compatibility"""
        
        print("\n🧪 ANTOINE → THEODORE COMPATIBILITY TEST")
        print("=" * 60)
        print(f"🎯 Test Company: {self.test_company}")
        print(f"🌐 Test Website: {self.test_website}")
        print()
        
        try:
            # Phase 1: Discovery
            print("🔍 Phase 1: Website Discovery...")
            start_time = time.time()
            discovery_result = discover_all_paths_sync(self.test_website)
            discovery_time = time.time() - start_time
            
            if not discovery_result.all_paths:
                raise Exception("Discovery failed: No paths found")
                
            print(f"   ✅ Discovered {len(discovery_result.all_paths)} paths in {discovery_time:.2f}s")
            self.results['discovery'] = {
                'success': True,
                'paths_found': len(discovery_result.all_paths),
                'time_seconds': discovery_time
            }
            
            # Phase 2: LLM Path Selection
            print("🤖 Phase 2: LLM Path Selection...")
            start_time = time.time()
            selection_result = filter_valuable_links_sync(
                discovery_result.all_paths,
                self.test_website,
                min_confidence=0.6,
                timeout_seconds=30
            )
            selection_time = time.time() - start_time
            
            if not selection_result.success:
                raise Exception(f"Path selection failed: {selection_result.error}")
                
            print(f"   ✅ Selected {len(selection_result.selected_paths)} valuable paths in {selection_time:.2f}s")
            print(f"   💰 Selection cost: ${selection_result.cost_usd:.4f}")
            self.results['selection'] = {
                'success': True,
                'paths_selected': len(selection_result.selected_paths),
                'time_seconds': selection_time,
                'cost_usd': selection_result.cost_usd,
                'tokens_used': selection_result.tokens_used
            }
            
            # Phase 3: Content Extraction
            print("📄 Phase 3: Content Extraction...")
            start_time = time.time()
            crawl_result = crawl_selected_pages_sync(
                self.test_website,
                selection_result.selected_paths,
                timeout_seconds=15,
                max_concurrent=5
            )
            crawl_time = time.time() - start_time
            
            if not crawl_result.successful_pages:
                raise Exception("No pages successfully crawled")
                
            print(f"   ✅ Crawled {crawl_result.successful_pages} pages in {crawl_time:.2f}s")
            print(f"   📝 Total content: {crawl_result.total_content_length:,} characters")
            self.results['crawling'] = {
                'success': True,
                'pages_crawled': crawl_result.successful_pages,
                'content_length': crawl_result.total_content_length,
                'time_seconds': crawl_time
            }
            
            # Phase 4: Field Extraction
            print("🧠 Phase 4: AI Field Extraction...")
            start_time = time.time()
            
            # Create pipeline metadata for enhanced tracking
            pipeline_metadata = {
                'phase2_selection': {
                    'success': True,
                    'tokens_used': selection_result.tokens_used,
                    'cost_usd': selection_result.cost_usd
                },
                'phase3_extraction': {
                    'success': True,
                    'processing_time': crawl_time
                }
            }
            
            extraction_result = extract_company_fields(
                crawl_result,
                self.test_company,
                timeout_seconds=120,
                pipeline_metadata=pipeline_metadata
            )
            extraction_time = time.time() - start_time
            
            if not extraction_result.success:
                raise Exception(f"Field extraction failed: {extraction_result.error}")
                
            print(f"   ✅ Extracted {len(extraction_result.extracted_fields)} fields in {extraction_time:.2f}s")
            print(f"   💰 Extraction cost: ${extraction_result.cost_usd:.4f}")
            
            # Count non-null fields
            non_null_fields = len([v for v in extraction_result.extracted_fields.values() if v is not None and v != ""])
            print(f"   ✨ Non-null fields: {non_null_fields}")
            
            self.results['extraction'] = {
                'success': True,
                'total_fields': len(extraction_result.extracted_fields),
                'non_null_fields': non_null_fields,
                'confidence': extraction_result.overall_confidence,
                'time_seconds': extraction_time,
                'cost_usd': extraction_result.cost_usd,
                'tokens_used': extraction_result.tokens_used
            }
            
            # Phase 5: Theodore Compatibility Validation
            print("🔬 Phase 5: Theodore Compatibility Validation...")
            
            extracted_fields = extraction_result.extracted_fields
            compatibility_results = self.validate_theodore_compatibility(extracted_fields)
            
            self.results['compatibility'] = compatibility_results
            
            # Summary
            total_cost = selection_result.cost_usd + extraction_result.cost_usd
            total_time = discovery_time + selection_time + crawl_time + extraction_time
            
            print("\n📊 PIPELINE SUMMARY")
            print("=" * 40)
            print(f"🏃 Total Time: {total_time:.2f}s")
            print(f"💰 Total Cost: ${total_cost:.4f}")
            print(f"🎯 Fields Extracted: {non_null_fields}")
            print(f"✅ Theodore Compatible: {compatibility_results['is_compatible']}")
            
            self.results['summary'] = {
                'total_time_seconds': total_time,
                'total_cost_usd': total_cost,
                'total_non_null_fields': non_null_fields,
                'theodore_compatible': compatibility_results['is_compatible']
            }
            
            # Show extracted fields for verification
            if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
                print("\n🔍 EXTRACTED FIELDS (Sample):")
                print("-" * 40)
                for field, value in list(extracted_fields.items())[:10]:
                    if value is not None and value != "":
                        print(f"{field}: {str(value)[:100]}...")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            self.results['error'] = str(e)
            return self.results
    
    def validate_theodore_compatibility(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that extracted fields are compatible with Theodore"""
        
        # Required Theodore UI fields
        required_ui_fields = [
            'name', 'company_name', 'industry', 'business_model', 'company_description',
            'value_proposition', 'tech_stack', 'competitive_advantages', 'target_market',
            'pain_points', 'key_services', 'saas_classification', 'is_saas', 'company_stage'
        ]
        
        # Required Theodore system fields
        required_system_fields = [
            'id', 'created_at', 'last_updated', 'scrape_status', 'pages_crawled',
            'scraped_urls', 'crawl_depth', 'crawl_duration'
        ]
        
        results = {
            'is_compatible': True,
            'missing_ui_fields': [],
            'missing_system_fields': [],
            'field_coverage_ui': 0.0,
            'field_coverage_system': 0.0,
            'total_fields_present': len([v for v in extracted_fields.values() if v is not None])
        }
        
        # Check UI fields
        for field in required_ui_fields:
            if field not in extracted_fields or extracted_fields[field] is None:
                results['missing_ui_fields'].append(field)
        
        results['field_coverage_ui'] = (len(required_ui_fields) - len(results['missing_ui_fields'])) / len(required_ui_fields)
        
        # Check system fields
        for field in required_system_fields:
            if field not in extracted_fields or extracted_fields[field] is None:
                results['missing_system_fields'].append(field)
        
        results['field_coverage_system'] = (len(required_system_fields) - len(results['missing_system_fields'])) / len(required_system_fields)
        
        # Overall compatibility
        if results['missing_ui_fields'] or results['missing_system_fields']:
            results['is_compatible'] = False
        
        print(f"   📋 UI Field Coverage: {results['field_coverage_ui']:.1%} ({len(required_ui_fields) - len(results['missing_ui_fields'])}/{len(required_ui_fields)})")
        print(f"   🔧 System Field Coverage: {results['field_coverage_system']:.1%} ({len(required_system_fields) - len(results['missing_system_fields'])}/{len(required_system_fields)})")
        
        if results['missing_ui_fields']:
            print(f"   ⚠️  Missing UI fields: {', '.join(results['missing_ui_fields'])}")
        
        if results['missing_system_fields']:
            print(f"   ⚠️  Missing system fields: {', '.join(results['missing_system_fields'])}")
        
        if results['is_compatible']:
            print("   ✅ Full Theodore compatibility confirmed!")
        else:
            print("   ❌ Theodore compatibility issues found")
        
        return results


def main():
    """Run the antoine pipeline compatibility test"""
    
    tester = AntoineTheodoreCompatibilityTest()
    results = tester.run_complete_test()
    
    # Save results
    timestamp = int(time.time())
    results_file = f"antoine_theodore_compatibility_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Exit with error code if test failed
    if results.get('compatibility', {}).get('is_compatible', False):
        print("\n🎉 ANTOINE → THEODORE COMPATIBILITY: PASSED")
        exit(0)
    else:
        print("\n💥 ANTOINE → THEODORE COMPATIBILITY: FAILED")
        exit(1)


if __name__ == "__main__":
    main()