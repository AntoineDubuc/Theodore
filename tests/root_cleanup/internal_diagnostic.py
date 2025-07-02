#!/usr/bin/env python3
"""
Internal diagnostic - run within the app context
"""

import os
import sys
sys.path.append(os.getcwd())

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("🔍 INTERNAL DIAGNOSTIC - DIRECT COMPONENT TESTING")
print("=" * 60)

# Test environment variables first
print("1️⃣ ENVIRONMENT VARIABLES:")
env_vars = {
    'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
    'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME'),
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
}

env_issues = []
for key, value in env_vars.items():
    if value:
        # Show partial key for security
        masked = f"{value[:6]}...{value[-4:]}" if len(value) > 10 else "***"
        print(f"   ✅ {key}: {masked}")
    else:
        print(f"   ❌ {key}: NOT SET")
        env_issues.append(key)

if env_issues:
    print(f"\n⚠️  Missing environment variables: {', '.join(env_issues)}")
    print("   This is likely the root cause!")

print("\n2️⃣ TESTING INDIVIDUAL COMPONENTS:")

# Test CompanyIntelligenceConfig
print("   Testing CompanyIntelligenceConfig...")
try:
    from src.models import CompanyIntelligenceConfig
    config = CompanyIntelligenceConfig()
    print("   ✅ CompanyIntelligenceConfig: SUCCESS")
except Exception as e:
    print(f"   ❌ CompanyIntelligenceConfig: FAILED - {e}")

# Test BedrockClient
print("   Testing BedrockClient...")
try:
    from src.bedrock_client import BedrockClient
    bedrock_client = BedrockClient(config)
    print("   ✅ BedrockClient: SUCCESS")
except Exception as e:
    print(f"   ❌ BedrockClient: FAILED - {e}")

# Test GeminiClient
print("   Testing GeminiClient...")
try:
    from src.gemini_client import GeminiClient
    gemini_client = GeminiClient(config)
    print("   ✅ GeminiClient: SUCCESS")
except Exception as e:
    print(f"   ❌ GeminiClient: FAILED - {e}")

# Test PineconeClient
print("   Testing PineconeClient...")
try:
    from src.pinecone_client import PineconeClient
    pinecone_client = PineconeClient(
        config,
        env_vars['PINECONE_API_KEY'],
        os.getenv('PINECONE_ENVIRONMENT'),
        env_vars['PINECONE_INDEX_NAME']
    )
    print("   ✅ PineconeClient: SUCCESS")
except Exception as e:
    print(f"   ❌ PineconeClient: FAILED - {e}")

print("\n3️⃣ TESTING FULL PIPELINE:")
try:
    from src.main_pipeline import TheodoreIntelligencePipeline
    
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=env_vars['PINECONE_API_KEY'],
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=env_vars['PINECONE_INDEX_NAME']
    )
    print("   ✅ FULL PIPELINE: SUCCESS!")
    print(f"   Pipeline type: {type(pipeline)}")
    
    # Test components
    components = {
        'scraper': hasattr(pipeline, 'scraper') and pipeline.scraper is not None,
        'bedrock_client': hasattr(pipeline, 'bedrock_client') and pipeline.bedrock_client is not None,
        'gemini_client': hasattr(pipeline, 'gemini_client') and pipeline.gemini_client is not None,
        'pinecone_client': hasattr(pipeline, 'pinecone_client') and pipeline.pinecone_client is not None
    }
    
    print("   Component Check:")
    for component, status in components.items():
        status_str = "✅ OK" if status else "❌ Missing"
        print(f"      {component}: {status_str}")
        
except Exception as e:
    print(f"   ❌ FULL PIPELINE: FAILED - {e}")
    import traceback
    print("\n   Full traceback:")
    traceback.print_exc()

print("\n📋 SUMMARY:")
print("If all components show SUCCESS, the issue is in the Flask app initialization.")
print("If any component shows FAILED, that's the root cause to fix.")

# Save results to file so we can read them
try:
    with open('diagnostic_results.txt', 'w') as f:
        f.write("DIAGNOSTIC RESULTS\n")
        f.write("==================\n")
        f.write(f"Environment Issues: {env_issues}\n")
        f.write("Component testing completed - see console output\n")
    print("\n💾 Results saved to diagnostic_results.txt")
except:
    pass