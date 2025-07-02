#!/usr/bin/env python3
"""
Auto-restart script for Theodore app with health checks
"""

import os
import sys
import time
import subprocess
import requests
from datetime import datetime

print("🔄 THEODORE AUTO-RESTART SYSTEM")
print("=" * 40)

# Change to correct directory
os.chdir('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
print(f"Working directory: {os.getcwd()}")

def check_app_health():
    """Check if the app is running and healthy"""
    try:
        response = requests.get('http://localhost:5002/api/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_app():
    """Start the Theodore app"""
    print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] Starting Theodore app...")
    
    # Kill any existing processes on port 5002
    try:
        subprocess.run(['lsof', '-ti:5002'], capture_output=True, check=True, text=True)
        subprocess.run(['kill', '-9'] + subprocess.run(['lsof', '-ti:5002'], capture_output=True, text=True).stdout.strip().split(), check=False)
        time.sleep(2)
    except:
        pass
    
    # Start the app
    process = subprocess.Popen([sys.executable, 'app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
    
    # Give it time to start
    time.sleep(10)
    
    if check_app_health():
        print(f"   ✅ App started successfully!")
        return True
    else:
        print(f"   ❌ App failed to start or is unhealthy")
        return False

def main():
    """Main restart loop"""
    restart_count = 0
    max_restarts = 3
    
    while restart_count < max_restarts:
        print(f"\n🔍 [{datetime.now().strftime('%H:%M:%S')}] Checking app health...")
        
        if check_app_health():
            print("   ✅ App is healthy!")
            print("\n🎯 SUCCESS! Theodore is running at:")
            print("   🌐 Main UI: http://localhost:5002")
            print("   🔍 Health Check: http://localhost:5002/api/health")
            break
        else:
            restart_count += 1
            print(f"   ❌ App is down. Restart attempt {restart_count}/{max_restarts}")
            
            if start_app():
                print(f"   🎉 Restart successful!")
                break
            else:
                if restart_count < max_restarts:
                    print(f"   ⏳ Waiting 5 seconds before next attempt...")
                    time.sleep(5)
                else:
                    print(f"   💥 Max restarts reached. Manual intervention required.")
                    break

if __name__ == "__main__":
    main()