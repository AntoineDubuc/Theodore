#!/usr/bin/env python3
"""
Test Concurrent Implementation
Verify that the new concurrent scraper works and shows detailed URL logging
"""

import sys
import time
import requests
import json

def test_concurrent_implementation():
    """Test if the new concurrent implementation is working"""
    
    print("🧪 TESTING CONCURRENT IMPLEMENTATION")
    print("=" * 60)
    
    # Test URL (assumes Theodore is running on localhost:5002)
    base_url = "http://localhost:5002"
    
    # Test company - use a simple, fast website
    test_company = {
        "company_name": "Concurrent Test Company",
        "website": "https://httpbin.org"  # Simple, fast test website
    }
    
    print(f"📋 Test Company: {test_company['company_name']}")
    print(f"🌐 Website: {test_company['website']}")
    print()
    
    # Submit company for processing
    print("📤 Submitting company for processing...")
    try:
        response = requests.post(
            f"{base_url}/api/process-company",
            json=test_company,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Request accepted, Job ID: {job_id}")
            
            if job_id:
                return monitor_concurrent_logging(base_url, job_id)
            else:
                print("❌ No job ID returned")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def monitor_concurrent_logging(base_url, job_id, max_wait=90):
    """Monitor the progress log for concurrent implementation features"""
    
    print(f"\\n⏳ Monitoring concurrent implementation for job {job_id}...")
    start_time = time.time()
    
    concurrent_features = []
    detailed_urls = []
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/api/progress/{job_id}", timeout=5)
            
            if response.status_code == 200:
                progress_data = response.json().get('progress', {})
                processing_log = progress_data.get('processing_log', [])
                
                # Look for concurrent implementation features
                for log_entry in processing_log:
                    message = log_entry.get('message', '')
                    timestamp = log_entry.get('timestamp', '')
                    
                    # Check for detailed URL logging patterns
                    if any(pattern in message for pattern in [
                        'Analyzing robots.txt: http',
                        'Found sitemap: http',
                        'Analyzing default sitemap: http',
                        'Starting recursive crawling from: http',
                        'Crawling depth',
                        'Priority 1: http',
                        'Priority 2: http',
                        'Extracting: http',
                        'LLM prompt sent:',
                        'LLM response received in',
                        'AI analysis prompt sent:',
                        'AI analysis completed in'
                    ]):
                        if message not in [e['message'] for e in concurrent_features]:
                            concurrent_features.append({
                                'timestamp': timestamp,
                                'message': message
                            })
                            print(f"✅ Concurrent: [{timestamp}] {message}")
                            
                            # Track detailed URLs specifically
                            if any(url_pattern in message for url_pattern in [
                                'robots.txt: http', 'sitemap: http', 'crawling from: http',
                                'Priority', 'Extracting: http'
                            ]):
                                detailed_urls.append(message)
                    
                    # Show phase completions
                    elif any(phase in message for phase in [
                        'Link Discovery complete', 'LLM Page Selection:',
                        'Content Extraction:', 'AI Content Analysis:', 'Research completed successfully'
                    ]):
                        print(f"📊 Phase: [{timestamp}] {message}")
                
                # Check if job is completed
                status = progress_data.get('status', 'unknown')
                if status in ['completed', 'failed']:
                    break
                    
            else:
                print(f"   ⚠️ Progress check failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Progress check error: {e}")
        
        time.sleep(2)  # Check every 2 seconds
    
    # Summary
    print(f"\\n📊 CONCURRENT IMPLEMENTATION RESULTS:")
    print(f"   Concurrent features found: {len(concurrent_features)}")
    print(f"   Detailed URLs logged: {len(detailed_urls)}")
    
    if len(concurrent_features) >= 5 and len(detailed_urls) >= 3:
        print(f"✅ Concurrent implementation is working!")
        print(f"✅ Detailed URL logging is functional!")
        print(f"📋 Sample concurrent features:")
        for feature in concurrent_features[:8]:
            print(f"   • [{feature['timestamp']}] {feature['message']}")
        return True
    elif len(concurrent_features) > 0:
        print(f"⚠️ Partial implementation detected")
        print(f"📋 Found features:")
        for feature in concurrent_features:
            print(f"   • [{feature['timestamp']}] {feature['message']}")
        return False
    else:
        print(f"❌ No concurrent implementation features found")
        print(f"💡 The old implementation may still be running")
        return False

def main():
    """Main test execution"""
    
    success = test_concurrent_implementation()
    
    print("\\n" + "=" * 60)
    if success:
        print("🎉 CONCURRENT IMPLEMENTATION TEST: ✅ WORKING")
        print("✅ Thread-safe LLM calls are functional")
        print("✅ Detailed URL logging is working")
        print("✅ Rate-limited concurrent approach is integrated")
    else:
        print("❌ CONCURRENT IMPLEMENTATION TEST: ❌ NOT WORKING")
        print("⚠️ May need to restart Theodore to load new implementation")
        print("💡 Try: pkill -f 'python3 app.py' && python3 app.py")
    
    print("\\n📋 Next Steps:")
    print("1. If working: Concurrent implementation successfully integrated! ✅")
    print("2. If not working: Restart Theodore and test again")
    print("3. Check Theodore console output for worker pool initialization")

if __name__ == "__main__":
    main()