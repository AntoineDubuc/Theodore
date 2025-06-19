#!/usr/bin/env python3
"""
Fix Strategy 3: Hybrid approach - direct execution with optional subprocess fallback
"""

import sys
import os
sys.path.append('src')

def create_hybrid_solution():
    """
    Create a hybrid solution that prefers direct execution but can fallback to subprocess
    """
    
    hybrid_code = '''
class IntelligentCompanyScraperHybrid:
    """Hybrid scraper: direct execution with subprocess fallback"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.scraper = IntelligentCompanyScraper(config, bedrock_client)
        self.prefer_direct = True  # Default to direct execution
        
    def scrape_company(self, company_data: CompanyData, job_id: str = None, timeout: int = None) -> CompanyData:
        """Hybrid execution with intelligent fallback"""
        
        if timeout is None:
            timeout = getattr(self.config, 'scraper_timeout', 120)
            
        print(f"🔬 HYBRID: Starting scrape for '{company_data.name}'")
        
        # Strategy 1: Try direct execution first (fast, reliable)
        if self.prefer_direct:
            try:
                print(f"🚀 HYBRID: Attempting direct execution...")
                result = self._direct_execution(company_data, job_id, timeout)
                
                # Validate result quality
                if self._is_good_result(result):
                    print(f"✅ HYBRID: Direct execution succeeded ({len(result.company_description or '')} chars)")
                    return result
                else:
                    print(f"⚠️ HYBRID: Direct execution gave poor results, trying subprocess...")
                    
            except Exception as e:
                print(f"❌ HYBRID: Direct execution failed: {e}")
                print(f"🔄 HYBRID: Falling back to subprocess...")
        
        # Strategy 2: Fallback to fixed subprocess
        try:
            result = self._subprocess_execution(company_data, job_id, timeout)
            print(f"🔄 HYBRID: Subprocess completed ({len(result.company_description or '')} chars)")
            return result
            
        except Exception as e:
            print(f"❌ HYBRID: Both methods failed, returning error result")
            company_data.scrape_status = "failed"
            company_data.scrape_error = f"Both direct and subprocess execution failed: {e}"
            return company_data
    
    def _direct_execution(self, company_data: CompanyData, job_id: str, timeout: int) -> CompanyData:
        """Direct async execution - preferred method"""
        import asyncio
        import signal
        
        # Set timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Direct execution timed out after {timeout}s")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = asyncio.run(
                self.scraper.scrape_company_intelligent(company_data, job_id)
            )
            signal.alarm(0)  # Cancel timeout
            return result
            
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            raise e
    
    def _subprocess_execution(self, company_data: CompanyData, job_id: str, timeout: int) -> CompanyData:
        """Fixed subprocess execution with proper error handling"""
        import subprocess
        import json
        import tempfile
        
        # Create input file
        input_data = {
            "company_name": company_data.name,
            "website": company_data.website, 
            "job_id": job_id,
            "timeout": timeout
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name
        
        # Simple, robust subprocess script
        script = f"""
import sys
import os
import json
import asyncio
sys.path.append('{os.getcwd()}')

from dotenv import load_dotenv
load_dotenv()

async def main():
    try:
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyData, CompanyIntelligenceConfig
        
        # Load input
        with open('{input_file}', 'r') as f:
            data = json.load(f)
        
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        company = CompanyData(name=data['company_name'], website=data['website'])
        
        result = await scraper.scrape_company_intelligent(company, data['job_id'])
        
        # Output clean JSON result
        output = {{
            'success': True,
            'company_description': result.company_description or '',
            'raw_content': result.raw_content or '',
            'pages_crawled': result.pages_crawled or [],
            'scrape_status': result.scrape_status or 'unknown',
            'scrape_error': result.scrape_error
        }}
        
        print(json.dumps(output))
        
    except Exception as e:
        output = {{
            'success': False,
            'error': str(e),
            'company_description': '',
            'scrape_status': 'failed'
        }}
        print(json.dumps(output))

if __name__ == '__main__':
    asyncio.run(main())
        """
        
        try:
            # Run subprocess with timeout
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=timeout + 10  # Add buffer
            )
            
            # Parse result
            if result.returncode == 0 and result.stdout.strip():
                output_data = json.loads(result.stdout.strip())
                
                if output_data.get('success'):
                    company_data.company_description = output_data.get('company_description', '')
                    company_data.raw_content = output_data.get('raw_content', '')
                    company_data.pages_crawled = output_data.get('pages_crawled', [])
                    company_data.scrape_status = output_data.get('scrape_status', 'success')
                else:
                    company_data.scrape_status = 'failed'
                    company_data.scrape_error = output_data.get('error', 'Unknown subprocess error')
            else:
                company_data.scrape_status = 'failed'
                company_data.scrape_error = f"Subprocess failed: {result.stderr}"
                
        finally:
            # Cleanup
            try:
                os.unlink(input_file)
            except:
                pass
        
        return company_data
    
    def _is_good_result(self, result: CompanyData) -> bool:
        """Check if result is high quality"""
        if not result or result.scrape_status != 'success':
            return False
            
        description_length = len(result.company_description or '')
        pages_count = len(result.pages_crawled or [])
        
        # Quality thresholds
        return (
            description_length > 500 and  # At least 500 chars
            pages_count > 10 and          # At least 10 pages
            'about' in str(result.pages_crawled).lower()  # Found about page
        )
    '''
    
    return hybrid_code

def create_implementation_plan():
    """
    Create step-by-step implementation plan
    """
    
    plan = {
        "Step 1": {
            "action": "Update main_pipeline.py",
            "change": "Replace IntelligentCompanyScraperSync with IntelligentCompanyScraperHybrid",
            "impact": "All API calls will use the new hybrid approach",
            "risk": "Low - maintains backward compatibility"
        },
        
        "Step 2": {
            "action": "Test the hybrid approach",
            "change": "Run comparative tests to verify improvements",
            "impact": "Proves the fix works before deployment",
            "risk": "None - testing only"
        },
        
        "Step 3": {
            "action": "Add configuration option",
            "change": "Allow choosing between direct/subprocess/hybrid modes",
            "impact": "Flexibility for different environments",
            "risk": "Low - adds options without breaking existing code"
        },
        
        "Step 4": {
            "action": "Monitor and optimize",
            "change": "Track performance metrics and optimize thresholds",
            "impact": "Continuous improvement of quality detection",
            "risk": "None - monitoring only"
        }
    }
    
    return plan

if __name__ == "__main__":
    print("🔧 FIX STRATEGY 3: HYBRID APPROACH")
    print("="*50)
    
    print("Hybrid Solution Code:")
    print(create_hybrid_solution())
    
    print("\n" + "="*50)
    print("Implementation Plan:")
    plan = create_implementation_plan()
    
    for step_id, step in plan.items():
        print(f"\n{step_id}: {step['action']}")
        print(f"  Change: {step['change']}")
        print(f"  Impact: {step['impact']}")
        print(f"  Risk: {step['risk']}")
    
    print(f"\n✅ RECOMMENDATION: Implement Strategy 3 (Hybrid)")
    print(f"   Pros: Best reliability, maintains compatibility, intelligent fallback")
    print(f"   Cons: Slightly more complex than pure direct execution")
    print(f"   Result: Should fix the 148-character issue immediately")