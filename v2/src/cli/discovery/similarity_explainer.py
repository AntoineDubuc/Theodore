"""
Similarity Explainer for Theodore CLI.

Provides transparent similarity scoring with factor-based explanations.
"""

from typing import Dict, Any, List
from src.core.domain.entities.company import Company


class SimilarityExplainer:
    """Generates explanations for similarity scores."""
    
    def __init__(self):
        self.similarity_factors = [
            'business_model_similarity',
            'industry_alignment', 
            'company_size_match',
            'technology_stack_overlap',
            'market_segment_similarity',
            'geographic_proximity'
        ]
    
    async def explain_similarity(
        self,
        target_company: str,
        similar_company: Company,
        similarity_score: float
    ) -> Dict[str, Any]:
        """
        Generate detailed similarity explanation.
        
        Args:
            target_company: Name of target company
            similar_company: Similar company object
            similarity_score: Overall similarity score
            
        Returns:
            Dictionary with detailed explanation
        """
        
        # Generate factor scores (simplified implementation)
        factors = self._calculate_factor_scores(target_company, similar_company, similarity_score)
        
        # Generate natural language explanation
        explanation_text = self._generate_explanation_text(target_company, similar_company, factors)
        
        # Calculate confidence
        confidence = self._calculate_explanation_confidence(factors, similarity_score)
        
        return {
            'overall_score': similarity_score,
            'factors': factors,
            'explanation': explanation_text,
            'confidence': confidence,
            'target_company': target_company,
            'similar_company': similar_company.name
        }
    
    def _calculate_factor_scores(
        self,
        target_company: str,
        similar_company: Company,
        overall_score: float
    ) -> Dict[str, float]:
        """Calculate individual factor scores (simplified implementation)."""
        
        # This is a simplified implementation
        # In a real system, this would analyze actual company data
        
        base_variance = 0.2
        factors = {}
        
        for i, factor in enumerate(self.similarity_factors):
            # Create some variation around the overall score
            variance = (i % 3 - 1) * base_variance * 0.3
            factor_score = min(1.0, max(0.0, overall_score + variance))
            factors[factor] = factor_score
        
        return factors
    
    def _generate_explanation_text(
        self,
        target_company: str,
        similar_company: Company,
        factors: Dict[str, float]
    ) -> str:
        """Generate natural language explanation."""
        
        # Find top factors
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
        
        explanation_parts = []
        explanation_parts.append(f"{similar_company.name} shows similarity to {target_company}")
        
        if top_factors:
            explanation_parts.append("based on")
            factor_descriptions = []
            
            for factor, score in top_factors:
                if score > 0.7:
                    strength = "strong"
                elif score > 0.5:
                    strength = "moderate" 
                else:
                    strength = "weak"
                
                factor_name = factor.replace('_', ' ')
                factor_descriptions.append(f"{strength} {factor_name}")
            
            explanation_parts.append(", ".join(factor_descriptions))
        
        explanation_parts.append(".")
        
        if similar_company.description:
            explanation_parts.append(f" {similar_company.description[:100]}...")
        
        return " ".join(explanation_parts)
    
    def _calculate_explanation_confidence(
        self,
        factors: Dict[str, float],
        overall_score: float
    ) -> float:
        """Calculate confidence in the explanation."""
        
        # Base confidence on consistency of factors
        factor_values = list(factors.values())
        if not factor_values:
            return 0.5
        
        # Calculate standard deviation of factors
        mean_factor = sum(factor_values) / len(factor_values)
        variance = sum((x - mean_factor) ** 2 for x in factor_values) / len(factor_values)
        
        # Lower variance means more consistent factors, higher confidence
        consistency_score = max(0.0, 1.0 - variance)
        
        # Higher overall score generally means higher confidence
        score_confidence = overall_score
        
        # Combine factors
        confidence = (consistency_score * 0.6 + score_confidence * 0.4)
        
        return min(1.0, max(0.0, confidence))