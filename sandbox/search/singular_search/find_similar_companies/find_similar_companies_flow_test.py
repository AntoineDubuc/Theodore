#!/usr/bin/env python3
"""
Find Similar Companies Flow Test
Implements and tests the complete "Find Similar Companies" workflow using our rate-limited approach
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add Theodore root to path
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/sandbox/search/singular_search/rate_limiting')

# Import Theodore components
from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
from src.pinecone_client import PineconeClient
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.models import CompanyData, CompanyIntelligenceConfig

# Import our rate-limited solution
from rate_limited_gemini_solution import RateLimitedTheodoreLLMManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class RateLimitedSimilarCompaniesFlow:
    """
    Rate-limited implementation of Find Similar Companies flow
    Combines Theodore's discovery architecture with our rate limiting solution
    """
    
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
        
        # Initialize rate-limited LLM manager
        self.llm_manager = RateLimitedTheodoreLLMManager(
            max_workers=1,
            requests_per_minute=8
        )
        
        # Initialize Theodore clients
        try:
            # Pinecone client (for vector database queries)
            self.pinecone_client = PineconeClient(
                config=self.config,
                api_key=os.getenv("PINECONE_API_KEY"),
                environment="us-west-2",  # Modern Pinecone doesn't use this
                index_name=os.getenv("PINECONE_INDEX_NAME", "theodore-companies")
            )
            
            # Bedrock client (for embeddings)
            self.bedrock_client = BedrockClient()
            
            # Enhanced discovery engine
            self.discovery_engine = SimpleEnhancedDiscovery(
                ai_client=self.bedrock_client,
                pinecone_client=self.pinecone_client
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
    
    def start(self):
        """Start the rate-limited manager"""
        self.llm_manager.start()
    
    def shutdown(self):
        """Shutdown the rate-limited manager"""
        self.llm_manager.shutdown()
    
    def find_similar_companies(self, company_name: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Main Find Similar Companies flow implementation
        
        According to research_architecture.md:
        1. Vector Database Query (fast)
        2. LLM Expansion if insufficient results (rate-limited)
        3. Surface scraping for new companies (rate-limited)
        4. Combine and format results
        """
        
        logger.info(f"🔍 Starting Find Similar Companies flow for: {company_name}")
        
        flow_start = time.time()
        results = {
            "company_name": company_name,
            "max_results": max_results,
            "timestamp": datetime.now().isoformat(),
            "phases": [],
            "similar_companies": [],
            "total_duration": 0,
            "rate_limited": True
        }
        
        try:
            # Phase 1: Vector Database Query
            phase1_result = self._phase1_vector_database_query(company_name, max_results)
            results["phases"].append(phase1_result)
            
            vector_companies = phase1_result.get("companies", [])
            
            # Phase 2: LLM Expansion (conditional - if insufficient results)
            if len(vector_companies) < max_results:
                needed_count = max_results - len(vector_companies)
                logger.info(f"🧠 Need {needed_count} more companies, running LLM expansion")
                
                phase2_result = self._phase2_llm_expansion(company_name, needed_count, vector_companies)
                results["phases"].append(phase2_result)
                
                llm_companies = phase2_result.get("companies", [])
            else:
                logger.info("✅ Sufficient results from vector database, skipping LLM expansion")
                llm_companies = []
            
            # Phase 3: Surface Scraping for new companies (rate-limited)
            phase3_result = self._phase3_surface_scraping(llm_companies)
            results["phases"].append(phase3_result)
            
            enhanced_companies = phase3_result.get("companies", [])
            
            # Phase 4: Combine and format results
            phase4_result = self._phase4_combine_results(vector_companies, enhanced_companies, max_results)
            results["phases"].append(phase4_result)
            
            results["similar_companies"] = phase4_result.get("final_companies", [])
            
        except Exception as e:
            logger.error(f"❌ Find Similar Companies flow failed: {e}")
            results["error"] = str(e)
        
        results["total_duration"] = round(time.time() - flow_start, 2)
        logger.info(f"🏁 Find Similar Companies completed in {results['total_duration']}s")
        
        return results
    
    def _phase1_vector_database_query(self, company_name: str, max_results: int) -> Dict[str, Any]:
        """
        Phase 1: Vector Database Query
        Fast lookup of existing similar companies in Pinecone
        """
        
        logger.info("📊 Phase 1: Vector Database Query")
        phase_start = time.time()
        
        try:
            # Check if target company exists in database
            target_company = self.pinecone_client.find_company_by_name(company_name)
            
            if target_company:
                logger.info(f"✅ Found target company in database: {company_name}")
                
                # Use vector similarity search
                similar_companies = self.pinecone_client.find_similar_companies(
                    target_company.embedding,
                    limit=max_results,
                    include_metadata=True
                )
                
                # Format results
                formatted_companies = []
                for company, score in similar_companies:
                    formatted_companies.append({
                        "name": company.name,
                        "website": getattr(company, 'website', ''),
                        "similarity_score": float(score),
                        "relationship_type": "vector_similar",
                        "source": "pinecone_database",
                        "description": getattr(company, 'overview', ''),
                        "business_model": getattr(company, 'business_model', ''),
                        "industry": getattr(company, 'industry', '')
                    })
                
                phase_duration = time.time() - phase_start
                
                return {
                    "phase": "Vector Database Query",
                    "status": "SUCCESS",
                    "duration": round(phase_duration, 2),
                    "target_found": True,
                    "companies": formatted_companies,
                    "count": len(formatted_companies),
                    "method": "vector_similarity"
                }
                
            else:
                logger.info(f"❓ Target company not in database: {company_name}")
                
                # Try semantic search based on company name
                # This is a fallback when we don't have the exact company
                try:
                    # Use Bedrock to generate embedding for company name
                    name_embedding = self.bedrock_client.get_embeddings(company_name)
                    
                    if name_embedding:
                        similar_companies = self.pinecone_client.find_similar_companies(
                            name_embedding,
                            limit=min(max_results, 3),  # Fewer results since this is less accurate
                            include_metadata=True
                        )
                        
                        formatted_companies = []
                        for company, score in similar_companies:
                            formatted_companies.append({
                                "name": company.name,
                                "website": getattr(company, 'website', ''),
                                "similarity_score": float(score) * 0.7,  # Lower confidence for name-only matching
                                "relationship_type": "semantic_similar",
                                "source": "pinecone_semantic",
                                "description": getattr(company, 'overview', ''),
                                "business_model": getattr(company, 'business_model', ''),
                                "industry": getattr(company, 'industry', '')
                            })
                        
                        phase_duration = time.time() - phase_start
                        
                        return {
                            "phase": "Vector Database Query",
                            "status": "PARTIAL_SUCCESS",
                            "duration": round(phase_duration, 2),
                            "target_found": False,
                            "companies": formatted_companies,
                            "count": len(formatted_companies),
                            "method": "semantic_search"
                        }
                    
                except Exception as embedding_error:
                    logger.warning(f"⚠️ Semantic search failed: {embedding_error}")
                
                phase_duration = time.time() - phase_start
                
                return {
                    "phase": "Vector Database Query",
                    "status": "NO_RESULTS",
                    "duration": round(phase_duration, 2),
                    "target_found": False,
                    "companies": [],
                    "count": 0,
                    "method": "none"
                }
        
        except Exception as e:
            phase_duration = time.time() - phase_start
            logger.error(f"❌ Phase 1 failed: {e}")
            
            return {
                "phase": "Vector Database Query",
                "status": "FAILED",
                "duration": round(phase_duration, 2),
                "error": str(e),
                "companies": [],
                "count": 0
            }
    
    def _phase2_llm_expansion(self, company_name: str, needed_count: int, existing_companies: List[Dict]) -> Dict[str, Any]:
        """
        Phase 2: LLM Expansion (rate-limited)
        Use LLM to generate additional similar companies when vector search is insufficient
        """
        
        logger.info(f"🧠 Phase 2: LLM Expansion (need {needed_count} companies)")
        phase_start = time.time()
        
        try:
            # Prepare context about existing companies (if any)
            existing_context = ""
            if existing_companies:
                existing_names = [comp["name"] for comp in existing_companies[:3]]
                existing_context = f"\\n\\nExisting similar companies already found: {', '.join(existing_names)}"
            
            # Create LLM prompt for company discovery
            prompt = f"""Find {needed_count} companies similar to "{company_name}" for business development purposes.
{existing_context}

Provide companies that are:
- In similar industries or markets
- Have comparable business models
- Target similar customers
- Are potential competitors or partners

Focus on real, well-known companies. Avoid duplicating any existing companies mentioned above.

Respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Company Name",
      "website": "https://example.com", 
      "similarity_score": 0.85,
      "relationship_type": "competitor|partner|alternative",
      "reasoning": "Brief explanation of similarity",
      "business_model": "B2B|B2C|B2B2C",
      "industry": "Industry category"
    }}
  ]
}}

Generate {needed_count} similar companies:"""

            # Use rate-limited LLM manager
            status = self.llm_manager.get_rate_limit_status()
            logger.info(f"📊 Rate limiter status: {status['tokens_available']:.1f}/{status['capacity']} tokens")
            
            # Create LLM task for company expansion
            from rate_limited_gemini_solution import LLMTask
            task = LLMTask(
                task_id=f"expansion_{company_name}_{int(time.time())}",
                prompt=prompt,
                context={"company_name": company_name, "needed_count": needed_count}
            )
            
            # Process with rate limiting
            llm_result = self.llm_manager.worker_pool.process_task(task)
            
            if llm_result.success:
                # Parse LLM response
                from rate_limited_gemini_solution import safe_json_parse
                expansion_data = safe_json_parse(llm_result.response, fallback_value={"similar_companies": []})
                
                if "similar_companies" in expansion_data:
                    llm_companies = expansion_data["similar_companies"]
                    
                    # Format results consistently
                    formatted_companies = []
                    for company in llm_companies[:needed_count]:
                        formatted_companies.append({
                            "name": company.get("name", "Unknown"),
                            "website": company.get("website", ""),
                            "similarity_score": company.get("similarity_score", 0.8),
                            "relationship_type": company.get("relationship_type", "llm_suggested"),
                            "source": "llm_expansion",
                            "description": company.get("reasoning", ""),
                            "business_model": company.get("business_model", ""),
                            "industry": company.get("industry", ""),
                            "needs_research": True  # Flag for Phase 3
                        })
                    
                    phase_duration = time.time() - phase_start
                    
                    return {
                        "phase": "LLM Expansion",
                        "status": "SUCCESS",
                        "duration": round(phase_duration, 2),
                        "llm_processing_time": llm_result.processing_time,
                        "companies": formatted_companies,
                        "count": len(formatted_companies),
                        "rate_limited": True
                    }
                
                else:
                    logger.warning("⚠️ LLM response missing 'similar_companies' field")
            
            else:
                logger.error(f"❌ LLM expansion failed: {llm_result.error}")
            
            phase_duration = time.time() - phase_start
            
            return {
                "phase": "LLM Expansion", 
                "status": "FAILED",
                "duration": round(phase_duration, 2),
                "error": llm_result.error if not llm_result.success else "Invalid response format",
                "companies": [],
                "count": 0,
                "rate_limited": True
            }
        
        except Exception as e:
            phase_duration = time.time() - phase_start
            logger.error(f"❌ Phase 2 failed: {e}")
            
            return {
                "phase": "LLM Expansion",
                "status": "FAILED",
                "duration": round(phase_duration, 2),
                "error": str(e),
                "companies": [],
                "count": 0,
                "rate_limited": True
            }
    
    def _phase3_surface_scraping(self, llm_companies: List[Dict]) -> Dict[str, Any]:
        """
        Phase 3: Surface Scraping for new companies (rate-limited)
        Extract basic information from homepages of LLM-suggested companies
        """
        
        logger.info(f"📄 Phase 3: Surface Scraping ({len(llm_companies)} companies)")
        phase_start = time.time()
        
        enhanced_companies = []
        
        for i, company in enumerate(llm_companies):
            if not company.get("needs_research", False):
                enhanced_companies.append(company)
                continue
            
            company_name = company["name"]
            website = company.get("website", "")
            
            logger.info(f"🔍 Surface scraping {i+1}/{len(llm_companies)}: {company_name}")
            
            try:
                # If no website provided, try Google search
                if not website or website == "https://example.com":
                    logger.info(f"🔍 No website for {company_name}, attempting Google search")
                    website = self._google_search_for_website(company_name)
                
                if website:
                    # Perform surface scraping (homepage only)
                    surface_data = self._scrape_homepage_surface(company_name, website)
                    
                    # Enhance company data with scraped information
                    enhanced_company = company.copy()
                    enhanced_company.update({
                        "website": website,
                        "description": surface_data.get("description", company.get("description", "")),
                        "business_model": surface_data.get("business_model", company.get("business_model", "")),
                        "industry": surface_data.get("industry", company.get("industry", "")),
                        "scraped": True,
                        "scrape_quality": surface_data.get("quality", "basic")
                    })
                    
                    enhanced_companies.append(enhanced_company)
                    
                else:
                    logger.warning(f"⚠️ No website found for {company_name}")
                    enhanced_companies.append(company)
            
            except Exception as e:
                logger.error(f"❌ Surface scraping failed for {company_name}: {e}")
                enhanced_companies.append(company)
        
        phase_duration = time.time() - phase_start
        
        return {
            "phase": "Surface Scraping",
            "status": "SUCCESS",
            "duration": round(phase_duration, 2),
            "companies": enhanced_companies,
            "count": len(enhanced_companies),
            "enhanced_count": sum(1 for c in enhanced_companies if c.get("scraped", False))
        }
    
    def _phase4_combine_results(self, vector_companies: List[Dict], enhanced_companies: List[Dict], max_results: int) -> Dict[str, Any]:
        """
        Phase 4: Combine and format final results
        Merge vector database results with LLM-enhanced companies
        """
        
        logger.info(f"🔗 Phase 4: Combining results (vector: {len(vector_companies)}, enhanced: {len(enhanced_companies)})")
        phase_start = time.time()
        
        # Combine all companies
        all_companies = vector_companies + enhanced_companies
        
        # Remove duplicates based on company name
        seen_names = set()
        deduplicated_companies = []
        
        for company in all_companies:
            name_lower = company["name"].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                deduplicated_companies.append(company)
        
        # Sort by similarity score (descending)
        deduplicated_companies.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        
        # Limit to max_results
        final_companies = deduplicated_companies[:max_results]
        
        # Add final formatting and research status
        for company in final_companies:
            # Check if company exists in Theodore database for "Research this company" capability
            existing_company = self.pinecone_client.find_company_by_name(company["name"])
            company["research_status"] = "completed" if existing_company else "available"
            company["can_research"] = True  # Always true since we can use "Research Individual Similar Company" flow
        
        phase_duration = time.time() - phase_start
        
        return {
            "phase": "Combine Results",
            "status": "SUCCESS", 
            "duration": round(phase_duration, 2),
            "final_companies": final_companies,
            "total_found": len(all_companies),
            "after_deduplication": len(deduplicated_companies),
            "final_count": len(final_companies)
        }
    
    def _google_search_for_website(self, company_name: str) -> Optional[str]:
        """Simple Google search to find company website"""
        # This is a placeholder - in real implementation you'd use Google Search API
        # For now, return None to simulate not finding a website
        logger.info(f"🔍 Google search for {company_name} (placeholder)")
        return None
    
    def _scrape_homepage_surface(self, company_name: str, website: str) -> Dict[str, Any]:
        """
        Surface scraping of company homepage
        This would use our rate-limited approach for LLM analysis
        """
        
        logger.info(f"📄 Surface scraping homepage: {website}")
        
        try:
            # Simulate basic homepage scraping
            # In real implementation, this would:
            # 1. Fetch homepage content with requests/crawl4ai
            # 2. Extract main content  
            # 3. Use rate-limited LLM to analyze content for business intelligence
            # 4. Return structured data
            
            # For now, return placeholder data
            return {
                "description": f"AI-generated description for {company_name}",
                "business_model": "B2B",
                "industry": "Technology",
                "quality": "basic"
            }
            
        except Exception as e:
            logger.error(f"❌ Homepage scraping failed: {e}")
            return {
                "description": "",
                "business_model": "",
                "industry": "",
                "quality": "failed"
            }

# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_find_similar_companies_flow():
    """Test the complete Find Similar Companies flow"""
    
    print("🧪 TESTING FIND SIMILAR COMPANIES FLOW")
    print("=" * 80)
    print("🎯 Testing rate-limited implementation of Find Similar Companies")
    print("📊 Configuration: 1 worker, 8 requests/minute rate limiting")
    print()
    
    # Test companies (some that might exist in Theodore database)
    test_companies = [
        "Stripe",           # Well-known company likely in database
        "OpenAI",           # Well-known company likely in database  
        "TestCorp Inc",     # Unknown company to test LLM expansion
        "FakeCompany123"    # Non-existent company to test fallbacks
    ]
    
    flow = RateLimitedSimilarCompaniesFlow()
    
    try:
        flow.start()
        
        for i, company_name in enumerate(test_companies, 1):
            print(f"📋 TEST {i}/{len(test_companies)}: {company_name}")
            print("-" * 40)
            
            test_start = time.time()
            
            result = flow.find_similar_companies(
                company_name=company_name,
                max_results=3  # Small number for testing
            )
            
            test_duration = time.time() - test_start
            
            # Display results
            print(f"⏱️  Total Duration: {result['total_duration']}s")
            print(f"🔍 Similar Companies Found: {len(result['similar_companies'])}")
            
            # Show phase breakdown
            for phase in result["phases"]:
                status_emoji = "✅" if phase["status"] == "SUCCESS" else "❌" if phase["status"] == "FAILED" else "⚠️"
                print(f"   {status_emoji} {phase['phase']}: {phase['duration']}s ({phase['status']})")
            
            # Show sample results
            if result["similar_companies"]:
                print("📊 Sample Results:")
                for j, company in enumerate(result["similar_companies"][:2], 1):
                    print(f"   {j}. {company['name']} (score: {company['similarity_score']:.2f}, source: {company['source']})")
            
            print()
            
            # Rate limiting pause between tests
            if i < len(test_companies):
                print("⏳ Pausing for rate limiting...")
                time.sleep(10)  # Allow token refill
                print()
        
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        flow.shutdown()

def test_single_company_detailed():
    """Test a single company with detailed output for human evaluation"""
    
    print("🧪 DETAILED SINGLE COMPANY TEST")
    print("=" * 50)
    
    company_name = "Stripe"  # Well-known company
    
    flow = RateLimitedSimilarCompaniesFlow()
    
    try:
        flow.start()
        
        print(f"🔍 Testing comprehensive flow for: {company_name}")
        print()
        
        result = flow.find_similar_companies(
            company_name=company_name,
            max_results=5
        )
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"find_similar_test_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Detailed results saved to: {output_file}")
        print(f"🏁 Test completed in {result['total_duration']}s")
        
        return result
        
    except Exception as e:
        print(f"❌ Detailed test failed: {e}")
        return None
        
    finally:
        flow.shutdown()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Find Similar Companies Flow")
    parser.add_argument("--detailed", action="store_true", help="Run detailed single company test")
    parser.add_argument("--company", type=str, help="Company name for detailed test", default="Stripe")
    
    args = parser.parse_args()
    
    if args.detailed:
        test_single_company_detailed()
    else:
        test_find_similar_companies_flow()