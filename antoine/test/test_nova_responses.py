#!/usr/bin/env python3
"""
Nova Pro Response Structure Test
================================

Test suite to debug Nova Pro JSON parsing issues by capturing raw responses
from 4 different companies and analyzing their structure.

This will help identify why the current JSON parsing fails and provide
data for creating a more robust parsing solution.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Test imports
from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync, create_openrouter_client

def setup_test_directories():
    """Create test result directories"""
    results_dir = Path(__file__).parent / "results" / "nova_responses"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def test_companies_list():
    """Define test companies with varying complexities"""
    return [
        {
            "name": "Linear",
            "website": "https://linear.app",
            "description": "Simple SaaS tool, clean structure"
        },
        {
            "name": "Rogers Communications", 
            "website": "https://www.rogers.com",
            "description": "Complex corporate site, currently failing"
        },
        {
            "name": "Stripe",
            "website": "https://stripe.com", 
            "description": "Well-structured tech company"
        },
        {
            "name": "Shopify",
            "website": "https://www.shopify.com",
            "description": "E-commerce platform with good structure"
        }
    ]

def test_single_company_nova_response(company_info, results_dir):
    """Test Nova Pro response for a single company"""
    
    print(f"\n🧪 Testing Nova Pro for: {company_info['name']}")
    print(f"📍 Website: {company_info['website']}")
    print(f"📝 Description: {company_info['description']}")
    
    test_result = {
        "company": company_info,
        "timestamp": datetime.utcnow().isoformat(),
        "discovery_result": None,
        "nova_request": None,
        "nova_response": None,
        "parsing_attempts": [],
        "success": False,
        "error": None
    }
    
    try:
        # Phase 1: Discovery
        print(f"🔍 Phase 1: Discovering paths for {company_info['website']}")
        discovery_start = time.time()
        
        discovery_result = discover_all_paths_sync(
            company_info['website'], 
            timeout_seconds=30
        )
        
        discovery_time = time.time() - discovery_start
        
        if not discovery_result.all_paths:
            test_result["error"] = "No paths discovered"
            return test_result
            
        print(f"✅ Discovered {len(discovery_result.all_paths)} paths in {discovery_time:.1f}s")
        
        test_result["discovery_result"] = {
            "success": True,
            "total_paths": len(discovery_result.all_paths),
            "discovery_time": discovery_time,
            "sample_paths": discovery_result.all_paths[:10]  # First 10 for reference
        }
        
        # Phase 2: Nova Pro Selection (with detailed response capture)
        print(f"🤖 Phase 2: Testing Nova Pro selection")
        selection_start = time.time()
        
        # Create OpenRouter client
        openrouter_client = create_openrouter_client()
        
        # Create prompt (same as in antoine_selection.py)
        from src.antoine_selection import create_path_selection_prompt
        prompt = create_path_selection_prompt(
            discovery_result.all_paths,
            company_info['website'],
            min_confidence=0.6
        )
        
        test_result["nova_request"] = {
            "prompt_length": len(prompt),
            "total_paths": len(discovery_result.all_paths),
            "model": "amazon/nova-pro-v1",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"📝 Sending {len(discovery_result.all_paths)} paths to Nova Pro")
        print(f"📏 Prompt length: {len(prompt):,} characters")
        
        # Make OpenRouter request
        openrouter_response = openrouter_client.analyze_paths(prompt)
        selection_time = time.time() - selection_start
        
        print(f"✅ Nova Pro response received in {selection_time:.1f}s")
        
        # Capture detailed response information
        test_result["nova_response"] = {
            "success": openrouter_response.success,
            "model_used": openrouter_response.model_used,
            "tokens_used": openrouter_response.tokens_used,
            "cost_usd": openrouter_response.cost_usd,
            "processing_time": openrouter_response.processing_time,
            "response_length": len(openrouter_response.content) if openrouter_response.content else 0,
            "raw_content": openrouter_response.content,  # FULL RAW RESPONSE
            "error": openrouter_response.error
        }
        
        if not openrouter_response.success:
            test_result["error"] = f"Nova Pro request failed: {openrouter_response.error}"
            return test_result
        
        # Test different JSON parsing approaches
        content = openrouter_response.content.strip()
        test_result["parsing_attempts"] = test_json_parsing_methods(content)
        
        # Determine if any parsing method succeeded
        successful_parsing = any(attempt["success"] for attempt in test_result["parsing_attempts"])
        test_result["success"] = successful_parsing
        
        print(f"📊 Parsing Results:")
        for i, attempt in enumerate(test_result["parsing_attempts"], 1):
            status = "✅" if attempt["success"] else "❌"
            print(f"   {status} Method {i} ({attempt['method']}): {attempt['result_summary']}")
        
    except Exception as e:
        test_result["error"] = f"Test failed: {str(e)}"
        print(f"❌ Test failed: {str(e)}")
    
    # Save individual company result
    company_filename = f"{company_info['name'].lower().replace(' ', '_')}_response.json"
    company_file = results_dir / company_filename
    
    with open(company_file, 'w') as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved results to: {company_file}")
    
    return test_result

def test_json_parsing_methods(content):
    """Test different JSON parsing approaches on Nova Pro response"""
    
    parsing_attempts = []
    
    # Method 1: Current approach - look for { } first, then [ ]
    try:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            # Fallback to array
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON markers found")
        
        json_content = content[json_start:json_end]
        parsed = json.loads(json_content)
        
        parsing_attempts.append({
            "method": "current_method",
            "success": True,
            "extracted_json": json_content,
            "parsed_type": type(parsed).__name__,
            "result_summary": f"Extracted {type(parsed).__name__} with {len(parsed) if hasattr(parsed, '__len__') else 'N/A'} items"
        })
        
    except Exception as e:
        parsing_attempts.append({
            "method": "current_method",
            "success": False,
            "error": str(e),
            "result_summary": f"Failed: {str(e)}"
        })
    
    # Method 2: Find largest valid JSON object
    try:
        import re
        
        # Find all potential JSON objects/arrays
        json_patterns = []
        
        # Look for objects
        for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content):
            json_patterns.append(("object", match.group()))
        
        # Look for arrays  
        for match in re.finditer(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', content):
            json_patterns.append(("array", match.group()))
        
        if not json_patterns:
            raise ValueError("No JSON patterns found")
        
        # Try to parse the largest valid JSON
        largest_valid = None
        largest_size = 0
        
        for json_type, json_text in json_patterns:
            try:
                parsed = json.loads(json_text)
                if len(json_text) > largest_size:
                    largest_valid = (json_type, json_text, parsed)
                    largest_size = len(json_text)
            except:
                continue
        
        if largest_valid:
            json_type, json_text, parsed = largest_valid
            parsing_attempts.append({
                "method": "regex_largest_valid",
                "success": True,
                "extracted_json": json_text,
                "parsed_type": type(parsed).__name__,
                "result_summary": f"Found valid {json_type} with {len(json_text)} chars"
            })
        else:
            raise ValueError("No valid JSON found in patterns")
            
    except Exception as e:
        parsing_attempts.append({
            "method": "regex_largest_valid", 
            "success": False,
            "error": str(e),
            "result_summary": f"Failed: {str(e)}"
        })
    
    # Method 3: Line-by-line JSON search
    try:
        lines = content.split('\n')
        valid_json_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('{', '[')):
                try:
                    parsed = json.loads(line)
                    valid_json_lines.append((line, parsed))
                except:
                    continue
        
        if valid_json_lines:
            # Use the first valid JSON line
            json_line, parsed = valid_json_lines[0]
            parsing_attempts.append({
                "method": "line_by_line_search",
                "success": True,
                "extracted_json": json_line,
                "parsed_type": type(parsed).__name__,
                "result_summary": f"Found {type(parsed).__name__} in line-by-line search"
            })
        else:
            raise ValueError("No valid JSON lines found")
            
    except Exception as e:
        parsing_attempts.append({
            "method": "line_by_line_search",
            "success": False, 
            "error": str(e),
            "result_summary": f"Failed: {str(e)}"
        })
    
    # Method 4: Simple JSON validation of entire response
    try:
        parsed = json.loads(content)
        parsing_attempts.append({
            "method": "full_content_parse",
            "success": True,
            "extracted_json": content,
            "parsed_type": type(parsed).__name__,
            "result_summary": f"Entire response is valid {type(parsed).__name__}"
        })
        
    except Exception as e:
        parsing_attempts.append({
            "method": "full_content_parse",
            "success": False,
            "error": str(e),
            "result_summary": f"Failed: {str(e)}"
        })
    
    return parsing_attempts

def generate_analysis_report(all_results, results_dir):
    """Generate comprehensive analysis report"""
    
    report = {
        "test_summary": {
            "timestamp": datetime.utcnow().isoformat(),
            "total_companies_tested": len(all_results),
            "successful_discoveries": sum(1 for r in all_results if r.get("discovery_result") and r.get("discovery_result", {}).get("success")),
            "successful_nova_requests": sum(1 for r in all_results if r.get("nova_response") and r.get("nova_response", {}).get("success")),
            "successful_json_parsing": sum(1 for r in all_results if r.get("success"))
        },
        "company_results": {},
        "parsing_method_analysis": {},
        "nova_response_patterns": {},
        "recommendations": []
    }
    
    # Analyze each company
    for result in all_results:
        company_name = result["company"]["name"]
        
        report["company_results"][company_name] = {
            "discovery_success": result.get("discovery_result", {}).get("success", False),
            "discovery_paths": result.get("discovery_result", {}).get("total_paths", 0),
            "nova_success": result.get("nova_response", {}).get("success", False),
            "nova_response_length": result.get("nova_response", {}).get("response_length", 0),
            "parsing_success": result.get("success", False),
            "parsing_methods_tried": len(result.get("parsing_attempts", [])),
            "successful_parsing_methods": [
                attempt["method"] for attempt in result.get("parsing_attempts", [])
                if attempt["success"]
            ]
        }
    
    # Analyze parsing methods across all companies
    method_stats = {}
    for result in all_results:
        for attempt in result.get("parsing_attempts", []):
            method = attempt["method"]
            if method not in method_stats:
                method_stats[method] = {"total": 0, "successful": 0, "errors": []}
            
            method_stats[method]["total"] += 1
            if attempt["success"]:
                method_stats[method]["successful"] += 1
            else:
                method_stats[method]["errors"].append(attempt.get("error", "Unknown error"))
    
    report["parsing_method_analysis"] = method_stats
    
    # Analyze Nova Pro response patterns
    response_patterns = {
        "response_lengths": [],
        "common_prefixes": [],
        "common_suffixes": [],
        "contains_json_markers": {"objects": 0, "arrays": 0, "neither": 0}
    }
    
    for result in all_results:
        nova_response = result.get("nova_response", {})
        if nova_response.get("success") and nova_response.get("raw_content"):
            content = nova_response["raw_content"]
            response_patterns["response_lengths"].append(len(content))
            
            # Check for JSON markers
            has_object = '{' in content and '}' in content
            has_array = '[' in content and ']' in content
            
            if has_object:
                response_patterns["contains_json_markers"]["objects"] += 1
            elif has_array:
                response_patterns["contains_json_markers"]["arrays"] += 1
            else:
                response_patterns["contains_json_markers"]["neither"] += 1
    
    report["nova_response_patterns"] = response_patterns
    
    # Generate recommendations
    recommendations = []
    
    # Check if current method is consistently failing
    current_method_stats = method_stats.get("current_method", {})
    if current_method_stats.get("total", 0) > 0:
        success_rate = current_method_stats["successful"] / current_method_stats["total"]
        if success_rate < 0.5:
            recommendations.append({
                "priority": "high",
                "issue": "Current JSON parsing method has low success rate",
                "recommendation": f"Current method succeeds only {success_rate:.1%} of the time. Consider implementing alternative parsing methods.",
                "details": current_method_stats
            })
    
    # Check for better alternative methods
    best_method = None
    best_success_rate = 0
    for method, stats in method_stats.items():
        if stats["total"] > 0:
            success_rate = stats["successful"] / stats["total"]
            if success_rate > best_success_rate:
                best_success_rate = success_rate
                best_method = method
    
    if best_method and best_method != "current_method":
        recommendations.append({
            "priority": "medium",
            "issue": "Alternative parsing method shows better results",
            "recommendation": f"Method '{best_method}' has {best_success_rate:.1%} success rate. Consider implementing as primary method.",
            "details": method_stats[best_method]
        })
    
    # Check response pattern insights
    if response_patterns["contains_json_markers"]["neither"] > 0:
        recommendations.append({
            "priority": "high",
            "issue": "Some Nova Pro responses contain no JSON markers",
            "recommendation": "Implement fallback handling for responses without JSON objects or arrays.",
            "details": f"{response_patterns['contains_json_markers']['neither']} responses had no JSON markers"
        })
    
    report["recommendations"] = recommendations
    
    # Save analysis report
    report_file = results_dir / "analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def main():
    """Run Nova Pro response structure tests"""
    
    print("🧪 NOVA PRO RESPONSE STRUCTURE TEST")
    print("=" * 50)
    
    # Setup
    results_dir = setup_test_directories()
    test_companies = test_companies_list()
    
    print(f"📁 Results directory: {results_dir}")
    print(f"🏢 Testing {len(test_companies)} companies")
    
    # Test each company
    all_results = []
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n📊 Testing {i}/{len(test_companies)}")
        result = test_single_company_nova_response(company, results_dir)
        all_results.append(result)
        
        # Brief result summary
        if result.get("success"):
            print(f"✅ {company['name']}: JSON parsing successful")
        else:
            print(f"❌ {company['name']}: {result.get('error', 'Unknown error')}")
    
    # Generate analysis report
    print(f"\n📋 Generating analysis report...")
    report = generate_analysis_report(all_results, results_dir)
    
    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print(f"=" * 30)
    print(f"Companies tested: {report['test_summary']['total_companies_tested']}")
    print(f"Successful discoveries: {report['test_summary']['successful_discoveries']}")
    print(f"Successful Nova requests: {report['test_summary']['successful_nova_requests']}")
    print(f"Successful JSON parsing: {report['test_summary']['successful_json_parsing']}")
    
    print(f"\n🎯 TOP RECOMMENDATIONS:")
    for rec in report["recommendations"][:3]:  # Top 3
        print(f"   {rec['priority'].upper()}: {rec['recommendation']}")
    
    print(f"\n💾 All results saved to: {results_dir}")
    print(f"📄 Analysis report: {results_dir}/analysis_report.json")

if __name__ == "__main__":
    main()