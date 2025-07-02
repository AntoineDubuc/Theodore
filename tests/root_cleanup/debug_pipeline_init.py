#!/usr/bin/env python3
"""
Debug pipeline initialization to find why it's failing
"""

import os
import sys
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

print("🔍 DEBUGGING PIPELINE INITIALIZATION")
print("=" * 50)

# Check environment variables
required_env_vars = [
    'PINECONE_API_KEY',
    'PINECONE_INDEX_NAME',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'GEMINI_API_KEY'
]

print("📋 Environment Variables:")
for var in required_env_vars:
    value = os.getenv(var)
    if value:
        # Show first/last few chars for security
        if len(value) > 10:
            display_value = f"{value[:6]}...{value[-4:]}"
        else:
            display_value = "***"
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NOT SET")

print("\n🔧 Testing Pipeline Components:")

# Test config
try:
    from src.models import CompanyIntelligenceConfig
    config = CompanyIntelligenceConfig()
    print("  ✅ CompanyIntelligenceConfig: OK")
except Exception as e:
    print(f"  ❌ CompanyIntelligenceConfig: {e}")

# Test TheodoreIntelligencePipeline import
try:
    from src.main_pipeline import TheodoreIntelligencePipeline
    print("  ✅ TheodoreIntelligencePipeline import: OK")
except Exception as e:
    print(f"  ❌ TheodoreIntelligencePipeline import: {e}")
    sys.exit(1)

# Test pipeline initialization step by step
print("\n🚀 Testing Pipeline Initialization:")

try:
    print("  Step 1: Creating pipeline...")
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    print("  ✅ Pipeline created successfully!")
    
    # Test pipeline components
    print("  Step 2: Testing components...")
    print(f"    Scraper: {hasattr(pipeline, 'scraper') and pipeline.scraper is not None}")
    print(f"    Bedrock: {hasattr(pipeline, 'bedrock_client') and pipeline.bedrock_client is not None}")
    print(f"    Gemini: {hasattr(pipeline, 'gemini_client') and pipeline.gemini_client is not None}")
    print(f"    Pinecone: {hasattr(pipeline, 'pinecone_client') and pipeline.pinecone_client is not None}")
    
    print("\n🎉 Pipeline initialization successful!")
    
except Exception as e:
    print(f"  ❌ Pipeline initialization failed: {e}")
    import traceback
    traceback.print_exc()