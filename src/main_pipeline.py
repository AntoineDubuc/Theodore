"""
Main processing pipeline for Theodore company intelligence system
"""

import os
import csv
import logging
from typing import List, Dict, Any
from datetime import datetime
import json

from src.models import (
    CompanyData, SurveyResponse, ProcessingJob, 
    CompanyIntelligenceConfig, SectorCluster
)
from src.crawl4ai_scraper import CompanyWebScraper
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient
from src.clustering import SectorClusteringEngine

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
        self.scraper = CompanyWebScraper(config)
        self.bedrock_client = BedrockClient(config)
        self.pinecone_client = PineconeClient(
            config, pinecone_api_key, pinecone_environment, pinecone_index
        )
        self.clustering_engine = SectorClusteringEngine(config, self.pinecone_client)
        
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
    
    def process_single_company(self, company_name: str, website: str) -> CompanyData:
        """Process a single company for testing/demo purposes"""
        logger.info(f"Processing single company: {company_name}")
        
        # Create company data object
        company = CompanyData(name=company_name, website=website)
        
        # Scrape website
        company = self.scraper.scrape_company(company)
        
        if company.scrape_status != "success":
            logger.warning(f"Scraping failed for {company_name}: {company.scrape_error}")
            return company
        
        # Analyze with Bedrock
        analysis_result = self.bedrock_client.analyze_company_content(company)
        self._apply_analysis_to_company(company, analysis_result)
        
        # Generate embedding
        embedding_text = self._prepare_embedding_text(company)
        company.embedding = self.bedrock_client.generate_embedding(embedding_text)
        
        # Store in Pinecone
        if company.embedding:
            self.pinecone_client.upsert_company(company)
        
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
    
    def _convert_survey_to_companies(self, survey_responses: List[SurveyResponse]) -> List[CompanyData]:
        """Convert survey responses to CompanyData objects"""
        companies = []
        
        for response in survey_responses:
            company = CompanyData(
                name=response.company_name,
                website=response.website or f"https://{response.company_name.lower().replace(' ', '')}.com",
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
        
        # Update company data with analysis results
        company.industry = analysis_result.get("industry", company.industry)
        company.business_model = analysis_result.get("business_model", company.business_model)
        company.company_size = analysis_result.get("company_size", company.company_size)
        company.target_market = analysis_result.get("target_market", company.target_market)
        company.ai_summary = analysis_result.get("ai_summary", "")
        
        # Merge lists (avoid duplicates)
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
    
    def _prepare_embedding_text(self, company: CompanyData) -> str:
        """Prepare text for embedding generation"""
        text_parts = [
            f"Company: {company.name}",
            f"Industry: {company.industry or 'unknown'}",
            f"Business Model: {company.business_model or 'unknown'}",
        ]
        
        if company.key_services:
            text_parts.append(f"Services: {', '.join(company.key_services)}")
        
        if company.tech_stack:
            text_parts.append(f"Technologies: {', '.join(company.tech_stack)}")
        
        if company.pain_points:
            text_parts.append(f"Challenges: {', '.join(company.pain_points)}")
        
        if company.ai_summary:
            text_parts.append(f"Summary: {company.ai_summary}")
        
        return " | ".join(text_parts)
    
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


# CLI interface for testing
def main():
    """Main function for CLI usage"""
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Theodore Company Intelligence Pipeline')
    parser.add_argument('--input-csv', required=True, help='Input CSV file with survey data')
    parser.add_argument('--output-csv', required=True, help='Output CSV file for results')
    parser.add_argument('--single-company', help='Process single company (name:website)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize pipeline
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    if args.single_company:
        # Process single company
        name, website = args.single_company.split(':')
        result = pipeline.process_single_company(name.strip(), website.strip())
        print(f"Processed {result.name}: {result.scrape_status}")
        if result.ai_summary:
            print(f"Summary: {result.ai_summary}")
    else:
        # Process CSV
        job = pipeline.process_survey_csv(args.input_csv, args.output_csv)
        print(f"Job completed: {job.status}")
        print(f"Processed: {job.processed_companies}/{job.total_companies}")
        print(f"Sectors discovered: {job.sectors_discovered}")


if __name__ == "__main__":
    main()