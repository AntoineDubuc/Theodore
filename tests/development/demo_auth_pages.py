#!/usr/bin/env python3
"""
Demo Script: Beautiful Authentication Pages
Opens the stunning login and registration pages in the browser
"""

import webbrowser
import time
import sys

def demo_auth_pages():
    """Demo the beautiful authentication pages"""
    
    print("🎨 THEODORE AUTHENTICATION PAGES DEMO")
    print("=" * 60)
    print()
    
    print("✨ Features showcased:")
    print("   🌟 Animated gradient backgrounds")
    print("   🎭 Floating particle effects")
    print("   💎 Glass morphism design")
    print("   🔮 Glowing gradient text")
    print("   🚀 Smooth animations & transitions")
    print("   💫 Interactive form elements")
    print("   🎪 Loading states with shimmer effects")
    print("   🎨 Beautiful hover effects")
    print()
    
    # Check if app is running
    import requests
    try:
        response = requests.get("http://localhost:5002/api/health", timeout=3)
        if response.status_code != 200:
            print("❌ Theodore app is not responding properly")
            print("Please start Theodore with: python3 app.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ Theodore app is not running")
        print("Please start Theodore with: python3 app.py")
        return False
    
    print("🚀 Opening beautiful authentication pages...")
    print()
    
    # Open login page
    print("1️⃣ Opening Login Page (with amazing animations)...")
    login_url = "http://localhost:5002/auth/login"
    webbrowser.open(login_url)
    print(f"   📱 {login_url}")
    
    time.sleep(2)
    
    # Open registration page
    print("2️⃣ Opening Registration Page (with password validation)...")
    register_url = "http://localhost:5002/auth/register"
    webbrowser.open(register_url)
    print(f"   📱 {register_url}")
    
    print()
    print("🎉 DEMO FEATURES TO TRY:")
    print("━" * 60)
    print("🔮 Login Page:")
    print("   • Watch the floating shapes animate")
    print("   • See the shimmering card effects")
    print("   • Try the smooth focus transitions")
    print("   • Hover over the sign-in button")
    print("   • Click 'Sign up' link animation")
    print()
    print("🚀 Registration Page:")
    print("   • Type in the password field")
    print("   • Watch real-time validation indicators")
    print("   • See requirements turn green with ✓")
    print("   • Try the animated form transitions")
    print("   • Experience the loading button effects")
    print()
    print("💡 UI/UX Features:")
    print("   • Glassmorphism design with backdrop blur")
    print("   • Animated gradient backgrounds")
    print("   • Smooth staggered form animations")
    print("   • Interactive hover states")
    print("   • Beautiful error/success alerts")
    print("   • Professional typography (Inter font)")
    print()
    print("🎨 Color Palette:")
    print("   • Purple (#a855f7) → Blue (#3b82f6) gradients")
    print("   • Dark theme with transparency")
    print("   • Soft glowing effects")
    print("   • Elegant contrast ratios")
    print()
    
    return True

if __name__ == "__main__":
    print("🎭 BEAUTIFUL AUTHENTICATION SYSTEM DEMO")
    print("=" * 60)
    
    success = demo_auth_pages()
    
    if success:
        print("✅ DEMO LAUNCHED SUCCESSFULLY!")
        print("Enjoy exploring the beautiful authentication pages! 🎨✨")
    else:
        print("❌ DEMO FAILED")
        print("Please ensure Theodore is running first.")
        
    print()
    input("Press Enter to exit...")