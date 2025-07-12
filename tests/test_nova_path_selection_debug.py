#!/usr/bin/env python3
"""
Nova Pro Path Selection Debug Test
==================================

Debug why Nova Pro is returning 0 paths for companies like Volvo Canada.
This test will isolate the path selection component and analyze the issue.
"""

import sys
import os
import time
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync


class NovaProPathSelectionDebugger:
    """Debug Nova Pro path selection issues"""
    
    def __init__(self):
        self.test_companies = [
            {
                "name": "Volvo Canada",
                "website": "https://www.volvocars.com/en-ca/",
                "expected_issue": "Returns 0 paths"
            },
            {
                "name": "Stripe",
                "website": "https://stripe.com",
                "expected_issue": "Should work"
            },
            {
                "name": "Linear",
                "website": "https://linear.app",
                "expected_issue": "Should work"
            }
        ]
    
    def test_path_discovery_only(self, company_name: str, website: str):
        """Test just the path discovery phase"""
        print(f"\n{'='*80}")
        print(f"TESTING PATH DISCOVERY: {company_name}")
        print(f"Website: {website}")
        print(f"{'='*80}")
        
        try:
            start_time = time.time()
            discovery_result = discover_all_paths_sync(website, timeout_seconds=30)
            elapsed = time.time() - start_time
            
            print(f"⏱️ Discovery completed in {elapsed:.1f}s")
            print(f"📊 Results:")
            print(f"   Total paths: {len(discovery_result.all_paths)}")
            print(f"   Navigation paths: {len(discovery_result.navigation_paths)}")
            print(f"   Content paths: {len(discovery_result.content_paths)}")
            print(f"   Restricted paths: {len(discovery_result.restricted_paths)}")
            print(f"   Errors: {discovery_result.errors}")
            
            if discovery_result.all_paths:
                print(f"\n📋 Sample paths ({min(10, len(discovery_result.all_paths))} of {len(discovery_result.all_paths)}):")
                for i, path in enumerate(discovery_result.all_paths[:10]):
                    print(f"   {i+1:2d}. {path}")
                
                if len(discovery_result.all_paths) > 10:
                    print(f"   ... and {len(discovery_result.all_paths) - 10} more")
                
                return discovery_result
            else:
                print("❌ No paths discovered!")
                return None
                
        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_nova_pro_selection(self, company_name: str, website: str, discovered_paths: list):
        """Test Nova Pro path selection with different parameters"""
        print(f"\n🤖 TESTING NOVA PRO PATH SELECTION")
        print(f"Input: {len(discovered_paths)} paths")
        
        # Test with different confidence thresholds
        confidence_levels = [0.8, 0.6, 0.4, 0.2]
        
        for confidence in confidence_levels:
            print(f"\n🎯 Testing with confidence threshold: {confidence}")
            
            try:
                start_time = time.time()
                selection_result = filter_valuable_links_sync(
                    discovered_paths,
                    website,
                    min_confidence=confidence,
                    timeout_seconds=90
                )
                elapsed = time.time() - start_time
                
                print(f"⏱️ Selection completed in {elapsed:.1f}s")
                print(f"📊 Results:")
                print(f"   Success: {selection_result.success}")
                print(f"   Selected paths: {len(selection_result.selected_paths)}")
                print(f"   Rejected paths: {len(selection_result.rejected_paths)}")
                print(f"   Model used: {selection_result.model_used}")
                print(f"   Tokens used: {selection_result.tokens_used:,}")
                print(f"   Cost: ${selection_result.cost_usd:.4f}")
                print(f"   Confidence threshold: {selection_result.confidence_threshold}")
                
                if selection_result.error:
                    print(f"   Error: {selection_result.error}")
                
                if selection_result.selected_paths:
                    print(f"\n✅ Selected paths:")
                    for i, path in enumerate(selection_result.selected_paths):
                        priority = selection_result.path_priorities.get(path, 0.0)
                        reasoning = selection_result.path_reasoning.get(path, "No reasoning")
                        print(f"   {i+1:2d}. {path} (priority: {priority:.2f}) - {reasoning}")
                    
                    return selection_result  # Success - return result
                else:
                    print(f"❌ No paths selected at confidence {confidence}")
                    
                    # Show some rejected paths for analysis
                    if selection_result.rejected_paths:
                        print(f"\n📋 Sample rejected paths:")
                        for i, path in enumerate(selection_result.rejected_paths[:10]):
                            print(f"   {i+1:2d}. {path}")
                
            except Exception as e:
                print(f"❌ Selection failed at confidence {confidence}: {e}")
                import traceback
                traceback.print_exc()
        
        return None  # All confidence levels failed
    
    def analyze_prompt_and_response(self, company_name: str, website: str, paths: list):
        """Analyze the exact prompt being sent and response received"""
        print(f"\n🔍 ANALYZING PROMPT AND RESPONSE")
        
        try:
            from src.antoine_selection import create_openrouter_client
            from src.theodore_prompts import get_page_selection_prompt
            
            # Get the selection prompt
            prompt_template = get_page_selection_prompt()
            
            # Format the prompt exactly like the selection module does
            from urllib.parse import urlparse
            parsed_url = urlparse(website)
            domain = parsed_url.netloc
            
            # Use only first 50 paths for analysis
            analysis_paths = paths[:50]
            paths_text = "\n".join([f"- {path}" for path in analysis_paths])
            
            prompt = prompt_template.format(
                domain=domain,
                company_name=company_name,
                total_paths=len(analysis_paths),
                paths_list=paths_text
            )
            
            print(f"📝 Prompt length: {len(prompt):,} characters")
            print(f"📝 Analyzing {len(analysis_paths)} paths for {domain}")
            
            # Show prompt preview
            print(f"\n📋 Prompt preview (first 500 chars):")
            print("-" * 60)
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print("-" * 60)
            
            # Make the actual API call
            client = create_openrouter_client()
            
            print(f"\n🚀 Sending to Nova Pro...")
            response = client.analyze_paths(prompt, timeout=90)
            
            print(f"📊 Response analysis:")
            print(f"   Success: {response.success}")
            print(f"   Model: {response.model_used}")
            print(f"   Tokens: {response.tokens_used:,}")
            print(f"   Cost: ${response.cost_usd:.4f}")
            print(f"   Time: {response.processing_time:.1f}s")
            
            if response.error:
                print(f"   Error: {response.error}")
            
            print(f"\n📋 Response content ({len(response.content)} chars):")
            print("-" * 60)
            print(response.content)
            print("-" * 60)
            
            # Try to parse the response
            try:
                content = response.content.strip()
                
                # Look for JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    
                    print(f"\n✅ Parsed JSON response:")
                    print(f"   Keys: {list(data.keys())}")
                    
                    if 'selected_paths' in data:
                        selected = data['selected_paths']
                        print(f"   Selected paths: {len(selected) if isinstance(selected, list) else 'Not a list'}")
                        if isinstance(selected, list) and selected:
                            print(f"   Sample selections: {selected[:5]}")
                    
                    if 'explanations' in data:
                        explanations = data['explanations']
                        print(f"   Explanations: {len(explanations) if isinstance(explanations, dict) else 'Not a dict'}")
                    
                else:
                    print(f"❌ No JSON found in response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
            
            return response
            
        except Exception as e:
            print(f"❌ Prompt analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_full_debug_test(self, company_name: str, website: str):
        """Run complete debug test for a company"""
        print(f"\n🔬 FULL DEBUG TEST: {company_name}")
        print(f"🌐 Website: {website}")
        
        # Step 1: Test path discovery
        discovery_result = self.test_path_discovery_only(company_name, website)
        if not discovery_result or not discovery_result.all_paths:
            print(f"❌ Cannot proceed - no paths discovered")
            return False
        
        # Step 2: Analyze prompt and response
        response = self.analyze_prompt_and_response(company_name, website, discovery_result.all_paths)
        
        # Step 3: Test Nova Pro selection
        selection_result = self.test_nova_pro_selection(company_name, website, discovery_result.all_paths)
        
        if selection_result and selection_result.selected_paths:
            print(f"\n✅ {company_name} - Nova Pro selection SUCCEEDED")
            return True
        else:
            print(f"\n❌ {company_name} - Nova Pro selection FAILED")
            return False
    
    def run_all_tests(self):
        """Run debug tests for all companies"""
        print(f"\n🧪 NOVA PRO PATH SELECTION DEBUG SUITE")
        print(f"{'='*80}")
        
        results = {}
        
        for company in self.test_companies:
            success = self.run_full_debug_test(company['name'], company['website'])
            results[company['name']] = success
        
        # Summary
        print(f"\n📊 DEBUG RESULTS SUMMARY")
        print(f"{'='*80}")
        
        for company_name, success in results.items():
            status = "✅ WORKING" if success else "❌ FAILING"
            print(f"{status:<12} {company_name}")
        
        working = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\n📈 Overall: {working}/{total} companies working")
        
        if working < total:
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"   1. Check Nova Pro API availability and rate limits")
            print(f"   2. Verify prompt format matches Nova Pro expectations")
            print(f"   3. Consider adjusting confidence thresholds")
            print(f"   4. Review path filtering logic")
        
        return working == total


def main():
    """Run the debug test suite"""
    debugger = NovaProPathSelectionDebugger()
    success = debugger.run_all_tests()
    
    if success:
        print(f"\n🎉 All tests passed - Nova Pro selection working correctly!")
    else:
        print(f"\n⚠️ Some tests failed - Nova Pro selection needs investigation")
    
    return success


if __name__ == "__main__":
    main()