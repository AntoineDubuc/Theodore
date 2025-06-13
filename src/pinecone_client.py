"""
Pinecone vector database client for company similarity analysis
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
import uuid
import json
from pinecone import Pinecone, PodSpec
from src.models import CompanyData, SimilarityRelation, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


class PineconeClient:
    """Pinecone vector database client for company intelligence"""
    
    def __init__(self, config: CompanyIntelligenceConfig, api_key: str, environment: str, index_name: str):
        self.config = config
        self.api_key = api_key
        self.environment = environment  # Not used in newer Pinecone API
        self.index_name = index_name
        
        # Initialize Pinecone (projects-based, no environment needed)
        self.pc = Pinecone(api_key=api_key)
        self.index = None
        
        
        # Initialize index if it exists
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or create Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self._create_index()
            else:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            raise
    
    def _create_index(self):
        """Create new Pinecone index with appropriate configuration"""
        try:
            from pinecone import ServerlessSpec
            
            self.pc.create_index(
                name=self.index_name,
                dimension=self.config.pinecone_dimension,
                metric=self.config.pinecone_metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
            )
            logger.info(f"Successfully created Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to create Pinecone index: {e}")
            raise
    
    def upsert_company(self, company: CompanyData) -> bool:
        """Store company embedding in Pinecone"""
        if not company.embedding:
            logger.warning(f"No embedding available for {company.name}")
            return False
        
        try:
            # Prepare optimized metadata for filtering
            metadata = self._prepare_optimized_metadata(company)
            
            # Upsert vector with optimized metadata (full data is in vector content)
            self.index.upsert(
                vectors=[{
                    "id": company.id,
                    "values": company.embedding,
                    "metadata": metadata
                }]
            )
            
            logger.info(f"Successfully stored {company.name} in Pinecone with metadata")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store {company.name} in Pinecone: {e}")
            return False
    
    def batch_upsert_companies(self, companies: List[CompanyData], batch_size: int = 100) -> int:
        """Batch upsert multiple companies to Pinecone"""
        successful_upserts = 0
        
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            
            # Prepare batch vectors
            vectors = []
            for company in batch:
                if not company.embedding:
                    logger.warning(f"Skipping {company.name} - no embedding")
                    continue
                
                # Prepare optimized metadata
                metadata = self._prepare_optimized_metadata(company)
                
                vectors.append({
                    "id": company.id,
                    "values": company.embedding,
                    "metadata": metadata
                })
            
            if vectors:
                try:
                    self.index.upsert(vectors=vectors)
                    successful_upserts += len(vectors)
                    logger.info(f"Batch {i//batch_size + 1}: Upserted {len(vectors)} companies")
                except Exception as e:
                    logger.error(f"Batch upsert failed: {e}")
        
        return successful_upserts
    
    def find_similar_companies(self, company_id: str, top_k: int = 10, 
                             min_similarity: float = 0.7, 
                             industry_filter: str = None,
                             business_model_filter: str = None,
                             company_size_filter: List[str] = None,
                             use_enhanced: bool = True) -> List[Dict[str, Any]]:
        """Find companies similar to the given company with optional filtering"""
        
        if use_enhanced:
            return self.find_similar_companies_enhanced(
                company_id, 
                similarity_threshold=min_similarity,
                top_k=top_k,
                industry_filter=industry_filter
            )
        
        # Fallback to original vector similarity approach
        try:
            # Get the company's vector
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found in Pinecone")
                return []
            
            company_vector = fetch_response.vectors[company_id].values
            
            # Build filter query
            filter_conditions = []
            if industry_filter:
                filter_conditions.append({"industry": {"$eq": industry_filter}})
            if business_model_filter:
                filter_conditions.append({"business_model": {"$eq": business_model_filter}})
            if company_size_filter:
                filter_conditions.append({"company_size": {"$in": company_size_filter}})
            
            # Construct final filter
            filter_query = None
            if filter_conditions:
                if len(filter_conditions) == 1:
                    filter_query = filter_conditions[0]
                else:
                    filter_query = {"$and": filter_conditions}
            
            # Query for similar companies
            query_response = self.index.query(
                vector=company_vector,
                top_k=top_k + 1,  # +1 to exclude self
                filter=filter_query,
                include_metadata=True,
                include_values=False
            )
            
            # Filter results
            similar_companies = []
            for match in query_response.matches:
                # Skip self-match
                if match.id == company_id:
                    continue
                
                # Apply similarity threshold
                if match.score >= min_similarity:
                    similar_companies.append({
                        "company_id": match.id,
                        "similarity_score": match.score,
                        "metadata": match.metadata
                    })
            
            return similar_companies
            
        except Exception as e:
            logger.error(f"Failed to find similar companies for {company_id}: {e}")
            return []
    
    def find_companies_by_industry(self, industry: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Find companies in a specific industry using optimized filtering"""
        try:
            # Use the new filtering approach without dummy vectors
            return self.find_companies_by_filters(
                filters={"industry": {"$eq": industry}},
                top_k=top_k
            )
            
        except Exception as e:
            logger.error(f"Failed to find companies in industry {industry}: {e}")
            return []
    
    def find_companies_by_filters(self, filters: Dict[str, Any], top_k: int = 50) -> List[Dict[str, Any]]:
        """Find companies using metadata filters without dummy vectors"""
        try:
            # Use scan or list operations if available, otherwise minimal vector query
            # For now, we'll use a minimal vector query with filters
            query_response = self.index.query(
                vector=[0.0] * self.config.pinecone_dimension,  # Minimal dummy vector
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
    
    def find_company_by_name(self, company_name: str) -> Optional[CompanyData]:
        """Find a company by name using optimized filtering"""
        try:
            # Search with exact name filter first
            companies = self.find_companies_by_filters(
                filters={"company_name": {"$eq": company_name}},
                top_k=10
            )
            
            if companies:
                # Convert first match to CompanyData
                match_data = companies[0]
                return self._metadata_to_company_data(match_data["company_id"], match_data["metadata"])
            
            # Try partial matching if exact fails
            # Get a broader set and filter client-side
            all_companies = self.find_companies_by_filters(filters={}, top_k=100)
            
            search_name = company_name.lower()
            for company_data in all_companies:
                stored_name = company_data["metadata"].get('company_name', '').lower()
                if search_name in stored_name or stored_name in search_name:
                    return self._metadata_to_company_data(company_data["company_id"], company_data["metadata"])
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to find company by name {company_name}: {e}")
            return None
    
    def _metadata_to_company_data(self, company_id: str, metadata: Dict[str, Any]) -> CompanyData:
        """Convert metadata to CompanyData object using enhanced similarity fields"""
        company = CompanyData(
            id=company_id,
            name=metadata.get('company_name', ''),
            website=metadata.get('website', ''),  # Add website field - required by model
            industry=metadata.get('industry', ''),
            business_model=metadata.get('business_model', ''),
            target_market=metadata.get('target_market', ''),
            company_size=metadata.get('company_size', ''),
            funding_status=metadata.get('funding_stage', '')
        )
        
        # Add similarity-specific fields
        company.company_stage = metadata.get('company_stage')
        company.tech_sophistication = metadata.get('tech_sophistication')
        company.business_model_type = metadata.get('business_model_type')
        company.geographic_scope = metadata.get('geographic_scope')
        company.decision_maker_type = metadata.get('decision_maker_type')
        
        # Add confidence scores
        company.stage_confidence = metadata.get('stage_confidence')
        company.tech_confidence = metadata.get('tech_confidence')
        company.industry_confidence = metadata.get('industry_confidence')
        
        return company
    
    def _vector_match_to_company_data(self, match) -> CompanyData:
        """Convert a Pinecone vector match to CompanyData object using optimized metadata"""
        company = self._metadata_to_company_data(match.id, match.metadata)
        
        # Set embedding if available
        if hasattr(match, 'values') and match.values:
            company.embedding = list(match.values)
            
        return company
    
    def calculate_sector_similarity(self, sector_a_companies: List[str], 
                                   sector_b_companies: List[str]) -> float:
        """Calculate similarity between two sectors using their company centroids"""
        try:
            # Get vectors for both sectors
            all_company_ids = sector_a_companies + sector_b_companies
            fetch_response = self.index.fetch(ids=all_company_ids)
            
            # Calculate centroids
            sector_a_vectors = []
            sector_b_vectors = []
            
            for company_id in sector_a_companies:
                if company_id in fetch_response.vectors:
                    sector_a_vectors.append(fetch_response.vectors[company_id].values)
            
            for company_id in sector_b_companies:
                if company_id in fetch_response.vectors:
                    sector_b_vectors.append(fetch_response.vectors[company_id].values)
            
            if not sector_a_vectors or not sector_b_vectors:
                return 0.0
            
            # Calculate centroids
            import numpy as np
            centroid_a = np.mean(sector_a_vectors, axis=0)
            centroid_b = np.mean(sector_b_vectors, axis=0)
            
            # Calculate cosine similarity
            similarity = np.dot(centroid_a, centroid_b) / (
                np.linalg.norm(centroid_a) * np.linalg.norm(centroid_b)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate sector similarity: {e}")
            return 0.0
    
    def get_company_metadata(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company metadata from Pinecone"""
        try:
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id in fetch_response.vectors:
                return fetch_response.vectors[company_id].metadata
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get metadata for {company_id}: {e}")
            return None
    
    def delete_company(self, company_id: str) -> bool:
        """Delete a company from Pinecone"""
        try:
            self.index.delete(ids=[company_id])
            logger.info(f"Deleted company {company_id} from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {e}")
            return False
    
    def clear_all_records(self) -> bool:
        """Clear all records from Pinecone index"""
        try:
            # Delete all vectors in the default namespace
            self.index.delete(delete_all=True)
            logger.info("Successfully cleared all records from Pinecone index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Pinecone index: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def _prepare_optimized_metadata(self, company: CompanyData) -> Dict[str, Any]:
        """Prepare enhanced metadata for similarity-based filtering"""
        
        def safe_get(value, default="Unknown"):
            """Safely get value with default"""
            return value if value and value.strip() else default
        
        def safe_join(items, separator=", "):
            """Safely join list items"""
            if not items:
                return ""
            if isinstance(items, str):
                return items
            return separator.join(str(item) for item in items if item)
        
        # Enhanced metadata with similarity metrics and sales intelligence
        metadata = {
            # Core identification
            "company_name": safe_get(company.name),
            "website": safe_get(company.website),
            
            # Sales intelligence (key addition for new scraper)
            "company_description": safe_get(company.company_description, ""),
            "has_description": bool(company.company_description and company.company_description.strip()),
            
            # Rich data fields (THE FIX: Add missing fields that were being lost)
            "ai_summary": safe_get(company.ai_summary, ""),
            "value_proposition": safe_get(company.value_proposition, ""),
            "key_services": safe_join(company.key_services),
            "competitive_advantages": safe_join(company.competitive_advantages),
            "tech_stack": safe_join(company.tech_stack),
            "pain_points": safe_join(company.pain_points),
            
            # Processing metadata
            "pages_crawled": company.pages_crawled if company.pages_crawled else [],
            "crawl_duration": company.crawl_duration or 0,
            "scrape_status": safe_get(company.scrape_status, "unknown"),
            "last_updated": company.last_updated.isoformat() if company.last_updated else "",
            
            # Similarity dimensions
            "company_stage": safe_get(company.company_stage),
            "tech_sophistication": safe_get(company.tech_sophistication), 
            "industry": safe_get(company.industry),
            "business_model_type": safe_get(company.business_model_type),
            "geographic_scope": safe_get(company.geographic_scope),
            "decision_maker_type": safe_get(company.decision_maker_type),
            
            # Legacy fields (for compatibility)
            "business_model": safe_get(company.business_model),
            "target_market": safe_get(company.target_market),
            "company_size": safe_get(company.company_size or company.employee_count_range)
        }
        
        # Add confidence scores if available
        confidence_fields = ['stage_confidence', 'tech_confidence', 'industry_confidence']
        for field in confidence_fields:
            if hasattr(company, field) and getattr(company, field) is not None:
                metadata[field] = getattr(company, field)
        
        return metadata
    
    def _prepare_vector_content(self, company: CompanyData) -> str:
        """Prepare comprehensive company data as text content for vector embedding"""
        
        def safe_join(items, separator=", "):
            """Safely join list items"""
            if not items:
                return ""
            if isinstance(items, str):
                return items
            return separator.join(str(item) for item in items if item)
        
        def safe_get(value, default=""):
            """Safely get value"""
            return str(value).strip() if value else default
        
        # Create comprehensive text representation
        content_parts = [
            f"Company Name: {safe_get(company.name)}",
            f"Website: {safe_get(company.website)}",
            f"Industry: {safe_get(company.industry)}",
            f"Business Model: {safe_get(company.business_model)}",
            f"Target Market: {safe_get(company.target_market)}",
            f"Company Size: {safe_get(company.company_size or company.employee_count_range)}",
        ]
        
        # Add detailed descriptions
        if company.company_description:
            content_parts.append(f"Description: {safe_get(company.company_description)}")
        
        if company.value_proposition:
            content_parts.append(f"Value Proposition: {safe_get(company.value_proposition)}")
        
        # Add services and technology
        if company.key_services:
            content_parts.append(f"Key Services: {safe_join(company.key_services)}")
            
        if company.tech_stack:
            content_parts.append(f"Technology Stack: {safe_join(company.tech_stack)}")
        
        # Add competitive advantages
        if company.competitive_advantages:
            content_parts.append(f"Competitive Advantages: {safe_join(company.competitive_advantages)}")
        
        # Add leadership and culture
        if company.leadership_team:
            content_parts.append(f"Leadership Team: {safe_join(company.leadership_team)}")
            
        if company.company_culture:
            content_parts.append(f"Company Culture: {safe_get(company.company_culture)}")
        
        # Add location and other details
        if company.location:
            content_parts.append(f"Location: {safe_get(company.location)}")
            
        if company.founding_year:
            content_parts.append(f"Founded: {safe_get(company.founding_year)}")
        
        # Add pain points if available
        if company.pain_points:
            content_parts.append(f"Pain Points Addressed: {safe_join(company.pain_points)}")
        
        # Add AI summary if available
        if company.ai_summary:
            content_parts.append(f"AI Analysis: {safe_get(company.ai_summary)}")
        
        return "\n".join(content_parts)
    
    def get_full_company_data(self, company_id: str) -> Optional[CompanyData]:
        """
        Retrieve company data from Pinecone optimized metadata.
        Note: Full company details are now embedded in the vector content, 
        so this only returns the basic fields stored in metadata.
        """
        try:
            logger.info(f"Fetching company {company_id} from Pinecone...")
            fetch_response = self.index.fetch(ids=[company_id])
            logger.info(f"Fetch response has {len(fetch_response.vectors)} vectors")
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found in Pinecone")
                logger.info(f"Available vector IDs: {list(fetch_response.vectors.keys())}")
                return None
            
            vector_data = fetch_response.vectors[company_id]
            metadata = vector_data.metadata
            
            # Build CompanyData object with available metadata
            company = CompanyData(
                id=company_id,
                name=metadata.get('company_name', ''),
                website=metadata.get('website', ''),  # Add website field - required by model
                industry=metadata.get('industry', ''),
                business_model=metadata.get('business_model', ''),
                target_market=metadata.get('target_market', ''),
                company_size=metadata.get('company_size', ''),
                embedding=list(vector_data.values) if vector_data.values else None
            )
            
            # Add funding stage if available
            if 'funding_stage' in metadata:
                company.funding_status = metadata['funding_stage']
            
            return company
            
        except Exception as e:
            logger.error(f"Failed to load data for {company_id}: {e}")
            return None
    
    def search_companies_by_text(self, query_text: str, embedding_function, 
                                top_k: int = 10) -> List[Dict[str, Any]]:
        """Search companies using text query (requires embedding function)"""
        try:
            # Generate embedding for query text
            query_embedding = embedding_function(query_text)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Search Pinecone
            query_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            results = []
            for match in query_response.matches:
                results.append({
                    "company_id": match.id,
                    "similarity_score": match.score,
                    "metadata": match.metadata
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search companies by text: {e}")
            return []
    
    def store_similarity_relationships(self, similarities: List['CompanySimilarity']) -> bool:
        """
        Store similarity relationships in Pinecone metadata
        
        Note: For POC, we store similarity data in the company metadata.
        In production, consider a dedicated similarity index.
        """
        try:
            from src.models import CompanySimilarity
            
            for similarity in similarities:
                # Update both companies' metadata with similarity info
                self._add_similarity_to_company_metadata(
                    similarity.original_company_id,
                    similarity.similar_company_id,
                    similarity
                )
                
                # Store bidirectional relationship if specified
                if similarity.is_bidirectional:
                    self._add_similarity_to_company_metadata(
                        similarity.similar_company_id,
                        similarity.original_company_id,
                        similarity
                    )
            
            logger.info(f"Stored {len(similarities)} similarity relationships")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store similarity relationships: {e}")
            return False
    
    def _add_similarity_to_company_metadata(self, 
                                          company_id: str, 
                                          similar_company_id: str,
                                          similarity: 'CompanySimilarity') -> bool:
        """
        Add similarity relationship to a company's metadata
        """
        try:
            # Get current metadata
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found for similarity update")
                return False
            
            metadata = fetch_response.vectors[company_id].metadata.copy()
            
            # Initialize similarity list if not exists
            similar_companies_key = "similar_companies"
            if similar_companies_key not in metadata:
                metadata[similar_companies_key] = json.dumps([])
            
            # Parse existing similarities
            try:
                existing_similarities = json.loads(metadata[similar_companies_key])
            except json.JSONDecodeError:
                existing_similarities = []
            
            # Check if relationship already exists
            existing_ids = [sim.get('company_id') for sim in existing_similarities]
            if similar_company_id not in existing_ids:
                # Add new similarity
                similarity_data = {
                    "company_id": similar_company_id,
                    "company_name": similarity.similar_company_name,
                    "similarity_score": similarity.similarity_score,
                    "confidence": similarity.confidence,
                    "discovery_method": similarity.discovery_method,
                    "validation_methods": similarity.validation_methods,
                    "relationship_type": similarity.relationship_type,
                    "discovered_at": similarity.discovered_at.isoformat()
                }
                
                existing_similarities.append(similarity_data)
                
                # Update metadata
                metadata[similar_companies_key] = json.dumps(existing_similarities)
                
                # Update in Pinecone
                self.index.update(
                    id=company_id,
                    set_metadata=metadata
                )
                
                logger.debug(f"Added similarity {similar_company_id} to {company_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add similarity to company metadata: {e}")
            return False
    
    def get_stored_similarities(self, company_id: str, limit: int = 10) -> List['CompanySimilarity']:
        """
        Find companies similar to the given company ID
        """
        try:
            from src.models import CompanySimilarity
            from datetime import datetime
            
            # Get company metadata
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found")
                return []
            
            metadata = fetch_response.vectors[company_id].metadata
            similar_companies_data = metadata.get("similar_companies", "[]")
            
            try:
                similarities_list = json.loads(similar_companies_data)
            except json.JSONDecodeError:
                return []
            
            # Convert to CompanySimilarity objects
            similarities = []
            for sim_data in similarities_list[:limit]:
                try:
                    similarity = CompanySimilarity(
                        original_company_id=company_id,
                        similar_company_id=sim_data.get("company_id", ""),
                        original_company_name=metadata.get("company_name", ""),
                        similar_company_name=sim_data.get("company_name", ""),
                        similarity_score=sim_data.get("similarity_score", 0.0),
                        confidence=sim_data.get("confidence", 0.0),
                        discovery_method=sim_data.get("discovery_method", "unknown"),
                        validation_methods=sim_data.get("validation_methods", []),
                        relationship_type=sim_data.get("relationship_type", "competitor"),
                        discovered_at=datetime.fromisoformat(sim_data.get("discovered_at", datetime.now().isoformat()))
                    )
                    similarities.append(similarity)
                except Exception as e:
                    logger.error(f"Error creating CompanySimilarity object: {e}")
                    continue
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to find similar companies for {company_id}: {e}")
            return []
    
    def get_similarity_score(self, company_a_id: str, company_b_id: str) -> Optional[float]:
        """
        Get similarity score between two specific companies
        """
        try:
            similarities = self.find_similar_companies(company_a_id)
            
            for similarity in similarities:
                if similarity.similar_company_id == company_b_id:
                    return similarity.similarity_score
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get similarity score: {e}")
            return None
    
    def get_company_by_id(self, company_id: str) -> Optional['CompanyData']:
        """
        Get company data by ID (alias for get_full_company_data)
        """
        return self.get_full_company_data(company_id)
    
    def find_similar_companies_enhanced(self, company_id: str, 
                                     similarity_threshold: float = 0.7,
                                     top_k: int = 10,
                                     stage_filter: str = None,
                                     tech_filter: str = None,
                                     industry_filter: str = None) -> List[Dict[str, Any]]:
        """Find similar companies using enhanced similarity algorithm"""
        try:
            from src.similarity_engine import SimilarityEngine
            
            # Get target company
            target_company = self.get_full_company_data(company_id)
            if not target_company:
                logger.warning(f"Target company {company_id} not found")
                return []
            
            # Build filter query
            filter_conditions = []
            if stage_filter:
                filter_conditions.append({"company_stage": {"$eq": stage_filter}})
            if tech_filter:
                filter_conditions.append({"tech_sophistication": {"$eq": tech_filter}})
            if industry_filter:
                filter_conditions.append({"industry": {"$eq": industry_filter}})
            
            filter_query = None
            if filter_conditions:
                if len(filter_conditions) == 1:
                    filter_query = filter_conditions[0]
                else:
                    filter_query = {"$and": filter_conditions}
            
            # Get candidate companies
            query_response = self.index.query(
                vector=[0.0] * self.config.pinecone_dimension,  # Dummy vector for metadata search
                top_k=min(top_k * 5, 100),  # Get more candidates for similarity filtering
                filter=filter_query,
                include_metadata=True,
                include_values=False
            )
            
            # Convert to CompanyData objects
            candidate_companies = []
            for match in query_response.matches:
                if match.id != company_id:  # Exclude self
                    company = self._metadata_to_company_data(match.id, match.metadata)
                    candidate_companies.append(company)
            
            # Calculate similarities using enhanced algorithm
            similarity_engine = SimilarityEngine()
            similar_companies = similarity_engine.find_similar_companies(
                target_company, 
                candidate_companies, 
                threshold=similarity_threshold,
                limit=top_k
            )
            
            # Format results
            results = []
            for company, similarity_result in similar_companies:
                results.append({
                    "company_id": company.id,
                    "company_name": company.name,
                    "similarity_score": similarity_result['overall_similarity'],
                    "confidence": similarity_result['overall_confidence'],
                    "explanation": similarity_result['explanation'],
                    "dimension_scores": similarity_result['dimension_similarities'],
                    "metadata": {
                        "company_stage": company.company_stage,
                        "tech_sophistication": company.tech_sophistication,
                        "industry": company.industry,
                        "business_model_type": company.business_model_type,
                        "geographic_scope": company.geographic_scope
                    }
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced similarity search failed for {company_id}: {e}")
            return []
    
    def get_similarity_insights(self, company_id: str) -> Dict[str, Any]:
        """Get similarity insights and recommendations for a company"""
        try:
            company = self.get_full_company_data(company_id)
            if not company:
                return {"error": "Company not found"}
            
            # Get similar companies
            similar_companies = self.find_similar_companies_enhanced(company_id, top_k=5)
            
            # Analyze patterns
            if similar_companies:
                # Extract common characteristics
                stages = [comp["metadata"]["company_stage"] for comp in similar_companies]
                tech_levels = [comp["metadata"]["tech_sophistication"] for comp in similar_companies]
                industries = [comp["metadata"]["industry"] for comp in similar_companies]
                
                common_stage = max(set(stages), key=stages.count) if stages else "unknown"
                common_tech = max(set(tech_levels), key=tech_levels.count) if tech_levels else "unknown"
                common_industry = max(set(industries), key=industries.count) if industries else "unknown"
                
                insights = {
                    "target_company": {
                        "id": company.id,
                        "name": company.name,
                        "stage": company.company_stage,
                        "tech_level": company.tech_sophistication,
                        "industry": company.industry
                    },
                    "similar_companies": similar_companies,
                    "patterns": {
                        "common_stage": common_stage,
                        "common_tech_level": common_tech,
                        "common_industry": common_industry
                    },
                    "sales_recommendations": self._generate_sales_recommendations(company, similar_companies)
                }
            else:
                insights = {
                    "target_company": {
                        "id": company.id,
                        "name": company.name
                    },
                    "similar_companies": [],
                    "message": "No similar companies found with current criteria"
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get similarity insights for {company_id}: {e}")
            return {"error": str(e)}
    
    def _generate_sales_recommendations(self, target_company: CompanyData, similar_companies: List[Dict]) -> List[str]:
        """Generate sales approach recommendations based on similar companies"""
        recommendations = []
        
        if not similar_companies:
            return ["Unique company profile - develop custom sales approach"]
        
        # Analyze patterns from similar companies
        avg_similarity = sum(comp["similarity_score"] for comp in similar_companies) / len(similar_companies)
        
        if avg_similarity > 0.85:
            recommendations.append("High similarity - use proven playbooks from similar companies")
        elif avg_similarity > 0.7:
            recommendations.append("Good similarity - adapt successful approaches with minor modifications")
        else:
            recommendations.append("Moderate similarity - use similar companies as starting point but customize heavily")
        
        # Stage-specific recommendations
        stage = target_company.company_stage
        if stage == "startup":
            recommendations.append("Focus on ROI and fast implementation")
        elif stage == "growth":
            recommendations.append("Emphasize scalability and growth enablement")
        elif stage == "enterprise":
            recommendations.append("Highlight security, compliance, and enterprise features")
        
        # Tech sophistication recommendations
        tech_level = target_company.tech_sophistication
        if tech_level == "high":
            recommendations.append("Lead with technical depth and API capabilities")
        elif tech_level == "medium":
            recommendations.append("Balance technical features with business benefits")
        elif tech_level == "low":
            recommendations.append("Focus on ease of use and business outcomes")
        
        return recommendations