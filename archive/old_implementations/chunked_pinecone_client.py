"""
Corrected Pinecone client using proper chunking strategy
Multiple focused vectors per company with minimal metadata
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
import uuid
import json
from pinecone import Pinecone, PodSpec
from src.models import CompanyData, CompanyIntelligenceConfig

logger = logging.getLogger(__name__)


class ChunkedPineconeClient:
    """Pinecone client using proper chunking strategy for company data"""
    
    def __init__(self, config: CompanyIntelligenceConfig, api_key: str, environment: str, index_name: str):
        self.config = config
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.index = None
        
        # Initialize index
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or create Pinecone index"""
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name in existing_indexes:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
                self.index = self.pc.Index(self.index_name)
            else:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self._create_index()
                self.index = self.pc.Index(self.index_name)
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            raise
    
    def _create_index(self):
        """Create new Pinecone index optimized for company chunks"""
        try:
            from pinecone import ServerlessSpec
            
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # Standard for text-embedding-ada-002 and Titan
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info(f"Successfully created Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise
    
    def extract_company_chunks(self, company: CompanyData) -> List[Dict[str, Any]]:
        """Extract focused chunks from company data"""
        chunks = []
        
        # 1. Company Overview Chunk
        if company.company_description or company.industry or company.target_market:
            overview_parts = [company.name or "Company"]
            
            if company.company_description:
                overview_parts.append(company.company_description)
            
            if company.industry:
                overview_parts.append(f"Industry: {company.industry}")
            
            if company.business_model:
                overview_parts.append(f"Business model: {company.business_model}")
            
            if company.target_market:
                overview_parts.append(f"Target market: {company.target_market}")
            
            if company.founding_year:
                overview_parts.append(f"Founded: {company.founding_year}")
            
            chunks.append({
                "content": " ".join(overview_parts),
                "type": "overview",
                "priority": "high"
            })
        
        # 2. Leadership Team Chunk
        if company.leadership_team:
            leadership_text = f"{company.name} leadership team includes: " + ". ".join(company.leadership_team)
            
            chunks.append({
                "content": leadership_text,
                "type": "leadership", 
                "priority": "high"
            })
        
        # 3. Products/Services Chunk
        if company.key_services:
            services_text = f"{company.name} provides the following services and products: " + ". ".join(company.key_services)
            
            chunks.append({
                "content": services_text,
                "type": "products",
                "priority": "high"
            })
        
        # 4. Technology Stack Chunk
        if company.tech_stack:
            tech_text = f"{company.name} uses the following technologies and capabilities: " + ". ".join(company.tech_stack)
            
            chunks.append({
                "content": tech_text,
                "type": "technology",
                "priority": "medium"
            })
        
        # 5. Contact/Location Chunk
        contact_parts = [f"{company.name} contact information:"]
        
        if company.location:
            contact_parts.append(f"Located at {company.location}")
        
        if company.contact_info:
            for key, value in company.contact_info.items():
                if value:
                    contact_parts.append(f"{key}: {value}")
        
        if len(contact_parts) > 1:  # More than just the header
            chunks.append({
                "content": " ".join(contact_parts),
                "type": "contact",
                "priority": "low"
            })
        
        return chunks
    
    def prepare_chunk_metadata(self, company: CompanyData, chunk_type: str) -> Dict[str, Any]:
        """Prepare minimal metadata for a chunk"""
        
        # Extract location components
        location_city = None
        location_state = None
        location_country = None
        
        if company.location:
            # Simple parsing - can be enhanced
            location_parts = company.location.split(",")
            if len(location_parts) >= 2:
                location_city = location_parts[-2].strip().lower()
                location_state = location_parts[-1].strip().lower()
                location_country = "usa"  # Assume USA for now
        
        metadata = {
            # Company identifiers
            "company_id": company.id,
            "company_name": company.name,
            
            # Chunk information
            "chunk_type": chunk_type,
            
            # Searchable categorical fields
            "industry": (company.industry or "unknown").lower(),
            "business_model": (company.business_model or "unknown").lower(),
            "target_market": (company.target_market or "unknown").lower()[:100],  # Truncate long values
            
            # Location data
            "location_city": location_city or "unknown",
            "location_state": location_state or "unknown", 
            "location_country": location_country or "unknown",
            
            # Company characteristics
            "company_size": (company.employee_count_range or "unknown").lower(),
            "founding_year": company.founding_year or "unknown",
            
            # Data flags
            "has_leadership_data": bool(company.leadership_team),
            "has_product_data": bool(company.key_services),
            "has_tech_data": bool(company.tech_stack),
            "has_contact_data": bool(company.contact_info),
            
            # Processing metadata
            "crawl_date": company.created_at.isoformat() if company.created_at else None,
            "source_website": company.website
        }
        
        # Remove None values and ensure strings are reasonable length
        filtered_metadata = {}
        for key, value in metadata.items():
            if value is not None:
                if isinstance(value, str) and len(value) > 200:
                    filtered_metadata[key] = value[:200]
                else:
                    filtered_metadata[key] = value
        
        return filtered_metadata
    
    def upsert_company_chunks(self, company: CompanyData, bedrock_client) -> List[str]:
        """Store company as multiple focused chunks"""
        
        if not company.name:
            logger.warning("Company missing name, skipping")
            return []
        
        # Extract chunks
        chunks = self.extract_company_chunks(company)
        
        if not chunks:
            logger.warning(f"No chunks extracted for {company.name}")
            return []
        
        vectors = []
        chunk_ids = []
        
        for chunk in chunks:
            try:
                # Generate embedding for chunk content
                embedding = bedrock_client.generate_embedding(chunk["content"])
                
                if not embedding:
                    logger.warning(f"Failed to generate embedding for {company.name} {chunk['type']} chunk")
                    continue
                
                # Create chunk ID
                chunk_id = f"{company.id}-{chunk['type']}"
                chunk_ids.append(chunk_id)
                
                # Prepare metadata
                metadata = self.prepare_chunk_metadata(company, chunk["type"])
                
                # Create vector
                vector = {
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": metadata
                }
                
                vectors.append(vector)
                
                logger.info(f"Prepared {chunk['type']} chunk for {company.name} ({len(chunk['content'])} chars)")
                
            except Exception as e:
                logger.error(f"Failed to process {chunk['type']} chunk for {company.name}: {e}")
                continue
        
        # Upsert all chunks
        if vectors:
            try:
                self.index.upsert(vectors=vectors)
                logger.info(f"Successfully stored {len(vectors)} chunks for {company.name}")
                return chunk_ids
                
            except Exception as e:
                logger.error(f"Failed to upsert chunks for {company.name}: {e}")
                return []
        else:
            logger.warning(f"No vectors generated for {company.name}")
            return []
    
    def search_companies(self, query: str, bedrock_client, 
                        chunk_types: Optional[List[str]] = None,
                        filters: Optional[Dict[str, Any]] = None,
                        top_k: int = 20) -> List[Dict[str, Any]]:
        """Search for companies using semantic similarity and filtering"""
        
        try:
            # Generate query embedding
            query_embedding = bedrock_client.generate_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Prepare filters
            search_filters = filters or {}
            
            # Add chunk type filter if specified
            if chunk_types:
                search_filters["chunk_type"] = {"$in": chunk_types}
            
            # Perform search
            response = self.index.query(
                vector=query_embedding,
                filter=search_filters if search_filters else None,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Process results
            results = []
            for match in response.matches:
                result = {
                    "chunk_id": match.id,
                    "score": match.score,
                    "company_id": match.metadata.get("company_id"),
                    "company_name": match.metadata.get("company_name"),
                    "chunk_type": match.metadata.get("chunk_type"),
                    "metadata": match.metadata
                }
                results.append(result)
            
            logger.info(f"Search returned {len(results)} chunks for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_company_chunks(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific company"""
        
        try:
            # Search for all chunks of this company
            response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                filter={"company_id": company_id},
                top_k=10,  # Should be enough for all chunks of one company
                include_metadata=True,
                include_values=False
            )
            
            chunks = []
            for match in response.matches:
                chunk = {
                    "chunk_id": match.id,
                    "chunk_type": match.metadata.get("chunk_type"),
                    "metadata": match.metadata
                }
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks for company {company_id}: {e}")
            return []
    
    def delete_company_chunks(self, company_id: str) -> bool:
        """Delete all chunks for a company"""
        
        try:
            # Get all chunk IDs for this company
            chunks = self.get_company_chunks(company_id)
            chunk_ids = [chunk["chunk_id"] for chunk in chunks]
            
            if chunk_ids:
                self.index.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for company {company_id}")
                return True
            else:
                logger.info(f"No chunks found for company {company_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete chunks for company {company_id}: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index"""
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}