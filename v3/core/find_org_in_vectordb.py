"""
Organization Finder for Pinecone Vector Database - V3 CLI Integration
====================================================================

Enhanced module to find and retrieve complete organization data from Pinecone.
Adapted from the proven V2 antoine code with 51-field retrieval capability.

This module provides:
- Complete organization data retrieval (all 51 available fields)
- Search by company name (exact and partial matching)  
- Similarity search for discovery functionality
- Full error handling and logging
- Direct Pinecone integration using existing credentials

Usage:
    from find_org_in_vectordb import OrganizationFinder
    
    finder = OrganizationFinder()
    company = finder.find_by_name("CloudGeometry")
    
    if company:
        print(f"Found: {company.name}")
        print(f"Industry: {company.industry}")
        # ... all 51 fields available
    else:
        print("Company not found")
"""

import os
import sys
import logging
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone
from datetime import datetime

# Add the parent directory to the path to import from src
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from src.models import CompanyData
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import CompanyData model: {e}")
    MODELS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrganizationFinder:
    """
    Enhanced Pinecone client for V3 CLI with complete organization data retrieval.
    
    Adapted from proven V2 antoine code to provide comprehensive company intelligence.
    Retrieves all 51 available Pinecone fields including:
    - Core business intelligence (descriptions, value propositions)
    - Technology information (tech stacks, services, pain points)
    - Contact information (email, phone, social media)
    - Processing metadata (costs, tokens, URLs, timestamps)
    - Classification data (SaaS categories, confidence scores)
    """
    
    def __init__(self, env_file_path: Optional[str] = None):
        """
        Initialize the OrganizationFinder with Pinecone configuration.
        
        Args:
            env_file_path: Optional path to .env file. If None, uses root .env
        """
        # Load environment variables from root .env file
        if env_file_path is None:
            # Default to root .env file - check multiple possible locations
            current_dir = os.path.dirname(__file__)
            possible_paths = [
                os.path.join(current_dir, '..', '..', '.env'),  # v3/core -> root
                os.path.join(current_dir, '..', '.env'),         # v3/core -> v3
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'),  # 3 levels up
                '.env'  # Current working directory
            ]
            
            env_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    env_file_path = path
                    break
            
            if not env_file_path:
                raise ValueError("Could not find .env file in any expected locations")
        
        load_dotenv(env_file_path)
        
        # Get Pinecone configuration from environment
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        self.environment = os.getenv('PINECONE_ENVIRONMENT', 'Theodore')
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self.dimension = 1536  # Standard dimension used in Theodore
        
        # Initialize index connection
        self._initialize_index()
        
        logger.info(f"OrganizationFinder initialized with index: {self.index_name}")
    
    def _initialize_index(self):
        """Initialize connection to existing Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.error(f"Pinecone index '{self.index_name}' not found")
                logger.info(f"Available indexes: {existing_indexes}")
                raise ValueError(f"Index '{self.index_name}' does not exist")
            
            # Connect to existing index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to existing Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            raise
    
    def find_by_name(self, company_name: str) -> Optional[CompanyData]:
        """
        Find a company by name using exact and partial matching.
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            CompanyData object with all fields if found, None otherwise
        """
        if not MODELS_AVAILABLE:
            logger.error("CompanyData model not available. Cannot return structured data.")
            return None
            
        try:
            logger.info(f"Searching for company: {company_name}")
            
            # First try exact name match
            companies = self._find_companies_by_filters(
                filters={"company_name": {"$eq": company_name}},
                top_k=10
            )
            
            if companies:
                logger.info(f"Found exact match for: {company_name}")
                match_data = companies[0]
                return self._build_complete_company_data(match_data["company_id"], match_data["metadata"])
            
            # Try partial matching if exact fails
            logger.info(f"No exact match found, trying partial matching for: {company_name}")
            all_companies = self._find_companies_by_filters(filters={}, top_k=100)
            
            search_name = company_name.lower()
            for company_data in all_companies:
                stored_name = company_data["metadata"].get('company_name', '').lower()
                if search_name in stored_name or stored_name in search_name:
                    logger.info(f"Found partial match: {stored_name} for search: {company_name}")
                    return self._build_complete_company_data(company_data["company_id"], company_data["metadata"])
            
            logger.info(f"No matches found for: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find company by name '{company_name}': {e}")
            return None
    
    def get_company_data(self, company_id: str) -> Optional[CompanyData]:
        """
        Retrieve complete company data by ID.
        
        Args:
            company_id: Unique identifier for the company
            
        Returns:
            CompanyData object with all fields if found, None otherwise
        """
        if not MODELS_AVAILABLE:
            logger.error("CompanyData model not available. Cannot return structured data.")
            return None
            
        try:
            logger.info(f"Fetching company data for ID: {company_id}")
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found in Pinecone")
                return None
            
            vector_data = fetch_response.vectors[company_id]
            metadata = vector_data.metadata
            
            # Build complete CompanyData object from metadata
            company = self._build_complete_company_data(company_id, metadata, vector_data.values)
            
            logger.info(f"Successfully retrieved data for: {company.name}")
            return company
            
        except Exception as e:
            logger.error(f"Failed to get company data for ID '{company_id}': {e}")
            return None
    
    def search_similar_companies(self, query: str, limit: int = 10, industry_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar companies using text query and optional filters.
        
        Args:
            query: Search query (company name, description, or industry term)
            limit: Maximum number of results to return
            industry_filter: Optional industry filter
            
        Returns:
            List of company dictionaries with similarity scores
        """
        try:
            logger.info(f"Searching for similar companies: {query}")
            
            # Build filter
            filters = {}
            if industry_filter:
                filters["industry"] = {"$eq": industry_filter}
            
            # For text-based similarity, we'll search by partial name matching
            # and industry matching. In a full implementation, this would use
            # text embeddings for semantic similarity
            companies = self._find_companies_by_filters(filters=filters, top_k=limit * 3)
            
            # Filter by query relevance
            query_lower = query.lower()
            relevant_companies = []
            
            for company_data in companies:
                metadata = company_data["metadata"]
                company_name = metadata.get('company_name', '').lower()
                industry = metadata.get('industry', '').lower()
                description = metadata.get('company_description', '').lower()
                
                # Calculate relevance score
                relevance_score = 0.0
                
                if query_lower in company_name:
                    relevance_score += 1.0
                elif any(word in company_name for word in query_lower.split()):
                    relevance_score += 0.7
                
                if query_lower in industry:
                    relevance_score += 0.8
                elif any(word in industry for word in query_lower.split()):
                    relevance_score += 0.5
                
                if query_lower in description:
                    relevance_score += 0.6
                elif any(word in description for word in query_lower.split()):
                    relevance_score += 0.3
                
                if relevance_score > 0:
                    relevant_companies.append({
                        'name': metadata.get('company_name', 'Unknown'),
                        'industry': metadata.get('industry', 'Unknown'),
                        'description': metadata.get('company_description', 'No description'),
                        'website': metadata.get('website', ''),
                        'similarity_score': relevance_score,
                        'company_id': company_data["company_id"]
                    })
            
            # Sort by relevance and return top results
            relevant_companies.sort(key=lambda x: x['similarity_score'], reverse=True)
            return relevant_companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search similar companies for '{query}': {e}")
            return []
    
    def _find_companies_by_filters(self, filters: Dict[str, Any], top_k: int = 50) -> List[Dict[str, Any]]:
        """Find companies using metadata filters"""
        try:
            # Use minimal vector query with filters
            query_response = self.index.query(
                vector=[0.0] * self.dimension,  # Minimal dummy vector
                top_k=top_k,
                filter=filters,
                include_metadata=True,
                include_values=False
            )
            
            companies = []
            for match in query_response.matches:
                companies.append({
                    "company_id": match.id,
                    "metadata": match.metadata,
                    "score": match.score
                })
            
            return companies
            
        except Exception as e:
            logger.error(f"Failed to find companies with filters {filters}: {e}")
            return []
    
    def _build_complete_company_data(self, company_id: str, metadata: Dict[str, Any], values: Optional[List[float]] = None) -> CompanyData:
        """
        Build complete CompanyData object with ALL fields from metadata.
        This is the enhanced method that restores all 51 available fields.
        
        Enhanced to retrieve:
        - AI summaries and LLM cost tracking
        - Scraped URLs and processing metadata  
        - Classification timestamps
        - Proper data type conversions for founding year and job counts
        """
        # Start with basic CompanyData object
        company = CompanyData(
            id=company_id,
            name=metadata.get('company_name', ''),
            website=metadata.get('website', ''),
            industry=metadata.get('industry', ''),
            business_model=metadata.get('business_model', ''),
            target_market=metadata.get('target_market', ''),
            company_size=metadata.get('company_size', ''),
            embedding=list(values) if values else None
        )
        
        # Restore all enhanced fields from metadata
        company.raw_content = metadata.get('raw_content', '')
        company.founding_year = metadata.get('founding_year')
        company.location = metadata.get('location', '')
        company.employee_count_range = metadata.get('employee_count_range', '')
        company.company_description = metadata.get('company_description', '')
        company.value_proposition = metadata.get('value_proposition', '')
        company.funding_status = metadata.get('funding_status', '')
        company.company_culture = metadata.get('company_culture', '')
        
        # Convert comma-separated strings back to lists
        def split_safe(value):
            if not value or not isinstance(value, str):
                return []
            return [item.strip() for item in value.split(',') if item.strip()]
        
        company.leadership_team = split_safe(metadata.get('leadership_team', ''))
        company.key_services = split_safe(metadata.get('key_services', ''))
        company.tech_stack = split_safe(metadata.get('tech_stack', ''))
        company.competitive_advantages = split_safe(metadata.get('competitive_advantages', ''))
        company.products_services_offered = split_safe(metadata.get('products_services_offered', ''))
        company.partnerships = split_safe(metadata.get('partnerships', ''))
        company.awards = split_safe(metadata.get('awards', ''))
        company.recent_news_events = split_safe(metadata.get('recent_news_events', ''))
        company.pain_points = split_safe(metadata.get('pain_points', ''))
        
        # Restore structured data fields (convert from JSON strings)
        contact_info_str = metadata.get('contact_info', '')
        social_media_str = metadata.get('social_media', '')
        
        try:
            company.contact_info = json.loads(contact_info_str) if contact_info_str else {}
        except:
            company.contact_info = {}
            
        try:
            company.social_media = json.loads(social_media_str) if social_media_str else {}
        except:
            company.social_media = {}
        
        # Restore processing metadata
        company.pages_crawled = metadata.get('pages_crawled', [])
        company.crawl_duration = metadata.get('crawl_duration', 0)
        company.scrape_status = metadata.get('scrape_status', 'unknown')
        company.ai_summary = metadata.get('ai_summary', '')
        
        # ENHANCED: Add scraped URLs (convert from comma-separated string)
        scraped_urls_str = metadata.get('scraped_urls', '')
        company.scraped_urls = split_safe(scraped_urls_str)
        
        # ENHANCED: Add LLM token usage and cost tracking
        company.total_input_tokens = int(metadata.get('total_input_tokens', 0))
        company.total_output_tokens = int(metadata.get('total_output_tokens', 0))
        company.total_cost_usd = float(metadata.get('total_cost_usd', 0.0))
        
        # Restore similarity dimensions
        company.company_stage = metadata.get('company_stage', '')
        company.tech_sophistication = metadata.get('tech_sophistication', '')
        
        # ENHANCED: Fix data type for job listings count (stored as float in Pinecone)
        company.job_listings_count = int(metadata.get('job_listings_count', 0)) if metadata.get('job_listings_count') else 0
        company.job_listings = metadata.get('job_listings', '')
        company.job_listings_details = split_safe(metadata.get('job_listings_details', ''))
        
        # Restore SaaS classification
        company.saas_classification = metadata.get('saas_classification', '')
        company.classification_confidence = metadata.get('classification_confidence')
        company.classification_justification = metadata.get('classification_justification', '')
        company.is_saas = metadata.get('is_saas')
        
        # ENHANCED: Fix data type for founding year (stored as float in Pinecone)
        if metadata.get('founding_year'):
            try:
                company.founding_year = int(metadata.get('founding_year'))
            except (ValueError, TypeError):
                company.founding_year = None
        
        # Handle timestamp fields
        if metadata.get('last_updated'):
            try:
                company.last_updated = datetime.fromisoformat(metadata['last_updated'])
            except:
                pass
        
        # ENHANCED: Add classification timestamp (identified in Pinecone)
        if metadata.get('classification_timestamp'):
            try:
                company.classification_timestamp = datetime.fromisoformat(metadata['classification_timestamp'])
            except:
                pass
        
        # Additional fields that might be stored
        company.business_model_framework = metadata.get('business_model_framework', '')
        company.has_chat_widget = metadata.get('has_chat_widget', False)
        company.has_forms = metadata.get('has_forms', False)
        company.geographic_scope = metadata.get('geographic_scope', '')
        company.sales_complexity = metadata.get('sales_complexity', '')
        
        # Confidence scores
        company.stage_confidence = metadata.get('stage_confidence')
        company.tech_confidence = metadata.get('tech_confidence')
        company.industry_confidence = metadata.get('industry_confidence')
        
        return company
    
    def list_all_companies(self, limit: int = 100) -> List[str]:
        """
        Get a list of all company names in the database.
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of company names
        """
        try:
            companies = self._find_companies_by_filters(filters={}, top_k=limit)
            return [comp["metadata"].get('company_name', 'Unknown') for comp in companies]
        except Exception as e:
            logger.error(f"Failed to list companies: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about the database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_name': self.index_name,
                'environment': self.environment
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# V3 CLI specific functions
def search_similar_companies(query: str, limit: int = 10, industry_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function for V3 CLI discover command.
    
    Args:
        query: Search query (company name, description, or industry term)
        limit: Maximum number of results to return
        industry_filter: Optional industry filter
        
    Returns:
        List of company dictionaries with similarity scores
    """
    finder = OrganizationFinder()
    return finder.search_similar_companies(query, limit, industry_filter)


# Convenience functions for easy usage
def find_organization(company_name: str) -> Optional[CompanyData]:
    """
    Convenience function to find an organization by name.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        CompanyData object if found, None otherwise
    """
    finder = OrganizationFinder()
    return finder.find_by_name(company_name)


def get_organization_by_id(company_id: str) -> Optional[CompanyData]:
    """
    Convenience function to get organization data by ID.
    
    Args:
        company_id: Unique identifier for the company
        
    Returns:
        CompanyData object if found, None otherwise
    """
    finder = OrganizationFinder()
    return finder.get_company_data(company_id)


if __name__ == "__main__":
    """Test the OrganizationFinder with a sample search"""
    print("Testing V3 OrganizationFinder...")
    
    try:
        finder = OrganizationFinder()
        print(f"Database stats: {finder.get_database_stats()}")
        
        # Test search
        test_company = "Cloud Geometry"
        print(f"\nSearching for: {test_company}")
        
        company = finder.find_by_name(test_company)
        
        if company:
            print(f" Found: {company.name}")
            print(f"Website: {company.website}")
            print(f"Industry: {company.industry}")
            print(f"Business Model: {company.business_model}")
            print(f"Description: {company.company_description[:200]}..." if company.company_description else "No description")
            print(f"Value Proposition: {company.value_proposition[:200]}..." if company.value_proposition else "No value proposition")
            print(f"Location: {company.location}")
            print(f"Tech Stack: {company.tech_stack}")
        else:
            print(f"L Company '{test_company}' not found")
            
        # Test similarity search
        print(f"\nTesting similarity search for 'cloud consulting'...")
        similar = finder.search_similar_companies("cloud consulting", limit=3)
        print(f"Found {len(similar)} similar companies:")
        for i, comp in enumerate(similar, 1):
            print(f"  {i}. {comp['name']} (score: {comp['similarity_score']:.2f})")
            
    except Exception as e:
        print(f"L Error testing OrganizationFinder: {e}")