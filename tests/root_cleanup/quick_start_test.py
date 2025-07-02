#!/usr/bin/env python3
"""
Quick test to see if app can start with fixes
"""

import os
import sys
import subprocess
import time

print("🚀 THEODORE QUICK START TEST")
print("=" * 40)

# Change to correct directory
os.chdir('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
print(f"Working directory: {os.getcwd()}")

# Test 1: Check if minimal app can start
print("\n1️⃣ Testing minimal app...")
try:
    # Start minimal app for 5 seconds
    process = subprocess.Popen([sys.executable, 'minimal_app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
    
    time.sleep(3)  # Give it time to start
    
    # Test if it's responding
    try:
        import requests
        response = requests.get('http://localhost:5002/', timeout=2)
        if response.status_code == 200:
            print("   ✅ Minimal app works!")
            minimal_works = True
        else:
            print(f"   ❌ Minimal app responded with {response.status_code}")
            minimal_works = False
    except:
        print("   ❌ Minimal app not responding")
        minimal_works = False
    
    # Stop minimal app
    process.terminate()
    time.sleep(1)
    
except Exception as e:
    print(f"   ❌ Minimal app failed: {e}")
    minimal_works = False

# Test 2: Try main app if minimal works
if minimal_works:
    print("\n2️⃣ Testing main app...")
    try:
        # Start main app
        process = subprocess.Popen([sys.executable, 'app.py'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, 
                                  text=True)
        
        time.sleep(5)  # Give it more time to start
        
        # Test if it's responding
        try:
            import requests
            response = requests.get('http://localhost:5002/', timeout=3)
            if response.status_code == 200:
                print("   ✅ Main app works!")
                
                # Test diagnostic endpoint
                diag_response = requests.get('http://localhost:5002/api/diagnostic', timeout=3)
                if diag_response.status_code == 200:
                    data = diag_response.json()
                    status = data.get('pipeline_status', 'unknown')
                    print(f"   🔧 Pipeline status: {status}")
                    
                    if status == 'success':
                        print("   🎉 PIPELINE IS WORKING!")
                    else:
                        print("   ⚠️  Pipeline needs attention")
                
                print("\n🎯 SUCCESS! App is running at:")
                print("   🌐 Main UI: http://localhost:5002")
                print("   🔍 Diagnostic: http://localhost:5002/diagnostic")
                
            else:
                print(f"   ❌ Main app responded with {response.status_code}")
        except:
            print("   ❌ Main app not responding")
        
        # Don't terminate - leave it running if successful
        
    except Exception as e:
        print(f"   ❌ Main app failed: {e}")
else:
    print("\n⚠️  Skipping main app test - minimal app failed")
    print("Check Python environment and dependencies")

print("\n📋 Test complete!")