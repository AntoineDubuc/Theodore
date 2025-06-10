"""
Simplified Enhanced Similarity Discovery
Uses LLM for contextual discovery without async complications
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models import CompanyData
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)

class SimpleEnhancedDiscovery:
    """Simplified enhanced similarity discovery using LLM + Vector search"""
    
    def __init__(self, ai_client, pinecone_client: PineconeClient, scraper=None):
        # Accept either Bedrock or Gemini client
        self.ai_client = ai_client
        self.pinecone_client = pinecone_client
        self.scraper = scraper  # Add scraper for temporary company research
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def discover_similar_companies(self, company_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Discover similar companies using LLM + Vector search"""
        self.logger.info(f"Starting enhanced discovery for: {company_name}")
        
        try:
            # Step 1: Get company data (if exists in database)
            target_company = self.pinecone_client.find_company_by_name(company_name)
            
            if target_company:
                self.logger.info(f"Company found in database: {company_name}")
                # Step 2: LLM contextual discovery using existing data
                llm_results = self._llm_contextual_discovery(target_company, limit)
                
                # Step 3: Vector similarity discovery
                vector_results = self._vector_similarity_discovery(target_company, limit)
                
                # Step 4: Combine and deduplicate
                combined_results = self._combine_results(llm_results, vector_results, limit)
            else:
                self.logger.info(f"Company not in database, using LLM-only discovery: {company_name}")
                # For unknown companies, use LLM with just the company name
                llm_results = self._llm_discovery_unknown_company(company_name, limit)
                
                # No vector search possible without existing data
                vector_results = []
                
                # Format results
                combined_results = self._format_llm_only_results(llm_results)
            
            self.logger.info(f"Enhanced discovery complete: {len(combined_results)} results")
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Enhanced discovery failed: {e}")
            return []
    
    def _llm_contextual_discovery(self, target_company: CompanyData, limit: int) -> List[Dict[str, Any]]:
        """Use LLM for contextual similarity discovery with web scraping"""
        self.logger.info(f"Running LLM discovery for: {target_company.name}")
        
        try:
            # Prepare context
            context = self._prepare_company_context(target_company)
            
            prompt = f"""Find companies similar to this target company for business development purposes.

TARGET COMPANY:
{context}

Find {limit} similar companies considering:
- Business model and services
- Target market and customers
- Industry and technology
- Size and stage

Respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Company Name",
      "website": "https://example.com",
      "similarity_score": 0.85,
      "relationship_type": "competitor",
      "reasoning": "Brief explanation",
      "business_context": "Why they are similar"
    }}
  ]
}}"""
            
            response = self.ai_client.analyze_content(prompt)
            
            if response:
                self.logger.info(f"LLM Response: {response[:200]}...")  # Debug log
                try:
                    # Try to extract JSON from response
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = response[json_start:json_end]
                        data = json.loads(json_text)
                        companies = data.get('similar_companies', [])
                        self.logger.info(f"LLM found {len(companies)} companies")
                        
                        # Keep LLM suggestions without scraping (scraping done on demand)
                        # Web scraping will be triggered by research button
                        
                        return companies
                    else:
                        self.logger.error("No JSON found in LLM response")
                        return []
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse LLM JSON: {e}")
                    self.logger.error(f"Raw response: {response}")
                    return []
            
            return []
            
        except Exception as e:
            self.logger.error(f"LLM discovery failed: {e}")
            return []
    
    def _vector_similarity_discovery(self, target_company: CompanyData, limit: int) -> List[Dict[str, Any]]:
        """Use vector search for similarity discovery"""
        self.logger.info(f"Running vector discovery for: {target_company.name}")
        
        try:
            if not target_company.embedding:
                self.logger.warning(f"No embedding for {target_company.name}")
                return []
            
            similar_companies = self.pinecone_client.find_similar_companies(
                target_company.id, 
                top_k=limit,
                score_threshold=0.4  # Lower threshold
            )
            
            # Convert to standard format
            results = []
            for comp in similar_companies:
                results.append({
                    'name': comp.get('company_name', ''),
                    'website': comp.get('website', ''),
                    'similarity_score': comp.get('score', 0.0),
                    'relationship_type': 'vector_similar',
                    'reasoning': f"Vector similarity: {comp.get('score', 0.0):.2f}",
                    'business_context': "Semantic similarity in business profiles"
                })
            
            self.logger.info(f"Vector search found {len(results)} companies")
            return results
            
        except Exception as e:
            self.logger.error(f"Vector discovery failed: {e}")
            return []
    
    def _combine_results(self, llm_results: List[Dict], vector_results: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from LLM and vector search"""
        self.logger.info("Combining LLM and vector results")
        
        try:
            # Track companies by name (case insensitive)
            combined = {}
            
            # Add LLM results
            for comp in llm_results:
                name = comp.get('name', '').strip().lower()
                if name:
                    combined[name] = {
                        'company_name': comp.get('name', ''),
                        'website': comp.get('website', ''),
                        'similarity_score': comp.get('similarity_score', 0.0),
                        'confidence': comp.get('similarity_score', 0.0),
                        'reasoning': [comp.get('reasoning', 'LLM Analysis')],
                        'relationship_type': comp.get('relationship_type', 'similar'),
                        'discovery_method': 'LLM Contextual Analysis',
                        'business_context': comp.get('business_context', ''),
                        'sources': ['llm']
                    }
            
            # Add vector results (merge if duplicate)
            for comp in vector_results:
                name = comp.get('name', '').strip().lower()
                if name:
                    if name in combined:
                        # Merge with existing
                        combined[name]['sources'].append('vector')
                        combined[name]['reasoning'].append(comp.get('reasoning', 'Vector similarity'))
                        # Boost confidence for multi-source
                        combined[name]['confidence'] = min(1.0, combined[name]['confidence'] + 0.1)
                        combined[name]['discovery_method'] = 'Multi-Source (LLM + Vector)'
                    else:
                        # Add new
                        combined[name] = {
                            'company_name': comp.get('name', ''),
                            'website': comp.get('website', ''),
                            'similarity_score': comp.get('similarity_score', 0.0),
                            'confidence': comp.get('similarity_score', 0.0),
                            'reasoning': [comp.get('reasoning', 'Vector similarity')],
                            'relationship_type': comp.get('relationship_type', 'similar'),
                            'discovery_method': 'Vector Similarity',
                            'business_context': comp.get('business_context', ''),
                            'sources': ['vector']
                        }
            
            # Convert to list and sort by confidence
            results = list(combined.values())
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            self.logger.info(f"Combined results: {len(results)} total companies")
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Result combination failed: {e}")
            return []
    
    def _prepare_company_context(self, company: CompanyData) -> str:
        """Prepare company context for LLM"""
        context_parts = []
        
        context_parts.append(f"Company Name: {company.name}")
        if company.website:
            context_parts.append(f"Website: {company.website}")
        if company.industry:
            context_parts.append(f"Industry: {company.industry}")
        if company.business_model:
            context_parts.append(f"Business Model: {company.business_model}")
        if company.target_market:
            context_parts.append(f"Target Market: {company.target_market}")
        if company.company_size:
            context_parts.append(f"Size: {company.company_size}")
        if company.ai_summary:
            context_parts.append(f"Summary: {company.ai_summary}")
        
        return "\n".join(context_parts)
    
    def _llm_discovery_unknown_company(self, company_name: str, limit: int) -> List[Dict[str, Any]]:
        """Use LLM to find similar companies for an unknown company with web scraping"""
        self.logger.info(f"Running LLM discovery for unknown company: {company_name}")
        
        try:
            prompt = f"""Find companies similar to "{company_name}" for business development purposes.

IMPORTANT: Research and identify real companies that would be competitors, partners, or similar businesses to "{company_name}".

Consider all possible interpretations of what "{company_name}" could be:
- A technology company
- A software/SaaS company  
- A consulting firm
- A service provider
- Any other type of business

Find {limit} real, similar companies and respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Real Company Name",
      "website": "https://realcompany.com",
      "similarity_score": 0.85,
      "relationship_type": "competitor",
      "reasoning": "Brief explanation of similarity",
      "business_context": "Why they are similar to {company_name}"
    }}
  ]
}}

Make sure to suggest REAL companies with actual websites, not fictional ones."""
            
            response = self.ai_client.analyze_content(prompt)
            
            if response:
                self.logger.info(f"LLM Response: {response[:200]}...")
                try:
                    # Extract JSON from response
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = response[json_start:json_end]
                        data = json.loads(json_text)
                        companies = data.get('similar_companies', [])
                        self.logger.info(f"LLM found {len(companies)} companies for unknown company")
                        
                        # Keep LLM suggestions without scraping (scraping done on demand)
                        # Web scraping will be triggered by research button
                        
                        return companies
                    else:
                        self.logger.error("No JSON found in LLM response for unknown company")
                        return []
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse LLM JSON for unknown company: {e}")
                    return []
            
            return []
            
        except Exception as e:
            self.logger.error(f"LLM discovery for unknown company failed: {e}")
            return []
    
    def _format_llm_only_results(self, llm_results: List[Dict]) -> List[Dict[str, Any]]:
        """Format LLM-only results for unknown companies"""
        self.logger.info(f"Formatting {len(llm_results)} LLM-only results")
        
        try:
            formatted_results = []
            
            for comp in llm_results:
                formatted_results.append({
                    'company_name': comp.get('name', ''),
                    'website': comp.get('website', ''),
                    'similarity_score': comp.get('similarity_score', 0.0),
                    'confidence': comp.get('similarity_score', 0.0),
                    'reasoning': [comp.get('reasoning', 'LLM Analysis')],
                    'relationship_type': comp.get('relationship_type', 'similar'),
                    'discovery_method': 'LLM Research',
                    'business_context': comp.get('business_context', ''),
                    'sources': ['llm']
                })
            
            # Sort by confidence
            formatted_results.sort(key=lambda x: x['confidence'], reverse=True)
            
            self.logger.info(f"Formatted {len(formatted_results)} LLM-only results")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Failed to format LLM-only results: {e}")
            return []
    
    def _scrape_suggested_companies(self, suggested_companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape LLM-suggested companies to get rich data WITHOUT storing in index"""
        self.logger.info(f"Scraping {len(suggested_companies)} suggested companies...")
        
        enhanced_companies = []
        
        for suggestion in suggested_companies:
            try:
                company_name = suggestion.get('name', '').strip()
                company_website = suggestion.get('website', '').strip()
                
                if not company_name or not company_website:
                    self.logger.warning(f"Skipping company with missing name or website: {suggestion}")
                    # Keep original suggestion without enhancement
                    enhanced_companies.append(suggestion)
                    continue
                
                self.logger.info(f"Scraping suggested company: {company_name}")
                
                # Create temporary CompanyData object for scraping
                from src.models import CompanyData
                temp_company = CompanyData(
                    name=company_name,
                    website=company_website
                )
                
                # Scrape company WITHOUT storing in database
                scraped_company = self.scraper.scrape_company(temp_company)
                
                if scraped_company.scrape_status == "success":
                    # Enhance the suggestion with scraped data
                    enhanced_suggestion = {
                        'company_name': scraped_company.name,
                        'website': scraped_company.website,
                        'similarity_score': suggestion.get('similarity_score', 0.8),
                        'confidence': suggestion.get('similarity_score', 0.8),
                        'reasoning': [suggestion.get('reasoning', 'LLM suggestion with web scraping')],
                        'relationship_type': suggestion.get('relationship_type', 'similar'),
                        'discovery_method': 'LLM + Web Scraping',
                        'business_context': suggestion.get('business_context', ''),
                        'sources': ['llm', 'web_scraping'],
                        
                        # Add scraped intelligence
                        'industry': scraped_company.industry or 'Unknown',
                        'business_model': scraped_company.business_model or 'Unknown', 
                        'company_description': scraped_company.company_description or 'No description available',
                        'target_market': scraped_company.target_market or 'Unknown',
                        'key_services': scraped_company.key_services[:3] if scraped_company.key_services else [],
                        'company_size': scraped_company.company_size or 'Unknown',
                        'location': scraped_company.location or 'Unknown',
                        'tech_stack': scraped_company.tech_stack[:5] if scraped_company.tech_stack else [],
                        'value_proposition': scraped_company.value_proposition or '',
                        
                        # Indicate this is scraped data (not stored in index)
                        'is_scraped_data': True,
                        'scrape_status': 'success'
                    }
                    
                    self.logger.info(f"Successfully enhanced {company_name} with scraped data")
                    enhanced_companies.append(enhanced_suggestion)
                    
                else:
                    # Scraping failed, keep original suggestion with note
                    enhanced_suggestion = suggestion.copy()
                    enhanced_suggestion.update({
                        'discovery_method': 'LLM only (scraping failed)',
                        'sources': ['llm'],
                        'is_scraped_data': False,
                        'scrape_status': 'failed',
                        'scrape_error': scraped_company.scrape_error or 'Unknown error'
                    })
                    
                    self.logger.warning(f"Scraping failed for {company_name}: {scraped_company.scrape_error}")
                    enhanced_companies.append(enhanced_suggestion)
                
            except Exception as e:
                self.logger.error(f"Error scraping suggested company {suggestion.get('name', 'unknown')}: {e}")
                # Keep original suggestion on error
                error_suggestion = suggestion.copy()
                error_suggestion.update({
                    'discovery_method': 'LLM only (scraping error)',
                    'sources': ['llm'],
                    'is_scraped_data': False,
                    'scrape_status': 'error',
                    'scrape_error': str(e)
                })
                enhanced_companies.append(error_suggestion)
        
        self.logger.info(f"Enhanced {len(enhanced_companies)} companies with scraping")
        return enhanced_companies
    
    def research_company_on_demand(self, company_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Research a specific company suggestion on-demand via web scraping"""
        print(f"🧬 RESEARCH: Starting on-demand research process")
        print(f"🧬 RESEARCH: Input company suggestion: {company_suggestion}")
        
        self.logger.info(f"On-demand research for: {company_suggestion.get('name', 'unknown')}")
        
        if not self.scraper:
            print(f"🧬 RESEARCH: ❌ No scraper available - returning original suggestion")
            self.logger.warning("No scraper available for on-demand research")
            return company_suggestion
        
        try:
            print(f"🧬 RESEARCH: Extracting company details from suggestion...")
            company_name = company_suggestion.get('company_name', company_suggestion.get('name', '')).strip()
            company_website = company_suggestion.get('website', '').strip()
            print(f"🧬 RESEARCH: Extracted name='{company_name}', website='{company_website}'")
            
            if not company_name or not company_website:
                print(f"🧬 RESEARCH: ❌ Missing required data - name or website empty")
                print(f"🧬 RESEARCH: ❌ Returning original suggestion unchanged")
                self.logger.warning(f"Missing name or website for research: {company_suggestion}")
                return company_suggestion
            
            print(f"🧬 RESEARCH: Creating CompanyData object for scraping...")
            # Create temporary CompanyData object for scraping
            from src.models import CompanyData
            temp_company = CompanyData(
                name=company_name,
                website=company_website
            )
            print(f"🧬 RESEARCH: CompanyData object created successfully")
            
            print(f"🧬 RESEARCH: Initializing progress tracking system...")
            # Start progress tracking for research
            from src.progress_logger import start_company_processing
            job_id = start_company_processing(company_name)
            print(f"🧬 RESEARCH: Progress tracking started with job_id: {job_id}")
            
            print(f"🧬 RESEARCH: ===== STARTING SCRAPER =====")
            print(f"🧬 RESEARCH: Calling scraper.scrape_company for '{company_name}'")
            print(f"🧬 RESEARCH: Target website: {company_website}")
            
            # This should now work with the subprocess-based scraper
            scraped_company = self.scraper.scrape_company(temp_company, job_id)
            
            print(f"🧬 RESEARCH: ===== SCRAPER COMPLETED =====")
            print(f"🧬 RESEARCH: Final scrape status: {scraped_company.scrape_status}")
            print(f"🧬 RESEARCH: Scrape error (if any): {scraped_company.scrape_error}")
            print(f"🧬 RESEARCH: Pages crawled: {len(scraped_company.pages_crawled or [])}")
            print(f"🧬 RESEARCH: Crawl duration: {scraped_company.crawl_duration}")
            
            if scraped_company.scrape_status == "success":
                print(f"🧬 RESEARCH: ✅ Scraping successful! Starting LLM analysis...")
                # Run scraped content through LLM analysis for intelligent extraction
                self.logger.info(f"Analyzing scraped content with LLM for {company_name}")
                print(f"🧬 RESEARCH: Calling AI client for content analysis...")
                
                analysis_result = self.ai_client.analyze_company_content(scraped_company)
                print(f"🧬 RESEARCH: AI analysis completed")
                print(f"🧬 RESEARCH: Analysis result keys: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'Not a dict'}")
                
                # Apply LLM analysis to the scraped company data
                if "error" not in analysis_result:
                    print(f"🧬 RESEARCH: ✅ Applying AI analysis to company data...")
                    self._apply_analysis_to_company(scraped_company, analysis_result)
                    print(f"🧬 RESEARCH: ✅ AI analysis applied successfully")
                    self.logger.info(f"LLM analysis completed for {company_name}")
                else:
                    print(f"🧬 RESEARCH: ❌ AI analysis failed: {analysis_result.get('error')}")
                    self.logger.warning(f"LLM analysis failed for {company_name}: {analysis_result.get('error')}")
                
                print(f"🧬 RESEARCH: Starting job listings research...")
                # Execute job listings research
                job_listings_data = self._execute_job_listings_research(company_name, company_website)
                print(f"🧬 RESEARCH: Job listings research completed")
                
                print(f"🧬 RESEARCH: Marking job as completed in progress tracker...")
                # Complete the job tracking
                from src.progress_logger import complete_company_processing
                complete_company_processing(job_id, True, summary=f"Research completed for {company_name}")
                print(f"🧬 RESEARCH: Progress tracking completed")
                
                # Enhance the suggestion with analyzed scraped data
                enhanced_suggestion = {
                    'company_name': scraped_company.name,
                    'website': scraped_company.website,
                    'similarity_score': company_suggestion.get('similarity_score', 0.8),
                    'confidence': company_suggestion.get('similarity_score', 0.8),
                    'reasoning': [company_suggestion.get('reasoning', 'LLM suggestion with web research & analysis')],
                    'relationship_type': company_suggestion.get('relationship_type', 'similar'),
                    'discovery_method': 'LLM + On-Demand Research + AI Analysis',
                    'business_context': company_suggestion.get('business_context', ''),
                    'sources': ['llm', 'web_research', 'ai_analysis'],
                    
                    # Add LLM-analyzed intelligence (with intelligent fallbacks)
                    'industry': scraped_company.industry or 'Unknown',
                    'business_model': scraped_company.business_model or 'Unknown', 
                    'company_description': scraped_company.ai_summary or scraped_company.company_description or 'No description available',
                    'target_market': scraped_company.target_market or 'Unknown',
                    'key_services': scraped_company.key_services[:3] if scraped_company.key_services else [],
                    'company_size': scraped_company.company_size or 'Unknown',
                    'location': scraped_company.location or 'Unknown',
                    'tech_stack': scraped_company.tech_stack[:5] if scraped_company.tech_stack else [],
                    'value_proposition': scraped_company.value_proposition or '',
                    'pain_points': scraped_company.pain_points[:3] if scraped_company.pain_points else [],
                    
                    # Add job listings research data
                    'job_listings': job_listings_data.get('job_listings', 'Job data unavailable'),
                    'job_listings_details': job_listings_data.get('details', {}),
                    
                    # Add research metadata
                    'pages_crawled': scraped_company.pages_crawled or [],
                    'processing_time': scraped_company.crawl_duration,
                    'crawl_depth': scraped_company.crawl_depth or 0,
                    
                    # Indicate this is researched and analyzed data (not stored in index)
                    'is_researched': True,
                    'research_status': 'success',
                    'research_timestamp': self._get_timestamp(),
                    'analysis_applied': "error" not in analysis_result
                }
                
                print(f"🧬 RESEARCH: ===== RESEARCH COMPLETED SUCCESSFULLY =====")
                print(f"🧬 RESEARCH: Enhanced suggestion created with comprehensive data")
                self.logger.info(f"Successfully researched {company_name}")
                return enhanced_suggestion
                
            else:
                print(f"🧬 RESEARCH: ❌ Scraping failed - status: {scraped_company.scrape_status}")
                print(f"🧬 RESEARCH: ❌ Error: {scraped_company.scrape_error}")
                
                # Complete the job tracking with failure
                print(f"🧬 RESEARCH: Marking job as failed in progress tracker...")
                from src.progress_logger import complete_company_processing
                complete_company_processing(job_id, False, error=scraped_company.scrape_error or 'Research failed')
                
                # Research failed, return original with error info
                enhanced_suggestion = company_suggestion.copy()
                enhanced_suggestion.update({
                    'discovery_method': 'LLM only (research failed)',
                    'sources': ['llm'],
                    'is_researched': False,
                    'research_status': 'failed',
                    'research_error': scraped_company.scrape_error or 'Unknown error',
                    'research_timestamp': self._get_timestamp()
                })
                
                print(f"🧬 RESEARCH: ===== RESEARCH FAILED =====")
                print(f"🧬 RESEARCH: Returning failed result with error info")
                self.logger.warning(f"Research failed for {company_name}: {scraped_company.scrape_error}")
                return enhanced_suggestion
            
        except Exception as e:
            print(f"🧬 RESEARCH: ❌ CRITICAL ERROR during research: {e}")
            print(f"🧬 RESEARCH: ❌ Exception type: {type(e).__name__}")
            
            import traceback
            traceback_str = traceback.format_exc()
            print(f"🧬 RESEARCH: ❌ Full traceback:\n{traceback_str}")
            
            self.logger.error(f"Error in on-demand research for {company_suggestion.get('name', 'unknown')}: {e}")
            
            # Complete the job tracking with error (if job_id exists)
            print(f"🧬 RESEARCH: Attempting to mark job as failed due to exception...")
            try:
                if 'job_id' in locals():
                    from src.progress_logger import complete_company_processing
                    complete_company_processing(job_id, False, error=str(e))
                    print(f"🧬 RESEARCH: Job marked as failed successfully")
                else:
                    print(f"🧬 RESEARCH: No job_id available for cleanup")
            except Exception as cleanup_error:
                print(f"🧬 RESEARCH: ❌ Cleanup error: {cleanup_error}")
            
            # Return original suggestion with error info
            error_suggestion = company_suggestion.copy()
            error_suggestion.update({
                'discovery_method': 'LLM only (research error)',
                'sources': ['llm'],
                'is_researched': False,
                'research_status': 'error',
                'research_error': str(e),
                'research_timestamp': self._get_timestamp()
            })
            print(f"🧬 RESEARCH: ===== RESEARCH ERROR =====")
            print(f"🧬 RESEARCH: Returning error result with exception details")
            return error_suggestion
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for research tracking"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _apply_analysis_to_company(self, company: CompanyData, analysis_result: Dict[str, Any]):
        """Apply Bedrock analysis results to company data"""
        if "error" in analysis_result:
            self.logger.warning(f"Analysis error for {company.name}: {analysis_result['error']}")
            return
        
        # Update company data with analysis results
        company.industry = analysis_result.get("industry", company.industry)
        company.business_model = analysis_result.get("business_model", company.business_model)
        company.company_size = analysis_result.get("company_size", company.company_size)
        company.target_market = analysis_result.get("target_market", company.target_market)
        company.ai_summary = analysis_result.get("ai_summary", "")
        
        # Merge lists (avoid duplicates)
        if analysis_result.get("tech_stack"):
            existing_tech = set(company.tech_stack or [])
            new_tech = set(analysis_result["tech_stack"])
            company.tech_stack = list(existing_tech.union(new_tech))
        
        if analysis_result.get("key_services"):
            existing_services = set(company.key_services or [])
            new_services = set(analysis_result["key_services"])
            company.key_services = list(existing_services.union(new_services))
        
        if analysis_result.get("pain_points"):
            existing_pains = set(company.pain_points or [])
            new_pains = set(analysis_result["pain_points"])
            company.pain_points = list(existing_pains.union(new_pains))
    
    def _execute_job_listings_research(self, company_name: str, company_website: str) -> Dict[str, Any]:
        """Execute job listings research using intelligent crawling"""
        try:
            self.logger.info(f"Executing intelligent job listings crawl for {company_name}")
            
            # Import the OpenAI client and job listings crawler
            from src.job_listings_crawler import JobListingsCrawler
            
            # Try to use OpenAI client first, fallback to Bedrock
            llm_client = None
            try:
                from src.openai_client import SimpleOpenAIClient
                llm_client = SimpleOpenAIClient()
                self.logger.info("✅ Using OpenAI for job listings analysis")
            except Exception as e:
                self.logger.warning(f"OpenAI not available, trying Bedrock: {e}")
                if self.bedrock_client:
                    llm_client = self.bedrock_client
                    self.logger.info("✅ Using Bedrock for job listings analysis")
                else:
                    self.logger.warning("No AI client available for job listings research")
                    return {'job_listings': 'AI client not available', 'details': {}}
            
            # Create crawler instance with appropriate client
            if hasattr(llm_client, 'analyze_content') and 'SimpleOpenAIClient' in str(type(llm_client)):
                crawler = JobListingsCrawler(openai_client=llm_client)
            else:
                crawler = JobListingsCrawler(bedrock_client=llm_client)
            
            # Execute intelligent crawling
            self.logger.info(f"Starting intelligent job listings crawl for {company_name}")
            result = crawler.crawl_job_listings(company_name, company_website)
            
            self.logger.info(f"Job listings crawl completed for {company_name}: {result.get('job_listings', 'Unknown')}")
            return result
                
        except Exception as e:
            self.logger.error(f"Job listings research failed for {company_name}: {e}")
            return {'job_listings': f'Research failed: {str(e)}', 'details': {}}
    
    def _parse_job_listings_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response for job listings data"""
        try:
            import json
            
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                # Extract key information
                job_listings = "No job listings found"
                details = {}
                
                # Check for various indicators of active hiring
                if data.get('current_positions') or data.get('open_positions'):
                    positions = data.get('current_positions', data.get('open_positions', []))
                    if isinstance(positions, list) and len(positions) > 0:
                        job_listings = f"Yes - {len(positions)} open positions"
                        details['positions'] = positions[:5]  # Limit to first 5
                    elif isinstance(positions, str) and positions.lower() not in ['none', 'no', '']:
                        job_listings = "Yes - Multiple positions available"
                        details['description'] = positions
                
                # Check for hiring indicators
                if data.get('active_hiring') or data.get('hiring_status'):
                    hiring_status = data.get('active_hiring', data.get('hiring_status'))
                    if str(hiring_status).lower() in ['true', 'yes', 'active']:
                        if job_listings == "No job listings found":
                            job_listings = "Yes - Actively hiring"
                
                # Extract additional details
                if data.get('frequent_roles'):
                    details['frequent_roles'] = data['frequent_roles']
                if data.get('required_skills'):
                    details['required_skills'] = data['required_skills']
                if data.get('remote_work'):
                    details['remote_work'] = data['remote_work']
                
                return {
                    'job_listings': job_listings,
                    'details': details,
                    'raw_data': data
                }
            else:
                # Fallback: analyze text for hiring indicators
                response_lower = response.lower()
                if any(indicator in response_lower for indicator in ['hiring', 'open position', 'job opening', 'career', 'apply now']):
                    return {
                        'job_listings': 'Yes - Hiring activity detected',
                        'details': {'analysis': 'Text analysis indicates hiring activity'},
                        'raw_response': response[:200]
                    }
                else:
                    return {
                        'job_listings': 'No clear hiring indicators found',
                        'details': {'analysis': 'No obvious hiring signals detected'},
                        'raw_response': response[:200]
                    }
                    
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback to text analysis
            response_lower = response.lower()
            if any(indicator in response_lower for indicator in ['hiring', 'open position', 'job opening', 'career']):
                return {
                    'job_listings': 'Yes - Hiring activity detected (text analysis)',
                    'details': {'note': 'JSON parsing failed, used text analysis'},
                    'raw_response': response[:200]
                }
            else:
                return {
                    'job_listings': 'No hiring indicators found',
                    'details': {'note': 'JSON parsing failed, no clear signals'},
                    'raw_response': response[:200]
                }
        except Exception as e:
            self.logger.error(f"Error parsing job listings response: {e}")
            return {
                'job_listings': f'Parsing error: {str(e)}',
                'details': {},
                'raw_response': response[:200] if response else 'No response'
            }