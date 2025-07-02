#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd())

print("Checking critical imports...")

try:
    from src.models import CompanyIntelligenceConfig
    print("✅ CompanyIntelligenceConfig")
except Exception as e:
    print(f"❌ CompanyIntelligenceConfig: {e}")

try:
    from src.main_pipeline import TheodoreIntelligencePipeline  
    print("✅ TheodoreIntelligencePipeline")
except Exception as e:
    print(f"❌ TheodoreIntelligencePipeline: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    pinecone_key = os.getenv('PINECONE_API_KEY')
    pinecone_index = os.getenv('PINECONE_INDEX_NAME')
    
    print(f"Pinecone Key: {'✅ Set' if pinecone_key else '❌ Missing'}")
    print(f"Pinecone Index: {pinecone_index or '❌ Missing'}")
    
except Exception as e:
    print(f"❌ Environment check: {e}")

print("\nAttempting minimal pipeline creation...")
try:
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    print("✅ Pipeline created successfully!")
except Exception as e:
    print(f"❌ Pipeline creation failed: {e}")
    import traceback
    traceback.print_exc()