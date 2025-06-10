#!/usr/bin/env python3
"""
Quick test for V2 research with a simpler company
"""

import asyncio
import aiohttp

async def test_quick_research():
    """Test with a simpler company site"""
    
    print("🧪 Testing V2 Quick Research")
    print("=" * 40)
    
    # Simpler test company
    test_company = {
        "company_name": "Example Company", 
        "website_url": "https://example.com"
    }
    
    base_url = "http://localhost:5004"
    
    async with aiohttp.ClientSession() as session:
        print(f"🚀 Starting research for {test_company['company_name']}...")
        
        # Start research
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
        print(f"📋 Job ID: {job_id}")
        
        # Quick polling for completion
        for i in range(30):
            try:
                async with session.get(f"{base_url}/api/progress/current?job_id={job_id}") as response:
                    progress_data = await response.json()
                    
                if progress_data.get("success") and progress_data.get("progress"):
                    progress = progress_data["progress"]
                    status = progress.get("status")
                    
                    print(f"[{i:2d}] Status: {status}")
                    
                    if status == "completed":
                        print(f"✅ Research completed!")
                        results = progress.get("results", {})
                        print(f"📊 Pages analyzed: {results.get('pages_analyzed', 'N/A')}")
                        print(f"📝 Analysis available: {'Yes' if results.get('analysis') else 'No'}")
                        
                        # Show a snippet of the analysis if available
                        if results.get('analysis'):
                            analysis_snippet = results['analysis'][:200] + "..." if len(results['analysis']) > 200 else results['analysis']
                            print(f"📋 Analysis snippet: {analysis_snippet}")
                        return
                    elif status == "failed":
                        print(f"❌ Research failed: {progress.get('error')}")
                        return
                        
            except Exception as e:
                print(f"[{i:2d}] Error: {e}")
            
            await asyncio.sleep(1)
        
        print("⏰ Test timeout")

if __name__ == "__main__":
    asyncio.run(test_quick_research())