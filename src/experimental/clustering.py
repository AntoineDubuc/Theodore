"""
Sector clustering engine for company intelligence
"""

import logging
from typing import List, Dict, Any, Set
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from src.models import CompanyData, SectorCluster, CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

logger = logging.getLogger(__name__)


class SectorClusteringEngine:
    """Engine for clustering companies into sectors"""
    
    def __init__(self, config: CompanyIntelligenceConfig, pinecone_client: PineconeClient):
        self.config = config
        self.pinecone_client = pinecone_client
    
    def cluster_companies_by_sector(self, companies: List[CompanyData]) -> List[SectorCluster]:
        """Cluster companies into sectors using multiple approaches"""
        
        # Try different clustering approaches
        industry_clusters = self._cluster_by_industry(companies)
        embedding_clusters = self._cluster_by_embeddings(companies)
        
        # Merge and refine clusters
        final_clusters = self._merge_clustering_results(
            companies, industry_clusters, embedding_clusters
        )
        
        # Generate sector metadata
        sectors = []
        for cluster_name, company_ids in final_clusters.items():
            sector = self._create_sector_cluster(cluster_name, company_ids, companies)
            if len(sector.companies) >= self.config.min_cluster_size:
                sectors.append(sector)
        
        logger.info(f"Generated {len(sectors)} sector clusters")
        return sectors
    
    def _cluster_by_industry(self, companies: List[CompanyData]) -> Dict[str, List[str]]:
        """Cluster companies by detected industry"""
        industry_clusters = defaultdict(list)
        
        for company in companies:
            industry = company.industry or "unknown"
            
            # Normalize industry names
            normalized_industry = self._normalize_industry_name(industry)
            industry_clusters[normalized_industry].append(company.id)
        
        logger.info(f"Industry clustering created {len(industry_clusters)} clusters")
        return dict(industry_clusters)
    
    def _cluster_by_embeddings(self, companies: List[CompanyData], n_clusters: int = None) -> Dict[str, List[str]]:
        """Cluster companies by embedding similarity"""
        
        # Extract embeddings and company IDs
        embeddings = []
        company_ids = []
        
        for company in companies:
            if company.embedding:
                embeddings.append(company.embedding)
                company_ids.append(company.id)
        
        if len(embeddings) < self.config.min_cluster_size:
            logger.warning("Not enough embeddings for clustering")
            return {}
        
        # Determine optimal number of clusters
        if n_clusters is None:
            n_clusters = self._estimate_optimal_clusters(embeddings)
        
        # Perform K-means clustering
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Group companies by cluster
            embedding_clusters = defaultdict(list)
            for company_id, cluster_label in zip(company_ids, cluster_labels):
                cluster_name = f"embedding_cluster_{cluster_label}"
                embedding_clusters[cluster_name].append(company_id)
            
            logger.info(f"Embedding clustering created {len(embedding_clusters)} clusters")
            return dict(embedding_clusters)
            
        except Exception as e:
            logger.error(f"Embedding clustering failed: {e}")
            return {}
    
    def _merge_clustering_results(self, companies: List[CompanyData], 
                                 industry_clusters: Dict[str, List[str]], 
                                 embedding_clusters: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge industry and embedding clustering results"""
        
        # Create company lookup
        company_lookup = {comp.id: comp for comp in companies}
        
        # Start with industry clusters as base
        merged_clusters = {}
        
        for industry_name, company_ids in industry_clusters.items():
            if len(company_ids) >= self.config.min_cluster_size:
                # Use industry name as cluster name
                cluster_name = self._generate_sector_name(industry_name, company_ids, company_lookup)
                merged_clusters[cluster_name] = company_ids
            else:
                # Small industry clusters - try to merge with similar ones
                best_match = self._find_best_cluster_match(
                    company_ids, merged_clusters, company_lookup
                )
                
                if best_match:
                    merged_clusters[best_match].extend(company_ids)
                else:
                    # Create new cluster if no good match
                    cluster_name = self._generate_sector_name(industry_name, company_ids, company_lookup)
                    merged_clusters[cluster_name] = company_ids
        
        # Refine clusters using embedding similarity
        refined_clusters = self._refine_clusters_with_embeddings(
            merged_clusters, company_lookup
        )
        
        return refined_clusters
    
    def _create_sector_cluster(self, cluster_name: str, company_ids: List[str], 
                              companies: List[CompanyData]) -> SectorCluster:
        """Create a SectorCluster object with metadata"""
        
        # Get company objects
        cluster_companies = [comp for comp in companies if comp.id in company_ids]
        
        # Analyze common patterns
        common_pain_points = self._find_common_patterns(
            [comp.pain_points for comp in cluster_companies]
        )
        
        common_technologies = self._find_common_patterns(
            [comp.tech_stack for comp in cluster_companies]
        )
        
        # Determine average company size
        company_sizes = [comp.company_size for comp in cluster_companies if comp.company_size]
        size_counter = Counter(company_sizes)
        average_company_size = size_counter.most_common(1)[0][0] if size_counter else "unknown"
        
        # Calculate centroid embedding
        embeddings = [comp.embedding for comp in cluster_companies if comp.embedding]
        centroid_embedding = None
        if embeddings:
            centroid_embedding = np.mean(embeddings, axis=0).tolist()
        
        return SectorCluster(
            name=cluster_name,
            companies=company_ids,
            common_pain_points=common_pain_points,
            common_technologies=common_technologies,
            average_company_size=average_company_size,
            centroid_embedding=centroid_embedding,
            similarity_threshold=self.config.similarity_threshold
        )
    
    def _normalize_industry_name(self, industry: str) -> str:
        """Normalize industry names for better clustering"""
        industry_mappings = {
            'healthcare': ['health', 'medical', 'clinical', 'hospital'],
            'fintech': ['financial', 'banking', 'payment', 'finance'],
            'saas': ['software', 'platform', 'cloud', 'api'],
            'ecommerce': ['commerce', 'retail', 'shop', 'marketplace'],
            'education': ['learning', 'school', 'university', 'course'],
            'manufacturing': ['production', 'factory', 'industrial'],
            'marketing': ['advertising', 'agency', 'seo', 'campaign'],
            'logistics': ['shipping', 'delivery', 'transport', 'supply']
        }
        
        industry_lower = industry.lower()
        
        for normalized_name, keywords in industry_mappings.items():
            if any(keyword in industry_lower for keyword in keywords):
                return normalized_name
        
        return industry_lower
    
    def _estimate_optimal_clusters(self, embeddings: List[List[float]], max_clusters: int = 15) -> int:
        """Estimate optimal number of clusters using elbow method"""
        if len(embeddings) < 6:
            return min(2, len(embeddings) - 1)
        
        max_k = min(max_clusters, len(embeddings) // 2)
        inertias = []
        
        for k in range(2, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=5)
                kmeans.fit(embeddings)
                inertias.append(kmeans.inertia_)
            except:
                break
        
        if not inertias:
            return 3  # Default fallback
        
        # Find elbow point (simplified)
        if len(inertias) >= 3:
            diffs = np.diff(inertias)
            second_diffs = np.diff(diffs)
            
            if len(second_diffs) > 0:
                elbow_point = np.argmax(second_diffs) + 2  # +2 because we started from k=2
                return min(elbow_point, max_k)
        
        # Fallback: use square root heuristic
        return max(2, int(np.sqrt(len(embeddings) / 2)))
    
    def _generate_sector_name(self, base_name: str, company_ids: List[str], 
                             company_lookup: Dict[str, CompanyData]) -> str:
        """Generate a descriptive sector name"""
        
        # Get companies in cluster
        companies = [company_lookup[cid] for cid in company_ids if cid in company_lookup]
        
        # Analyze common characteristics
        business_models = [comp.business_model for comp in companies if comp.business_model]
        company_sizes = [comp.company_size for comp in companies if comp.company_size]
        
        # Build sector name
        sector_parts = [base_name.replace('_', ' ').title()]
        
        # Add business model if consistent
        if business_models:
            model_counter = Counter(business_models)
            dominant_model = model_counter.most_common(1)[0]
            if dominant_model[1] > len(companies) * 0.7:  # 70% threshold
                sector_parts.append(dominant_model[0])
        
        # Add size indicator if consistent
        if company_sizes:
            size_counter = Counter(company_sizes)
            dominant_size = size_counter.most_common(1)[0]
            if dominant_size[1] > len(companies) * 0.7:  # 70% threshold
                if dominant_size[0] in ['startup', 'enterprise']:
                    sector_parts.append(dominant_size[0].title())
        
        return ' '.join(sector_parts)
    
    def _find_best_cluster_match(self, company_ids: List[str], 
                                existing_clusters: Dict[str, List[str]], 
                                company_lookup: Dict[str, CompanyData]) -> str:
        """Find the best existing cluster to merge small clusters into"""
        
        if not existing_clusters:
            return None
        
        # Get companies to match
        companies_to_match = [company_lookup[cid] for cid in company_ids if cid in company_lookup]
        
        best_match = None
        best_similarity = 0.0
        
        for cluster_name, cluster_company_ids in existing_clusters.items():
            # Calculate similarity between clusters
            cluster_companies = [company_lookup[cid] for cid in cluster_company_ids if cid in company_lookup]
            
            similarity = self._calculate_cluster_similarity(companies_to_match, cluster_companies)
            
            if similarity > best_similarity and similarity > 0.5:  # Minimum similarity threshold
                best_similarity = similarity
                best_match = cluster_name
        
        return best_match
    
    def _calculate_cluster_similarity(self, cluster_a: List[CompanyData], 
                                    cluster_b: List[CompanyData]) -> float:
        """Calculate similarity between two clusters of companies"""
        
        # Industry similarity
        industries_a = set(comp.industry for comp in cluster_a if comp.industry)
        industries_b = set(comp.industry for comp in cluster_b if comp.industry)
        
        industry_similarity = 0.0
        if industries_a and industries_b:
            industry_overlap = len(industries_a.intersection(industries_b))
            industry_union = len(industries_a.union(industries_b))
            industry_similarity = industry_overlap / industry_union if industry_union > 0 else 0.0
        
        # Technology similarity
        tech_a = set()
        tech_b = set()
        
        for comp in cluster_a:
            tech_a.update(comp.tech_stack)
        
        for comp in cluster_b:
            tech_b.update(comp.tech_stack)
        
        tech_similarity = 0.0
        if tech_a and tech_b:
            tech_overlap = len(tech_a.intersection(tech_b))
            tech_union = len(tech_a.union(tech_b))
            tech_similarity = tech_overlap / tech_union if tech_union > 0 else 0.0
        
        # Weighted average
        return (industry_similarity * 0.6) + (tech_similarity * 0.4)
    
    def _refine_clusters_with_embeddings(self, clusters: Dict[str, List[str]], 
                                        company_lookup: Dict[str, CompanyData]) -> Dict[str, List[str]]:
        """Refine clusters using embedding similarity"""
        
        refined_clusters = {}
        
        for cluster_name, company_ids in clusters.items():
            companies = [company_lookup[cid] for cid in company_ids if cid in company_lookup]
            
            # Check internal cluster cohesion
            cohesion = self._calculate_cluster_cohesion(companies)
            
            if cohesion > 0.6:  # Good cohesion
                refined_clusters[cluster_name] = company_ids
            else:
                # Try to split cluster
                sub_clusters = self._split_cluster_by_embeddings(companies)
                
                for i, sub_cluster in enumerate(sub_clusters):
                    if len(sub_cluster) >= self.config.min_cluster_size:
                        sub_cluster_name = f"{cluster_name}_sub_{i+1}"
                        refined_clusters[sub_cluster_name] = [comp.id for comp in sub_cluster]
        
        return refined_clusters
    
    def _calculate_cluster_cohesion(self, companies: List[CompanyData]) -> float:
        """Calculate how cohesive a cluster is based on embeddings"""
        
        embeddings = [comp.embedding for comp in companies if comp.embedding]
        
        if len(embeddings) < 2:
            return 1.0
        
        # Calculate average pairwise similarity
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _split_cluster_by_embeddings(self, companies: List[CompanyData]) -> List[List[CompanyData]]:
        """Split a cluster into sub-clusters using embeddings"""
        
        embeddings = []
        valid_companies = []
        
        for company in companies:
            if company.embedding:
                embeddings.append(company.embedding)
                valid_companies.append(company)
        
        if len(embeddings) < 4:  # Too small to split meaningfully
            return [companies]
        
        try:
            # Use 2-means clustering to split
            kmeans = KMeans(n_clusters=2, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Group companies by sub-cluster
            sub_clusters = [[], []]
            for company, label in zip(valid_companies, cluster_labels):
                sub_clusters[label].append(company)
            
            # Add companies without embeddings to the larger sub-cluster
            companies_without_embeddings = [comp for comp in companies if not comp.embedding]
            if companies_without_embeddings:
                larger_cluster_idx = 0 if len(sub_clusters[0]) > len(sub_clusters[1]) else 1
                sub_clusters[larger_cluster_idx].extend(companies_without_embeddings)
            
            return [cluster for cluster in sub_clusters if cluster]
            
        except Exception as e:
            logger.warning(f"Failed to split cluster: {e}")
            return [companies]
    
    def _find_common_patterns(self, item_lists: List[List[str]], min_frequency: float = 0.3) -> List[str]:
        """Find common patterns across multiple lists"""
        
        # Flatten all items and count frequencies
        all_items = []
        total_lists = len([lst for lst in item_lists if lst])  # Non-empty lists
        
        if total_lists == 0:
            return []
        
        for item_list in item_lists:
            if item_list:
                all_items.extend(item_list)
        
        item_counter = Counter(all_items)
        
        # Return items that appear in at least min_frequency of lists
        min_count = max(1, int(total_lists * min_frequency))
        common_items = [item for item, count in item_counter.items() if count >= min_count]
        
        # Sort by frequency and return top items
        return sorted(common_items, key=lambda x: item_counter[x], reverse=True)[:5]