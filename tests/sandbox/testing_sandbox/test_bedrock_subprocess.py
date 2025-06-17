#!/usr/bin/env python3
"""
Test script to see if BedrockClient works in subprocess
"""
import asyncio
import json
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

async def test_bedrock():
    try:
        print("🧪 TEST: Starting BedrockClient test...", file=sys.stderr)
        
        # Test 1: Basic imports
        print("🧪 TEST: Testing imports...", file=sys.stderr)
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        print("✅ TEST: BedrockClient imports successful", file=sys.stderr)
        
        # Test 2: BedrockClient initialization
        print("🧪 TEST: Testing BedrockClient initialization...", file=sys.stderr)
        start_time = time.time()
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        init_time = time.time() - start_time
        print(f"✅ TEST: BedrockClient initialized in {init_time:.2f}s", file=sys.stderr)
        
        # Test 3: Simple analyze_content call
        print("🧪 TEST: Testing analyze_content...", file=sys.stderr)
        start_time = time.time()
        
        response = bedrock_client.analyze_content("What is 2+2?")
        
        analysis_time = time.time() - start_time
        print(f"✅ TEST: analyze_content completed in {analysis_time:.2f}s", file=sys.stderr)
        print(f"✅ TEST: Response length: {len(response)}", file=sys.stderr)
        
        return {
            "success": True,
            "init_time": init_time,
            "analysis_time": analysis_time,
            "response_length": len(response),
            "response_preview": response[:100]
        }
            
    except Exception as e:
        print(f"❌ TEST: Error: {e}", file=sys.stderr)
        import traceback
        print(f"❌ TEST: Traceback: {traceback.format_exc()}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    print("🧪 TEST: Starting bedrock test...", file=sys.stderr)
    result = asyncio.run(test_bedrock())
    print(json.dumps(result, default=str))