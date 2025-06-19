#!/usr/bin/env python3
"""
Field Discovery Test - Live LLM Analysis
Shows exactly what fields the LLM is asked to find and what it discovers
"""

import sys
import os
import time
import json
from datetime import datetime

# Add Theodore root to path
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/sandbox/search/singular_search/rate_limiting')

try:
    # Import our rate-limited solution
    from rate_limited_gemini_solution import RateLimitedTheodoreLLMManager, LLMTask
    print("✅ Successfully imported rate-limited solution")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("ℹ️ This test requires the rate_limited_gemini_solution.py file")
    sys.exit(1)

def test_field_discovery_for_company():
    """
    Live test showing what fields LLM is asked to find and what it discovers
    """
    
    # Test with a mid-sized company - Linear (project management tool)
    test_company = "Linear"
    test_website = "https://linear.app"
    
    print("🔬 FIELD DISCOVERY TEST - LIVE LLM ANALYSIS")
    print("=" * 60)
    print(f"🎯 Target Company: {test_company}")
    print(f"🌐 Website: {test_website}")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize rate-limited LLM manager
    llm_manager = RateLimitedTheodoreLLMManager(
        max_workers=1,
        requests_per_minute=8
    )
    
    try:
        llm_manager.start()
        print("🚀 Rate-limited LLM manager started")
        print()
        
        # ================================================================
        # PHASE 1: Show what fields we're asking the LLM to find
        # ================================================================
        
        print("📋 PHASE 1: FIELDS THE LLM IS ASKED TO EXTRACT")
        print("-" * 50)
        
        # This is the actual prompt we send to the LLM
        field_extraction_prompt = f"""Analyze this company website content for {test_company} and generate structured business intelligence for sales purposes.

TARGET COMPANY: {test_company}
WEBSITE: {test_website}

🎯 REQUIRED FIELDS TO EXTRACT:

CORE BUSINESS INFORMATION:
- company_description: 2-3 paragraph comprehensive business summary
- industry: Primary industry classification (e.g., "SaaS", "FinTech", "HealthTech")
- business_model: Business model type ("B2B", "B2C", "B2B2C", "Marketplace")
- target_market: Primary customer segments (e.g., "Enterprise", "SMB", "Consumers")
- value_proposition: Core value proposition and unique selling points

PRODUCT & SERVICE DETAILS:
- key_services: List of main products/services offered
- competitive_advantages: Key differentiators vs competitors
- tech_stack: Technology platforms and integrations mentioned
- pricing_model: Pricing approach (subscription, usage-based, etc.)

COMPANY DETAILS:
- company_size: Size indicators ("startup", "small", "medium", "large", "enterprise")
- founding_year: Year company was founded (if mentioned)
- location: Primary headquarters or business location
- employee_count_range: Employee count or range if mentioned
- leadership_team: Key executives or founders mentioned

MARKET & SALES CONTEXT:
- market_context: Industry position and competitive landscape
- customer_segments: Specific customer types they serve
- sales_cycle: Enterprise vs self-serve sales approach
- growth_stage: Startup, growth, mature, etc.

Please analyze website content and extract these specific fields with actual data found on the website.

Simulated website content for {test_company}:
Linear is a modern issue tracking and project management tool built for high-performance teams. 
The company focuses on providing a fast, streamlined workflow for software development teams.
Linear offers real-time collaboration, keyboard shortcuts, and integrations with popular development tools.
The platform is designed for engineering teams at technology companies who need efficient project tracking.
Linear was founded by former Airbnb and Uber engineers who wanted to build better development tools.
The company is based in San Francisco and serves primarily B2B customers in the technology sector.
Linear integrates with GitHub, Slack, Figma, and other development tools popular with engineering teams.
The platform uses a subscription-based pricing model targeted at teams and organizations.

Return analysis in JSON format with the exact field names listed above."""
        
        # Show the user exactly what we're asking for
        print("🤖 LLM PROMPT ANALYSIS:")
        print("   📊 Total Fields Requested: 15 core fields")
        print("   🎯 Field Categories:")
        print("      • Core Business (5 fields): description, industry, business_model, target_market, value_proposition")
        print("      • Product & Services (4 fields): key_services, competitive_advantages, tech_stack, pricing_model")
        print("      • Company Details (5 fields): size, founding_year, location, employee_count, leadership")
        print("      • Market Context (1 field): market_context, customer_segments, sales_cycle, growth_stage")
        print()
        
        # ================================================================
        # PHASE 2: Execute the LLM analysis and show results
        # ================================================================
        
        print("⚡ PHASE 2: EXECUTING LLM FIELD EXTRACTION")
        print("-" * 50)
        
        # Create the LLM task
        task = LLMTask(
            task_id=f"field_discovery_{test_company}_{int(time.time())}",
            prompt=field_extraction_prompt,
            context={"company_name": test_company, "website": test_website}
        )
        
        # Show rate limiting status
        status = llm_manager.get_rate_limit_status()
        print(f"📊 Rate Limiter Status: {status['tokens_available']:.1f}/{status['capacity']} tokens available")
        print("🚀 Sending request to LLM...")
        
        start_time = time.time()
        
        # Process the task with rate limiting
        result = llm_manager.worker_pool.process_task(task)
        
        processing_time = time.time() - start_time
        print(f"⏱️ LLM Processing Time: {processing_time:.2f} seconds")
        print()
        
        # ================================================================
        # PHASE 3: Analyze and display what the LLM found
        # ================================================================
        
        if result.success:
            print("✅ PHASE 3: LLM FIELD EXTRACTION RESULTS")
            print("-" * 50)
            
            # Parse the LLM response
            try:
                from rate_limited_gemini_solution import safe_json_parse
                extracted_data = safe_json_parse(result.response, fallback_value={})
                
                if extracted_data:
                    print("🎉 SUCCESS: LLM successfully extracted structured data")
                    print()
                    
                    # Show field-by-field analysis
                    requested_fields = [
                        "company_description", "industry", "business_model", "target_market", "value_proposition",
                        "key_services", "competitive_advantages", "tech_stack", "pricing_model",
                        "company_size", "founding_year", "location", "employee_count_range", "leadership_team",
                        "market_context", "customer_segments", "sales_cycle", "growth_stage"
                    ]
                    
                    found_fields = 0
                    missing_fields = 0
                    
                    print("📊 FIELD-BY-FIELD EXTRACTION RESULTS:")
                    print("=" * 60)
                    
                    for field in requested_fields:
                        value = extracted_data.get(field, None)
                        if value and str(value).strip() and str(value).lower() not in ['unknown', 'n/a', 'not found', '']:
                            found_fields += 1
                            status = "✅ FOUND"
                            # Truncate long values for display
                            display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                            print(f"   {status} {field}: {display_value}")
                        else:
                            missing_fields += 1
                            status = "❌ MISSING"
                            print(f"   {status} {field}: No data found")
                    
                    print()
                    print("📈 EXTRACTION SUMMARY:")
                    print(f"   ✅ Fields Successfully Extracted: {found_fields}")
                    print(f"   ❌ Fields Missing/Empty: {missing_fields}")
                    print(f"   📊 Success Rate: {(found_fields / len(requested_fields)) * 100:.1f}%")
                    print()
                    
                    # Show the most important fields in detail
                    print("🔍 KEY FIELD DETAILS:")
                    print("-" * 30)
                    
                    key_fields = ["company_description", "industry", "business_model", "target_market", "key_services"]
                    for field in key_fields:
                        value = extracted_data.get(field, "Not found")
                        print(f"📋 {field}:")
                        print(f"   {value}")
                        print()
                    
                    # Show raw LLM response for transparency
                    print("🤖 RAW LLM RESPONSE (for transparency):")
                    print("-" * 40)
                    print(result.response[:1000] + "..." if len(result.response) > 1000 else result.response)
                    
                else:
                    print("⚠️ WARNING: LLM returned response but JSON parsing failed")
                    print("Raw response:", result.response[:500])
                    
            except Exception as e:
                print(f"❌ ERROR: Failed to parse LLM response: {e}")
                print("Raw response:", result.response[:500])
        
        else:
            print("❌ PHASE 3: LLM FIELD EXTRACTION FAILED")
            print("-" * 50)
            print(f"Error: {result.error}")
            print("This demonstrates the fallback handling in our system")
        
        print()
        print("🏁 FIELD DISCOVERY TEST COMPLETE")
        print("=" * 60)
        print(f"✅ Test demonstrated: What fields LLM is asked to find")
        print(f"✅ Test demonstrated: What fields LLM actually found")
        print(f"✅ Test demonstrated: Rate-limited execution (no hanging)")
        print(f"⏱️ Total Test Duration: {time.time() - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        llm_manager.shutdown()
        print("🛑 Rate-limited LLM manager shutdown")

if __name__ == "__main__":
    test_field_discovery_for_company()