"""
Main processing pipeline for Theodore company intelligence system
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.models import (
    CompanyData, SurveyResponse, ProcessingJob, 
    CompanyIntelligenceConfig, SectorCluster, CompanySimilarity
)
# Core modules only - experimental modules commented out
# from src.experimental.crawl4ai_scraper import CompanyWebScraper
from src.async_execution_manager import IntelligentCompanyScraperAsync
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.pinecone_client import PineconeClient
# from src.experimental.clustering import SectorClusteringEngine
# from src.experimental.similarity_pipeline import SimilarityDiscoveryPipeline
# from src.experimental.company_discovery import CompanyDiscoveryService
# from src.experimental.similarity_validator import SimilarityValidator
# from src.experimental.extraction_improvements import enhance_company_extraction, ENHANCED_EXTRACTION_PROMPTS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TheodoreIntelligencePipeline:
    """Main pipeline for processing company intelligence"""
    
    def __init__(self, config: CompanyIntelligenceConfig, 
                 pinecone_api_key: str, pinecone_environment: str, pinecone_index: str):
        self.config = config
        
        # Initialize components
        self.bedrock_client = BedrockClient(config)  # Keep for embeddings
        self.gemini_client = GeminiClient(config)    # Use for analysis and similarity
        # Use concurrent intelligent scraper with detailed URL logging and thread-safe LLM calls
        from src.concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
        self.scraper = ConcurrentIntelligentScraperSync(config, self.bedrock_client)
        # Legacy scraper removed - using intelligent scraper only
        # self.legacy_scraper = CompanyWebScraper(config, self.bedrock_client)
        self.pinecone_client = PineconeClient(
            config, pinecone_api_key, pinecone_environment, pinecone_index
        )
        # Experimental clustering engine removed
        # self.clustering_engine = SectorClusteringEngine(config, self.pinecone_client)
        # self.similarity_pipeline = SimilarityDiscoveryPipeline(config)
        
        # Similarity pipeline removed - using simple enhanced discovery in app.py
        # self.similarity_pipeline.bedrock_client = self.gemini_client  # Use Gemini instead of Bedrock
        # self.similarity_pipeline.pinecone_client = self.pinecone_client
        # self.similarity_pipeline.discovery_service = CompanyDiscoveryService(self.gemini_client)
        # self.similarity_pipeline.similarity_validator = SimilarityValidator(self.gemini_client)
        
        logger.info("Theodore Intelligence Pipeline initialized")
    
    def process_survey_csv(self, input_csv_path: str, output_csv_path: str) -> ProcessingJob:
        """Process survey CSV and generate company intelligence"""
        
        # Create processing job
        job = ProcessingJob(
            total_companies=0,  # Will be updated after loading CSV
            started_at=datetime.utcnow()
        )
        job.status = "running"
        
        try:
            # Load survey data
            logger.info(f"Loading survey data from {input_csv_path}")
            survey_responses = self._load_survey_csv(input_csv_path)
            job.total_companies = len(survey_responses)
            
            # Convert to CompanyData objects
            companies = self._convert_survey_to_companies(survey_responses)
            
            # Process companies in batches
            logger.info(f"Processing {len(companies)} companies")
            processed_companies = self._process_companies_batch(companies, job)
            
            # Generate sector clusters
            logger.info("Generating sector clusters")
            sectors = self._generate_sector_clusters(processed_companies, job)
            
            # Save results
            logger.info(f"Saving results to {output_csv_path}")
            self._save_results_csv(processed_companies, sectors, output_csv_path)
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            logger.info(f"Pipeline completed successfully. Processed {job.processed_companies} companies, discovered {job.sectors_discovered} sectors")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            job.status = "failed"
            job.errors.append(str(e))
            job.completed_at = datetime.utcnow()
        
        return job
    
    def process_single_company(self, company_name: str, website: str, job_id: str = None) -> CompanyData:
        """Process a single company for testing/demo purposes"""
        logger.info(f"Processing single company: {company_name}")
        
        # Get existing company or create new one to prevent duplicates
        company = self._get_or_create_company(company_name, website)
        
        # Scrape website with progress tracking
        company = self.scraper.scrape_company(company, job_id=job_id)
        
        if company.scrape_status != "success":
            logger.warning(f"Scraping failed for {company_name}: {company.scrape_error}")
            return company
        
        # Analyze with Bedrock
        analysis_result = self.bedrock_client.analyze_company_content(company)
        self._apply_analysis_to_company(company, analysis_result)
        
        # Classify business model and category
        try:
            from src.classification.saas_classifier import SaaSBusinessModelClassifier
            classifier = SaaSBusinessModelClassifier(self.bedrock_client)
            classification_result = classifier.classify_company(company)
            
            # Apply classification results (classification_result is a ClassificationResult object)
            if hasattr(classification_result, 'category'):
                company.saas_classification = classification_result.category
                company.classification_confidence = classification_result.confidence
                company.classification_justification = classification_result.justification
                company.is_saas = classification_result.is_saas
                company.classification_timestamp = datetime.utcnow()
            else:
                # Handle dict format as fallback
                company.saas_classification = classification_result.get('category', 'Unclassified')
                company.classification_confidence = classification_result.get('confidence', 0.0)
                company.classification_justification = classification_result.get('justification', '')
                company.is_saas = classification_result.get('is_saas', None)
                company.classification_timestamp = datetime.utcnow()
            
            logger.info(f"Classified {company_name}: {company.saas_classification} ({company.classification_confidence:.1%} confidence)")
        except Exception as e:
            logger.warning(f"Classification failed for {company_name}: {e}")
            company.saas_classification = 'Unclassified'
            company.is_saas = None
        
        # Apply enhanced extraction for missing fields (temporarily disabled)
        # if company.raw_content:
        #     logger.info(f"Applying enhanced extraction for {company_name}")
        #     company = enhance_company_extraction(company, company.raw_content)
        
        # Use Gemini for detailed extraction if still missing key fields (temporarily disabled)
        # if not company.founding_year or not company.employee_count_range or not company.social_media:
        #     try:
        #         detailed_result = self.gemini_client.analyze_content(
        #             ENHANCED_EXTRACTION_PROMPTS['detailed_extraction'] + f"\n\nContent:\n{company.raw_content[:5000]}"
        #         )
        #         # Parse and apply results
        #         import json
        #         import re
        #         json_match = re.search(r'\{.*\}', detailed_result, re.DOTALL)
        #         if json_match:
        #             extra_data = json.loads(json_match.group())
        #             if extra_data.get('founding_year') and not company.founding_year:
        #                 company.founding_year = extra_data['founding_year']
        #             if extra_data.get('employee_count_range') and not company.employee_count_range:
        #                 company.employee_count_range = extra_data['employee_count_range']
        #             if extra_data.get('social_media') and not company.social_media:
        #                 company.social_media = extra_data['social_media']
        #             if extra_data.get('certifications'):
        #                 company.certifications = extra_data['certifications']
        #             if extra_data.get('partnerships'):
        #                 company.partnerships = extra_data['partnerships']
        #     except Exception as e:
        #         logger.warning(f"Enhanced extraction failed: {e}")
        
        # Generate embedding
        embedding_text = self._prepare_embedding_text(company)
        company.embedding = self.bedrock_client.generate_embedding(embedding_text)
        
        # Update timestamp when processing/updating company
        company.last_updated = datetime.utcnow()
        
        # Store in Pinecone (will update existing entry if company already exists)
        if company.embedding:
            self.pinecone_client.upsert_company(company)
            logger.info(f"Successfully upserted {company_name} to Pinecone database")
        
        logger.info(f"Successfully processed {company_name}")
        return company
    
    def find_similar_companies_for_company(self, company_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find companies similar to a given company"""
        return self.pinecone_client.find_similar_companies(company_id, top_k)
    
    def get_sector_analysis(self, sector_name: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific sector"""
        # Find companies in sector
        companies_data = self.pinecone_client.find_companies_by_industry(sector_name)
        
        if not companies_data:
            return {"error": f"No companies found in sector: {sector_name}"}
        
        # Get full company data (this is simplified - in practice you'd want to cache this)
        company_ids = [comp["company_id"] for comp in companies_data]
        
        # Generate sector summary using Bedrock
        # This is a simplified version - you'd want to reconstruct full CompanyData objects
        sector_summary = f"Sector analysis for {sector_name} with {len(companies_data)} companies"
        
        return {
            "sector_name": sector_name,
            "company_count": len(companies_data),
            "companies": companies_data,
            "summary": sector_summary
        }
    
    def _load_survey_csv(self, csv_path: str) -> List[SurveyResponse]:
        """Load survey responses from CSV"""
        survey_responses = []
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                response = SurveyResponse(
                    company_name=row.get('company_name', '').strip(),
                    website=row.get('website', '').strip(),
                    contact_email=row.get('contact_email', '').strip(),
                    pain_points=row.get('pain_points', '').strip(),
                    survey_date=datetime.utcnow(),  # Default to now
                    survey_source=row.get('survey_source', 'csv_import')
                )
                
                if response.company_name:  # Only add if we have a company name
                    survey_responses.append(response)
        
        logger.info(f"Loaded {len(survey_responses)} survey responses")
        return survey_responses
    
    def _get_or_create_company(self, company_name: str, website: str, **kwargs) -> CompanyData:
        """Get existing company or create new one to prevent duplicates"""
        # Check if company already exists
        existing_company = self.pinecone_client.find_company_by_name(company_name)
        
        if existing_company:
            logger.info(f"Found existing company: {company_name} (ID: {existing_company.id})")
            # Update website if different
            if website and website != existing_company.website:
                logger.info(f"Updating website from {existing_company.website} to {website}")
                existing_company.website = website
            
            # Update any additional fields from kwargs
            for key, value in kwargs.items():
                if hasattr(existing_company, key) and value:
                    current_value = getattr(existing_company, key)
                    # For list fields, extend rather than replace
                    if isinstance(current_value, list) and isinstance(value, list):
                        if not current_value:  # If current is empty, use new value
                            setattr(existing_company, key, value)
                    elif not current_value:  # For other fields, only update if current is empty
                        setattr(existing_company, key, value)
            
            return existing_company
        else:
            # Create new company
            logger.info(f"Creating new company entry for: {company_name}")
            return CompanyData(name=company_name, website=website, **kwargs)
    
    def _convert_survey_to_companies(self, survey_responses: List[SurveyResponse]) -> List[CompanyData]:
        """Convert survey responses to CompanyData objects"""
        companies = []
        
        for response in survey_responses:
            website = response.website or f"https://{response.company_name.lower().replace(' ', '')}.com"
            company = self._get_or_create_company(
                company_name=response.company_name,
                website=website,
                pain_points=[response.pain_points] if response.pain_points else []
            )
            companies.append(company)
        
        return companies
    
    def _process_companies_batch(self, companies: List[CompanyData], job: ProcessingJob) -> List[CompanyData]:
        """Process companies in batches"""
        processed_companies = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(companies)-1)//batch_size + 1}")
            
            # Scrape websites
            scraped_batch = self.scraper.batch_scrape_companies(batch)
            
            # Analyze with Bedrock and generate embeddings
            for company in scraped_batch:
                try:
                    if company.scrape_status == "success":
                        # AI analysis
                        analysis_result = self.bedrock_client.analyze_company_content(company)
                        self._apply_analysis_to_company(company, analysis_result)
                        
                        # Generate embedding
                        embedding_text = self._prepare_embedding_text(company)
                        company.embedding = self.bedrock_client.generate_embedding(embedding_text)
                        
                        job.processed_companies += 1
                    else:
                        job.failed_companies += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {company.name}: {str(e)}")
                    job.failed_companies += 1
                    job.errors.append(f"{company.name}: {str(e)}")
                
                processed_companies.append(company)
        
        # Batch upload to Pinecone
        companies_with_embeddings = [c for c in processed_companies if c.embedding]
        if companies_with_embeddings:
            self.pinecone_client.batch_upsert_companies(companies_with_embeddings)
        
        return processed_companies
    
    def _generate_sector_clusters(self, companies: List[CompanyData], job: ProcessingJob) -> List[SectorCluster]:
        """Generate sector clusters from processed companies"""
        try:
            companies_with_embeddings = [c for c in companies if c.embedding and c.industry]
            
            if len(companies_with_embeddings) < self.config.min_cluster_size:
                logger.warning("Not enough companies with embeddings for clustering")
                return []
            
            sectors = self.clustering_engine.cluster_companies_by_sector(companies_with_embeddings)
            job.sectors_discovered = len(sectors)
            
            return sectors
            
        except Exception as e:
            logger.error(f"Clustering failed: {str(e)}")
            job.errors.append(f"Clustering error: {str(e)}")
            return []
    
    def _apply_analysis_to_company(self, company: CompanyData, analysis_result: Dict[str, Any]):
        """Apply Bedrock analysis results to company data"""
        if "error" in analysis_result:
            logger.warning(f"Analysis error for {company.name}: {analysis_result['error']}")
            return
        
        # Update basic company data with analysis results
        company.industry = analysis_result.get("industry", company.industry)
        company.business_model = analysis_result.get("business_model", company.business_model)
        company.company_size = analysis_result.get("company_size", company.company_size)
        company.target_market = analysis_result.get("target_market", company.target_market)
        company.ai_summary = analysis_result.get("ai_summary", "")
        
        # Apply enhanced fields from the new comprehensive prompt
        company.company_stage = analysis_result.get("company_stage", company.company_stage)
        company.founding_year = analysis_result.get("founding_year", company.founding_year)
        company.location = analysis_result.get("location", company.location)
        company.employee_count_range = analysis_result.get("employee_count_range", company.employee_count_range)
        company.company_description = analysis_result.get("company_description", company.company_description)
        company.value_proposition = analysis_result.get("value_proposition", company.value_proposition)
        company.funding_status = analysis_result.get("funding_status", company.funding_status)
        company.company_culture = analysis_result.get("company_culture", company.company_culture)
        
        # Apply structured data fields (contact_info, social_media)
        if analysis_result.get("contact_info"):
            company.contact_info = analysis_result["contact_info"]
        
        if analysis_result.get("social_media"):
            company.social_media = analysis_result["social_media"]
        
        # Merge lists (avoid duplicates) - existing fields
        if analysis_result.get("tech_stack"):
            existing_tech = set(company.tech_stack)
            new_tech = set(analysis_result["tech_stack"])
            company.tech_stack = list(existing_tech.union(new_tech))
        
        if analysis_result.get("key_services"):
            existing_services = set(company.key_services)
            new_services = set(analysis_result["key_services"])
            company.key_services = list(existing_services.union(new_services))
        
        if analysis_result.get("pain_points"):
            existing_pains = set(company.pain_points)
            new_pains = set(analysis_result["pain_points"])
            company.pain_points = list(existing_pains.union(new_pains))
        
        # Merge new enhanced list fields
        if analysis_result.get("products_services_offered"):
            existing_products = set(company.products_services_offered)
            new_products = set(analysis_result["products_services_offered"])
            company.products_services_offered = list(existing_products.union(new_products))
        
        if analysis_result.get("competitive_advantages"):
            existing_advantages = set(company.competitive_advantages)
            new_advantages = set(analysis_result["competitive_advantages"])
            company.competitive_advantages = list(existing_advantages.union(new_advantages))
        
        if analysis_result.get("leadership_team"):
            existing_leadership = set(company.leadership_team)
            new_leadership = set(analysis_result["leadership_team"])
            company.leadership_team = list(existing_leadership.union(new_leadership))
        
        if analysis_result.get("partnerships"):
            existing_partnerships = set(company.partnerships)
            new_partnerships = set(analysis_result["partnerships"])
            company.partnerships = list(existing_partnerships.union(new_partnerships))
        
        if analysis_result.get("awards"):
            existing_awards = set(company.awards)
            new_awards = set(analysis_result["awards"])
            company.awards = list(existing_awards.union(new_awards))
        
        if analysis_result.get("recent_news"):
            existing_news = set(company.recent_news_events)
            new_news = set(analysis_result["recent_news"])
            company.recent_news_events = list(existing_news.union(new_news))
        
        # Job-related fields
        if analysis_result.get("job_listings_count"):
            company.job_listings_count = analysis_result["job_listings_count"]
        
        if analysis_result.get("job_listings"):
            company.job_listings = analysis_result["job_listings"]
            
        if analysis_result.get("job_listings_details"):
            existing_jobs = set(company.job_listings_details)
            new_jobs = set(analysis_result["job_listings_details"])
            company.job_listings_details = list(existing_jobs.union(new_jobs))
    
    def _prepare_embedding_text(self, company: CompanyData) -> str:
        """Prepare comprehensive text for embedding generation using vector content approach"""
        # Use the comprehensive vector content from PineconeClient
        return self.pinecone_client._prepare_vector_content(company)
    
    def _save_results_csv(self, companies: List[CompanyData], sectors: List[SectorCluster], output_path: str):
        """Save processing results to CSV"""
        
        # Create sector lookup
        company_to_sector = {}
        for sector in sectors:
            for company_id in sector.companies:
                company_to_sector[company_id] = sector.name
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = [
                'company_id', 'company_name', 'website', 'industry', 'sector_cluster',
                'business_model', 'company_size', 'tech_stack', 'key_services',
                'pain_points', 'target_market', 'ai_summary', 'has_chat_widget',
                'has_forms', 'scrape_status', 'created_at'
            ]
            
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for company in companies:
                writer.writerow({
                    'company_id': company.id,
                    'company_name': company.name,
                    'website': company.website,
                    'industry': company.industry or '',
                    'sector_cluster': company_to_sector.get(company.id, ''),
                    'business_model': company.business_model or '',
                    'company_size': company.company_size or '',
                    'tech_stack': ', '.join(company.tech_stack) if company.tech_stack else '',
                    'key_services': ', '.join(company.key_services) if company.key_services else '',
                    'pain_points': ', '.join(company.pain_points) if company.pain_points else '',
                    'target_market': company.target_market or '',
                    'ai_summary': company.ai_summary or '',
                    'has_chat_widget': company.has_chat_widget,
                    'has_forms': company.has_forms,
                    'scrape_status': company.scrape_status,
                    'created_at': company.created_at.isoformat()
                })
        
        # Also save sector summary
        sector_output_path = output_path.replace('.csv', '_sectors.json')
        with open(sector_output_path, 'w', encoding='utf-8') as file:
            sector_data = []
            for sector in sectors:
                sector_data.append({
                    'sector_name': sector.name,
                    'company_count': len(sector.companies),
                    'companies': sector.companies,
                    'common_pain_points': sector.common_pain_points,
                    'common_technologies': sector.common_technologies,
                    'average_company_size': sector.average_company_size
                })
            
            json.dump(sector_data, file, indent=2)
        
        logger.info(f"Results saved to {output_path} and {sector_output_path}")
    
    def analyze_company_similarity(self, company_name: str, top_k: int = 5) -> Dict[str, Any]:
        """Analyze similarity for a company and return insights"""
        try:
            # Find company in database
            company = self.pinecone_client.find_company_by_name(company_name)
            if not company:
                return {
                    "error": f"Company '{company_name}' not found in database",
                    "suggestion": "Try processing the company first"
                }
            
            # Get similarity insights
            insights = self.pinecone_client.get_similarity_insights(company.id)
            return insights
            
        except Exception as e:
            logger.error(f"Similarity analysis failed for {company_name}: {e}")
            return {"error": str(e)}
    
    def find_companies_like(self, company_name: str, 
                           filters: Dict[str, str] = None,
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """Find companies similar to the given company with optional filters"""
        try:
            # Find target company
            company = self.pinecone_client.find_company_by_name(company_name)
            if not company:
                return []
            
            # Apply filters
            stage_filter = filters.get('stage') if filters else None
            tech_filter = filters.get('tech_level') if filters else None
            industry_filter = filters.get('industry') if filters else None
            
            # Find similar companies
            similar_companies = self.pinecone_client.find_similar_companies_enhanced(
                company.id,
                top_k=top_k,
                stage_filter=stage_filter,
                tech_filter=tech_filter,
                industry_filter=industry_filter
            )
            
            return similar_companies
            
        except Exception as e:
            logger.error(f"Find companies like {company_name} failed: {e}")
            return []
    
    def get_similarity_report(self, company_name: str) -> str:
        """Generate a detailed similarity report for sales team"""
        try:
            insights = self.analyze_company_similarity(company_name)
            
            if "error" in insights:
                return f"Error: {insights['error']}"
            
            # Generate report
            target = insights["target_company"]
            similar = insights.get("similar_companies", [])
            recommendations = insights.get("sales_recommendations", [])
            
            report = f"""
SIMILARITY ANALYSIS REPORT
==========================

Target Company: {target['name']}
Company Stage: {target.get('stage', 'Unknown')}
Tech Level: {target.get('tech_level', 'Unknown')}
Industry: {target.get('industry', 'Unknown')}

SIMILAR COMPANIES ({len(similar)} found):
"""
            
            for i, comp in enumerate(similar[:5], 1):
                report += f"""
{i}. {comp['company_name']} (Similarity: {comp['similarity_score']:.2f})
   - {comp['explanation']}
   - Stage: {comp['metadata'].get('company_stage', 'Unknown')}
   - Tech: {comp['metadata'].get('tech_sophistication', 'Unknown')}
"""
            
            if recommendations:
                report += f"""

SALES RECOMMENDATIONS:
"""
                for rec in recommendations:
                    report += f"• {rec}\n"
            
            return report
            
        except Exception as e:
            return f"Error generating report: {e}"


# CLI interface
def main():
    """Main function for CLI usage"""
    import argparse
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Theodore Company Intelligence Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Original survey processing commands
    survey_parser = subparsers.add_parser('process-survey', help='Process survey CSV')
    survey_parser.add_argument('--input-csv', required=True, help='Input CSV file with survey data')
    survey_parser.add_argument('--output-csv', required=True, help='Output CSV file for results')
    
    single_parser = subparsers.add_parser('process-single', help='Process single company')
    single_parser.add_argument('--company', required=True, help='Company (name:website)')
    
    # NEW: Similarity discovery commands
    discover_parser = subparsers.add_parser('discover-similar', help='Discover similar companies')
    discover_parser.add_argument('company_name', help='Company name to find similarities for')
    discover_parser.add_argument('--limit', type=int, default=5, help='Maximum similar companies to find')
    discover_parser.add_argument('--output', help='Save results to JSON file')
    
    batch_discover_parser = subparsers.add_parser('batch-discover', help='Batch discover similarities')
    batch_discover_parser.add_argument('--input-csv', required=True, help='CSV with company_name,company_id columns')
    batch_discover_parser.add_argument('--output-csv', required=True, help='Output CSV with similarities')
    batch_discover_parser.add_argument('--limit', type=int, default=3, help='Similar companies per company')
    
    query_parser = subparsers.add_parser('query-similar', help='Query existing similarities')
    query_parser.add_argument('company_name', help='Company name to query')
    query_parser.add_argument('--limit', type=int, default=10, help='Maximum results to show')
    query_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize pipeline
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Execute commands
    if args.command == 'process-survey':
        job = pipeline.process_survey_csv(args.input_csv, args.output_csv)
        print(f"Job completed: {job.status}")
        print(f"Processed: {job.processed_companies}/{job.total_companies}")
        print(f"Sectors discovered: {job.sectors_discovered}")
        
    elif args.command == 'process-single':
        # Split on first colon only to handle URLs with colons
        parts = args.company.split(':', 1)
        if len(parts) != 2:
            print("Error: --company format should be 'name:website'")
            return
        name, website = parts
        result = pipeline.process_single_company(name.strip(), website.strip())
        print(f"Processed {result.name}: {result.scrape_status}")
        if result.ai_summary:
            print(f"Summary: {result.ai_summary}")
            
    elif args.command == 'discover-similar':
        asyncio.run(discover_similar_command(pipeline, args))
        
    elif args.command == 'batch-discover':
        asyncio.run(batch_discover_command(pipeline, args))
        
    elif args.command == 'query-similar':
        asyncio.run(query_similar_command(pipeline, args))


async def discover_similar_command(pipeline: TheodoreIntelligencePipeline, args):
    """CLI command to discover similar companies"""
    print(f"🔍 Discovering companies similar to: {args.company_name}")
    print("=" * 50)
    
    try:
        # Find company in database
        company_data = await find_company_by_name(pipeline, args.company_name)
        if not company_data:
            print(f"❌ Company '{args.company_name}' not found in database")
            print("💡 Try processing the company first with: process-single --company 'name:website'")
            return
        
        # Discover similar companies
        similarities = await pipeline.similarity_pipeline.discover_and_validate_similar_companies(
            company_data.id, 
            limit=args.limit
        )
        
        if not similarities:
            print(f"🤷 No similar companies found for {args.company_name}")
            return
        
        # Display results
        print(f"✅ Found {len(similarities)} similar companies:")
        print()
        
        for i, sim in enumerate(similarities, 1):
            print(f"{i}. {sim.similar_company_name}")
            print(f"   Similarity Score: {sim.similarity_score:.2f}")
            print(f"   Confidence: {sim.confidence:.2f}")
            print(f"   Relationship: {sim.relationship_type}")
            if sim.reasoning:
                print(f"   Reasoning: {'; '.join(sim.reasoning)}")
            print()
        
        # Save to file if requested
        if args.output:
            save_similarities_to_json(similarities, args.output)
            print(f"💾 Results saved to {args.output}")
            
    except Exception as e:
        print(f"❌ Error discovering similarities: {e}")
        logger.error(f"Discovery error: {e}")


async def batch_discover_command(pipeline: TheodoreIntelligencePipeline, args):
    """CLI command to batch discover similarities"""
    print(f"🔄 Batch discovering similarities from: {args.input_csv}")
    print("=" * 50)
    
    try:
        # Read input CSV
        company_data = []
        with open(args.input_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'company_name' in row and 'company_id' in row:
                    company_data.append({
                        'name': row['company_name'].strip(),
                        'id': row['company_id'].strip()
                    })
        
        if not company_data:
            print(f"❌ No valid company data found in {args.input_csv}")
            print("💡 CSV should have columns: company_name, company_id")
            return
        
        print(f"📋 Processing {len(company_data)} companies...")
        
        # Process companies
        company_ids = [comp['id'] for comp in company_data]
        results = await pipeline.similarity_pipeline.batch_discover_similarities(
            company_ids,
            limit_per_company=args.limit
        )
        
        # Write results to CSV
        with open(args.output_csv, 'w', newline='') as f:
            fieldnames = [
                'original_company_name', 'similar_company_name', 
                'similarity_score', 'confidence', 'relationship_type',
                'discovery_method', 'reasoning'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            total_similarities = 0
            for company_id, similarities in results.items():
                # Find company name
                company_name = next((c['name'] for c in company_data if c['id'] == company_id), company_id)
                
                for sim in similarities:
                    writer.writerow({
                        'original_company_name': sim.original_company_name,
                        'similar_company_name': sim.similar_company_name,
                        'similarity_score': sim.similarity_score,
                        'confidence': sim.confidence,
                        'relationship_type': sim.relationship_type,
                        'discovery_method': sim.discovery_method,
                        'reasoning': '; '.join(sim.reasoning) if sim.reasoning else ''
                    })
                    total_similarities += 1
        
        print(f"✅ Batch processing complete!")
        print(f"📊 Found {total_similarities} total similarities")
        print(f"💾 Results saved to {args.output_csv}")
        
    except Exception as e:
        print(f"❌ Error in batch discovery: {e}")
        logger.error(f"Batch discovery error: {e}")


async def query_similar_command(pipeline: TheodoreIntelligencePipeline, args):
    """CLI command to query existing similarities"""
    print(f"🔎 Querying similarities for: {args.company_name}")
    print("=" * 40)
    
    try:
        # Find company in database
        company_data = await find_company_by_name(pipeline, args.company_name)
        if not company_data:
            print(f"❌ Company '{args.company_name}' not found in database")
            return
        
        # Query existing similarities
        similarities = await pipeline.similarity_pipeline.query_similar_companies(
            company_data.id,
            limit=args.limit
        )
        
        if not similarities:
            print(f"🤷 No existing similarities found for {args.company_name}")
            print(f"💡 Try running: discover-similar '{args.company_name}' to find new similarities")
            return
        
        # Display results
        if args.format == 'json':
            # JSON output
            results = []
            for sim in similarities:
                results.append({
                    'similar_company_name': sim.similar_company_name,
                    'similarity_score': sim.similarity_score,
                    'confidence': sim.confidence,
                    'relationship_type': sim.relationship_type,
                    'discovered_at': sim.discovered_at.isoformat()
                })
            print(json.dumps(results, indent=2))
        else:
            # Table output
            print(f"📊 Found {len(similarities)} existing similarities:")
            print()
            print(f"{'#':<3} {'Company Name':<30} {'Score':<8} {'Type':<12} {'Discovered':<12}")
            print("-" * 70)
            
            for i, sim in enumerate(similarities, 1):
                discovered_date = sim.discovered_at.strftime("%Y-%m-%d") if sim.discovered_at else "Unknown"
                print(f"{i:<3} {sim.similar_company_name[:29]:<30} {sim.similarity_score:<8.2f} {sim.relationship_type[:11]:<12} {discovered_date:<12}")
        
    except Exception as e:
        print(f"❌ Error querying similarities: {e}")
        logger.error(f"Query error: {e}")


async def find_company_by_name(pipeline: TheodoreIntelligencePipeline, company_name: str) -> Optional[CompanyData]:
    """Helper function to find company by name in Pinecone"""
    try:
        logger.info(f"Searching for company: {company_name}")
        
        # Use the pinecone client to search by name
        company_data = pipeline.pinecone_client.find_company_by_name(company_name)
        
        if company_data:
            logger.info(f"Found company: {company_data.name}")
            return company_data
        else:
            logger.warning(f"Company not found: {company_name}")
            return None
        
    except Exception as e:
        logger.error(f"Error finding company by name: {e}")
        return None


def save_similarities_to_json(similarities: List[CompanySimilarity], output_path: str):
    """Save similarities to JSON file"""
    results = []
    for sim in similarities:
        results.append({
            'original_company_name': sim.original_company_name,
            'similar_company_name': sim.similar_company_name,
            'similarity_score': sim.similarity_score,
            'confidence': sim.confidence,
            'relationship_type': sim.relationship_type,
            'discovery_method': sim.discovery_method,
            'validation_methods': sim.validation_methods,
            'reasoning': sim.reasoning,
            'discovered_at': sim.discovered_at.isoformat()
        })
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()