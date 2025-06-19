"""
SaaS Business Model Classifier
Analyzes company data and classifies using 59-category taxonomy
"""

import logging
import re
from datetime import datetime
from typing import Optional

from models import CompanyData, ClassificationResult, SaaSCategory
from .classification_prompts import get_classification_prompt, CLASSIFICATION_TAXONOMY

logger = logging.getLogger(__name__)


class SaaSBusinessModelClassifier:
    """
    Analyzes company data and classifies business model using 59-category taxonomy
    """
    
    def __init__(self, ai_client):
        """
        Initialize classifier
        
        Args:
            ai_client: AI client for LLM inference (Bedrock, Gemini, etc.)
        """
        self.ai_client = ai_client
        self.model_version = "v1.0"
        self.taxonomy = self._load_classification_taxonomy()
        
        logger.info("🏷️ SaaS Business Model Classifier initialized")
    
    def _load_classification_taxonomy(self) -> dict:
        """Load the 59-category taxonomy for validation"""
        taxonomy = {}
        
        # Add all SaaS categories
        saas_categories = [
            "AdTech", "AssetManagement", "Billing", "Bio/LS", "CollabTech",
            "Data/BI/Analytics", "DevOps/CloudInfra", "E-commerce & Retail",
            "EdTech", "Enertech", "FinTech", "GovTech", "HRTech", "HealthTech",
            "Identity & Access Management (IAM)", "InsureTech", "LawTech", 
            "LeisureTech", "Manufacturing/AgTech/IoT", "Martech & CRM", 
            "MediaTech", "PropTech", "Risk/Audit/Governance", 
            "Social / Community / Non Profit", "Supply Chain & Logistics", "TranspoTech"
        ]
        
        # Add all Non-SaaS categories
        non_saas_categories = [
            "Advertising & Media Services", "Biopharma R&D", "Combo HW & SW",
            "Education", "Energy", "Financial Services", "Healthcare Services",
            "Industry Consulting Services", "Insurance", "IT Consulting Services",
            "Logistics Services", "Manufacturing", "Non-Profit", "Retail", 
            "Sports", "Travel & Leisure", "Wholesale Distribution & Supply"
        ]
        
        for category in saas_categories:
            taxonomy[category] = {"type": "saas", "valid": True}
        
        for category in non_saas_categories:
            taxonomy[category] = {"type": "non_saas", "valid": True}
            
        taxonomy["Unclassified"] = {"type": "unclassified", "valid": True}
        
        return taxonomy
    
    def classify_company(self, company_data: CompanyData) -> ClassificationResult:
        """
        Main classification method
        
        Args:
            company_data: CompanyData object with business intelligence
            
        Returns:
            ClassificationResult with category, confidence, and justification
        """
        try:
            logger.info(f"🔍 Classifying business model for: {company_data.name}")
            
            # Prepare input for classification
            classification_input = self._prepare_classification_input(company_data)
            
            # Get LLM classification
            response = self.ai_client.generate_response(classification_input)
            
            # Parse response into structured result
            result = self._parse_classification_response(response)
            
            # Validate classification
            if self._validate_classification(result):
                logger.info(f"✅ Classification complete: {result.category.value} ({result.confidence:.2f})")
                return result
            else:
                logger.warning(f"⚠️ Low quality classification, using fallback")
                return self._create_fallback_classification(company_data)
                
        except Exception as e:
            logger.error(f"❌ Classification failed for {company_data.name}: {e}")
            return self._create_error_classification(str(e))
    
    def _prepare_classification_input(self, company_data: CompanyData) -> str:
        """
        Extract and format relevant content for classification
        
        Args:
            company_data: Company data to analyze
            
        Returns:
            Formatted prompt string for LLM
        """
        # Use the prompt template with company data
        prompt = get_classification_prompt(company_data)
        
        logger.debug(f"📝 Prepared classification input for {company_data.name}")
        return prompt
    
    def _parse_classification_response(self, response: str) -> ClassificationResult:
        """
        Parse LLM response into structured ClassificationResult
        
        Args:
            response: Raw LLM response text
            
        Returns:
            ClassificationResult object
        """
        try:
            # Extract classification using regex patterns
            classification_match = re.search(r"Classification:\s*(.+)", response, re.IGNORECASE)
            confidence_match = re.search(r"Confidence:\s*([\d.]+)", response, re.IGNORECASE)
            justification_match = re.search(r"Justification:\s*(.+)", response, re.IGNORECASE)
            is_saas_match = re.search(r"Is_SaaS:\s*(true|false)", response, re.IGNORECASE)
            
            if not all([classification_match, confidence_match, justification_match, is_saas_match]):
                raise ValueError("Missing required fields in LLM response")
            
            # Extract values
            category_name = classification_match.group(1).strip()
            confidence = float(confidence_match.group(1))
            justification = justification_match.group(1).strip()
            is_saas = is_saas_match.group(1).lower() == "true"
            
            # Validate category exists in taxonomy
            try:
                category = SaaSCategory(category_name)
            except ValueError:
                logger.warning(f"Unknown category '{category_name}', using Unclassified")
                category = SaaSCategory.UNCLASSIFIED
                confidence = 0.0
                justification = f"Unknown category '{category_name}' returned by classifier"
            
            # Create result
            result = ClassificationResult(
                category=category,
                confidence=confidence,
                justification=justification,
                model_version=self.model_version,
                timestamp=datetime.now(),
                is_saas=is_saas
            )
            
            logger.debug(f"📊 Parsed classification: {category.value} ({confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to parse classification response: {e}")
            logger.debug(f"Raw response: {response}")
            
            return ClassificationResult(
                category=SaaSCategory.UNCLASSIFIED,
                confidence=0.0,
                justification=f"Response parsing failed: {str(e)}",
                model_version=self.model_version,
                timestamp=datetime.now(),
                is_saas=False
            )
    
    def _validate_classification(self, result: ClassificationResult) -> bool:
        """
        Validate classification result quality
        
        Args:
            result: Classification result to validate
            
        Returns:
            True if classification meets quality standards
        """
        # Check confidence threshold
        if result.confidence < 0.3:
            return False
        
        # Check justification length and quality
        if len(result.justification) < 10:
            return False
        
        # Check if category is valid
        if result.category == SaaSCategory.UNCLASSIFIED and result.confidence > 0.5:
            return False
        
        return True
    
    def _create_fallback_classification(self, company_data: CompanyData) -> ClassificationResult:
        """
        Create fallback classification when primary method fails quality check
        
        Args:
            company_data: Company data for context
            
        Returns:
            Basic classification result
        """
        # Simple heuristic: check for SaaS indicators in company description
        business_intel = (company_data.company_description or company_data.ai_summary or "").lower()
        
        is_saas = any(indicator in business_intel for indicator in [
            "saas", "software as a service", "subscription", "platform", 
            "api", "cloud", "dashboard", "analytics", "automation"
        ])
        
        if is_saas:
            category = SaaSCategory.DATA_BI_ANALYTICS  # Generic SaaS category
            justification = "Fallback classification based on SaaS indicators in company description"
        else:
            category = SaaSCategory.UNCLASSIFIED
            justification = "Insufficient information for reliable classification"
        
        return ClassificationResult(
            category=category,
            confidence=0.4,  # Low confidence for fallback
            justification=justification,
            model_version=self.model_version,
            timestamp=datetime.now(),
            is_saas=is_saas
        )
    
    def _create_error_classification(self, error_message: str) -> ClassificationResult:
        """
        Create error classification when classification completely fails
        
        Args:
            error_message: Error description
            
        Returns:
            Error classification result
        """
        return ClassificationResult(
            category=SaaSCategory.UNCLASSIFIED,
            confidence=0.0,
            justification=f"Classification error: {error_message}",
            model_version=self.model_version,
            timestamp=datetime.now(),
            is_saas=False
        )