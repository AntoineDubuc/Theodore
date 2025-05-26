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
            # Prepare complete metadata with all company data
            metadata = self._prepare_complete_metadata(company)
            
            # Upsert vector with complete company data in metadata
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
                
                # Prepare complete metadata
                metadata = self._prepare_complete_metadata(company)
                
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
                             min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Find companies similar to the given company"""
        try:
            # Get the company's vector
            fetch_response = self.index.fetch(ids=[company_id])
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found in Pinecone")
                return []
            
            company_vector = fetch_response.vectors[company_id].values
            
            # Query for similar companies
            query_response = self.index.query(
                vector=company_vector,
                top_k=top_k + 1,  # +1 to exclude self
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
        """Find companies in a specific industry"""
        try:
            query_response = self.index.query(
                vector=[0.0] * self.config.pinecone_dimension,  # Dummy vector
                top_k=top_k,
                include_metadata=True,
                include_values=False,
                filter={"industry": {"$eq": industry}}
            )
            
            companies = []
            for match in query_response.matches:
                companies.append({
                    "company_id": match.id,
                    "metadata": match.metadata
                })
            
            return companies
            
        except Exception as e:
            logger.error(f"Failed to find companies in industry {industry}: {e}")
            return []
    
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
    
    def _prepare_complete_metadata(self, company: CompanyData) -> Dict[str, Any]:
        """Prepare complete company data as Pinecone metadata"""
        
        def safe_str(value) -> str:
            """Convert value to string, handling None and complex types"""
            if value is None:
                return ""
            elif isinstance(value, (list, dict)):
                return json.dumps(value) if value else ""
            elif hasattr(value, 'isoformat'):  # datetime objects
                return value.isoformat()
            else:
                return str(value)
        
        def safe_get_attr(obj, attr_name: str, default=""):
            """Safely get attribute from object"""
            return safe_str(getattr(obj, attr_name, default))
        
        metadata = {
            # Core identifiers
            "company_name": safe_get_attr(company, "name"),
            "website": safe_get_attr(company, "website"),
            
            # Business fundamentals
            "industry": safe_get_attr(company, "industry"),
            "business_model": safe_get_attr(company, "business_model"),
            "target_market": safe_get_attr(company, "target_market"),
            "company_description": safe_get_attr(company, "company_description"),
            "value_proposition": safe_get_attr(company, "value_proposition"),
            
            # Company details
            "founding_year": safe_get_attr(company, "founding_year"),
            "location": safe_get_attr(company, "location"),
            "employee_count_range": safe_get_attr(company, "employee_count_range"),
            "company_culture": safe_get_attr(company, "company_culture"),
            "company_size": safe_get_attr(company, "company_size"),
            
            # Services and technology
            "key_services": safe_get_attr(company, "key_services"),
            "tech_stack": safe_get_attr(company, "tech_stack"),
            "competitive_advantages": safe_get_attr(company, "competitive_advantages"),
            "pain_points": safe_get_attr(company, "pain_points"),
            
            # Team and leadership
            "leadership_team": safe_get_attr(company, "leadership_team"),
            
            # Contact information
            "contact_info": safe_get_attr(company, "contact_info"),
            "social_media": safe_get_attr(company, "social_media"),
            
            # Crawling metadata
            "scrape_status": safe_get_attr(company, "scrape_status"),
            "scrape_error": safe_get_attr(company, "scrape_error"),
            "crawl_depth": safe_get_attr(company, "crawl_depth"),
            "crawl_duration": safe_get_attr(company, "crawl_duration"),
            "pages_crawled": safe_get_attr(company, "pages_crawled"),
            "created_at": safe_get_attr(company, "created_at"),
            
            # Technical features
            "has_chat_widget": safe_get_attr(company, "has_chat_widget"),
            "has_forms": safe_get_attr(company, "has_forms"),
            
            # Additional fields that might exist
            "funding_status": safe_get_attr(company, "funding_status"),
            "recent_news": safe_get_attr(company, "recent_news"),
            "certifications": safe_get_attr(company, "certifications"),
            "partnerships": safe_get_attr(company, "partnerships"),
            "awards": safe_get_attr(company, "awards")
        }
        
        # Remove empty values to optimize storage
        return {k: v for k, v in metadata.items() if v}
    
    def get_full_company_data(self, company_id: str) -> Optional[CompanyData]:
        """Retrieve complete company data from Pinecone metadata"""
        try:
            logger.info(f"Fetching company {company_id} from Pinecone...")
            fetch_response = self.index.fetch(ids=[company_id])
            logger.info(f"Fetch response has {len(fetch_response.vectors)} vectors")
            
            if company_id not in fetch_response.vectors:
                logger.warning(f"Company {company_id} not found in Pinecone")
                logger.info(f"Available vector IDs: {list(fetch_response.vectors.keys())}")
                return None
            
            metadata = fetch_response.vectors[company_id].metadata
            
            # Convert metadata back to CompanyData
            # Parse JSON strings back to lists/dicts where needed
            def parse_value(key: str, value: str):
                if not value:
                    return None
                
                # Lists that were JSON encoded
                if key in ['key_services', 'tech_stack', 'competitive_advantages', 'leadership_team', 'pages_crawled']:
                    try:
                        parsed = json.loads(value)
                        return parsed if isinstance(parsed, list) else None
                    except json.JSONDecodeError:
                        return None
                
                # Dicts that were JSON encoded
                elif key in ['contact_info']:
                    try:
                        parsed = json.loads(value)
                        return parsed if isinstance(parsed, dict) else None
                    except json.JSONDecodeError:
                        return None
                
                # Integers
                elif key in ['founding_year', 'crawl_depth']:
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return None
                
                # Floats
                elif key in ['crawl_duration']:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
                
                # Booleans
                elif key in ['has_chat_widget', 'has_forms']:
                    return value.lower() in ['true', '1', 'yes']
                
                # Datetime
                elif key in ['created_at']:
                    try:
                        from datetime import datetime
                        return datetime.fromisoformat(value)
                    except ValueError:
                        return None
                
                # Everything else as string
                else:
                    return value
            
            # Build CompanyData object
            company_dict = {
                'id': company_id,
                'name': metadata.get('company_name', ''),
                'website': metadata.get('website', ''),
                'embedding': fetch_response.vectors[company_id].values
            }
            
            # Add all other fields
            for key, value in metadata.items():
                if key == 'company_name':
                    continue  # Already mapped to 'name'
                
                # Map metadata keys to CompanyData fields
                field_name = key
                parsed_value = parse_value(key, value)
                company_dict[field_name] = parsed_value
            
            return CompanyData(**company_dict)
            
        except Exception as e:
            logger.error(f"Failed to load full data for {company_id}: {e}")
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
    
    def find_similar_companies(self, company_id: str, limit: int = 10) -> List['CompanySimilarity']:
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