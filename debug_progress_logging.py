#!/usr/bin/env python3
"""
Debug Progress Logging
Test if the enhanced logging is working when Theodore processes a company
"""

import sys
import time
import requests
import json

def test_progress_logging():
    """Test if enhanced logging appears in progress data"""
    
    print("🧪 TESTING ENHANCED PROGRESS LOGGING")
    print("=" * 60)
    
    # Test URL (assumes Theodore is running on localhost:5002)
    base_url = "http://localhost:5002"
    
    # Test company
    test_company = {
        "company_name": "Test Enhanced Logging",
        "website": "https://anthropic.com"  # Known working website
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
                return monitor_enhanced_logging(base_url, job_id)
            else:
                print("❌ No job ID returned")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def monitor_enhanced_logging(base_url, job_id, max_wait=60):
    """Monitor the progress log for enhanced logging messages"""
    
    print(f"\n⏳ Monitoring enhanced logging for job {job_id}...")
    start_time = time.time()
    
    enhanced_messages = []
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/api/progress/{job_id}", timeout=5)
            
            if response.status_code == 200:
                progress_data = response.json().get('progress', {})
                processing_log = progress_data.get('processing_log', [])
                
                # Look for enhanced messages
                for log_entry in processing_log:
                    message = log_entry.get('message', '')
                    timestamp = log_entry.get('timestamp', '')
                    
                    # Check for our enhanced logging patterns
                    if any(pattern in message for pattern in [
                        'Analyzing robots.txt:', 
                        'Analyzing sitemap.xml:',
                        'Starting recursive crawling',
                        'Crawling depth',
                        'Links being sent to LLM',
                        'Extracting:'
                    ]):
                        if message not in [e['message'] for e in enhanced_messages]:
                            enhanced_messages.append({
                                'timestamp': timestamp,
                                'message': message
                            })
                            print(f"✅ Enhanced: [{timestamp}] {message}")
                    else:
                        # Show old-style messages for comparison
                        if 'Link Discovery:' in message or 'LLM Page Selection:' in message:
                            print(f"⚠️  Generic: [{timestamp}] {message}")
                
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
    print(f"\n📊 ENHANCED LOGGING RESULTS:")
    print(f"   Enhanced messages found: {len(enhanced_messages)}")
    
    if enhanced_messages:
        print(f"✅ Enhanced logging is working!")
        print(f"📋 Sample enhanced messages:")
        for msg in enhanced_messages[:5]:
            print(f"   • [{msg['timestamp']}] {msg['message']}")
        return True
    else:
        print(f"❌ No enhanced logging messages found")
        print(f"💡 The enhanced logging may not be working or Theodore needs restart")
        return False

def main():
    """Main test execution"""
    
    success = test_progress_logging()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ENHANCED LOGGING TEST: ✅ WORKING")
        print("✅ The enhanced logging system is functional")
        print("✅ Detailed URLs and progress are being logged")
    else:
        print("❌ ENHANCED LOGGING TEST: ❌ NOT WORKING")
        print("⚠️ Enhanced logging is not appearing in UI progress")
        print("💡 Try restarting Theodore: python3 app.py")
    
    print("\n📋 Next Steps:")
    print("1. If working: Enhanced logging is ready ✅")
    print("2. If not working: Restart Theodore and test again")
    print("3. Check console output of Theodore for enhanced messages")

if __name__ == "__main__":
    main()