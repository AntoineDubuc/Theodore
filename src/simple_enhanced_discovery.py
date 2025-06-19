"""
Simplified Enhanced Similarity Discovery
Uses LLM for contextual discovery without async complications
"""

import logging
import json
import os
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup

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
        """Discover similar companies using LLM + Vector search + Google search"""
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
            
            # Step 5: If we have few or no results, enhance with Google search
            if len(combined_results) < limit:
                self.logger.info(f"Only {len(combined_results)} results found, enhancing with Google search")
                google_results = self._google_search_discovery(company_name, limit - len(combined_results))
                combined_results.extend(google_results)
            
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
        
        self.logger.info(f"On-demand research for: {company_suggestion.get('name', 'unknown')}")
        
        if not self.scraper:
            self.logger.warning("No scraper available for on-demand research")
            return company_suggestion
        
        try:
            company_name = company_suggestion.get('company_name', company_suggestion.get('name', '')).strip()
            company_website = company_suggestion.get('website', '').strip()
            
            if not company_name or not company_website:
                self.logger.warning(f"Missing name or website for research: {company_suggestion}")
                return company_suggestion
            
            # Create temporary CompanyData object for scraping
            from src.models import CompanyData
            temp_company = CompanyData(
                name=company_name,
                website=company_website
            )
            
            # Start progress tracking for research
            from src.progress_logger import start_company_processing
            job_id = start_company_processing(company_name)
            
            
            # This should now work with the subprocess-based scraper
            scraped_company = self.scraper.scrape_company(temp_company, job_id)
            
            
            if scraped_company.scrape_status == "success":
                # Run scraped content through LLM analysis for intelligent extraction
                self.logger.info(f"Analyzing scraped content with LLM for {company_name}")
                
                analysis_result = self.ai_client.analyze_company_content(scraped_company)
                
                # Apply LLM analysis to the scraped company data
                if "error" not in analysis_result:
                    self._apply_analysis_to_company(scraped_company, analysis_result)
                    self.logger.info(f"LLM analysis completed for {company_name}")
                else:
                    self.logger.warning(f"LLM analysis failed for {company_name}: {analysis_result.get('error')}")
                
                # Execute job listings research
                job_listings_data = self._execute_job_listings_research(company_name, company_website)
                
                # Complete the job tracking
                from src.progress_logger import complete_company_processing
                complete_company_processing(job_id, True, summary=f"Research completed for {company_name}")
                
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
                
                self.logger.info(f"Successfully researched {company_name}")
                return enhanced_suggestion
                
            else:
                
                # Complete the job tracking with failure
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
                
                self.logger.warning(f"Research failed for {company_name}: {scraped_company.scrape_error}")
                return enhanced_suggestion
            
        except Exception as e:
            
            import traceback
            traceback_str = traceback.format_exc()
            
            self.logger.error(f"Error in on-demand research for {company_suggestion.get('name', 'unknown')}: {e}")
            
            # Complete the job tracking with error (if job_id exists)
            try:
                if 'job_id' in locals():
                    from src.progress_logger import complete_company_processing
                    complete_company_processing(job_id, False, error=str(e))
                else:
                    pass
            except Exception as cleanup_error:
                pass
            
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
    
    def _google_search_discovery(self, company_name: str, limit: int) -> List[Dict[str, Any]]:
        """Use Google search to discover similar companies"""
        self.logger.info(f"🔍 Starting Google search discovery for: {company_name}")
        
        try:
            # First, use LLM to generate search queries for similar companies
            search_queries = self._generate_similarity_search_queries(company_name)
            
            all_results = []
            for query in search_queries[:3]:  # Limit to 3 queries
                self.logger.info(f"🔍 Searching: {query}")
                urls = self._google_search_api(query)
                
                for url in urls[:limit]:
                    # Extract company name from URL/search result
                    company_info = self._extract_company_from_url(url)
                    if company_info:
                        all_results.append({
                            'company_name': company_info['name'],
                            'website': url,
                            'similarity_score': 0.75,  # Default score for Google results
                            'confidence': 0.75,
                            'reasoning': [f"Found via Google search: '{query}'"],
                            'relationship_type': 'competitor',
                            'discovery_method': 'Google Search',
                            'business_context': f"Discovered as similar to {company_name}",
                            'sources': ['google'],
                            'requires_research': True
                        })
            
            # Deduplicate by company name
            unique_results = {}
            for result in all_results:
                name = result['company_name'].lower()
                if name not in unique_results:
                    unique_results[name] = result
            
            results = list(unique_results.values())[:limit]
            self.logger.info(f"✅ Google search found {len(results)} unique companies")
            return results
            
        except Exception as e:
            self.logger.error(f"Google search discovery failed: {e}")
            return []
    
    def _generate_similarity_search_queries(self, company_name: str) -> List[str]:
        """Generate Google search queries to find similar companies"""
        try:
            prompt = f"""Generate 3 specific Google search queries to find companies similar to "{company_name}".

For each query, think about:
- Competitors in the same industry
- Companies offering similar services
- Alternative solutions to the same problem

Return ONLY the 3 search queries, one per line. Make them specific and likely to return company websites.

Example format:
"CRM software companies like Salesforce"
"Salesforce competitors enterprise"
"cloud CRM platforms similar to Salesforce"

Search queries for companies similar to {company_name}:"""

            response = self.ai_client.analyze_content(prompt)
            if response:
                queries = [q.strip().strip('"') for q in response.strip().split('\n') if q.strip()]
                return queries[:3]
            
            # Fallback queries
            return [
                f"companies similar to {company_name}",
                f"{company_name} competitors",
                f"alternatives to {company_name}"
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to generate search queries: {e}")
            return [f"{company_name} competitors"]
    
    def _google_search_api(self, query: str) -> List[str]:
        """Perform actual Google search using multiple methods"""
        self.logger.info(f"🔍 Searching Google for: '{query}'")
        
        try:
            # Method 1: Try Google Custom Search API if available
            google_api_key = os.getenv('GOOGLE_API_KEY')
            google_cx = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
            
            if google_api_key and google_cx:
                return self._google_custom_search_api(query, google_api_key, google_cx)
            
            # Method 2: Try SerpAPI if available
            serpapi_key = os.getenv('SERPAPI_KEY')
            if serpapi_key:
                return self._serpapi_search(query, serpapi_key)
            
            # Method 3: DuckDuckGo as fallback
            return self._duckduckgo_search(query)
            
        except Exception as e:
            self.logger.error(f"Google search API failed: {e}")
            return []
    
    def _google_custom_search_api(self, query: str, api_key: str, cx: str) -> List[str]:
        """Use Google Custom Search API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'num': 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            urls = []
            
            if 'items' in data:
                for item in data['items']:
                    urls.append(item['link'])
                    
            self.logger.info(f"✅ Google Custom Search found {len(urls)} results")
            return urls
            
        except Exception as e:
            self.logger.error(f"Google Custom Search API failed: {e}")
            return []
    
    def _serpapi_search(self, query: str, api_key: str) -> List[str]:
        """Use SerpAPI for Google search"""
        try:
            url = "https://serpapi.com/search"
            params = {
                'api_key': api_key,
                'engine': 'google',
                'q': query,
                'num': 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            urls = []
            
            if 'organic_results' in data:
                for result in data['organic_results']:
                    urls.append(result['link'])
                    
            self.logger.info(f"✅ SerpAPI found {len(urls)} results")
            return urls
            
        except Exception as e:
            self.logger.error(f"SerpAPI failed: {e}")
            return []
    
    def _duckduckgo_search(self, query: str) -> List[str]:
        """Use DuckDuckGo as fallback search"""
        try:
            search_url = f"https://duckduckgo.com/html/?q={quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            
            # Find result links
            for result in soup.find_all('a', {'class': 'result__a'}):
                href = result.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
                    if len(urls) >= 5:
                        break
            
            self.logger.info(f"✅ DuckDuckGo found {len(urls)} results")
            return urls
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _extract_company_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """Extract company name from URL"""
        try:
            from urllib.parse import urlparse
            
            # Parse the URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            domain = domain.replace('www.', '')
            
            # Extract company name from domain
            company_name = domain.split('.')[0]
            
            # Clean up company name
            company_name = company_name.replace('-', ' ').replace('_', ' ')
            company_name = ' '.join(word.capitalize() for word in company_name.split())
            
            # Skip generic domains
            if company_name.lower() in ['google', 'wikipedia', 'linkedin', 'facebook', 'twitter', 'youtube']:
                return None
            
            return {
                'name': company_name,
                'domain': domain
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract company from URL {url}: {e}")
            return None