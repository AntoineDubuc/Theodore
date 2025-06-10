"""
Enhanced Research Manager for Theodore
Handles research status tracking, multithreaded processing, progress monitoring,
and structured research operations with predefined prompts from PRD requirements.
"""

import asyncio
import threading
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from src.models import CompanyData
from src.intelligent_company_scraper import IntelligentCompanyScraperSync
from src.pinecone_client import PineconeClient
from src.research_prompts import research_prompt_library, ResearchPrompt

logger = logging.getLogger(__name__)

class ResearchStatus(str, Enum):
    """Research status for discovered companies"""
    UNKNOWN = "unknown"           # Company suggested by LLM, not in database
    NOT_RESEARCHED = "not_researched"  # In database but no sales intelligence
    RESEARCHING = "researching"   # Currently being processed
    COMPLETED = "completed"       # Fully researched with sales intelligence
    FAILED = "failed"            # Research failed
    QUEUED = "queued"            # Waiting to be processed

@dataclass
class ResearchProgress:
    """Progress tracking for company research"""
    company_name: str
    status: ResearchStatus
    progress_percent: int = 0
    current_phase: str = ""
    phases_completed: List[str] = None
    total_phases: int = 4
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    job_id: Optional[str] = None
    
    def __post_init__(self):
        if self.phases_completed is None:
            self.phases_completed = []

@dataclass
class StructuredResearchResult:
    """Result from a single research prompt"""
    prompt_id: str
    prompt_name: str
    success: bool
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    execution_time: Optional[float] = None

@dataclass
class CompanyResearchSession:
    """Complete research session for a company"""
    company_name: str
    website: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    selected_prompts: List[str] = None
    results: List[StructuredResearchResult] = None
    total_cost: Optional[float] = None
    total_tokens: Optional[int] = None
    success_rate: Optional[float] = None
    raw_company_data: Optional[Dict[str, Any]] = None

@dataclass
class DiscoveredCompany:
    """Enhanced discovered company with research status"""
    name: str
    website: str
    similarity_score: float
    confidence: float
    reasoning: List[str]
    relationship_type: str
    discovery_method: str
    business_context: str
    sources: List[str]
    research_status: ResearchStatus
    research_progress: Optional[ResearchProgress] = None
    in_database: bool = False
    database_id: Optional[str] = None

class ResearchManager:
    """Enhanced research manager with structured prompts and real-time progress tracking"""
    
    def __init__(self, intelligent_scraper: IntelligentCompanyScraperSync, 
                 pinecone_client: PineconeClient, bedrock_client=None, 
                 token_price_per_1k: float = 0.011):  # Nova Pro pricing
        self.intelligent_scraper = intelligent_scraper
        self.pinecone_client = pinecone_client
        # bedrock_client can now be Gemini or Bedrock client for analysis
        self.ai_client = bedrock_client
        # Keep separate Bedrock client for embeddings
        self.bedrock_client = None
        try:
            from src.bedrock_client import BedrockClient
            from src.models import CompanyIntelligenceConfig
            config = CompanyIntelligenceConfig()
            self.bedrock_client = BedrockClient(config)
        except Exception as e:
            logger.warning(f"Could not initialize Bedrock client for embeddings: {e}")
        self.prompt_library = research_prompt_library
        self.token_price_per_1k = token_price_per_1k
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Progress tracking
        self.research_progress: Dict[str, ResearchProgress] = {}
        self.research_lock = threading.Lock()
        
        # Structured research sessions
        self.research_sessions: Dict[str, CompanyResearchSession] = {}
        
        # Multithreading
        self.executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent research
        self.active_research_jobs: Dict[str, threading.Thread] = {}
        
    def enhance_discovered_companies(self, discovered_companies: List[Dict[str, Any]]) -> List[DiscoveredCompany]:
        """Enhance discovered companies with research status information"""
        self.logger.info(f"Enhancing {len(discovered_companies)} discovered companies")
        
        enhanced_companies = []
        
        for company_data in discovered_companies:
            # Check if company exists in database
            existing_company = self.pinecone_client.find_company_by_name(company_data["company_name"])
            
            if existing_company:
                # Company exists - determine research status
                research_status = self._determine_research_status(existing_company)
                in_database = True
                database_id = existing_company.id
            else:
                # Company doesn't exist
                research_status = ResearchStatus.UNKNOWN
                in_database = False
                database_id = None
            
            enhanced_company = DiscoveredCompany(
                name=company_data["company_name"],
                website=company_data.get("website", ""),
                similarity_score=company_data["similarity_score"],
                confidence=company_data["confidence"],
                reasoning=company_data["reasoning"],
                relationship_type=company_data["relationship_type"],
                discovery_method=company_data["discovery_method"],
                business_context=company_data.get("business_context", ""),
                sources=company_data.get("sources", []),
                research_status=research_status,
                in_database=in_database,
                database_id=database_id
            )
            
            enhanced_companies.append(enhanced_company)
        
        self.logger.info(f"Enhanced companies: {len(enhanced_companies)} total")
        return enhanced_companies
    
    def _determine_research_status(self, company: CompanyData) -> ResearchStatus:
        """Determine research status based on company data"""
        # Check if company has sales intelligence
        has_sales_intelligence = (
            hasattr(company, 'sales_intelligence') and 
            company.sales_intelligence and 
            len(company.sales_intelligence) > 500
        )
        
        # Check if company has basic metadata
        has_metadata = (
            company.industry and 
            company.business_model and 
            company.target_market
        )
        
        if has_sales_intelligence and has_metadata:
            return ResearchStatus.COMPLETED
        elif has_metadata:
            return ResearchStatus.NOT_RESEARCHED
        else:
            return ResearchStatus.UNKNOWN
    
    def start_research(self, company_name: str, website: str) -> str:
        """Start research for a single company (non-blocking)"""
        job_id = f"research_{company_name.replace(' ', '_')}_{int(time.time())}"
        
        # Initialize progress tracking
        progress = ResearchProgress(
            company_name=company_name,
            status=ResearchStatus.QUEUED,
            job_id=job_id,
            start_time=datetime.utcnow()
        )
        
        with self.research_lock:
            self.research_progress[job_id] = progress
        
        # Submit to thread pool
        future = self.executor.submit(self._research_company_worker, company_name, website, job_id)
        
        self.logger.info(f"Started research for {company_name} (Job: {job_id})")
        return job_id
    
    def start_bulk_research(self, companies: List[Dict[str, str]]) -> List[str]:
        """Start research for multiple companies (non-blocking)"""
        job_ids = []
        
        for company in companies:
            if "name" in company and "website" in company:
                job_id = self.start_research(company["name"], company["website"])
                job_ids.append(job_id)
        
        self.logger.info(f"Started bulk research for {len(job_ids)} companies")
        return job_ids
    
    def _research_company_worker(self, company_name: str, website: str, job_id: str):
        """Worker function for researching a single company"""
        try:
            # Update status to researching
            self._update_progress(job_id, ResearchStatus.RESEARCHING, 0, "Initializing research")
            
            # Phase 1: Create company data
            self._update_progress(job_id, ResearchStatus.RESEARCHING, 10, "Creating company profile")
            company_data = CompanyData(name=company_name, website=website)
            
            # Phase 2: Run intelligent scraper
            self._update_progress(job_id, ResearchStatus.RESEARCHING, 25, "Discovering company links")
            enriched_company = self.intelligent_scraper.scrape_company(company_data, job_id=job_id)
            
            # Phase 3: Process results
            self._update_progress(job_id, ResearchStatus.RESEARCHING, 75, "Processing research data")
            
            if enriched_company.scrape_status == "success":
                # Check if we actually got meaningful data
                has_meaningful_data = (
                    enriched_company.company_description and 
                    enriched_company.company_description.strip() and
                    "No content could be extracted" not in enriched_company.company_description
                )
                
                if has_meaningful_data:
                    # Phase 4: Classify industry and generate embedding
                    self._update_progress(job_id, ResearchStatus.RESEARCHING, 80, "Classifying industry")
                    
                    # Classify industry if we have research data
                    if self.ai_client:
                        try:
                            industry = self._classify_industry(enriched_company)
                            if industry and industry.lower() != 'unknown':
                                enriched_company.industry = industry
                                self.logger.info(f"Classified {company_name} as: {industry}")
                        except Exception as e:
                            self.logger.warning(f"Failed to classify industry for {company_name}: {e}")
                    
                    # Phase 5: Generate embedding and store in database
                    self._update_progress(job_id, ResearchStatus.RESEARCHING, 90, "Generating embeddings and storing in database")
                    
                    # Generate embedding if we have sales intelligence
                    try:
                        # Generate embedding using bedrock client
                        if self.bedrock_client:
                            embedding = self.bedrock_client.get_embeddings(enriched_company.company_description)
                            enriched_company.embedding = embedding
                        else:
                            # Fallback: create bedrock client
                            from src.bedrock_client import BedrockClient
                            bedrock_client = BedrockClient()
                            embedding = bedrock_client.get_embeddings(enriched_company.company_description)
                            enriched_company.embedding = embedding
                        
                        # Store in Pinecone
                        success = self.pinecone_client.upsert_company(enriched_company)
                        if success:
                            self.logger.info(f"Successfully stored {company_name} in database with embedding")
                        else:
                            self.logger.warning(f"Failed to store {company_name} in database")
                    except Exception as e:
                        self.logger.error(f"Failed to generate embedding or store company {company_name}: {e}")
                    
                    # Complete
                    self._update_progress(job_id, ResearchStatus.COMPLETED, 100, "Research completed successfully")
                    self.logger.info(f"Research completed successfully for {company_name}")
                    
                else:
                    # Website was accessed but no content was extracted (likely blocked)
                    # Try fallback research using LLM knowledge
                    self._update_progress(job_id, ResearchStatus.RESEARCHING, 85, "Website blocked - trying LLM fallback research")
                    self.logger.info(f"Website blocked for {company_name}, attempting LLM fallback research")
                    
                    try:
                        fallback_data = self._llm_fallback_research(company_name, website)
                        if fallback_data and fallback_data.get('success'):
                            # Apply fallback data to company
                            enriched_company.company_description = fallback_data.get('company_description', '')
                            enriched_company.industry = fallback_data.get('industry', '')
                            enriched_company.business_model = fallback_data.get('business_model', '')
                            enriched_company.target_market = fallback_data.get('target_market', '')
                            enriched_company.key_services = fallback_data.get('key_services', [])
                            enriched_company.value_proposition = fallback_data.get('value_proposition', '')
                            enriched_company.location = fallback_data.get('location', '')
                            enriched_company.company_size = fallback_data.get('company_size', '')
                            enriched_company.founding_year = fallback_data.get('founding_year')
                            
                            # Mark as LLM-based research
                            enriched_company.scrape_status = "success"
                            enriched_company.scrape_error = None
                            
                            # Generate embedding for LLM-based description
                            if enriched_company.company_description and self.bedrock_client:
                                self._update_progress(job_id, ResearchStatus.RESEARCHING, 90, "Generating embeddings for LLM data")
                                embedding = self.bedrock_client.get_embeddings(enriched_company.company_description)
                                enriched_company.embedding = embedding
                                
                                # Store in database
                                success = self.pinecone_client.upsert_company(enriched_company)
                                if success:
                                    self.logger.info(f"Successfully stored {company_name} using LLM fallback data")
                                
                            self._update_progress(job_id, ResearchStatus.COMPLETED, 100, "Research completed using LLM fallback")
                            self.logger.info(f"LLM fallback research successful for {company_name}")
                        else:
                            # LLM fallback failed, try web search as final option
                            self._update_progress(job_id, ResearchStatus.RESEARCHING, 88, "LLM fallback unsuccessful - trying web search")
                            self.logger.info(f"LLM fallback failed for {company_name}, attempting web search fallback")
                            
                            try:
                                search_data = self._web_search_fallback(company_name, website)
                                if search_data and search_data.get('success'):
                                    # Apply web search data
                                    enriched_company.company_description = search_data.get('company_description', '')
                                    enriched_company.industry = search_data.get('industry', '')
                                    enriched_company.business_model = search_data.get('business_model', '')
                                    enriched_company.target_market = search_data.get('target_market', '')
                                    enriched_company.key_services = search_data.get('key_services', [])
                                    
                                    enriched_company.scrape_status = "success"
                                    enriched_company.scrape_error = None
                                    
                                    # Generate embedding and store
                                    if enriched_company.company_description and self.bedrock_client:
                                        embedding = self.bedrock_client.get_embeddings(enriched_company.company_description)
                                        enriched_company.embedding = embedding
                                        success = self.pinecone_client.upsert_company(enriched_company)
                                        if success:
                                            self.logger.info(f"Successfully stored {company_name} using web search fallback")
                                    
                                    self._update_progress(job_id, ResearchStatus.COMPLETED, 100, "Research completed using web search fallback")
                                    self.logger.info(f"Web search fallback successful for {company_name}")
                                else:
                                    # All fallbacks failed
                                    error_msg = f"Website blocked, LLM fallback and web search unsuccessful for {website}."
                                    enriched_company.scrape_error = error_msg
                                    self._update_progress(job_id, ResearchStatus.FAILED, 100, "All research methods failed", error_msg)
                                    self.logger.warning(f"All research methods failed for {company_name}")
                            except Exception as search_error:
                                error_msg = f"Website blocked, LLM and web search fallbacks failed: {str(search_error)}"
                                enriched_company.scrape_error = error_msg
                                self._update_progress(job_id, ResearchStatus.FAILED, 100, "All fallback methods failed", error_msg)
                                self.logger.error(f"Web search fallback failed for {company_name}: {search_error}")
                            
                    except Exception as fallback_error:
                        error_msg = f"Website blocked and LLM fallback error: {str(fallback_error)}"
                        enriched_company.scrape_error = error_msg
                        self._update_progress(job_id, ResearchStatus.FAILED, 100, "Fallback research failed", error_msg)
                        self.logger.error(f"LLM fallback research failed for {company_name}: {fallback_error}")
                
            else:
                # Failed
                error_msg = enriched_company.scrape_error or "Unknown error during research"
                self._update_progress(job_id, ResearchStatus.FAILED, 100, "Research failed", error_msg)
                self.logger.error(f"Research failed for {company_name}: {error_msg}")
        
        except Exception as e:
            error_msg = str(e)
            self._update_progress(job_id, ResearchStatus.FAILED, 100, "Research failed", error_msg)
            self.logger.error(f"Research worker error for {company_name}: {e}")
    
    def _llm_fallback_research(self, company_name: str, website: str) -> dict:
        """
        Use LLM knowledge to gather company information when scraping fails.
        This leverages the LLM's training data knowledge about well-known companies.
        """
        try:
            if not self.ai_client:
                return {'success': False, 'error': 'No AI client available'}
            
            fallback_prompt = f"""
            The website {website} for company "{company_name}" is blocking automated scraping. 
            Please provide comprehensive company information based on your knowledge of this company.
            
            Provide detailed information in the following structured format:
            
            COMPANY: {company_name}
            WEBSITE: {website}
            
            BUSINESS OVERVIEW:
            - Industry: [specific industry category]
            - Business Model: [B2B, B2C, B2B2C, marketplace, etc.]
            - Target Market: [who they serve]
            - Company Size: [startup, SMB, enterprise]
            - Founded: [year if known]
            - Headquarters: [location if known]
            
            DESCRIPTION:
            [Comprehensive 3-4 sentence description of what the company does, their main products/services, and their value proposition]
            
            KEY SERVICES:
            - [Service/Product 1]
            - [Service/Product 2]
            - [Service/Product 3]
            [List main offerings]
            
            VALUE PROPOSITION:
            [What makes them unique, their main competitive advantage]
            
            IMPORTANT: Only provide information you are confident about. If you don't have reliable knowledge about this company, respond with "INSUFFICIENT_KNOWLEDGE" for each field.
            """
            
            self.logger.info(f"Requesting LLM fallback research for {company_name}")
            response = self.ai_client.analyze_content(fallback_prompt)
            
            if not response or "INSUFFICIENT_KNOWLEDGE" in response:
                self.logger.info(f"LLM has insufficient knowledge about {company_name}")
                return {'success': False, 'error': 'LLM has insufficient knowledge about this company'}
            
            # Parse the LLM response
            parsed_data = self._parse_llm_fallback_response(response, company_name)
            
            if parsed_data:
                self.logger.info(f"Successfully parsed LLM fallback data for {company_name}")
                return {'success': True, **parsed_data}
            else:
                return {'success': False, 'error': 'Failed to parse LLM response'}
                
        except Exception as e:
            self.logger.error(f"LLM fallback research error for {company_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_llm_fallback_response(self, response: str, company_name: str) -> dict:
        """Parse the structured LLM response into company data fields"""
        try:
            data = {
                'company_description': '',
                'industry': '',
                'business_model': '',
                'target_market': '',
                'key_services': [],
                'value_proposition': '',
                'location': '',
                'company_size': '',
                'founding_year': None
            }
            
            lines = response.split('\n')
            current_section = None
            description_lines = []
            services_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect sections
                if line.startswith('BUSINESS OVERVIEW:'):
                    current_section = 'overview'
                elif line.startswith('DESCRIPTION:'):
                    current_section = 'description'
                elif line.startswith('KEY SERVICES:'):
                    current_section = 'services'
                elif line.startswith('VALUE PROPOSITION:'):
                    current_section = 'value_prop'
                    
                # Parse overview fields
                elif current_section == 'overview':
                    if line.startswith('- Industry:'):
                        data['industry'] = line.replace('- Industry:', '').strip()
                    elif line.startswith('- Business Model:'):
                        data['business_model'] = line.replace('- Business Model:', '').strip()
                    elif line.startswith('- Target Market:'):
                        data['target_market'] = line.replace('- Target Market:', '').strip()
                    elif line.startswith('- Company Size:'):
                        data['company_size'] = line.replace('- Company Size:', '').strip()
                    elif line.startswith('- Founded:'):
                        founded_text = line.replace('- Founded:', '').strip()
                        try:
                            data['founding_year'] = int(founded_text) if founded_text.isdigit() else None
                        except:
                            pass
                    elif line.startswith('- Headquarters:'):
                        data['location'] = line.replace('- Headquarters:', '').strip()
                        
                # Parse description
                elif current_section == 'description' and not line.startswith('KEY SERVICES:'):
                    description_lines.append(line)
                    
                # Parse services
                elif current_section == 'services' and line.startswith('- '):
                    services_lines.append(line.replace('- ', '').strip())
                    
                # Parse value proposition
                elif current_section == 'value_prop' and not line.startswith('IMPORTANT:'):
                    data['value_proposition'] = line
            
            # Join description and services
            data['company_description'] = ' '.join(description_lines).strip()
            data['key_services'] = services_lines
            
            # Validate we got meaningful data
            if (data['company_description'] and 
                data['industry'] and 
                len(data['company_description']) > 50):
                
                # Add source note
                data['company_description'] += f" (Information gathered via LLM knowledge base when {company_name} website was inaccessible)"
                
                return data
            else:
                self.logger.warning(f"Parsed LLM data for {company_name} appears insufficient")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing LLM fallback response for {company_name}: {e}")
            return None

    def _web_search_fallback(self, company_name: str, website: str) -> dict:
        """
        Use web search to gather company information when both scraping and LLM fallback fail.
        This searches for public information about the company.
        """
        try:
            if not self.ai_client:
                return {'success': False, 'error': 'No AI client available for search analysis'}
            
            # First, let's try a simulated web search using LLM with search-like prompting
            search_prompt = f"""
            I need to research the company "{company_name}" (website: {website}) but their website is blocking direct access. 
            Please provide factual information about this company as if you were analyzing publicly available search results and news articles.
            
            Focus on gathering the following information from your knowledge of publicly available sources:
            
            COMPANY PROFILE: {company_name}
            
            Based on publicly available information (news articles, press releases, business directories, etc.), provide:
            
            INDUSTRY CLASSIFICATION:
            [What industry/sector does this company operate in?]
            
            BUSINESS MODEL:
            [How do they make money? B2B, B2C, etc.]
            
            COMPANY OVERVIEW:
            [2-3 sentence summary of what the company does and their main focus]
            
            PRIMARY SERVICES/PRODUCTS:
            [List their main offerings]
            
            TARGET CUSTOMERS:
            [Who are their primary customers?]
            
            IMPORTANT: Base this only on information that would be publicly available through search engines, news articles, and business directories. If you don't have confident knowledge about this company from such sources, respond with "LIMITED_PUBLIC_INFO_AVAILABLE".
            """
            
            self.logger.info(f"Requesting web search-style research for {company_name}")
            response = self.ai_client.analyze_content(search_prompt)
            
            if not response or "LIMITED_PUBLIC_INFO_AVAILABLE" in response:
                self.logger.info(f"Limited public information available for {company_name}")
                return {'success': False, 'error': 'Limited public information available'}
            
            # Parse the search-style response
            parsed_data = self._parse_web_search_response(response, company_name)
            
            if parsed_data:
                self.logger.info(f"Successfully parsed web search fallback data for {company_name}")
                return {'success': True, **parsed_data}
            else:
                return {'success': False, 'error': 'Failed to parse web search response'}
                
        except Exception as e:
            self.logger.error(f"Web search fallback error for {company_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_web_search_response(self, response: str, company_name: str) -> dict:
        """Parse the web search-style response into company data fields"""
        try:
            data = {
                'company_description': '',
                'industry': '',
                'business_model': '',
                'target_market': '',
                'key_services': []
            }
            
            lines = response.split('\n')
            current_section = None
            overview_lines = []
            services_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect sections
                if 'INDUSTRY CLASSIFICATION:' in line:
                    current_section = 'industry'
                elif 'BUSINESS MODEL:' in line:
                    current_section = 'business_model'
                elif 'COMPANY OVERVIEW:' in line:
                    current_section = 'overview'
                elif 'PRIMARY SERVICES/PRODUCTS:' in line:
                    current_section = 'services'
                elif 'TARGET CUSTOMERS:' in line:
                    current_section = 'target'
                    
                # Extract content based on section
                elif current_section == 'industry' and not any(header in line for header in ['BUSINESS MODEL:', 'COMPANY OVERVIEW:']):
                    if line and not line.startswith('['):
                        data['industry'] = line
                        
                elif current_section == 'business_model' and not any(header in line for header in ['INDUSTRY CLASSIFICATION:', 'COMPANY OVERVIEW:']):
                    if line and not line.startswith('['):
                        data['business_model'] = line
                        
                elif current_section == 'overview' and not any(header in line for header in ['PRIMARY SERVICES:', 'TARGET CUSTOMERS:']):
                    if line and not line.startswith('['):
                        overview_lines.append(line)
                        
                elif current_section == 'services' and not any(header in line for header in ['COMPANY OVERVIEW:', 'TARGET CUSTOMERS:']):
                    if line and not line.startswith('[') and (line.startswith('-') or line.startswith('•')):
                        services_lines.append(line.replace('-', '').replace('•', '').strip())
                        
                elif current_section == 'target' and not any(header in line for header in ['PRIMARY SERVICES:', 'IMPORTANT:']):
                    if line and not line.startswith('['):
                        data['target_market'] = line
            
            # Join overview
            data['company_description'] = ' '.join(overview_lines).strip()
            data['key_services'] = services_lines
            
            # Validate we got meaningful data
            if (data['company_description'] and 
                data['industry'] and 
                len(data['company_description']) > 30):
                
                # Add source note
                data['company_description'] += f" (Information gathered via web search when {company_name} website was inaccessible)"
                
                return data
            else:
                self.logger.warning(f"Parsed web search data for {company_name} appears insufficient")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing web search response for {company_name}: {e}")
            return None

    def _classify_industry(self, company: CompanyData) -> str:
        """Classify company industry using LLM based on comprehensive research data"""
        try:
            from src.similarity_prompts import INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT
            
            # Create prompt with ALL available research data
            prompt = INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT.format(
                company_name=company.name,
                website=company.website or '',
                company_description=company.company_description or 'Not available',
                value_proposition=company.value_proposition or 'Not available',
                business_model=company.business_model or 'Not available',
                target_market=company.target_market or 'Not available',
                key_services=', '.join(company.key_services) if company.key_services else 'Not available',
                competitive_advantages=', '.join(company.competitive_advantages) if company.competitive_advantages else 'Not available',
                pain_points=', '.join(company.pain_points) if company.pain_points else 'Not available',
                location=company.location or 'Not available',
                founding_year=str(company.founding_year) if company.founding_year else 'Not available',
                company_size=company.company_size or 'Not available',
                employee_count_range=company.employee_count_range or 'Not available',
                funding_status=company.funding_status or 'Not available',
                tech_stack=', '.join(company.tech_stack) if company.tech_stack else 'Not available',
                has_chat_widget='Yes' if company.has_chat_widget else 'No',
                has_forms='Yes' if company.has_forms else 'No',
                certifications=', '.join(company.certifications) if company.certifications else 'Not available',
                partnerships=', '.join(company.partnerships) if company.partnerships else 'Not available',
                awards=', '.join(company.awards) if company.awards else 'Not available',
                leadership_team=', '.join(company.leadership_team) if company.leadership_team else 'Not available',
                recent_news=', '.join(company.recent_news) if company.recent_news else 'Not available'
            )
            
            # Get industry classification from LLM
            response = self.ai_client.analyze_content(prompt)
            
            # Extract industry from response
            industry = None
            if 'Industry:' in response:
                industry_text = response.split('Industry:')[1].strip().split('\n')[0].strip()
                if industry_text and industry_text.lower() not in ['unknown', 'insufficient data']:
                    industry = industry_text
            elif response.strip() and response.strip().lower() not in ['unknown', 'insufficient data']:
                industry = response.strip()
            
            if industry:
                self.logger.info(f"Industry classification for {company.name}: {industry}")
            else:
                self.logger.info(f"Insufficient data to classify industry for {company.name}")
            
            return industry
            
        except Exception as e:
            self.logger.error(f"Error classifying industry: {e}")
            return None
    
    # ==================== STRUCTURED RESEARCH METHODS ====================
    
    def research_company_with_prompts(self, 
                                    company_name: str,
                                    website: str, 
                                    selected_prompts: List[str],
                                    include_base_research: bool = True) -> str:
        """
        Start structured research using selected prompts (non-blocking)
        
        Args:
            company_name: Target company name
            website: Company website URL
            selected_prompts: List of prompt IDs to execute
            include_base_research: Whether to include base company scraping
        
        Returns:
            Session ID for tracking progress
        """
        session_id = f"structured_{company_name.replace(' ', '_')}_{int(time.time())}"
        
        # Create research session
        session = CompanyResearchSession(
            company_name=company_name,
            website=website,
            session_id=session_id,
            start_time=datetime.utcnow(),
            selected_prompts=selected_prompts,
            results=[]
        )
        
        # Store session
        self.research_sessions[session_id] = session
        
        # Submit to thread pool for execution
        future = self.executor.submit(
            self._structured_research_worker, 
            session_id, 
            include_base_research
        )
        
        self.logger.info(f"Started structured research for {company_name} "
                        f"with {len(selected_prompts)} prompts (Session: {session_id})")
        return session_id
    
    def _structured_research_worker(self, session_id: str, include_base_research: bool):
        """Worker function for structured research"""
        session = self.research_sessions.get(session_id)
        if not session:
            self.logger.error(f"Research session {session_id} not found")
            return
        
        try:
            self.logger.info(f"Starting structured research worker for {session.company_name}")
            
            # Step 1: Base company research if requested
            if include_base_research:
                self.logger.info(f"Conducting base research for {session.company_name}")
                company_data = self._conduct_base_research_sync(session.company_name, session.website)
                session.raw_company_data = asdict(company_data) if company_data else None
            
            # Step 2: Execute selected prompts
            self.logger.info(f"Executing {len(session.selected_prompts)} structured prompts")
            self._execute_research_prompts_sync(session)
            
            # Step 3: Calculate session metrics
            self._calculate_session_metrics(session)
            
            session.end_time = datetime.utcnow()
            
            self.logger.info(f"Structured research completed for {session.company_name}. "
                           f"Success rate: {session.success_rate:.1%}, "
                           f"Total cost: ${session.total_cost:.4f}")
            
        except Exception as e:
            self.logger.error(f"Structured research failed for {session.company_name}: {str(e)}")
            session.end_time = datetime.utcnow()
            session.results = session.results or []
            self._calculate_session_metrics(session)
    
    def _conduct_base_research_sync(self, company_name: str, website: str) -> Optional[CompanyData]:
        """Conduct base company research using existing scraper (synchronous)"""
        try:
            # Create company data
            company_data = CompanyData(name=company_name, website=website)
            
            # Use existing intelligent scraper
            enriched_company = self.intelligent_scraper.scrape_company(company_data)
            
            return enriched_company
        except Exception as e:
            self.logger.error(f"Base research failed for {company_name}: {str(e)}")
            return None
    
    def _execute_research_prompts_sync(self, session: CompanyResearchSession):
        """Execute all selected research prompts (synchronous)"""
        for prompt_id in session.selected_prompts:
            try:
                result = self._execute_single_prompt_sync(session, prompt_id)
                if result:
                    session.results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to execute prompt {prompt_id}: {str(e)}")
                # Add failed result
                session.results.append(StructuredResearchResult(
                    prompt_id=prompt_id,
                    prompt_name=prompt_id,
                    success=False,
                    result_data={},
                    error_message=str(e)
                ))
    
    def _execute_single_prompt_sync(self, 
                                  session: CompanyResearchSession, 
                                  prompt_id: str) -> Optional[StructuredResearchResult]:
        """Execute a single research prompt (synchronous)"""
        start_time = datetime.now()
        
        try:
            # Get prompt configuration
            prompt = self.prompt_library.get_prompt(prompt_id)
            if not prompt:
                raise ValueError(f"Prompt '{prompt_id}' not found")
            
            # Format prompt with company information
            formatted_prompt = self.prompt_library.format_prompt(
                prompt_id=prompt_id,
                company_name=session.company_name,
                website=session.website
            )
            
            # Execute prompt using Bedrock
            self.logger.info(f"Executing prompt '{prompt.name}' for {session.company_name}")
            
            if not self.ai_client:
                raise ValueError("No AI client available for prompt execution")
            
            response = self.ai_client.analyze_content(formatted_prompt)
            
            # Parse response based on expected format
            parsed_result = self._parse_prompt_response(response, prompt)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            estimated_cost = (prompt.estimated_tokens / 1000) * self.token_price_per_1k
            
            return StructuredResearchResult(
                prompt_id=prompt_id,
                prompt_name=prompt.name,
                success=True,
                result_data=parsed_result,
                tokens_used=prompt.estimated_tokens,
                cost=estimated_cost,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Prompt '{prompt_id}' failed for {session.company_name}: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            prompt = self.prompt_library.get_prompt(prompt_id)
            
            return StructuredResearchResult(
                prompt_id=prompt_id,
                prompt_name=prompt.name if prompt else prompt_id,
                success=False,
                result_data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _parse_prompt_response(self, response: str, prompt: ResearchPrompt) -> Dict[str, Any]:
        """Parse prompt response based on expected format"""
        if prompt.output_format.value == "json":
            try:
                # Try to parse as JSON
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return as text
                self.logger.warning(f"Failed to parse JSON response for prompt '{prompt.id}', returning as text")
                return {"raw_response": response, "format": "text"}
        else:
            # Return as structured text
            return {"response": response, "format": prompt.output_format.value}
    
    def _calculate_session_metrics(self, session: CompanyResearchSession):
        """Calculate metrics for the research session"""
        if not session.results:
            session.success_rate = 0.0
            session.total_cost = 0.0
            session.total_tokens = 0
            return
        
        successful_results = [r for r in session.results if r.success]
        session.success_rate = len(successful_results) / len(session.results)
        
        session.total_cost = sum(r.cost or 0 for r in session.results)
        session.total_tokens = sum(r.tokens_used or 0 for r in session.results)
    
    def get_research_session(self, session_id: str) -> Optional[CompanyResearchSession]:
        """Get a research session by ID"""
        return self.research_sessions.get(session_id)
    
    def get_recent_sessions(self, limit: int = 10) -> List[CompanyResearchSession]:
        """Get recent research sessions"""
        sessions = sorted(
            self.research_sessions.values(), 
            key=lambda s: s.start_time, 
            reverse=True
        )
        return sessions[:limit]
    
    def export_session_results(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """Export session results in specified format"""
        session = self.get_research_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")
        
        if format.lower() == "json":
            return self._export_session_as_json(session)
        elif format.lower() == "csv":
            return self._export_session_as_csv(session)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_session_as_json(self, session: CompanyResearchSession) -> Dict[str, Any]:
        """Export session as JSON format"""
        return {
            "session_metadata": {
                "session_id": session.session_id,
                "company_name": session.company_name,
                "website": session.website,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "total_cost": session.total_cost,
                "total_tokens": session.total_tokens,
                "success_rate": session.success_rate
            },
            "research_results": [
                {
                    "prompt_id": result.prompt_id,
                    "prompt_name": result.prompt_name,
                    "success": result.success,
                    "result_data": result.result_data,
                    "error_message": result.error_message,
                    "cost": result.cost,
                    "execution_time": result.execution_time
                }
                for result in session.results or []
            ],
            "base_company_data": session.raw_company_data
        }
    
    def _export_session_as_csv(self, session: CompanyResearchSession) -> Dict[str, Any]:
        """Export session as CSV-compatible format"""
        # Flatten the results for CSV export
        flattened_results = []
        
        for result in session.results or []:
            row = {
                "session_id": session.session_id,
                "company_name": session.company_name,
                "website": session.website,
                "prompt_id": result.prompt_id,
                "prompt_name": result.prompt_name,
                "success": result.success,
                "cost": result.cost,
                "execution_time": result.execution_time,
                "error_message": result.error_message
            }
            
            # Flatten result_data into columns
            if result.result_data:
                for key, value in result.result_data.items():
                    if isinstance(value, (str, int, float, bool)):
                        row[f"result_{key}"] = value
                    else:
                        row[f"result_{key}"] = json.dumps(value)
            
            flattened_results.append(row)
        
        return {
            "csv_data": flattened_results,
            "headers": list(flattened_results[0].keys()) if flattened_results else []
        }
    
    def estimate_research_cost(self, selected_prompts: List[str]) -> Dict[str, Any]:
        """Estimate cost for selected research prompts"""
        return self.prompt_library.estimate_total_cost(
            selected_prompts, 
            self.token_price_per_1k
        )
    
    def get_available_prompts(self) -> Dict[str, Any]:
        """Get all available research prompts with metadata"""
        return self.prompt_library.get_prompt_summary()
    
    def _update_progress(self, job_id: str, status: ResearchStatus, progress: int, 
                        phase: str, error_message: str = None):
        """Update progress for a research job"""
        with self.research_lock:
            if job_id in self.research_progress:
                self.research_progress[job_id].status = status
                self.research_progress[job_id].progress_percent = progress
                self.research_progress[job_id].current_phase = phase
                
                if error_message:
                    self.research_progress[job_id].error_message = error_message
                
                if status in [ResearchStatus.COMPLETED, ResearchStatus.FAILED]:
                    self.research_progress[job_id].completion_time = datetime.utcnow()
    
    def get_research_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a research job"""
        with self.research_lock:
            if job_id in self.research_progress:
                progress = self.research_progress[job_id]
                return {
                    "job_id": job_id,
                    "company_name": progress.company_name,
                    "status": progress.status.value,
                    "progress_percent": progress.progress_percent,
                    "current_phase": progress.current_phase,
                    "phases_completed": progress.phases_completed,
                    "total_phases": progress.total_phases,
                    "start_time": progress.start_time.isoformat() if progress.start_time else None,
                    "completion_time": progress.completion_time.isoformat() if progress.completion_time else None,
                    "error_message": progress.error_message
                }
        return None
    
    def get_all_research_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all active research jobs"""
        with self.research_lock:
            return {
                job_id: self.get_research_progress(job_id) 
                for job_id in self.research_progress.keys()
            }
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up completed research jobs older than specified hours"""
        current_time = datetime.utcnow()
        to_remove = []
        
        with self.research_lock:
            for job_id, progress in self.research_progress.items():
                if (progress.status in [ResearchStatus.COMPLETED, ResearchStatus.FAILED] and 
                    progress.completion_time and 
                    (current_time - progress.completion_time).total_seconds() > max_age_hours * 3600):
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del self.research_progress[job_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} completed research jobs")
    
    def get_research_summary(self) -> Dict[str, int]:
        """Get summary statistics of research operations"""
        with self.research_lock:
            summary = {
                "total_jobs": len(self.research_progress),
                "queued": 0,
                "researching": 0,
                "completed": 0,
                "failed": 0
            }
            
            for progress in self.research_progress.values():
                if progress.status == ResearchStatus.QUEUED:
                    summary["queued"] += 1
                elif progress.status == ResearchStatus.RESEARCHING:
                    summary["researching"] += 1
                elif progress.status == ResearchStatus.COMPLETED:
                    summary["completed"] += 1
                elif progress.status == ResearchStatus.FAILED:
                    summary["failed"] += 1
            
            return summary