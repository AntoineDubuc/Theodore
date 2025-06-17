#!/usr/bin/env python3
"""
Automated Job Listings Crawler Test for Shake Shack
Tests the job_listings_crawler.py with detailed reporting and improvement recommendations
"""

import sys
import os
import json
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.job_listings_crawler import JobListingsCrawler
from src.bedrock_client import BedrockClient
from src.openai_client import SimpleOpenAIClient
from src.models import CompanyIntelligenceConfig

def test_job_crawler():
    """Run comprehensive test of job listings crawler"""
    
    # Test configuration
    company_name = "Shake Shack"
    website = "https://www.shakeshack.com"
    
    print(f"🧪 Starting Job Listings Crawler Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Company: {company_name}")
    print(f"🌐 Website: {website}")
    print("=" * 60)
    
    # Initialize crawler
    config = CompanyIntelligenceConfig()
    try:
        # Try to use OpenAI first, fallback to Bedrock
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key.startswith("sk-"):
            ai_client = SimpleOpenAIClient()
            print("✅ Using OpenAI for LLM analysis")
        else:
            ai_client = BedrockClient(config)
            print("✅ Using AWS Bedrock for LLM analysis")
            
        crawler = JobListingsCrawler(bedrock_client=ai_client if not openai_api_key else None, 
                                   openai_client=ai_client if openai_api_key else None)
        print("✅ Job Listings Crawler initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize crawler: {e}")
        return None
    
    # Run the test
    start_time = time.time()
    print(f"\n🚀 Starting crawl for {company_name}...")
    
    try:
        result = crawler.crawl_job_listings(company_name, website)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Crawl completed in {duration:.2f} seconds")
        print(f"📊 Result type: {type(result)}")
        
        # Generate detailed test report
        report = generate_test_report(company_name, website, result, duration)
        
        # Save report to markdown file
        report_filename = f"job_crawler_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"📄 Test report saved to: {report_filename}")
        
        # Print summary to console
        print_test_summary(result)
        
        return result
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"💥 Crawl failed after {error_time:.2f} seconds: {e}")
        
        # Generate error report
        error_report = generate_error_report(company_name, website, str(e), error_time)
        report_filename = f"job_crawler_error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(error_report)
            
        print(f"📄 Error report saved to: {report_filename}")
        return None

def generate_test_report(company_name, website, result, duration):
    """Generate comprehensive markdown test report"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# Job Listings Crawler Test Report

## Test Summary
- **Company**: {company_name}
- **Website**: {website}
- **Test Date**: {timestamp}
- **Duration**: {duration:.2f} seconds
- **Status**: {"✅ SUCCESS" if result.get('found_jobs') else "⚠️ PARTIAL SUCCESS" if 'job_listings' in result else "❌ FAILED"}

## Results Overview

### Job Listings Found
- **Has Job Listings**: {result.get('found_jobs', 'Unknown')}
- **Job Listings Info**: {result.get('job_listings', 'Not provided')}
- **Source**: {result.get('source', 'Unknown')}

### Career Page Discovery
- **Career Page Found**: {result.get('career_page_found', 'Unknown')}
- **Career Page URL**: {result.get('career_page_url', 'Not found')}
- **Steps Completed**: {result.get('steps_completed', 'Unknown')}

## Detailed Results

```json
{json.dumps(result, indent=2, default=str)}
```

## Analysis & Recommendations

### What Worked Well
"""

    # Analyze what worked well
    if result.get('found_jobs'):
        report += """
- ✅ **Job listings successfully discovered**
- ✅ **Crawler completed its primary objective**
- ✅ **Source identification working properly**
"""
    
    if result.get('career_page_found'):
        report += """
- ✅ **Career page discovery functioning**
- ✅ **Navigation logic working correctly**
"""
        
    if result.get('steps_completed', 0) >= 5:
        report += """
- ✅ **Comprehensive crawling process completed**
- ✅ **Multiple fallback mechanisms tested**
"""

    # Identify areas for improvement
    report += """
### Areas for Improvement
"""
    
    if not result.get('found_jobs'):
        report += """
- ⚠️ **Primary objective not achieved**: No job listings found
- 🔧 **Recommendation**: Enhance job listing detection patterns
- 🔧 **Recommendation**: Improve LLM prompts for job identification
"""
    
    if result.get('source') == 'google_search':
        report += """
- ⚠️ **Fallback dependency**: Relied on Google search
- 🔧 **Recommendation**: Improve direct website navigation
- 🔧 **Recommendation**: Enhance career page link detection
"""
        
    if duration > 30:
        report += """
- ⚠️ **Performance concern**: Crawl took longer than 30 seconds
- 🔧 **Recommendation**: Optimize timeout settings
- 🔧 **Recommendation**: Implement parallel processing where possible
"""

    # Technical recommendations
    report += """
### Technical Recommendations

#### 1. LLM Prompt Optimization
- Review and refine prompts for career page identification
- Add more specific job listing detection patterns
- Consider using different models for different tasks

#### 2. Website Navigation Improvements
- Enhance link filtering logic
- Add more career page URL patterns
- Implement better content analysis

#### 3. Performance Optimizations
- Reduce timeout values for faster failure detection
- Implement request caching
- Add parallel processing for multiple URL testing

#### 4. Error Handling Enhancements
- Add more specific error categorization
- Implement better fallback strategies
- Add retry mechanisms with exponential backoff

### Test Environment Details
- **Python Version**: {sys.version}
- **AI Client**: {"OpenAI" if "openai" in str(type(result)) else "AWS Bedrock"}
- **Google Search Available**: {bool(os.getenv('GOOGLE_API_KEY'))}

### Next Steps
1. **Immediate**: Test with 5-10 more companies to identify patterns
2. **Short-term**: Implement recommended LLM prompt improvements
3. **Medium-term**: Add performance optimizations and parallel processing
4. **Long-term**: Consider machine learning approach for career page detection

---
*Generated by Theodore Job Listings Crawler Test Suite*
"""
    
    return report

def generate_error_report(company_name, website, error_message, duration):
    """Generate error report for failed tests"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return f"""# Job Listings Crawler Error Report

## Error Summary
- **Company**: {company_name}
- **Website**: {website}
- **Test Date**: {timestamp}
- **Duration**: {duration:.2f} seconds
- **Status**: ❌ FAILED

## Error Details
```
{error_message}
```

## Potential Causes
1. **Network connectivity issues**
2. **Website blocking automated requests**
3. **API rate limiting**
4. **Invalid credentials**
5. **Code bugs or logic errors**

## Recommended Actions
1. **Check network connectivity**
2. **Verify API credentials in .env file**
3. **Review error logs for specific issues**
4. **Test with a simpler website first**
5. **Check if website has anti-bot protection**

## Environment Check
- **Google API Key**: {"✅ Present" if os.getenv('GOOGLE_API_KEY') else "❌ Missing"}
- **OpenAI API Key**: {"✅ Present" if os.getenv('OPENAI_API_KEY') else "❌ Missing"}
- **AWS Credentials**: {"✅ Present" if os.getenv('AWS_ACCESS_KEY_ID') else "❌ Missing"}

---
*Generated by Theodore Job Listings Crawler Test Suite*
"""

def print_test_summary(result):
    """Print concise test summary to console"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if result.get('found_jobs'):
        print("🎉 SUCCESS: Job listings found!")
        print(f"📋 Jobs: {result.get('job_listings', 'Details not available')}")
    else:
        print("⚠️ PARTIAL: No job listings found")
        print(f"📄 Info: {result.get('job_listings', 'No information available')}")
    
    print(f"🔗 Career page: {result.get('career_page_url', 'Not found')}")
    print(f"📡 Source: {result.get('source', 'Unknown')}")
    print(f"🎯 Steps completed: {result.get('steps_completed', 'Unknown')}")
    
    if 'details' in result and result['details']:
        print(f"🔍 Additional details available in full report")
    
    print("="*60)

if __name__ == "__main__":
    print("🧪 Theodore Job Listings Crawler Test Suite")
    print("🎯 Target: Shake Shack (https://www.shakeshack.com)")
    print()
    
    result = test_job_crawler()
    
    if result:
        print("\n✅ Test completed successfully")
        print("📄 Check the generated markdown report for detailed analysis")
    else:
        print("\n❌ Test failed")
        print("📄 Check the error report for troubleshooting guidance")