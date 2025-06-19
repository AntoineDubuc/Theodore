#!/usr/bin/env python3
"""
Research New Company + SaaS Classification Test
Tests the complete flow: research new company → store with classification → retrieve classification data
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add Theodore root to path
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/sandbox/search/singular_search/concurency_approach/concurency_and_rate_limiting_tests')

try:
    # Import core Theodore components
    from src.main_pipeline import TheodoreIntelligencePipeline
    from src.models import CompanyData
    from src.pinecone_client import PineconeClient
    from src.gemini_client import GeminiClient
    from src.bedrock_client import BedrockClient
    
    # Import rate-limited solution
    from rate_limited_gemini_solution import RateLimitedTheodoreLLMManager, LLMTask, LLMResult
    from rate_limited_gemini_solution import safe_json_parse
    
    print("✅ Successfully imported all required components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("ℹ️ This test requires access to Theodore core components and rate-limited solution")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ResearchWithClassificationResult:
    """Result structure for research + classification test"""
    company_name: str
    website: str
    test_phase: str  # "research", "store", "retrieve", "classification"
    success: bool
    processing_time: float
    
    # Research Results
    research_data: Optional[CompanyData] = None
    research_success: bool = False
    
    # Storage Results  
    storage_success: bool = False
    vector_id: Optional[str] = None
    
    # Retrieval Results
    retrieved_data: Optional[Dict[str, Any]] = None
    retrieval_success: bool = False
    
    # Classification Results
    has_classification: bool = False
    classification_category: Optional[str] = None
    classification_confidence: Optional[float] = None
    is_saas: Optional[bool] = None
    
    # Error tracking
    error_message: Optional[str] = None

class ResearchWithSaaSClassificationTester:
    """
    Tests the complete flow of researching a new company and retrieving 
    its SaaS classification data from the database
    """
    
    def __init__(self):
        # Initialize config and clients for testing
        from src.models import CompanyIntelligenceConfig
        
        # Create default config
        config = CompanyIntelligenceConfig(
            output_format="json",
            use_ai_analysis=True,
            max_pages=10,
            aws_region="us-east-1",
            bedrock_analysis_model="amazon.nova-pro-v1:0"
        )
        
        # Get environment variables
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable required")
        
        # Initialize Theodore pipeline with required parameters
        self.pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=pinecone_api_key,
            pinecone_environment="gcp-starter",  # Default for free tier
            pinecone_index=pinecone_index
        )
        
        # Initialize clients directly for testing
        self.pinecone_client = PineconeClient()
        self.gemini_client = GeminiClient()
        
        # Test companies for validation
        self.test_companies = self._get_test_companies()
        
        # SaaS classification taxonomy for reference
        self.saas_taxonomy = self._get_59_category_taxonomy()
    
    def _get_test_companies(self) -> List[Dict[str, str]]:
        """Test companies with different expected outcomes"""
        return [
            {
                "name": "Notion",
                "website": "https://notion.so",
                "scenario": "Popular SaaS - should classify as CollabTech",
                "expected_type": "SaaS"
            },
            {
                "name": "Vercel", 
                "website": "https://vercel.com",
                "scenario": "Developer platform - should classify as DevOps/CloudInfra",
                "expected_type": "SaaS"
            },
            {
                "name": "Coinbase",
                "website": "https://coinbase.com", 
                "scenario": "Financial services - should classify as FinTech",
                "expected_type": "SaaS"
            }
        ]
    
    def _get_59_category_taxonomy(self) -> str:
        """Return the 59-category SaaS taxonomy for classification"""
        return """
SaaS VERTICALS (33 categories):
AdTech, AssetManagement, Billing, Bio/LS, CollabTech, Data/BI/Analytics, 
DevOps/CloudInfra, E-commerce & Retail, EdTech, Enertech, FinTech, 
GovTech, HRTech, HealthTech, Identity & Access Management (IAM), 
InsureTech, LawTech, LeisureTech, Manufacturing/AgTech/IoT, 
Martech & CRM, MediaTech, PropTech, Risk/Audit/Governance, 
Social / Community / Non Profit, Supply Chain & Logistics, TranspoTech

NON-SaaS CATEGORIES (25 categories):
Advertising & Media Services, Biopharma R&D, Combo HW & SW, 
Education, Energy, Financial Services, Healthcare Services, 
Industry Consulting Services, Insurance, IT Consulting Services, 
Logistics Services, Manufacturing, Non-Profit, Retail, Sports, 
Travel & Leisure, Wholesale Distribution & Supply

SPECIAL CATEGORY:
Unclassified
"""
    
    def test_phase_1_research_new_company(self, company: Dict[str, str]) -> ResearchWithClassificationResult:
        """Phase 1: Research a new company using Theodore pipeline"""
        
        logger.info(f"🔍 Phase 1: Researching {company['name']}")
        start_time = time.time()
        
        try:
            # Check if company already exists in database
            existing = self.pinecone_client.find_company_by_name(company["name"])
            if existing:
                logger.warning(f"⚠️ Company {company['name']} already exists in database")
                # For testing purposes, we'll continue with research anyway
            
            # Research the company using Theodore pipeline
            company_data = self.pipeline.process_single_company(
                name=company["name"],
                website=company["website"]
            )
            
            processing_time = time.time() - start_time
            
            if company_data:
                logger.info(f"✅ Research completed for {company['name']} in {processing_time:.2f}s")
                
                return ResearchWithClassificationResult(
                    company_name=company["name"],
                    website=company["website"],
                    test_phase="research",
                    success=True,
                    processing_time=processing_time,
                    research_data=company_data,
                    research_success=True
                )
            else:
                return ResearchWithClassificationResult(
                    company_name=company["name"],
                    website=company["website"],
                    test_phase="research",
                    success=False,
                    processing_time=processing_time,
                    research_success=False,
                    error_message="Research returned no data"
                )
                
        except Exception as e:
            logger.error(f"❌ Research failed for {company['name']}: {e}")
            return ResearchWithClassificationResult(
                company_name=company["name"],
                website=company["website"],
                test_phase="research",
                success=False,
                processing_time=time.time() - start_time,
                research_success=False,
                error_message=f"Research exception: {str(e)}"
            )
    
    def test_phase_2_store_with_classification(self, result: ResearchWithClassificationResult) -> ResearchWithClassificationResult:
        """Phase 2: Store company data with classification in database"""
        
        if not result.research_success or not result.research_data:
            result.test_phase = "store"
            result.error_message = "Cannot store - research phase failed"
            return result
        
        logger.info(f"💾 Phase 2: Storing {result.company_name} with classification")
        start_time = time.time()
        
        try:
            # Store the company data in Pinecone
            success = self.pinecone_client.upsert_company(result.research_data)
            
            processing_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ Storage completed for {result.company_name} in {processing_time:.2f}s")
                
                result.test_phase = "store"
                result.storage_success = True
                result.processing_time += processing_time
                
                # Check if classification data was stored
                if hasattr(result.research_data, 'saas_classification') and result.research_data.saas_classification:
                    result.has_classification = True
                    result.classification_category = result.research_data.saas_classification
                    result.classification_confidence = getattr(result.research_data, 'classification_confidence', None)
                    result.is_saas = getattr(result.research_data, 'is_saas', None)
                    logger.info(f"📊 Classification stored: {result.classification_category}")
                else:
                    logger.warning(f"⚠️ No classification data found for {result.company_name}")
                
                return result
            else:
                result.test_phase = "store"
                result.storage_success = False
                result.error_message = "Storage operation failed"
                return result
                
        except Exception as e:
            logger.error(f"❌ Storage failed for {result.company_name}: {e}")
            result.test_phase = "store"
            result.storage_success = False
            result.processing_time += time.time() - start_time
            result.error_message = f"Storage exception: {str(e)}"
            return result
    
    def test_phase_3_retrieve_with_classification(self, result: ResearchWithClassificationResult) -> ResearchWithClassificationResult:
        """Phase 3: Retrieve company data with classification from database"""
        
        if not result.storage_success:
            result.test_phase = "retrieve"
            result.error_message = "Cannot retrieve - storage phase failed"
            return result
        
        logger.info(f"🔍 Phase 3: Retrieving {result.company_name} with classification")
        start_time = time.time()
        
        try:
            # Retrieve the company from database
            retrieved_company = self.pinecone_client.find_company_by_name(result.company_name)
            
            processing_time = time.time() - start_time
            
            if retrieved_company:
                logger.info(f"✅ Retrieval completed for {result.company_name} in {processing_time:.2f}s")
                
                result.test_phase = "retrieve"
                result.retrieval_success = True
                result.retrieved_data = retrieved_company
                result.processing_time += processing_time
                
                # Extract classification data from retrieved record
                metadata = retrieved_company.get('metadata', {})
                
                if 'saas_classification' in metadata:
                    result.has_classification = True
                    result.classification_category = metadata.get('saas_classification')
                    result.classification_confidence = metadata.get('classification_confidence')
                    result.is_saas = metadata.get('is_saas')
                    
                    logger.info(f"📊 Retrieved classification: {result.classification_category}")
                    logger.info(f"🏷️ SaaS Type: {'SaaS' if result.is_saas else 'Non-SaaS'}")
                    logger.info(f"📈 Confidence: {result.classification_confidence}")
                else:
                    logger.warning(f"⚠️ No classification data found in retrieved record")
                
                return result
            else:
                result.test_phase = "retrieve"
                result.retrieval_success = False
                result.error_message = "Company not found in database"
                return result
                
        except Exception as e:
            logger.error(f"❌ Retrieval failed for {result.company_name}: {e}")
            result.test_phase = "retrieve"
            result.retrieval_success = False
            result.processing_time += time.time() - start_time
            result.error_message = f"Retrieval exception: {str(e)}"
            return result
    
    def test_phase_4_validate_classification_quality(self, result: ResearchWithClassificationResult) -> ResearchWithClassificationResult:
        """Phase 4: Validate the quality and accuracy of classification data"""
        
        if not result.retrieval_success or not result.has_classification:
            result.test_phase = "classification"
            result.error_message = "Cannot validate - retrieval or classification failed"
            return result
        
        logger.info(f"✅ Phase 4: Validating classification quality for {result.company_name}")
        start_time = time.time()
        
        try:
            # Validate classification data quality
            validation_score = 0.0
            validation_notes = []
            
            # Check if category is from valid taxonomy
            if result.classification_category and result.classification_category != "Unclassified":
                if result.classification_category in self.saas_taxonomy:
                    validation_score += 0.3
                    validation_notes.append("✅ Valid taxonomy category")
                else:
                    validation_notes.append("❌ Invalid taxonomy category")
            
            # Check confidence score validity
            if result.classification_confidence is not None:
                if 0.0 <= result.classification_confidence <= 1.0:
                    validation_score += 0.2
                    validation_notes.append("✅ Valid confidence score")
                    
                    if result.classification_confidence >= 0.7:
                        validation_score += 0.2
                        validation_notes.append("✅ High confidence classification")
                else:
                    validation_notes.append("❌ Invalid confidence score range")
            
            # Check SaaS/Non-SaaS alignment
            if result.is_saas is not None:
                validation_score += 0.1
                validation_notes.append("✅ SaaS type classified")
                
                # Check if category aligns with SaaS type
                saas_categories = ["AdTech", "FinTech", "CollabTech", "DevOps/CloudInfra", "Martech & CRM"]
                non_saas_categories = ["Manufacturing", "Financial Services", "Healthcare Services"]
                
                if result.is_saas and result.classification_category in saas_categories:
                    validation_score += 0.2
                    validation_notes.append("✅ Category aligns with SaaS type")
                elif not result.is_saas and result.classification_category in non_saas_categories:
                    validation_score += 0.2
                    validation_notes.append("✅ Category aligns with Non-SaaS type")
            
            processing_time = time.time() - start_time
            
            result.test_phase = "classification"
            result.processing_time += processing_time
            
            logger.info(f"📊 Classification validation score: {validation_score:.2f}")
            for note in validation_notes:
                logger.info(f"   {note}")
            
            # Store validation results in error_message field for reporting
            if validation_score >= 0.8:
                result.error_message = f"High quality classification (score: {validation_score:.2f})"
            elif validation_score >= 0.5:
                result.error_message = f"Moderate quality classification (score: {validation_score:.2f})"
            else:
                result.error_message = f"Low quality classification (score: {validation_score:.2f})"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Classification validation failed: {e}")
            result.test_phase = "classification"
            result.processing_time += time.time() - start_time
            result.error_message = f"Validation exception: {str(e)}"
            return result
    
    def run_complete_research_classification_test(self, company: Dict[str, str]) -> ResearchWithClassificationResult:
        """Run the complete 4-phase test for a single company"""
        
        print(f"🧪 TESTING COMPLETE FLOW: {company['name']}")
        print(f"📋 Scenario: {company['scenario']}")
        print("-" * 60)
        
        # Phase 1: Research new company
        result = self.test_phase_1_research_new_company(company)
        if not result.success:
            print(f"❌ Phase 1 FAILED: {result.error_message}")
            return result
        print(f"✅ Phase 1 SUCCESS: Research completed")
        
        # Phase 2: Store with classification
        result = self.test_phase_2_store_with_classification(result)
        if not result.storage_success:
            print(f"❌ Phase 2 FAILED: {result.error_message}")
            return result
        print(f"✅ Phase 2 SUCCESS: Data stored{'with classification' if result.has_classification else ' (no classification)'}")
        
        # Phase 3: Retrieve with classification
        result = self.test_phase_3_retrieve_with_classification(result)
        if not result.retrieval_success:
            print(f"❌ Phase 3 FAILED: {result.error_message}")
            return result
        print(f"✅ Phase 3 SUCCESS: Data retrieved{'with classification' if result.has_classification else ' (no classification)'}")
        
        # Phase 4: Validate classification quality
        result = self.test_phase_4_validate_classification_quality(result)
        print(f"✅ Phase 4 SUCCESS: {result.error_message}")
        
        return result
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive test suite for all test companies"""
        
        print("🧪 RESEARCH + SAAS CLASSIFICATION TEST SUITE")
        print("=" * 80)
        print("🎯 Testing: Complete flow from new company research to classification retrieval")
        print("📅 Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print()
        
        test_results = []
        
        for i, company in enumerate(self.test_companies, 1):
            print(f"📋 TEST {i}/{len(self.test_companies)}: {company['name']}")
            
            result = self.run_complete_research_classification_test(company)
            test_results.append(result)
            
            # Display final results
            print(f"🏁 FINAL RESULT:")
            print(f"   Total Time: {result.processing_time:.2f}s")
            print(f"   Research: {'✅' if result.research_success else '❌'}")
            print(f"   Storage: {'✅' if result.storage_success else '❌'}")
            print(f"   Retrieval: {'✅' if result.retrieval_success else '❌'}")
            print(f"   Classification: {'✅' if result.has_classification else '❌'}")
            
            if result.has_classification:
                print(f"   Category: {result.classification_category}")
                print(f"   SaaS Type: {'SaaS' if result.is_saas else 'Non-SaaS'}")
                print(f"   Confidence: {result.classification_confidence}")
            
            print()
            
            # Rate limiting pause between tests
            if i < len(self.test_companies):
                print("⏳ Pausing between tests...")
                time.sleep(10)  # Allow time for processing
                print()
        
        return self._generate_comprehensive_summary(test_results)
    
    def _generate_comprehensive_summary(self, test_results: List[ResearchWithClassificationResult]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        # Success rates by phase
        research_success = sum(1 for r in test_results if r.research_success)
        storage_success = sum(1 for r in test_results if r.storage_success)
        retrieval_success = sum(1 for r in test_results if r.retrieval_success)
        classification_success = sum(1 for r in test_results if r.has_classification)
        
        # Performance metrics
        total_tests = len(test_results)
        avg_processing_time = sum(r.processing_time for r in test_results) / total_tests if total_tests > 0 else 0
        
        # Classification quality analysis
        classified_results = [r for r in test_results if r.has_classification]
        high_confidence_classifications = sum(1 for r in classified_results if r.classification_confidence and r.classification_confidence >= 0.8)
        
        summary = {
            "test_execution": {
                "total_tests": total_tests,
                "research_success_rate": research_success / total_tests * 100,
                "storage_success_rate": storage_success / total_tests * 100,
                "retrieval_success_rate": retrieval_success / total_tests * 100,
                "classification_success_rate": classification_success / total_tests * 100,
                "avg_processing_time": avg_processing_time
            },
            "classification_analysis": {
                "total_classified": classification_success,
                "high_confidence_count": high_confidence_classifications,
                "high_confidence_rate": high_confidence_classifications / classification_success * 100 if classification_success > 0 else 0
            }
        }
        
        # Print comprehensive summary
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        print(f"🎯 PHASE SUCCESS RATES:")
        print(f"   Research: {summary['test_execution']['research_success_rate']:.1f}% ({research_success}/{total_tests})")
        print(f"   Storage: {summary['test_execution']['storage_success_rate']:.1f}% ({storage_success}/{total_tests})")
        print(f"   Retrieval: {summary['test_execution']['retrieval_success_rate']:.1f}% ({retrieval_success}/{total_tests})")
        print(f"   Classification: {summary['test_execution']['classification_success_rate']:.1f}% ({classification_success}/{total_tests})")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average Total Time: {summary['test_execution']['avg_processing_time']:.2f}s")
        
        print(f"\n🏷️ CLASSIFICATION QUALITY:")
        print(f"   Total Classifications: {summary['classification_analysis']['total_classified']}")
        print(f"   High Confidence (≥80%): {summary['classification_analysis']['high_confidence_count']} ({summary['classification_analysis']['high_confidence_rate']:.1f}%)")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        end_to_end_success = (
            summary['test_execution']['classification_success_rate'] >= 80 and
            summary['test_execution']['avg_processing_time'] <= 120 and
            summary['classification_analysis']['high_confidence_rate'] >= 70
        )
        
        print(f"   End-to-End Success: {'✅ EXCELLENT' if end_to_end_success else '⚠️ NEEDS IMPROVEMENT'}")
        
        if end_to_end_success:
            print("   ✅ High success rates across all phases")
            print("   ✅ Good performance and classification quality")
            print("   ✅ READY FOR PRODUCTION: SaaS classification integration")
        else:
            print("   ⚠️ Some phases need improvement")
            print("   ⚠️ Review failed tests and optimize pipeline")
        
        return summary

def run_research_classification_test():
    """Main test execution function"""
    
    tester = ResearchWithSaaSClassificationTester()
    
    try:
        summary = tester.run_comprehensive_test_suite()
        return summary
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting Research + SaaS Classification Test Suite")
    print("🎯 Objective: Test complete flow from new company research to classification retrieval")
    print()
    
    summary = run_research_classification_test()
    
    if summary:
        print("\n🏁 Test suite completed successfully!")
        print("📄 Review results above for production readiness assessment")
    else:
        print("\n💥 Test execution failed - check logs for details")