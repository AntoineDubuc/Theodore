#!/usr/bin/env python3
"""
SaaS Classification Retrieval Test
Tests retrieval and analysis of existing SaaS classification data from Theodore database
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

try:
    # Import core Theodore components
    from src.pinecone_client import PineconeClient
    print("✅ Successfully imported Theodore components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("ℹ️ This test requires access to Theodore core components")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ClassificationRetrievalResult:
    """Result structure for classification retrieval test"""
    company_name: str
    retrieval_success: bool
    processing_time: float
    
    # Classification data
    has_classification: bool = False
    saas_classification: Optional[str] = None
    classification_confidence: Optional[float] = None
    is_saas: Optional[bool] = None
    classification_timestamp: Optional[str] = None
    classification_justification: Optional[str] = None
    
    # Data quality metrics
    confidence_level: str = "unknown"  # "high", "medium", "low"
    category_validity: bool = False
    has_justification: bool = False
    
    # Error tracking
    error_message: Optional[str] = None

class SaaSClassificationRetrievalTester:
    """
    Tests retrieval and analysis of existing SaaS classification data
    from Theodore's Pinecone database
    """
    
    def __init__(self):
        # Initialize Pinecone client
        self.pinecone_client = PineconeClient()
        
        # Valid SaaS taxonomy categories for validation
        self.valid_saas_categories = self._get_valid_categories()
        
        # Expected classified companies (if any exist in database)
        self.test_targets = self._get_test_targets()
    
    def _get_valid_categories(self) -> List[str]:
        """Return list of all valid SaaS classification categories"""
        return [
            # SaaS Verticals
            "AdTech", "AssetManagement", "Billing", "Bio/LS", "CollabTech",
            "Data/BI/Analytics", "DevOps/CloudInfra", "E-commerce & Retail",
            "EdTech", "Enertech", "FinTech", "GovTech", "HRTech", "HealthTech",
            "Identity & Access Management (IAM)", "InsureTech", "LawTech",
            "LeisureTech", "Manufacturing/AgTech/IoT", "Martech & CRM",
            "MediaTech", "PropTech", "Risk/Audit/Governance",
            "Social / Community / Non Profit", "Supply Chain & Logistics",
            "TranspoTech",
            
            # Non-SaaS Categories
            "Advertising & Media Services", "Biopharma R&D", "Combo HW & SW",
            "Education", "Energy", "Financial Services", "Healthcare Services",
            "Industry Consulting Services", "Insurance", "IT Consulting Services",
            "Logistics Services", "Manufacturing", "Non-Profit", "Retail",
            "Sports", "Travel & Leisure", "Wholesale Distribution & Supply",
            
            # Special Category
            "Unclassified"
        ]
    
    def _get_test_targets(self) -> List[str]:
        """Return list of company names to test for classification retrieval"""
        return [
            "Stripe",           # Should be FinTech SaaS
            "Linear",           # Should be CollabTech SaaS  
            "Notion",           # Should be CollabTech SaaS
            "Vercel",           # Should be DevOps/CloudInfra SaaS
            "Tesla",            # Should be Manufacturing Non-SaaS
            "Deloitte",         # Should be Industry Consulting Services Non-SaaS
            "Coinbase",         # Should be FinTech SaaS
            "MongoDB",          # Should be DevOps/CloudInfra SaaS
            "Shopify",          # Should be E-commerce & Retail SaaS
            "Salesforce"        # Should be Martech & CRM SaaS
        ]
    
    def retrieve_company_classification(self, company_name: str) -> ClassificationRetrievalResult:
        """Retrieve and analyze classification data for a single company"""
        
        logger.info(f"🔍 Retrieving classification for: {company_name}")
        start_time = time.time()
        
        try:
            # Query Pinecone for the company
            company_data = self.pinecone_client.find_company_by_name(company_name)
            processing_time = time.time() - start_time
            
            if not company_data:
                logger.warning(f"❌ Company not found: {company_name}")
                return ClassificationRetrievalResult(
                    company_name=company_name,
                    retrieval_success=False,
                    processing_time=processing_time,
                    error_message="Company not found in database"
                )
            
            logger.info(f"✅ Company found: {company_name}")
            
            # Extract metadata
            metadata = company_data.get('metadata', {})
            
            # Extract classification fields
            saas_classification = metadata.get('saas_classification')
            classification_confidence = metadata.get('classification_confidence')
            is_saas = metadata.get('is_saas')
            classification_timestamp = metadata.get('classification_timestamp')
            classification_justification = metadata.get('classification_justification')
            
            # Determine if classification exists
            has_classification = bool(saas_classification and saas_classification != "Unclassified")
            
            # Analyze classification quality
            confidence_level = self._analyze_confidence_level(classification_confidence)
            category_validity = self._validate_category(saas_classification)
            has_justification = bool(classification_justification and len(classification_justification.strip()) > 10)
            
            result = ClassificationRetrievalResult(
                company_name=company_name,
                retrieval_success=True,
                processing_time=processing_time,
                has_classification=has_classification,
                saas_classification=saas_classification,
                classification_confidence=classification_confidence,
                is_saas=is_saas,
                classification_timestamp=classification_timestamp,
                classification_justification=classification_justification,
                confidence_level=confidence_level,
                category_validity=category_validity,
                has_justification=has_justification
            )
            
            # Log classification details
            if has_classification:
                logger.info(f"📊 Classification: {saas_classification}")
                logger.info(f"🏷️ SaaS Type: {'SaaS' if is_saas else 'Non-SaaS'}")
                logger.info(f"📈 Confidence: {classification_confidence} ({confidence_level})")
                logger.info(f"✔️ Valid Category: {'Yes' if category_validity else 'No'}")
                logger.info(f"💭 Has Justification: {'Yes' if has_justification else 'No'}")
            else:
                logger.warning(f"⚠️ No classification data found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error retrieving {company_name}: {e}")
            return ClassificationRetrievalResult(
                company_name=company_name,
                retrieval_success=False,
                processing_time=time.time() - start_time,
                error_message=f"Retrieval exception: {str(e)}"
            )
    
    def _analyze_confidence_level(self, confidence: Optional[float]) -> str:
        """Analyze confidence score and return level"""
        if confidence is None:
            return "unknown"
        elif confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _validate_category(self, category: Optional[str]) -> bool:
        """Validate if category is in the official taxonomy"""
        if not category:
            return False
        return category in self.valid_saas_categories
    
    def analyze_database_classification_coverage(self) -> Dict[str, Any]:
        """Analyze overall classification coverage in the database"""
        
        logger.info("📊 Analyzing database classification coverage...")
        start_time = time.time()
        
        try:
            # Get all companies from database
            all_companies = self.pinecone_client.get_all_companies()
            processing_time = time.time() - start_time
            
            if not all_companies:
                logger.warning("❌ No companies found in database")
                return {
                    "total_companies": 0,
                    "analysis_time": processing_time,
                    "error": "No companies found in database"
                }
            
            # Analyze classification coverage
            total_companies = len(all_companies)
            classified_companies = 0
            saas_companies = 0
            non_saas_companies = 0
            high_confidence_count = 0
            category_distribution = {}
            
            for company in all_companies:
                metadata = company.get('metadata', {})
                
                saas_classification = metadata.get('saas_classification')
                classification_confidence = metadata.get('classification_confidence')
                is_saas = metadata.get('is_saas')
                
                # Count classified companies
                if saas_classification and saas_classification != "Unclassified":
                    classified_companies += 1
                    
                    # Count SaaS vs Non-SaaS
                    if is_saas:
                        saas_companies += 1
                    else:
                        non_saas_companies += 1
                    
                    # Count high confidence classifications
                    if classification_confidence and classification_confidence >= 0.8:
                        high_confidence_count += 1
                    
                    # Track category distribution
                    category_distribution[saas_classification] = category_distribution.get(saas_classification, 0) + 1
            
            # Calculate percentages
            classification_coverage = classified_companies / total_companies * 100 if total_companies > 0 else 0
            saas_percentage = saas_companies / classified_companies * 100 if classified_companies > 0 else 0
            high_confidence_rate = high_confidence_count / classified_companies * 100 if classified_companies > 0 else 0
            
            coverage_analysis = {
                "total_companies": total_companies,
                "classified_companies": classified_companies,
                "classification_coverage": classification_coverage,
                "saas_companies": saas_companies,
                "non_saas_companies": non_saas_companies,
                "saas_percentage": saas_percentage,
                "high_confidence_count": high_confidence_count,
                "high_confidence_rate": high_confidence_rate,
                "category_distribution": category_distribution,
                "analysis_time": processing_time
            }
            
            logger.info(f"📊 Coverage Analysis Complete:")
            logger.info(f"   Total Companies: {total_companies}")
            logger.info(f"   Classified: {classified_companies} ({classification_coverage:.1f}%)")
            logger.info(f"   SaaS: {saas_companies} ({saas_percentage:.1f}%)")
            logger.info(f"   Non-SaaS: {non_saas_companies}")
            logger.info(f"   High Confidence: {high_confidence_count} ({high_confidence_rate:.1f}%)")
            
            return coverage_analysis
            
        except Exception as e:
            logger.error(f"❌ Coverage analysis failed: {e}")
            return {
                "total_companies": 0,
                "analysis_time": time.time() - start_time,
                "error": f"Analysis exception: {str(e)}"
            }
    
    def run_classification_retrieval_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive classification retrieval test suite"""
        
        print("🧪 SAAS CLASSIFICATION RETRIEVAL TEST SUITE")
        print("=" * 80)
        print("🎯 Testing: Retrieval and analysis of existing SaaS classification data")
        print("📅 Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print()
        
        # Phase 1: Database coverage analysis
        print("📊 PHASE 1: DATABASE CLASSIFICATION COVERAGE ANALYSIS")
        print("-" * 60)
        
        coverage_analysis = self.analyze_database_classification_coverage()
        
        if "error" in coverage_analysis:
            print(f"❌ Coverage analysis failed: {coverage_analysis['error']}")
            return {"test_suite_success": False, "error": coverage_analysis["error"]}
        
        print(f"✅ Coverage analysis completed in {coverage_analysis['analysis_time']:.2f}s")
        print()
        
        # Phase 2: Individual company classification retrieval
        print("🔍 PHASE 2: INDIVIDUAL COMPANY CLASSIFICATION RETRIEVAL")
        print("-" * 60)
        
        retrieval_results = []
        
        for i, company_name in enumerate(self.test_targets, 1):
            print(f"📋 TEST {i}/{len(self.test_targets)}: {company_name}")
            
            result = self.retrieve_company_classification(company_name)
            retrieval_results.append(result)
            
            # Display results
            if result.retrieval_success:
                if result.has_classification:
                    print(f"✅ CLASSIFIED: {result.saas_classification}")
                    print(f"   Type: {'SaaS' if result.is_saas else 'Non-SaaS'}")
                    print(f"   Confidence: {result.classification_confidence} ({result.confidence_level})")
                    print(f"   Valid Category: {'✅' if result.category_validity else '❌'}")
                    print(f"   Has Justification: {'✅' if result.has_justification else '❌'}")
                else:
                    print(f"⚠️ FOUND BUT NOT CLASSIFIED")
            else:
                print(f"❌ NOT FOUND: {result.error_message}")
            
            print()
        
        # Generate comprehensive summary
        return self._generate_retrieval_summary(coverage_analysis, retrieval_results)
    
    def _generate_retrieval_summary(self, coverage_analysis: Dict[str, Any], 
                                  retrieval_results: List[ClassificationRetrievalResult]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        # Retrieval statistics
        total_tests = len(retrieval_results)
        successful_retrievals = sum(1 for r in retrieval_results if r.retrieval_success)
        found_classifications = sum(1 for r in retrieval_results if r.has_classification)
        high_confidence_retrievals = sum(1 for r in retrieval_results if r.confidence_level == "high")
        valid_categories = sum(1 for r in retrieval_results if r.category_validity)
        
        # Performance metrics
        avg_retrieval_time = sum(r.processing_time for r in retrieval_results) / total_tests if total_tests > 0 else 0
        
        summary = {
            "database_coverage": coverage_analysis,
            "retrieval_tests": {
                "total_tests": total_tests,
                "successful_retrievals": successful_retrievals,
                "found_classifications": found_classifications,
                "high_confidence_retrievals": high_confidence_retrievals,
                "valid_categories": valid_categories,
                "avg_retrieval_time": avg_retrieval_time,
                "retrieval_success_rate": successful_retrievals / total_tests * 100 if total_tests > 0 else 0,
                "classification_found_rate": found_classifications / successful_retrievals * 100 if successful_retrievals > 0 else 0,
                "high_confidence_rate": high_confidence_retrievals / found_classifications * 100 if found_classifications > 0 else 0
            }
        }
        
        # Print comprehensive summary
        print("=" * 80)
        print("📊 CLASSIFICATION RETRIEVAL TEST SUMMARY")
        print("=" * 80)
        
        print(f"🗄️ DATABASE COVERAGE:")
        print(f"   Total Companies: {coverage_analysis['total_companies']}")
        print(f"   Classified: {coverage_analysis['classified_companies']} ({coverage_analysis['classification_coverage']:.1f}%)")
        print(f"   SaaS Companies: {coverage_analysis['saas_companies']} ({coverage_analysis['saas_percentage']:.1f}%)")
        print(f"   High Confidence: {coverage_analysis['high_confidence_count']} ({coverage_analysis['high_confidence_rate']:.1f}%)")
        
        print(f"\n🔍 RETRIEVAL TESTS:")
        print(f"   Total Tests: {summary['retrieval_tests']['total_tests']}")
        print(f"   Successful Retrievals: {summary['retrieval_tests']['successful_retrievals']} ({summary['retrieval_tests']['retrieval_success_rate']:.1f}%)")
        print(f"   Found Classifications: {summary['retrieval_tests']['found_classifications']} ({summary['retrieval_tests']['classification_found_rate']:.1f}%)")
        print(f"   High Confidence: {summary['retrieval_tests']['high_confidence_retrievals']} ({summary['retrieval_tests']['high_confidence_rate']:.1f}%)")
        print(f"   Valid Categories: {summary['retrieval_tests']['valid_categories']}")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average Retrieval Time: {summary['retrieval_tests']['avg_retrieval_time']:.3f}s")
        
        # Top categories from database
        if coverage_analysis.get('category_distribution'):
            print(f"\n🏷️ TOP CATEGORIES IN DATABASE:")
            sorted_categories = sorted(coverage_analysis['category_distribution'].items(), 
                                     key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:5]:
                print(f"   {category}: {count} companies")
        
        # Overall assessment
        print(f"\n🎯 CLASSIFICATION RETRIEVAL ASSESSMENT:")
        
        retrieval_ready = (
            coverage_analysis['classification_coverage'] >= 50 and
            summary['retrieval_tests']['classification_found_rate'] >= 80 and
            summary['retrieval_tests']['high_confidence_rate'] >= 60
        )
        
        print(f"   Retrieval System Ready: {'✅ YES' if retrieval_ready else '⚠️ NEEDS IMPROVEMENT'}")
        
        if retrieval_ready:
            print("   ✅ Good database coverage and retrieval performance")
            print("   ✅ High-quality classification data available")
            print("   ✅ READY FOR PRODUCTION: Classification retrieval integration")
        else:
            print("   ⚠️ Low database coverage or classification quality")
            print("   ⚠️ Consider improving classification system before production")
        
        return summary

def run_classification_retrieval_test():
    """Main test execution function"""
    
    tester = SaaSClassificationRetrievalTester()
    
    try:
        summary = tester.run_classification_retrieval_test_suite()
        return summary
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting SaaS Classification Retrieval Test Suite")
    print("🎯 Objective: Test retrieval and analysis of existing classification data")
    print()
    
    summary = run_classification_retrieval_test()
    
    if summary:
        print("\n🏁 Classification retrieval test completed successfully!")
        print("📄 Review results above for production integration assessment")
    else:
        print("\n💥 Test execution failed - check logs for details")