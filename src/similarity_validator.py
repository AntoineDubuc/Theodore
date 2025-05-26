"""
Similarity validation engine for comparing companies across multiple dimensions
"""

import logging
import re
import math
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.bedrock_client import BedrockClient
from src.models import CompanyData

logger = logging.getLogger(__name__)


class SimilarityScore(BaseModel):
    """Individual similarity score for a specific method"""
    method: str = Field(..., description="Method used for similarity calculation")
    score: float = Field(..., description="Similarity score (0-1)")
    is_similar: bool = Field(..., description="Whether this method considers companies similar")
    details: Dict[str, Any] = Field(default_factory=dict, description="Method-specific details")


class SimilarityResult(BaseModel):
    """Complete similarity analysis result"""
    company_a_name: str = Field(..., description="First company name")
    company_b_name: str = Field(..., description="Second company name")
    is_similar: bool = Field(..., description="Final similarity decision")
    confidence: float = Field(..., description="Confidence in similarity decision (0-1)")
    overall_score: float = Field(..., description="Weighted composite similarity score")
    methods_used: List[str] = Field(default_factory=list, description="Methods used in analysis")
    method_scores: List[SimilarityScore] = Field(default_factory=list, description="Individual method scores")
    reasoning: List[str] = Field(default_factory=list, description="Human-readable reasons")
    votes: List[str] = Field(default_factory=list, description="Methods that voted 'similar'")
    analyzed_at: datetime = Field(default_factory=datetime.now)


class SimilarityValidator:
    """Multi-method similarity validation engine"""
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        self.bedrock_client = bedrock_client or BedrockClient()
        
        # Similarity thresholds for each method
        self.thresholds = {
            'structured': 0.6,
            'embedding': 0.75,
            'llm_judge': 7.0  # Out of 10
        }
        
        # Weights for composite scoring
        self.weights = {
            'structured': 0.4,
            'embedding': 0.4, 
            'llm_judge': 0.2
        }
    
    def validate_similarity(self, 
                          company_a: CompanyData, 
                          company_b: CompanyData,
                          use_llm: bool = True,
                          require_votes: int = 2) -> SimilarityResult:
        """
        Validate similarity between two companies using multiple methods
        
        Args:
            company_a: First company to compare
            company_b: Second company to compare
            use_llm: Whether to use expensive LLM judge
            require_votes: Minimum number of methods that must agree
            
        Returns:
            SimilarityResult with comprehensive analysis
        """
        logger.info(f"Validating similarity: {company_a.name} vs {company_b.name}")
        
        result = SimilarityResult(
            company_a_name=company_a.name,
            company_b_name=company_b.name,
            is_similar=False,
            confidence=0.0,
            overall_score=0.0
        )
        
        method_scores = []
        votes = []
        
        # Method 1: Structured data comparison
        try:
            struct_score = self._structured_comparison(company_a, company_b)
            is_similar_struct = struct_score.score >= self.thresholds['structured']
            
            method_scores.append(struct_score)
            result.methods_used.append('structured')
            
            if is_similar_struct:
                votes.append('structured')
                result.reasoning.append(f"Structured similarity: {struct_score.score:.2f}")
                
        except Exception as e:
            logger.error(f"Structured comparison failed: {e}")
        
        # Method 2: Embedding similarity
        try:
            emb_score = self._embedding_similarity(company_a, company_b)
            is_similar_emb = emb_score.score >= self.thresholds['embedding']
            
            method_scores.append(emb_score)
            result.methods_used.append('embedding')
            
            if is_similar_emb:
                votes.append('embedding')
                result.reasoning.append(f"Embedding similarity: {emb_score.score:.2f}")
                
        except Exception as e:
            logger.error(f"Embedding comparison failed: {e}")
        
        # Method 3: LLM judge (conditional)
        if use_llm and (len(votes) > 0 or len(method_scores) < 2):
            try:
                llm_score = self._llm_judge_similarity(company_a, company_b)
                is_similar_llm = llm_score.score >= self.thresholds['llm_judge']
                
                method_scores.append(llm_score)
                result.methods_used.append('llm_judge')
                
                if is_similar_llm:
                    votes.append('llm_judge')
                    reason = llm_score.details.get('reasoning', 'LLM judge agrees')
                    result.reasoning.append(f"LLM judge: {reason}")
                    
            except Exception as e:
                logger.error(f"LLM judge failed: {e}")
        
        # Store results
        result.method_scores = method_scores
        result.votes = votes
        
        # Calculate composite score
        result.overall_score = self._calculate_composite_score(method_scores)
        
        # Make final decision
        result.is_similar = len(votes) >= require_votes
        result.confidence = len(votes) / max(len(result.methods_used), 1)
        
        logger.info(f"Similarity result: {result.is_similar} (confidence: {result.confidence:.2f})")
        return result
    
    def _structured_comparison(self, company_a: CompanyData, company_b: CompanyData) -> SimilarityScore:
        """
        Compare companies based on structured field data
        """
        score = 0.0
        details = {}
        
        # Industry match (40% weight)
        if company_a.industry and company_b.industry:
            if company_a.industry.lower().strip() == company_b.industry.lower().strip():
                score += 0.4
                details['industry_exact_match'] = True
            else:
                # Check for partial industry overlap
                words_a = set(company_a.industry.lower().split())
                words_b = set(company_b.industry.lower().split())
                overlap = len(words_a & words_b)
                if overlap > 0:
                    score += 0.2
                    details['industry_partial_match'] = overlap
        
        # Business model match (30% weight)
        if company_a.business_model and company_b.business_model:
            if company_a.business_model.lower().strip() == company_b.business_model.lower().strip():
                score += 0.3
                details['business_model_match'] = True
        
        # Tech stack overlap (20% weight)
        if company_a.tech_stack and company_b.tech_stack:
            tech_a = set([tech.lower().strip() for tech in company_a.tech_stack])
            tech_b = set([tech.lower().strip() for tech in company_b.tech_stack])
            
            if tech_a and tech_b:
                overlap = len(tech_a & tech_b)
                union = len(tech_a | tech_b)
                jaccard = overlap / union if union > 0 else 0
                score += jaccard * 0.2
                details['tech_overlap_count'] = overlap
                details['tech_jaccard_similarity'] = jaccard
        
        # Company size compatibility (10% weight)
        if company_a.company_size and company_b.company_size:
            if company_a.company_size.lower() == company_b.company_size.lower():
                score += 0.1
                details['size_match'] = True
        
        # Employee count compatibility (if available)
        if hasattr(company_a, 'employee_count_range') and hasattr(company_b, 'employee_count_range'):
            if company_a.employee_count_range and company_b.employee_count_range:
                size_a = self._parse_employee_count(company_a.employee_count_range)
                size_b = self._parse_employee_count(company_b.employee_count_range)
                
                if size_a and size_b:
                    ratio = max(size_a, size_b) / min(size_a, size_b)
                    if ratio <= 3:  # Within 3x size
                        score += 0.05
                        details['employee_size_compatible'] = True
        
        return SimilarityScore(
            method='structured',
            score=min(score, 1.0),  # Cap at 1.0
            is_similar=score >= self.thresholds['structured'],
            details=details
        )
    
    def _embedding_similarity(self, company_a: CompanyData, company_b: CompanyData) -> SimilarityScore:
        """
        Compare companies using embedding similarity
        """
        # Create text representations
        text_a = self._create_company_text_representation(company_a)
        text_b = self._create_company_text_representation(company_b)
        
        # Get embeddings
        embedding_a = self.bedrock_client.get_embeddings(text_a)
        embedding_b = self.bedrock_client.get_embeddings(text_b)
        
        # Calculate cosine similarity
        similarity = cosine_similarity([embedding_a], [embedding_b])[0][0]
        
        return SimilarityScore(
            method='embedding',
            score=float(similarity),
            is_similar=similarity >= self.thresholds['embedding'],
            details={
                'cosine_similarity': float(similarity),
                'text_a_length': len(text_a),
                'text_b_length': len(text_b)
            }
        )
    
    def _llm_judge_similarity(self, company_a: CompanyData, company_b: CompanyData) -> SimilarityScore:
        """
        Use LLM as judge to evaluate company similarity
        """
        prompt = f"""You are a business analyst comparing two companies for similarity.

Company A:
Name: {company_a.name}
Industry: {company_a.industry or 'Not specified'}
Business Model: {company_a.business_model or 'Not specified'}
Description: {company_a.company_description or 'Not available'}
Key Services: {', '.join(company_a.key_services) if company_a.key_services else 'Not specified'}
Target Market: {company_a.target_market or 'Not specified'}
Location: {company_a.location or 'Not specified'}
Tech Stack: {', '.join(company_a.tech_stack) if company_a.tech_stack else 'Not specified'}

Company B:
Name: {company_b.name}
Industry: {company_b.industry or 'Not specified'}
Business Model: {company_b.business_model or 'Not specified'}
Description: {company_b.company_description or 'Not available'}
Key Services: {', '.join(company_b.key_services) if company_b.key_services else 'Not specified'}
Target Market: {company_b.target_market or 'Not specified'}
Location: {company_b.location or 'Not specified'}
Tech Stack: {', '.join(company_b.tech_stack) if company_b.tech_stack else 'Not specified'}

Rate their similarity on a scale of 0-10 where:
- 0-3: Not similar (different industries/markets)
- 4-6: Somewhat similar (adjacent markets or different approaches)
- 7-8: Similar (direct competitors or close alternatives)
- 9-10: Very similar (almost identical target market and offering)

Consider:
- Do they serve similar customers?
- Do they solve similar problems?
- Are they in the same market segment?
- Would a customer consider both companies?

Respond in this exact format:
SCORE: X/10
REASONING: [brief explanation in one sentence]
SIMILAR: [YES/NO for score 7+]"""

        try:
            response = self.bedrock_client.analyze_content(prompt)
            
            # Parse response
            score_match = re.search(r'SCORE:\\s*(\\d+)/10', response)
            similar_match = re.search(r'SIMILAR:\\s*(YES|NO)', response)
            reasoning_match = re.search(r'REASONING:\\s*(.+?)(?=\\nSIMILAR:|$)', response, re.DOTALL)
            
            if score_match:
                score = int(score_match.group(1))
                is_similar = similar_match.group(1) == 'YES' if similar_match else score >= 7
                reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
                
                return SimilarityScore(
                    method='llm_judge',
                    score=float(score),
                    is_similar=is_similar,
                    details={
                        'reasoning': reasoning,
                        'raw_response': response,
                        'score_out_of_10': score
                    }
                )
            else:
                # Fallback parsing
                return SimilarityScore(
                    method='llm_judge',
                    score=0.0,
                    is_similar=False,
                    details={
                        'error': 'Failed to parse LLM response',
                        'raw_response': response
                    }
                )
                
        except Exception as e:
            return SimilarityScore(
                method='llm_judge',
                score=0.0,
                is_similar=False,
                details={'error': str(e)}
            )
    
    def _create_company_text_representation(self, company: CompanyData) -> str:
        """
        Create a comprehensive text representation of a company for embedding
        """
        parts = []
        
        if company.name:
            parts.append(f"Company: {company.name}")
        if company.industry:
            parts.append(f"Industry: {company.industry}")
        if company.business_model:
            parts.append(f"Business Model: {company.business_model}")
        if company.company_description:
            parts.append(f"Description: {company.company_description}")
        if company.key_services:
            parts.append(f"Services: {', '.join(company.key_services)}")
        if company.target_market:
            parts.append(f"Target Market: {company.target_market}")
        if company.tech_stack:
            parts.append(f"Technology: {', '.join(company.tech_stack)}")
        if company.location:
            parts.append(f"Location: {company.location}")
        
        return " | ".join(parts)
    
    def _parse_employee_count(self, employee_str: str) -> Optional[int]:
        """
        Parse employee count string to approximate number
        """
        if not employee_str:
            return None
        
        # Handle ranges like "50-200", "100+"
        numbers = re.findall(r'\\d+', str(employee_str))
        if numbers:
            if len(numbers) == 1:
                return int(numbers[0])
            else:
                # Take average of range
                return int((int(numbers[0]) + int(numbers[1])) / 2)
        return None
    
    def _calculate_composite_score(self, method_scores: List[SimilarityScore]) -> float:
        """
        Calculate weighted composite similarity score
        """
        if not method_scores:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for score in method_scores:
            weight = self.weights.get(score.method, 0.1)  # Default small weight
            weighted_sum += score.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


def main():
    """Test the similarity validator"""
    pass


if __name__ == "__main__":
    main()