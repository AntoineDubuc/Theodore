#!/usr/bin/env python3
"""
Test credential detection to see why the check is failing
"""
import os
import sys
sys.path.append(os.getcwd())

def test_env_loading():
    print("🔍 Testing environment variable loading...")
    
    # Test direct access
    print(f"Direct AWS_ACCESS_KEY_ID: '{os.getenv('AWS_ACCESS_KEY_ID', 'NOT_FOUND')}'")
    print(f"Direct AWS_SECRET_ACCESS_KEY: '{os.getenv('AWS_SECRET_ACCESS_KEY', 'NOT_FOUND')}'")
    print(f"Direct AWS_DEFAULT_REGION: '{os.getenv('AWS_DEFAULT_REGION', 'NOT_FOUND')}'")
    print(f"Direct AWS_REGION: '{os.getenv('AWS_REGION', 'NOT_FOUND')}'")
    
    # Test with dotenv loading
    print("\n🔍 Testing with dotenv loading...")
    from dotenv import load_dotenv
    load_dotenv()
    
    print(f"After dotenv AWS_ACCESS_KEY_ID: '{os.getenv('AWS_ACCESS_KEY_ID', 'NOT_FOUND')}'")
    print(f"After dotenv AWS_SECRET_ACCESS_KEY: '{os.getenv('AWS_SECRET_ACCESS_KEY', 'NOT_FOUND')}'")
    print(f"After dotenv AWS_DEFAULT_REGION: '{os.getenv('AWS_DEFAULT_REGION', 'NOT_FOUND')}'")
    print(f"After dotenv AWS_REGION: '{os.getenv('AWS_REGION', 'NOT_FOUND')}'")
    
    # Test the credential check logic exactly as used in scraper
    print("\n🔍 Testing credential check logic...")
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION')
    
    print(f"aws_access_key: {bool(aws_access_key)} ('{aws_access_key[:10] if aws_access_key else 'None'}...')")
    print(f"aws_secret_key: {bool(aws_secret_key)} ('{aws_secret_key[:10] if aws_secret_key else 'None'}...')")
    print(f"aws_region: {bool(aws_region)} ('{aws_region}')")
    
    if not aws_access_key or not aws_secret_key:
        print("❌ WOULD FAIL: Missing AWS access key or secret key")
        return False
    
    if not aws_region:
        print("❌ WOULD FAIL: Missing AWS region") 
        return False
    
    print("✅ WOULD PASS: All credentials found")
    return True

def test_bedrock_client_creation():
    print("\n🔍 Testing BedrockClient creation with credentials...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        print("✅ BedrockClient created successfully")
        
        # Test a simple call
        print("🧪 Testing analyze_content call...")
        import time
        start_time = time.time()
        try:
            response = bedrock_client.analyze_content("What is 2+2?")
            call_time = time.time() - start_time
            print(f"✅ analyze_content completed in {call_time:.2f}s")
            print(f"Response length: {len(response)}")
            print(f"Response preview: '{response[:100]}...'")
            return True
        except Exception as e:
            call_time = time.time() - start_time
            print(f"❌ analyze_content failed in {call_time:.2f}s: {e}")
            return False
            
    except Exception as e:
        print(f"❌ BedrockClient creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CREDENTIAL DETECTION TEST")
    print("=" * 50)
    
    cred_check = test_env_loading()
    bedrock_check = test_bedrock_client_creation()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"Credential Detection: {'✅ PASS' if cred_check else '❌ FAIL'}")
    print(f"BedrockClient Test: {'✅ PASS' if bedrock_check else '❌ FAIL'}")
    
    if cred_check and bedrock_check:
        print("🎉 All tests passed - credentials should work!")
    else:
        print("🚨 Something is wrong with credential setup")