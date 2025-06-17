"""
Advanced similarity calculation engine for sales-focused company matching
"""

import logging
from typing import Dict, List, Tuple, Optional
from src.models import CompanyData

logger = logging.getLogger(__name__)

class SimilarityEngine:
    """Calculate similarity between companies based on sales-relevant metrics"""
    
    # Similarity weights (must sum to 1.0)
    WEIGHTS = {
        'company_stage': 0.30,      # Most important for sales approach
        'tech_sophistication': 0.25, # Affects technical depth needed
        'industry': 0.20,           # Domain expertise required
        'business_model_type': 0.15, # Budget and procurement differences
        'geographic_scope': 0.10    # Regional considerations
    }
    
    # Similarity matrices for each dimension
    STAGE_SIMILARITY = {
        ('startup', 'startup'): 1.0,
        ('startup', 'growth'): 0.6,
        ('startup', 'enterprise'): 0.2,
        ('growth', 'growth'): 1.0,
        ('growth', 'enterprise'): 0.7,
        ('enterprise', 'enterprise'): 1.0
    }
    
    TECH_SIMILARITY = {
        ('high', 'high'): 1.0,
        ('high', 'medium'): 0.5,
        ('high', 'low'): 0.2,
        ('medium', 'medium'): 1.0,
        ('medium', 'low'): 0.6,
        ('low', 'low'): 1.0
    }
    
    BUSINESS_MODEL_SIMILARITY = {
        ('saas', 'saas'): 1.0,
        ('saas', 'services'): 0.4,
        ('saas', 'marketplace'): 0.3,
        ('saas', 'ecommerce'): 0.2,
        ('services', 'services'): 1.0,
        ('services', 'marketplace'): 0.3,
        ('marketplace', 'marketplace'): 1.0,
        ('ecommerce', 'ecommerce'): 1.0
    }
    
    GEO_SIMILARITY = {
        ('local', 'local'): 1.0,
        ('local', 'regional'): 0.6,
        ('local', 'global'): 0.3,
        ('regional', 'regional'): 1.0,
        ('regional', 'global'): 0.8,
        ('global', 'global'): 1.0
    }
    
    def calculate_similarity(self, company_a: CompanyData, company_b: CompanyData) -> Dict:
        """Calculate overall similarity score between two companies"""
        
        similarities = {}
        confidences = {}
        
        # Calculate each dimension similarity
        similarities['company_stage'] = self._calculate_stage_similarity(company_a, company_b)
        similarities['tech_sophistication'] = self._calculate_tech_similarity(company_a, company_b)
        similarities['industry'] = self._calculate_industry_similarity(company_a, company_b)
        similarities['business_model_type'] = self._calculate_business_model_similarity(company_a, company_b)
        similarities['geographic_scope'] = self._calculate_geo_similarity(company_a, company_b)
        
        # Calculate confidence scores (handle None values)
        def safe_confidence(company, field, default=0.5):
            value = getattr(company, field, default)
            return value if value is not None else default
        
        confidences['company_stage'] = min(
            safe_confidence(company_a, 'stage_confidence'),
            safe_confidence(company_b, 'stage_confidence')
        )
        confidences['tech_sophistication'] = min(
            safe_confidence(company_a, 'tech_confidence'),
            safe_confidence(company_b, 'tech_confidence')
        )
        confidences['industry'] = min(
            safe_confidence(company_a, 'industry_confidence'),
            safe_confidence(company_b, 'industry_confidence')
        )
        
        # Calculate weighted overall similarity
        overall_similarity = sum(
            similarities[dim] * self.WEIGHTS[dim] 
            for dim in similarities.keys()
        )
        
        # Calculate overall confidence
        overall_confidence = sum(
            confidences.get(dim, 0.5) * self.WEIGHTS[dim]
            for dim in similarities.keys()
        )
        
        return {
            'overall_similarity': overall_similarity,
            'overall_confidence': overall_confidence,
            'dimension_similarities': similarities,
            'dimension_confidences': confidences,
            'explanation': self._generate_explanation(similarities, company_a, company_b)
        }
    
    def _calculate_stage_similarity(self, company_a: CompanyData, company_b: CompanyData) -> float:
        """Calculate similarity based on company stage"""
        stage_a = getattr(company_a, 'company_stage', 'unknown')
        stage_b = getattr(company_b, 'company_stage', 'unknown')
        
        if stage_a == 'unknown' or stage_b == 'unknown':
            return 0.5  # Default similarity for unknown
        
        # Use symmetric lookup
        key = tuple(sorted([stage_a, stage_b]))
        return self.STAGE_SIMILARITY.get(key, self.STAGE_SIMILARITY.get((stage_a, stage_b), 0.0))
    
    def _calculate_tech_similarity(self, company_a: CompanyData, company_b: CompanyData) -> float:
        """Calculate similarity based on technical sophistication"""
        tech_a = getattr(company_a, 'tech_sophistication', 'unknown')
        tech_b = getattr(company_b, 'tech_sophistication', 'unknown')
        
        if tech_a == 'unknown' or tech_b == 'unknown':
            return 0.5
        
        key = tuple(sorted([tech_a, tech_b]))
        return self.TECH_SIMILARITY.get(key, self.TECH_SIMILARITY.get((tech_a, tech_b), 0.0))
    
    def _calculate_industry_similarity(self, company_a: CompanyData, company_b: CompanyData) -> float:
        """Calculate similarity based on industry"""
        industry_a = getattr(company_a, 'industry', '').lower()
        industry_b = getattr(company_b, 'industry', '').lower()
        
        if not industry_a or not industry_b:
            return 0.5
        
        # Exact match
        if industry_a == industry_b:
            return 1.0
        
        # Partial match for related industries
        related_industries = {
            'ai': ['artificial intelligence', 'machine learning', 'ai'],
            'fintech': ['finance', 'financial', 'fintech', 'payments'],
            'healthcare': ['health', 'medical', 'healthcare', 'biotech'],
            'saas': ['software', 'saas', 'technology', 'tech']
        }
        
        for category, keywords in related_industries.items():
            if any(keyword in industry_a for keyword in keywords) and \
               any(keyword in industry_b for keyword in keywords):
                return 0.7
        
        return 0.1  # Different industries
    
    def _calculate_business_model_similarity(self, company_a: CompanyData, company_b: CompanyData) -> float:
        """Calculate similarity based on business model"""
        model_a = getattr(company_a, 'business_model_type', 'unknown')
        model_b = getattr(company_b, 'business_model_type', 'unknown')
        
        if model_a == 'unknown' or model_b == 'unknown':
            return 0.5
        
        key = tuple(sorted([model_a, model_b]))
        return self.BUSINESS_MODEL_SIMILARITY.get(key, self.BUSINESS_MODEL_SIMILARITY.get((model_a, model_b), 0.0))
    
    def _calculate_geo_similarity(self, company_a: CompanyData, company_b: CompanyData) -> float:
        """Calculate similarity based on geographic scope"""
        geo_a = getattr(company_a, 'geographic_scope', 'unknown')
        geo_b = getattr(company_b, 'geographic_scope', 'unknown')
        
        if geo_a == 'unknown' or geo_b == 'unknown':
            return 0.5
        
        key = tuple(sorted([geo_a, geo_b]))
        return self.GEO_SIMILARITY.get(key, self.GEO_SIMILARITY.get((geo_a, geo_b), 0.0))
    
    def _generate_explanation(self, similarities: Dict, company_a: CompanyData, company_b: CompanyData) -> str:
        """Generate human-readable explanation of similarity"""
        explanations = []
        
        for dimension, score in similarities.items():
            if score > 0.8:
                explanations.append(f"Very similar {dimension.replace('_', ' ')}")
            elif score > 0.6:
                explanations.append(f"Somewhat similar {dimension.replace('_', ' ')}")
            elif score < 0.3:
                explanations.append(f"Different {dimension.replace('_', ' ')}")
        
        return "; ".join(explanations)
    
    def find_similar_companies(self, target_company: CompanyData, 
                             companies: List[CompanyData], 
                             threshold: float = 0.7,
                             limit: int = 10) -> List[Tuple[CompanyData, Dict]]:
        """Find most similar companies to target"""
        
        similarities = []
        
        for company in companies:
            if company.id == target_company.id:
                continue  # Skip self
            
            similarity_result = self.calculate_similarity(target_company, company)
            
            if similarity_result['overall_similarity'] >= threshold:
                similarities.append((company, similarity_result))
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1]['overall_similarity'], reverse=True)
        
        return similarities[:limit]