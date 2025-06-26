#!/usr/bin/env python3
"""
Debug Authentication Issue
Tests the password hashing and verification process
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def debug_auth_issue():
    """Debug the authentication password issue"""
    
    print("🔍 DEBUGGING AUTHENTICATION ISSUE")
    print("=" * 60)
    
    try:
        from auth_models import User, UserRegistration
        
        # Test password hashing
        print("1️⃣ Testing password hashing...")
        test_password = "TestPassword123"
        
        user = User(
            email="debug@test.com",
            username="debuguser",
            password_hash=""
        )
        
        print(f"Original password: {test_password}")
        user.set_password(test_password)
        print(f"Password hash: {user.password_hash}")
        
        # Test password verification
        print("\n2️⃣ Testing password verification...")
        correct_result = user.check_password(test_password)
        wrong_result = user.check_password("wrongpassword")
        
        print(f"Correct password check: {correct_result}")
        print(f"Wrong password check: {wrong_result}")
        
        if correct_result and not wrong_result:
            print("✅ Password hashing/verification works correctly")
        else:
            print("❌ Password hashing/verification has issues")
            
        # Test UserRegistration validation
        print("\n3️⃣ Testing UserRegistration validation...")
        
        try:
            registration = UserRegistration(
                email="debug@test.com",
                username="debuguser",
                password=test_password,
                confirm_password=test_password
            )
            print("✅ UserRegistration validation works")
        except Exception as e:
            print(f"❌ UserRegistration validation failed: {e}")
            
        # Test database interaction
        print("\n4️⃣ Testing database operations...")
        
        try:
            from auth_service import AuthService
            import os
            
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            if not pinecone_api_key:
                print("❌ No Pinecone API key found")
                return
                
            auth_service = AuthService(pinecone_api_key)
            
            # Try to find the user we just registered
            existing_user = auth_service.get_user_by_email("test3@theodore.ai")
            if existing_user:
                print(f"✅ Found user: {existing_user.email}")
                print(f"Password hash: {existing_user.password_hash}")
                
                # Test password verification with the found user
                test_result = existing_user.check_password("TestPassword123")
                print(f"Password verification result: {test_result}")
                
                if not test_result:
                    print("❌ Password verification failed for existing user!")
                    print("This explains the login issue.")
                else:
                    print("✅ Password verification works for existing user")
                    
            else:
                print("❌ Could not find recently registered user")
                
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_auth_issue()