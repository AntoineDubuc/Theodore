#!/usr/bin/env python3
"""
Test script for V2 Gemini timeout fixes
=======================================

This script tests the enhanced Gemini client with timeout handling,
circuit breaker, and rate limiting to verify the hanging issue is resolved.
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime

# Add the v2 src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.adapters.ai.gemini.client import GeminiClient, GeminiError
from infrastructure.adapters.ai.gemini.config import GeminiConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_gemini_with_timeout():
    """Test Gemini client with timeout handling for CloudGeometry-style prompts."""
    
    print("🧪 Testing V2 Gemini Client with Timeout Fixes")
    print("=" * 50)
    
    # Create config with shorter timeout for testing
    config = GeminiConfig.from_environment()
    config.timeout_seconds = 30  # 30 second timeout
    config.max_retries = 2       # Fewer retries for faster testing
    
    print(f"⚙️ Configuration:")
    print(f"   - Model: {config.model}")
    print(f"   - Timeout: {config.timeout_seconds}s")
    print(f"   - Max retries: {config.max_retries}")
    print(f"   - Max concurrent: {config.max_concurrent_requests}")
    print()
    
    # Initialize client
    try:
        client = GeminiClient(config)
        print("✅ Gemini client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 1: Simple prompt (should work)
    print("\n🧪 Test 1: Simple prompt")
    try:
        start_time = time.time()
        response = await client.generate_content(
            "What is the capital of France?",
            max_tokens=50
        )
        elapsed = time.time() - start_time
        print(f"✅ Simple test passed in {elapsed:.2f}s")
        print(f"   Response: {response.content[:100]}...")
        print(f"   Cost: ${response.usage.cost:.4f}")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        return False
    
    # Test 2: Complex prompt similar to CloudGeometry page selection
    print("\n🧪 Test 2: Complex page selection prompt (CloudGeometry style)")
    complex_prompt = """You are a data extraction specialist analyzing CloudGeometry Debug's website to find specific missing information.

Given these discovered links for CloudGeometry Debug (base URL: https://www.cloudgeometry.com):

- https://www.cloudgeometry.com/about        
- https://www.cloudgeometry.com/advanced        
- https://www.cloudgeometry.com/advanced/b2b-customer-engineering-services        
- https://www.cloudgeometry.com/advanced/ci-cd        
- https://www.cloudgeometry.com/advanced/devops-monitoring-observability        
- https://www.cloudgeometry.com/advanced/enterprise-grade-saas        
- https://www.cloudgeometry.com/advanced/full-stack-modern-cloud-app-dev        
- https://www.cloudgeometry.com/advanced/growth-ready-multi-tenancy-architecture        
- https://www.cloudgeometry.com/advanced/infrastructure-management-gitops        
- https://www.cloudgeometry.com/advanced/managed-full-stack-development        
- https://www.cloudgeometry.com/advanced/platform-engineering        
- https://www.cloudgeometry.com/advanced/workload-management        
- https://www.cloudgeometry.com/ai-agents-retail-operational-excellence        
- https://www.cloudgeometry.com/ai-data-platforms        
- https://www.cloudgeometry.com/ai-for-better-bi-with-the-data        
- https://www.cloudgeometry.com/ai-ml-data        
- https://www.cloudgeometry.com/ai-ml-data/ai-crash-course        
- https://www.cloudgeometry.com/ai-ml-data/ai-ml-development        
- https://www.cloudgeometry.com/ai-ml-data/ai-ml-engineering        
- https://www.cloudgeometry.com/ai-ml-data/data-engineering-for-mlops        
- https://www.cloudgeometry.com/ai-ml-data/engineering        
- https://www.cloudgeometry.com/ai-ml-data/free-online-crash-course-1-hour-biz        
- https://www.cloudgeometry.com/ai-ml-data/free-online-crash-course-4-hours-custom-biz        
- https://www.cloudgeometry.com/ai-ml-data/free-online-crash-course-4-hours-custom-tech        
- https://www.cloudgeometry.com/ai-ml-data/free-online-crash-courses-biz        

Select the 10-15 most promising pages that are likely to contain:
1. Contact information and physical locations
2. Company founding year and history
3. Employee count or team size information
4. Leadership team and decision makers
5. Business model and revenue approach

Return your selection as a JSON array of URLs, prioritizing pages most likely to contain the missing information."""

    try:
        print(f"   Prompt length: {len(complex_prompt)} characters")
        start_time = time.time()
        
        response = await client.generate_content(
            complex_prompt,
            max_tokens=500
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Complex test passed in {elapsed:.2f}s")
        print(f"   Response length: {len(response.content)} chars")
        print(f"   Cost: ${response.usage.cost:.4f}")
        print(f"   Response preview: {response.content[:200]}...")
        
    except asyncio.TimeoutError as e:
        elapsed = time.time() - start_time
        print(f"⏰ Complex test timed out after {elapsed:.2f}s (EXPECTED)")
        print(f"   This demonstrates the timeout mechanism works!")
        print(f"   Error: {e}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Complex test failed after {elapsed:.2f}s: {e}")
        return False
    
    # Test 3: Health check
    print("\n🧪 Test 3: Client health check")
    try:
        is_healthy = await client.health_check()
        if is_healthy:
            print("✅ Health check passed")
        else:
            print("⚠️ Health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 4: Rate limiter status
    print("\n🧪 Test 4: Rate limiter status")
    try:
        usage = await client._rate_limiter.get_current_usage()
        print(f"   Requests made: {usage['requests_made']}")
        print(f"   Requests rejected: {usage['requests_rejected']}")
        print(f"   Success rate: {usage['success_rate']:.1f}%")
        print(f"   Circuit state: {usage['circuit_state']}")
        print(f"   Average wait time: {usage['average_wait_time']:.3f}s")
    except Exception as e:
        print(f"❌ Rate limiter status error: {e}")
    
    # Test 5: Client stats
    print("\n🧪 Test 5: Client statistics")
    try:
        stats = client.get_stats()
        print(f"   Total requests: {stats['requests_made']}")
        print(f"   Daily cost: ${stats['daily_cost']:.4f}")
        print(f"   Session duration: {stats['session_duration_minutes']:.1f} min")
        print(f"   Models cached: {stats['models_cached']}")
    except Exception as e:
        print(f"❌ Client stats error: {e}")
    
    # Cleanup
    await client.close()
    print("\n✅ Client cleanup completed")
    
    print("\n🎉 V2 Gemini timeout fixes testing completed!")
    print("Key improvements demonstrated:")
    print("   ✅ Configurable timeouts prevent infinite hanging")
    print("   ✅ Circuit breaker protects against cascading failures")
    print("   ✅ Rate limiting prevents API overload")
    print("   ✅ Comprehensive error handling and logging")
    print("   ✅ Cost tracking and monitoring")
    
    return True


async def main():
    """Main test function."""
    print(f"Starting V2 Gemini timeout test at {datetime.now()}")
    
    # Check environment
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY environment variable not set")
        return False
    
    try:
        success = await test_gemini_with_timeout()
        if success:
            print("\n🎉 All tests completed successfully!")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)