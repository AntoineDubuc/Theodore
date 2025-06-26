"""
Field Extraction Metrics Service
Tracks field-level success rates and performance for Theodore's scraping system
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from src.models import (
    FieldExtractionResult, 
    FieldExtractionMetrics, 
    CompanyFieldExtractionSession,
    CompanyData
)

logger = logging.getLogger(__name__)


class FieldMetricsService:
    """Service for tracking and analyzing field extraction performance"""
    
    def __init__(self, pinecone_client=None):
        self.pinecone_client = pinecone_client
        self.current_sessions: Dict[str, CompanyFieldExtractionSession] = {}
        
        # Define ALL fields we track from CompanyData model (53+ fields)
        self.tracked_fields = [
            # Core required fields
            'name', 'website',
            
            # Basic company info
            'industry', 'business_model', 'company_size',
            
            # Technology insights
            'tech_stack', 'has_chat_widget', 'has_forms',
            
            # Business intelligence
            'pain_points', 'key_services', 'competitive_advantages', 
            'target_market', 'business_model_framework',
            
            # Extended metadata from Crawl4AI
            'company_description', 'value_proposition', 'founding_year',
            'location', 'employee_count_range', 'company_culture',
            'funding_status', 'social_media', 'contact_info',
            'leadership_team', 'recent_news', 'certifications',
            'partnerships', 'awards',
            
            # Multi-page crawling results
            'pages_crawled', 'crawl_depth', 'crawl_duration',
            
            # SaaS Classification fields
            'saas_classification', 'classification_confidence',
            'classification_justification', 'classification_timestamp',
            'classification_model_version', 'is_saas',
            
            # Similarity metrics for sales intelligence
            'company_stage', 'tech_sophistication', 'geographic_scope',
            'business_model_type', 'decision_maker_type', 'sales_complexity',
            
            # Confidence scores for similarity metrics
            'stage_confidence', 'tech_confidence', 'industry_confidence',
            
            # Batch Research Intelligence
            'has_job_listings', 'job_listings_count', 'job_listings',
            'job_listings_details', 'products_services_offered',
            'key_decision_makers', 'funding_stage_detailed',
            'sales_marketing_tools', 'recent_news_events',
            
            # AI analysis
            'raw_content', 'ai_summary', 'embedding',
            
            # Scraping details
            'scraped_urls', 'scraped_content_details',
            
            # LLM interaction details
            'llm_prompts_sent', 'page_selection_prompt', 'content_analysis_prompt',
            
            # Token usage and cost tracking
            'total_input_tokens', 'total_output_tokens', 'total_cost_usd',
            'llm_calls_breakdown'
        ]
        
        # Field importance weights for overall scoring (organized by category)
        self.field_weights = {
            # Core Business Intelligence (High Value) - 40%
            'company_description': 0.08,
            'value_proposition': 0.06,
            'business_model': 0.05,
            'industry': 0.05,
            'target_market': 0.04,
            'competitive_advantages': 0.04,
            'key_services': 0.04,
            'products_services_offered': 0.04,
            
            # Company Fundamentals (Medium-High Value) - 25%
            'founding_year': 0.04,
            'location': 0.04,
            'company_size': 0.03,
            'employee_count_range': 0.03,
            'company_stage': 0.03,
            'funding_status': 0.03,
            'funding_stage_detailed': 0.03,
            'company_culture': 0.02,
            
            # Contact & Leadership (Medium Value) - 15%
            'leadership_team': 0.04,
            'key_decision_makers': 0.04,
            'contact_info': 0.04,
            'social_media': 0.03,
            
            # Technology & Sophistication (Medium Value) - 10%
            'tech_stack': 0.03,
            'tech_sophistication': 0.02,
            'sales_marketing_tools': 0.02,
            'has_chat_widget': 0.01,
            'has_forms': 0.01,
            'geographic_scope': 0.01,
            
            # Market Intelligence (Medium Value) - 5%
            'pain_points': 0.02,
            'partnerships': 0.01,
            'certifications': 0.01,
            'awards': 0.01,
            
            # Activity & Engagement (Low-Medium Value) - 3%
            'job_listings_count': 0.01,
            'has_job_listings': 0.01,
            'recent_news': 0.005,
            'recent_news_events': 0.005,
            
            # Classification & Analysis (Auto-Generated) - 2%
            'saas_classification': 0.01,
            'business_model_framework': 0.005,
            'is_saas': 0.005,
            
            # All other fields get minimal weight for completeness
            'ai_summary': 0.002,
            'classification_confidence': 0.002,
            'classification_justification': 0.002,
            'decision_maker_type': 0.002,
            'sales_complexity': 0.002,
            'job_listings': 0.001,
            'job_listings_details': 0.001,
            'stage_confidence': 0.001,
            'tech_confidence': 0.001,
            'industry_confidence': 0.001
        }
        
        # Field categories for better organization in UI
        self.field_categories = {
            'Core Business Intelligence': [
                'company_description', 'value_proposition', 'business_model', 
                'industry', 'target_market', 'competitive_advantages', 
                'key_services', 'products_services_offered'
            ],
            'Company Fundamentals': [
                'founding_year', 'location', 'company_size', 'employee_count_range',
                'company_stage', 'funding_status', 'funding_stage_detailed', 'company_culture'
            ],
            'Contact & Leadership': [
                'leadership_team', 'key_decision_makers', 'contact_info', 'social_media'
            ],
            'Technology & Tools': [
                'tech_stack', 'tech_sophistication', 'sales_marketing_tools',
                'has_chat_widget', 'has_forms', 'geographic_scope'
            ],
            'Market Intelligence': [
                'pain_points', 'partnerships', 'certifications', 'awards'
            ],
            'Activity & Engagement': [
                'job_listings_count', 'has_job_listings', 'recent_news', 
                'recent_news_events', 'job_listings', 'job_listings_details'
            ],
            'Classification & Analysis': [
                'saas_classification', 'business_model_framework', 'is_saas',
                'classification_confidence', 'classification_justification',
                'decision_maker_type', 'sales_complexity'
            ],
            'Technical Metadata': [
                'pages_crawled', 'crawl_depth', 'crawl_duration', 'scraped_urls',
                'scraped_content_details', 'raw_content', 'ai_summary',
                'llm_prompts_sent', 'page_selection_prompt', 'content_analysis_prompt',
                'total_input_tokens', 'total_output_tokens', 'total_cost_usd',
                'llm_calls_breakdown', 'embedding', 'stage_confidence', 
                'tech_confidence', 'industry_confidence'
            ]
        }
    
    def start_extraction_session(self, company_id: str, company_name: str) -> str:
        """Start a new field extraction session for a company"""
        session = CompanyFieldExtractionSession(
            company_id=company_id,
            company_name=company_name
        )
        
        self.current_sessions[session.id] = session
        logger.info(f"Started field extraction session {session.id} for {company_name}")
        return session.id
    
    def track_field_extraction(self, 
                             session_id: str,
                             field_name: str, 
                             success: bool,
                             value: Optional[str] = None,
                             confidence: Optional[float] = None,
                             method: str = "unknown",
                             source_page: Optional[str] = None,
                             extraction_time: float = 0.0,
                             error_message: Optional[str] = None) -> FieldExtractionResult:
        """Track a single field extraction attempt"""
        
        result = FieldExtractionResult(
            field_name=field_name,
            success=success,
            value=value,
            confidence=confidence,
            method=method,
            source_page=source_page,
            extraction_time=extraction_time,
            error_message=error_message
        )
        
        # Add to session if it exists
        if session_id in self.current_sessions:
            self.current_sessions[session_id].add_field_result(result)
            logger.debug(f"Tracked {field_name} extraction: {'SUCCESS' if success else 'FAILED'}")
        
        return result
    
    def complete_extraction_session(self, session_id: str, 
                                  pages_scraped: int = 0,
                                  ai_calls_made: int = 0,
                                  total_tokens_used: int = 0,
                                  total_cost_usd: float = 0.0) -> Optional[CompanyFieldExtractionSession]:
        """Complete a field extraction session and update metrics"""
        
        if session_id not in self.current_sessions:
            logger.warning(f"Session {session_id} not found")
            return None
        
        session = self.current_sessions[session_id]
        
        # Update session details
        session.pages_scraped = pages_scraped
        session.ai_calls_made = ai_calls_made
        session.total_tokens_used = total_tokens_used
        session.total_cost_usd = total_cost_usd
        session.complete_session()
        
        # Store session in Pinecone if available
        if self.pinecone_client:
            self._store_session_metrics(session)
        
        # Update global field metrics
        self._update_global_metrics(session)
        
        # Clean up
        del self.current_sessions[session_id]
        
        logger.info(f"Completed extraction session {session_id}: {session.fields_successful}/{session.fields_attempted} fields successful")
        return session
    
    def analyze_company_extraction(self, company_data: CompanyData) -> Dict[str, Any]:
        """Analyze field extraction success for a company"""
        
        analysis = {
            "company_id": company_data.id,
            "company_name": company_data.name,
            "total_fields": len(self.tracked_fields),
            "extracted_fields": 0,
            "missing_fields": [],
            "extraction_quality": 0.0,
            "weighted_score": 0.0,
            "field_details": {}
        }
        
        total_weight = 0.0
        weighted_success = 0.0
        
        for field_name in self.tracked_fields:
            field_value = getattr(company_data, field_name, None)
            
            # Determine if field was successfully extracted
            has_value = self._is_field_populated(field_value)
            
            if has_value:
                analysis["extracted_fields"] += 1
                
                # Calculate field weight
                weight = self.field_weights.get(field_name, 0.05)
                total_weight += weight
                weighted_success += weight
                
                analysis["field_details"][field_name] = {
                    "status": "extracted",
                    "value_preview": self._get_value_preview(field_value),
                    "weight": weight
                }
            else:
                analysis["missing_fields"].append(field_name)
                weight = self.field_weights.get(field_name, 0.05)
                total_weight += weight
                
                analysis["field_details"][field_name] = {
                    "status": "missing",
                    "weight": weight
                }
        
        # Calculate scores
        analysis["extraction_quality"] = analysis["extracted_fields"] / analysis["total_fields"]
        analysis["weighted_score"] = weighted_success / total_weight if total_weight > 0 else 0.0
        
        return analysis
    
    def get_field_performance_summary(self, field_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for specific field or all fields"""
        
        if field_name:
            # Get metrics for specific field
            metrics = self._get_field_metrics(field_name)
            if metrics:
                return self._format_field_metrics(metrics)
            else:
                return {"error": f"No metrics found for field {field_name}"}
        else:
            # Get summary for all fields
            summary = {
                "overall_performance": {},
                "field_breakdown": {},
                "trends": {},
                "recommendations": []
            }
            
            for field in self.tracked_fields:
                metrics = self._get_field_metrics(field)
                if metrics:
                    summary["field_breakdown"][field] = self._format_field_metrics(metrics)
            
            # Calculate overall performance
            if summary["field_breakdown"]:
                success_rates = [m["success_rate"] for m in summary["field_breakdown"].values()]
                summary["overall_performance"] = {
                    "average_success_rate": sum(success_rates) / len(success_rates),
                    "best_performing_field": max(summary["field_breakdown"].items(), key=lambda x: x[1]["success_rate"])[0],
                    "worst_performing_field": min(summary["field_breakdown"].items(), key=lambda x: x[1]["success_rate"])[0],
                    "total_fields_tracked": len(summary["field_breakdown"])
                }
            
            # Generate recommendations
            summary["recommendations"] = self._generate_improvement_recommendations(summary["field_breakdown"])
            
            return summary
    
    def _is_field_populated(self, field_value: Any) -> bool:
        """Check if a field has meaningful data"""
        if field_value is None:
            return False
        
        if isinstance(field_value, str):
            return len(field_value.strip()) > 0
        elif isinstance(field_value, (list, dict)):
            return len(field_value) > 0
        elif isinstance(field_value, (int, float)):
            return field_value is not None
        
        return bool(field_value)
    
    def _get_value_preview(self, field_value: Any) -> str:
        """Get a preview of the field value for display"""
        if isinstance(field_value, str):
            return field_value[:50] + "..." if len(field_value) > 50 else field_value
        elif isinstance(field_value, list):
            return f"[{len(field_value)} items]"
        elif isinstance(field_value, dict):
            return f"{{...{len(field_value)} keys...}}"
        else:
            return str(field_value)
    
    def _store_session_metrics(self, session: CompanyFieldExtractionSession):
        """Store session metrics in Pinecone"""
        try:
            # Store as metadata in the company's vector
            if self.pinecone_client and hasattr(self.pinecone_client, 'index'):
                
                # Get current company metadata
                metadata = self.pinecone_client.get_company_metadata(session.company_id) or {}
                
                # Add field extraction session data
                session_data = {
                    "field_session_id": session.id,
                    "session_success_rate": session.session_success_rate,
                    "fields_extracted": session.fields_successful,
                    "fields_attempted": session.fields_attempted,
                    "extraction_timestamp": session.session_start.isoformat(),
                    "processing_time": session.total_processing_time,
                    "ai_calls": session.ai_calls_made,
                    "tokens_used": session.total_tokens_used,
                    "cost_usd": session.total_cost_usd
                }
                
                # Store detailed field results
                field_results_summary = {}
                for result in session.field_results:
                    field_results_summary[result.field_name] = {
                        "success": result.success,
                        "method": result.method,
                        "confidence": result.confidence,
                        "extraction_time": result.extraction_time
                    }
                
                session_data["field_results"] = json.dumps(field_results_summary)
                
                # Update metadata
                metadata.update(session_data)
                
                # Update in Pinecone
                self.pinecone_client.index.update(
                    id=session.company_id,
                    set_metadata=metadata
                )
                
                logger.info(f"Stored field extraction metrics for {session.company_name}")
                
        except Exception as e:
            logger.error(f"Failed to store session metrics: {e}")
    
    def _update_global_metrics(self, session: CompanyFieldExtractionSession):
        """Update global field metrics based on session results"""
        # This would typically update aggregated metrics in a database
        # For now, we'll log the updates
        
        logger.info(f"Global metrics update for session {session.id}:")
        logger.info(f"  - Fields attempted: {session.fields_attempted}")
        logger.info(f"  - Fields successful: {session.fields_successful}")
        logger.info(f"  - Session success rate: {session.session_success_rate:.2%}")
        
        # Update method performance tracking
        method_performance = defaultdict(lambda: {"attempts": 0, "successes": 0})
        
        for result in session.field_results:
            method_performance[result.method]["attempts"] += 1
            if result.success:
                method_performance[result.method]["successes"] += 1
        
        for method, stats in method_performance.items():
            success_rate = stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0
            logger.info(f"  - {method}: {stats['successes']}/{stats['attempts']} ({success_rate:.2%})")
    
    def _get_field_metrics(self, field_name: str) -> Optional[FieldExtractionMetrics]:
        """Get metrics for a specific field (placeholder - would query from storage)"""
        # This would typically query from Pinecone or another database
        # For now, return mock data based on field importance
        
        base_success_rate = 0.7
        if field_name in ['company_description', 'value_proposition']:
            base_success_rate = 0.85  # These are typically easier to extract
        elif field_name in ['founding_year', 'leadership_team']:
            base_success_rate = 0.45  # These are typically harder to extract
        elif field_name in ['location', 'contact_info']:
            base_success_rate = 0.60
        
        metrics = FieldExtractionMetrics(
            field_name=field_name,
            total_attempts=100,  # Mock data
            successful_extractions=int(100 * base_success_rate),
            failed_extractions=int(100 * (1 - base_success_rate)),
            success_rate=base_success_rate,
            avg_extraction_time=0.5,
            avg_confidence=0.75,
            method_performance={
                "regex": {"attempts": 40, "successes": int(40 * 0.3), "avg_time": 0.1, "avg_confidence": 0.6},
                "ai_analysis": {"attempts": 60, "successes": int(60 * 0.8), "avg_time": 0.8, "avg_confidence": 0.85}
            }
        )
        
        return metrics
    
    def _format_field_metrics(self, metrics: FieldExtractionMetrics) -> Dict[str, Any]:
        """Format field metrics for API response"""
        return {
            "field_name": metrics.field_name,
            "success_rate": metrics.success_rate,
            "total_attempts": metrics.total_attempts,
            "successful_extractions": metrics.successful_extractions,
            "failed_extractions": metrics.failed_extractions,
            "avg_extraction_time": metrics.avg_extraction_time,
            "avg_confidence": metrics.avg_confidence,
            "method_performance": metrics.method_performance,
            "last_updated": metrics.last_updated.isoformat(),
            "improvement_suggestions": metrics.improvement_suggestions
        }
    
    def _generate_improvement_recommendations(self, field_breakdown: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on field performance"""
        recommendations = []
        
        # Analyze performance patterns
        low_performers = [field for field, metrics in field_breakdown.items() 
                         if metrics["success_rate"] < 0.5]
        
        high_performers = [field for field, metrics in field_breakdown.items() 
                          if metrics["success_rate"] > 0.8]
        
        if low_performers:
            recommendations.append(f"Focus on improving extraction for: {', '.join(low_performers)}")
        
        if len(high_performers) > 0:
            recommendations.append(f"High-performing fields that can serve as templates: {', '.join(high_performers[:3])}")
        
        # Method-specific recommendations
        ai_heavy_fields = []
        regex_heavy_fields = []
        
        for field, metrics in field_breakdown.items():
            method_perf = metrics.get("method_performance", {})
            ai_success = method_perf.get("ai_analysis", {}).get("successes", 0)
            regex_success = method_perf.get("regex", {}).get("successes", 0)
            
            if ai_success > regex_success:
                ai_heavy_fields.append(field)
            else:
                regex_heavy_fields.append(field)
        
        if len(ai_heavy_fields) > len(regex_heavy_fields):
            recommendations.append("Consider expanding AI-based extraction methods")
        
        if not recommendations:
            recommendations.append("Overall extraction performance is stable")
        
        return recommendations
    
    def export_metrics_report(self, format: str = "json") -> Dict[str, Any]:
        """Export comprehensive metrics report"""
        
        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "summary": self.get_field_performance_summary(),
            "tracked_fields": self.tracked_fields,
            "field_weights": self.field_weights,
            "active_sessions": len(self.current_sessions)
        }
        
        if format == "json":
            return report
        else:
            # Could add other formats like CSV, Excel, etc.
            return report