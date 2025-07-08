"""
Antoine Scraper Adapter for Theodore
====================================

Adapter that wraps the antoine 4-phase pipeline to provide the same interface
as Theodore's existing IntelligentCompanyScraperSync, ensuring drop-in compatibility.

This adapter:
1. Maintains the same scrape_company() method signature
2. Uses antoine's 4-phase pipeline internally (discovery → selection → crawling → extraction)
3. Returns CompanyData objects with the same field structure
4. Maintains progress tracking compatibility
5. Provides the same error handling patterns

Usage:
    # Drop-in replacement for IntelligentCompanyScraperSync
    scraper = AntoineScraperAdapter(config, bedrock_client)
    company_data = scraper.scrape_company(company, job_id=job_id)
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from src.models import CompanyData, CompanyIntelligenceConfig
from src.progress_logger import log_processing_phase

# Import antoine components
from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync
from src.antoine_crawler import crawl_selected_pages_sync
from src.antoine_extraction import extract_company_fields

logger = logging.getLogger(__name__)


class AntoineScraperAdapter:
    """
    Adapter that wraps antoine's 4-phase pipeline to provide Theodore compatibility.
    
    This class implements the same interface as IntelligentCompanyScraperSync
    but uses antoine's enhanced pipeline internally.
    """
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.bedrock_client = bedrock_client
        logger.info("Antoine scraper adapter initialized")
    
    def scrape_company(self, company: CompanyData, job_id: str = None) -> CompanyData:
        """
        Scrape company using antoine's 4-phase pipeline.
        
        This method provides the same interface as IntelligentCompanyScraperSync.scrape_company()
        but uses antoine's enhanced pipeline internally.
        
        Args:
            company: CompanyData object with at least name and website
            job_id: Optional job ID for progress tracking
            
        Returns:
            CompanyData object with extracted fields
        """
        
        # Start timing
        start_time = time.time()
        
        # Initialize company data
        company.scrape_status = "in_progress"
        company.scrape_error = None
        
        if not company.website:
            company.scrape_status = "failed"
            company.scrape_error = "No website URL provided"
            return company
        
        try:
            # Phase 1: Discovery
            if job_id:
                log_processing_phase(job_id, "discovery", "🔍 Discovering website paths...")
            
            logger.info(f"🔍 Phase 1: Starting path discovery for {company.website}")
            discovery_result = discover_all_paths_sync(
                company.website,
                timeout_seconds=30
            )
            
            if not discovery_result.all_paths:
                # Fallback for sites like Verizon where discovery times out
                logger.warning(f"No paths discovered for {company.website}, using fallback paths")
                
                # Use common corporate website paths as fallback
                fallback_paths = [
                    "/",
                    "/about",
                    "/about-us",
                    "/about/our-company",
                    "/company",
                    "/contact",
                    "/contact-us",
                    "/careers",
                    "/jobs",
                    "/business",
                    "/enterprise",
                    "/support",
                    "/help",
                    "/products",
                    "/services",
                    "/solutions",
                    "/leadership",
                    "/team",
                    "/news",
                    "/press"
                ]
                
                discovery_result.all_paths = fallback_paths
                logger.info(f"Using {len(fallback_paths)} fallback paths for {company.name}")
            
            logger.info(f"✅ Phase 1: Discovered {len(discovery_result.all_paths)} paths")
            
            # Phase 2: Selection
            if job_id:
                log_processing_phase(job_id, "selection", "🎯 Selecting valuable pages...")
            
            logger.info(f"🎯 Phase 2: Starting LLM path selection")
            selection_result = filter_valuable_links_sync(
                discovery_result.all_paths,
                company.website,
                min_confidence=0.6,
                timeout_seconds=60
            )
            
            if not selection_result.success or not selection_result.selected_paths:
                company.scrape_status = "failed"
                company.scrape_error = f"Path selection failed: {selection_result.error}"
                return company
            
            logger.info(f"✅ Phase 2: Selected {len(selection_result.selected_paths)} valuable paths")
            
            # Phase 3: Crawling
            if job_id:
                log_processing_phase(job_id, "crawling", "📄 Extracting page content...")
            
            logger.info(f"📄 Phase 3: Starting content crawling")
            # Ensure website has protocol for crawling
            crawl_base_url = company.website
            if not crawl_base_url.startswith(('http://', 'https://')):
                crawl_base_url = f"https://{crawl_base_url}"
            
            crawl_result = crawl_selected_pages_sync(
                crawl_base_url,
                selection_result.selected_paths,
                timeout_seconds=30,
                max_concurrent=10
            )
            
            if not crawl_result.aggregated_content:
                company.scrape_status = "failed"
                company.scrape_error = "No content extracted from pages"
                return company
            
            logger.info(f"✅ Phase 3: Crawled {crawl_result.successful_pages} pages, {len(crawl_result.aggregated_content)} chars")
            
            # Phase 4: Extraction
            if job_id:
                log_processing_phase(job_id, "extraction", "🧠 Extracting company fields...")
            
            logger.info(f"🧠 Phase 4: Starting field extraction")
            extraction_result = extract_company_fields(
                crawl_result,
                company.name or "Unknown Company",
                timeout_seconds=60
            )
            
            if not extraction_result.success:
                company.scrape_status = "failed"
                company.scrape_error = f"Field extraction failed: {extraction_result.error}"
                return company
            
            logger.info(f"✅ Phase 4: Extracted {len(extraction_result.extracted_fields)} fields")
            
            # Apply extracted fields to company object
            self._apply_extracted_fields_to_company(company, extraction_result.extracted_fields)
            
            # Track LLM costs and tokens from extraction
            company.total_input_tokens = extraction_result.tokens_used
            company.total_output_tokens = extraction_result.tokens_used  # Estimate - actual may vary
            company.total_cost_usd = extraction_result.cost_usd
            
            # Initialize LLM calls breakdown if not exists
            if not hasattr(company, 'llm_calls_breakdown') or company.llm_calls_breakdown is None:
                company.llm_calls_breakdown = []
            
            # Add extraction LLM call to breakdown
            company.llm_calls_breakdown.append({
                'model': extraction_result.model_used,
                'purpose': 'field_extraction',
                'input_tokens': extraction_result.tokens_used,
                'output_tokens': extraction_result.tokens_used,  # Estimate
                'cost_usd': extraction_result.cost_usd,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Also track selection costs if available
            if hasattr(selection_result, 'cost_usd') and selection_result.cost_usd > 0:
                company.total_cost_usd += selection_result.cost_usd
                company.llm_calls_breakdown.append({
                    'model': 'amazon/nova-pro-v1',
                    'purpose': 'page_selection',
                    'cost_usd': selection_result.cost_usd,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Set successful scrape status
            company.scrape_status = "success"
            company.crawl_duration = time.time() - start_time
            company.pages_crawled = [url for url in selection_result.selected_paths]
            company.scraped_urls = selection_result.selected_paths
            company.crawl_depth = len(selection_result.selected_paths)
            company.raw_content = crawl_result.aggregated_content[:10000]  # Limit to 10KB
            
            # Update timestamps
            company.last_updated = datetime.utcnow()
            
            logger.info(f"✅ Antoine pipeline completed successfully for {company.name} in {company.crawl_duration:.1f}s")
            
            return company
            
        except Exception as e:
            logger.error(f"❌ Antoine pipeline failed for {company.name}: {str(e)}")
            company.scrape_status = "failed"
            company.scrape_error = str(e)
            company.crawl_duration = time.time() - start_time
            return company
    
    def _apply_extracted_fields_to_company(self, company: CompanyData, extracted_fields: dict):
        """
        Apply extracted fields from antoine to CompanyData object.
        
        This method maps antoine's extracted fields to Theodore's CompanyData model,
        ensuring compatibility with the existing data structure.
        """
        
        # Core company information
        if extracted_fields.get('company_name') and not company.name:
            company.name = extracted_fields['company_name']
        
        if extracted_fields.get('company_description'):
            company.company_description = extracted_fields['company_description']
        
        if extracted_fields.get('value_proposition'):
            company.value_proposition = extracted_fields['value_proposition']
        
        if extracted_fields.get('industry'):
            company.industry = extracted_fields['industry']
        
        if extracted_fields.get('location'):
            company.location = extracted_fields['location']
        
        if extracted_fields.get('founding_year'):
            company.founding_year = extracted_fields['founding_year']
        
        if extracted_fields.get('company_size'):
            company.company_size = extracted_fields['company_size']
        
        if extracted_fields.get('employee_count_range'):
            company.employee_count_range = extracted_fields['employee_count_range']
        
        # Business model information
        if extracted_fields.get('business_model_type'):
            company.business_model_type = extracted_fields['business_model_type']
        
        if extracted_fields.get('business_model'):
            company.business_model = extracted_fields['business_model']
        
        if extracted_fields.get('saas_classification'):
            company.saas_classification = extracted_fields['saas_classification']
        
        if extracted_fields.get('is_saas') is not None:
            company.is_saas = extracted_fields['is_saas']
        elif extracted_fields.get('is_saas') is None and company.is_saas is None:
            # Ensure is_saas is not None for Pinecone compatibility
            company.is_saas = False
        
        if extracted_fields.get('classification_confidence'):
            company.classification_confidence = extracted_fields['classification_confidence']
        
        if extracted_fields.get('classification_justification'):
            company.classification_justification = extracted_fields['classification_justification']
        
        # Products and services
        if extracted_fields.get('products_services_offered'):
            company.products_services_offered = extracted_fields['products_services_offered']
        
        if extracted_fields.get('key_services'):
            company.key_services = extracted_fields['key_services']
        
        if extracted_fields.get('target_market'):
            company.target_market = extracted_fields['target_market']
        
        if extracted_fields.get('pain_points'):
            company.pain_points = extracted_fields['pain_points']
        
        if extracted_fields.get('competitive_advantages'):
            company.competitive_advantages = extracted_fields['competitive_advantages']
        
        if extracted_fields.get('tech_stack'):
            company.tech_stack = extracted_fields['tech_stack']
        
        # Company stage and metrics
        if extracted_fields.get('company_stage'):
            company.company_stage = extracted_fields['company_stage']
        
        if extracted_fields.get('funding_status'):
            company.funding_status = extracted_fields['funding_status']
        
        if extracted_fields.get('tech_sophistication'):
            company.tech_sophistication = extracted_fields['tech_sophistication']
        
        if extracted_fields.get('geographic_scope'):
            company.geographic_scope = extracted_fields['geographic_scope']
        
        # Leadership and people
        if extracted_fields.get('key_decision_makers'):
            company.key_decision_makers = extracted_fields['key_decision_makers']
        
        if extracted_fields.get('leadership_team'):
            company.leadership_team = extracted_fields['leadership_team']
        
        # Growth indicators
        if extracted_fields.get('has_job_listings') is not None:
            company.has_job_listings = extracted_fields['has_job_listings']
        
        if extracted_fields.get('job_listings_count'):
            company.job_listings_count = extracted_fields['job_listings_count']
        
        if extracted_fields.get('recent_news'):
            company.recent_news = extracted_fields['recent_news']
        
        # Technology and digital presence
        if extracted_fields.get('has_chat_widget') is not None:
            company.has_chat_widget = extracted_fields['has_chat_widget']
        
        if extracted_fields.get('has_forms') is not None:
            company.has_forms = extracted_fields['has_forms']
        
        if extracted_fields.get('social_media'):
            company.social_media = extracted_fields['social_media']
        
        if extracted_fields.get('contact_info'):
            company.contact_info = extracted_fields['contact_info']
        
        # Recognition and partnerships
        if extracted_fields.get('company_culture'):
            company.company_culture = extracted_fields['company_culture']
        
        if extracted_fields.get('awards'):
            company.awards = extracted_fields['awards']
        
        if extracted_fields.get('certifications'):
            company.certifications = extracted_fields['certifications']
        
        if extracted_fields.get('partnerships'):
            company.partnerships = extracted_fields['partnerships']
        
        logger.info(f"Applied {len([k for k, v in extracted_fields.items() if v is not None])} non-null fields to company data")
    
    def batch_scrape_companies(self, companies: list) -> list:
        """
        Batch scrape multiple companies using antoine batch processor.
        
        This method provides compatibility with the main pipeline's batch processing.
        
        Args:
            companies: List of CompanyData objects to scrape
            
        Returns:
            List of CompanyData objects with scraped data
        """
        # Import here to avoid circular dependency
        from antoine.batch.batch_processor import AntoineBatchProcessor
        
        logger.info(f"Starting batch scrape of {len(companies)} companies using antoine batch processor")
        
        # Convert CompanyData objects to dict format for batch processor
        company_dicts = []
        for company in companies:
            company_dicts.append({
                'name': company.name,
                'website': company.website
            })
        
        # Create batch processor
        batch_processor = AntoineBatchProcessor(
            config=self.config,
            bedrock_client=self.bedrock_client,
            max_concurrent_companies=3  # Conservative default
        )
        
        try:
            # Process batch
            batch_result = batch_processor.process_batch(company_dicts, batch_name="pipeline_batch")
            
            # Return the processed company results
            logger.info(f"Batch processing completed: {batch_result.successful}/{batch_result.total_companies} successful")
            return batch_result.company_results
            
        finally:
            # Cleanup
            batch_processor.shutdown()