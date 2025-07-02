#!/usr/bin/env python3

# Direct execution within the app context to test pipeline
import os
import sys
sys.path.append(os.getcwd())

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("🔍 MANUAL PIPELINE INVESTIGATION")
print("=" * 50)

# Check environment variables first
required_vars = ['PINECONE_API_KEY', 'PINECONE_INDEX_NAME', 'AWS_ACCESS_KEY_ID', 'GEMINI_API_KEY']
env_status = {}
for var in required_vars:
    value = os.getenv(var)
    env_status[var] = '✅ Set' if value else '❌ Missing'
    print(f"{var}: {env_status[var]}")

print("\n🧪 Testing imports...")
try:
    from src.models import CompanyIntelligenceConfig
    print("✅ CompanyIntelligenceConfig imported")
    
    from src.main_pipeline import TheodoreIntelligencePipeline
    print("✅ TheodoreIntelligencePipeline imported")
    
    print("\n🔧 Creating config...")
    config = CompanyIntelligenceConfig()
    print("✅ Config created")
    
    print("\n🚀 Attempting pipeline creation...")
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    print("✅ PIPELINE CREATED SUCCESSFULLY!")
    print(f"Pipeline type: {type(pipeline)}")
    print(f"Has scraper: {hasattr(pipeline, 'scraper') and pipeline.scraper is not None}")
    print(f"Has bedrock: {hasattr(pipeline, 'bedrock_client') and pipeline.bedrock_client is not None}")
    print(f"Has pinecone: {hasattr(pipeline, 'pinecone_client') and pipeline.pinecone_client is not None}")
    
    # Test if we can access app's pipeline variable
    print("\n🔍 Checking app's pipeline variable...")
    try:
        from app import pipeline as app_pipeline
        if app_pipeline:
            print("✅ App's pipeline variable is set!")
            print(f"App pipeline type: {type(app_pipeline)}")
        else:
            print("❌ App's pipeline variable is None")
    except Exception as e:
        print(f"❌ Could not import app pipeline: {e}")
        
except Exception as e:
    print(f"❌ Pipeline creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 SUMMARY:")
print(f"Environment: {sum(1 for v in env_status.values() if '✅' in v)}/{len(env_status)} variables set")
print("If pipeline creation worked here but fails in app, it's likely a Flask/import timing issue.")