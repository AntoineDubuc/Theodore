#!/usr/bin/env python3
"""
Test the async progress system for V2 Theodore
"""

import asyncio
import aiohttp
import json
import time

async def test_async_research():
    """Test the async research endpoint and progress polling"""
    
    print("🧪 Testing V2 Async Research System")
    print("=" * 50)
    
    # Test company data
    test_company = {
        "company_name": "Tesla",
        "website_url": "https://tesla.com"
    }
    
    base_url = "http://localhost:5004"
    
    async with aiohttp.ClientSession() as session:
        print(f"🚀 Starting research for {test_company['company_name']}...")
        
        # Step 1: Start async research
        async with session.post(
            f"{base_url}/api/v2/research/start",
            json=test_company,
            headers={"Content-Type": "application/json"}
        ) as response:
            start_result = await response.json()
            
        if not start_result.get("success"):
            print(f"❌ Failed to start research: {start_result.get('error')}")
            return
            
        job_id = start_result["job_id"]
        print(f"📋 Started job {job_id}")
        print(f"✅ Research job started successfully!")
        
        # Step 2: Poll for progress updates
        print("\n🔄 Polling for progress updates...")
        poll_count = 0
        max_polls = 60  # 60 seconds max
        
        while poll_count < max_polls:
            try:
                async with session.get(f"{base_url}/api/progress/current?job_id={job_id}") as response:
                    progress_data = await response.json()
                    
                if progress_data.get("success") and progress_data.get("progress"):
                    progress = progress_data["progress"]
                    status = progress.get("status", "unknown")
                    
                    print(f"[{poll_count:2d}] Status: {status}")
                    
                    # Show current phase details
                    phases = progress.get("phases", {})
                    for phase_name, phase_data in phases.items():
                        phase_status = phase_data.get("status", "unknown")
                        if phase_status == "running":
                            current_url = phase_data.get("current_url")
                            progress_step = phase_data.get("progress_step")
                            status_message = phase_data.get("status_message")
                            
                            details = []
                            if progress_step:
                                details.append(f"Step: {progress_step}")
                            if current_url:
                                details.append(f"URL: {current_url[:50]}...")
                            if status_message:
                                details.append(f"Message: {status_message}")
                            
                            detail_str = " | ".join(details) if details else "Processing..."
                            print(f"     📍 {phase_name}: {detail_str}")
                    
                    # Check for completion
                    if status == "completed":
                        print(f"\n✅ Research completed!")
                        
                        # Check if we have results
                        if progress.get("results"):
                            results = progress["results"]
                            print(f"📊 Results: {results.get('pages_analyzed', 'N/A')} pages analyzed")
                            print(f"📝 Analysis length: {len(results.get('analysis', ''))}")
                        break
                    elif status == "failed":
                        print(f"\n❌ Research failed: {progress.get('error', 'Unknown error')}")
                        break
                else:
                    print(f"[{poll_count:2d}] No progress data available")
                
            except Exception as e:
                print(f"[{poll_count:2d}] Error polling progress: {e}")
            
            poll_count += 1
            await asyncio.sleep(1)
        
        if poll_count >= max_polls:
            print(f"\n⏰ Polling timeout reached after {max_polls} seconds")

if __name__ == "__main__":
    asyncio.run(test_async_research())