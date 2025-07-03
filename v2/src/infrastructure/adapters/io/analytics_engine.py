#!/usr/bin/env python3
"""
Theodore v2 Analytics Engine Implementation

Comprehensive analytics engine for market analysis and business intelligence.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from collections import Counter, defaultdict
import statistics

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from ....core.ports.io.analytics_engine_port import AnalyticsEnginePort
from ....core.domain.models.company import CompanyData
from ....core.domain.models.export import (
    Analytics, AnalyticsReport, AnalysisType, CompetitiveLandscapeReport,
    Visualization, VisualizationType
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class AnalyticsError(Exception):
    """Analytics operation error"""
    pass


class AnalyticsEngine(AnalyticsEnginePort):
    """
    Comprehensive analytics engine for company intelligence
    
    Provides:
    - Market segmentation and analysis
    - Competitive landscape analysis
    - Trend analysis and forecasting
    - Similarity clustering
    - Statistical analysis
    """
    
    def __init__(self):
        self.available_features = {
            'numpy': HAS_NUMPY,
            'sklearn': HAS_SKLEARN
        }
    
    async def generate_analytics(
        self,
        companies: List[CompanyData],
        config: Optional[Dict[str, Any]] = None
    ) -> Analytics:
        """Generate comprehensive analytics for company data"""
        
        if not companies:
            return Analytics(
                total_companies=0,
                industries_count=0,
                industry_distribution={},
                size_distribution={},
                location_distribution={}
            )
        
        try:
            logger.info(f"Generating analytics for {len(companies)} companies")
            
            # Basic statistics
            total_companies = len(companies)
            industries = [c.industry for c in companies if c.industry]
            unique_industries = len(set(industries))
            
            # Distribution analytics
            industry_dist = self._calculate_industry_distribution(companies)
            size_dist = self._calculate_size_distribution(companies)
            location_dist = self._calculate_location_distribution(companies)
            
            # Advanced analytics (if dependencies available)
            similarity_clusters = []
            avg_similarity = None
            market_concentration = None
            competitive_density = None
            
            if HAS_SKLEARN and len(companies) >= 3:
                similarity_clusters = await self._calculate_similarity_clusters(companies)
                avg_similarity = self._calculate_average_similarity(companies)
                market_concentration = self._calculate_market_concentration(companies)
                competitive_density = self._calculate_competitive_density(companies)
            
            # Company size analysis
            average_company_size = self._calculate_average_company_size(companies)
            
            # Trend analysis
            growth_trends = self._analyze_growth_trends(companies)
            temporal_patterns = self._analyze_temporal_patterns(companies)
            
            analytics = Analytics(
                total_companies=total_companies,
                industries_count=unique_industries,
                average_company_size=average_company_size,
                industry_distribution=industry_dist,
                size_distribution=size_dist,
                location_distribution=location_dist,
                similarity_clusters=similarity_clusters,
                average_similarity=avg_similarity,
                market_concentration=market_concentration,
                competitive_density=competitive_density,
                growth_trends=growth_trends,
                temporal_patterns=temporal_patterns
            )
            
            logger.info(
                f"Analytics generated successfully",
                extra={
                    "total_companies": total_companies,
                    "industries_count": unique_industries,
                    "clusters_found": len(similarity_clusters)
                }
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}", exc_info=True)
            raise AnalyticsError(f"Failed to generate analytics: {e}") from e
    
    async def generate_market_analysis(
        self,
        companies: List[CompanyData],
        analysis_type: AnalysisType
    ) -> AnalyticsReport:
        """Generate market analysis report"""
        
        try:
            if analysis_type == AnalysisType.COMPETITIVE_LANDSCAPE:
                return await self._generate_competitive_analysis(companies)
            elif analysis_type == AnalysisType.MARKET_TRENDS:
                return await self._generate_trend_analysis(companies)
            elif analysis_type == AnalysisType.GROWTH_PATTERNS:
                return await self._generate_growth_analysis(companies)
            elif analysis_type == AnalysisType.SIMILARITY_CLUSTERS:
                return await self._generate_clustering_analysis(companies)
            else:
                return await self._generate_summary_analysis(companies)
                
        except Exception as e:
            logger.error(f"Market analysis failed: {e}", exc_info=True)
            raise AnalyticsError(f"Market analysis failed: {e}") from e
    
    async def analyze_competitive_landscape(
        self,
        companies: List[CompanyData]
    ) -> CompetitiveLandscapeReport:
        """Analyze competitive landscape and market positioning"""
        
        try:
            # Market segmentation
            segments = await self.segment_market(companies, ['industry', 'business_model'])
            
            # Competitive positioning analysis
            positioning = self._analyze_competitive_positioning(companies)
            
            # Market concentration metrics
            concentration = self._calculate_concentration_metrics(companies)
            
            # Identify opportunities
            opportunities = self._identify_market_opportunities(companies, segments)
            
            # Create visualizations
            visualizations = await self._create_competitive_visualizations(companies)
            
            return CompetitiveLandscapeReport(
                market_segments=segments,
                competitive_positioning=positioning,
                market_concentration=concentration,
                opportunities=opportunities,
                visualizations=visualizations,
                companies_analyzed=len(companies),
                market_coverage=0.8  # Placeholder - would calculate actual coverage
            )
            
        except Exception as e:
            logger.error(f"Competitive landscape analysis failed: {e}", exc_info=True)
            raise AnalyticsError(f"Competitive landscape analysis failed: {e}") from e
    
    async def calculate_market_metrics(
        self,
        companies: List[CompanyData]
    ) -> Dict[str, float]:
        """Calculate key market metrics"""
        
        metrics = {}
        
        try:
            # Market concentration (HHI)
            if companies:
                industry_counts = Counter(c.industry for c in companies if c.industry)
                total = len(companies)
                hhi = sum((count / total) ** 2 for count in industry_counts.values())
                metrics['herfindahl_index'] = hhi
                
                # Market diversity
                metrics['industry_diversity'] = len(industry_counts) / total if total > 0 else 0
                
                # Size distribution metrics
                sizes = [self._normalize_company_size(c) for c in companies]
                if sizes:
                    metrics['size_variance'] = statistics.variance(sizes) if len(sizes) > 1 else 0
                    metrics['average_size'] = statistics.mean(sizes)
                
                # Geographic concentration
                locations = [c.location for c in companies if c.location]
                if locations:
                    location_counts = Counter(locations)
                    location_hhi = sum((count / len(locations)) ** 2 for count in location_counts.values())
                    metrics['geographic_concentration'] = location_hhi
            
            return metrics
            
        except Exception as e:
            logger.error(f"Market metrics calculation failed: {e}", exc_info=True)
            return {}
    
    async def identify_trends(
        self,
        companies: List[CompanyData],
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Identify market trends and patterns"""
        
        trends = {
            'industry_trends': {},
            'size_trends': {},
            'geographic_trends': {},
            'growth_patterns': {}
        }
        
        try:
            # Industry growth trends
            industry_counts = Counter(c.industry for c in companies if c.industry)
            trends['industry_trends'] = dict(industry_counts.most_common(10))
            
            # Company size trends
            size_distribution = self._calculate_size_distribution(companies)
            trends['size_trends'] = size_distribution
            
            # Geographic expansion patterns
            location_counts = Counter(c.location for c in companies if c.location)
            trends['geographic_trends'] = dict(location_counts.most_common(10))
            
            # Growth stage patterns
            growth_stages = [getattr(c, 'growth_stage', 'unknown') for c in companies]
            growth_counts = Counter(growth_stages)
            trends['growth_patterns'] = dict(growth_counts)
            
            return trends
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}", exc_info=True)
            return trends
    
    async def segment_market(
        self,
        companies: List[CompanyData],
        segmentation_criteria: List[str]
    ) -> Dict[str, List[CompanyData]]:
        """Segment market based on specified criteria"""
        
        segments = defaultdict(list)
        
        try:
            for company in companies:
                # Create segment key based on criteria
                segment_key_parts = []
                for criterion in segmentation_criteria:
                    value = getattr(company, criterion, 'unknown')
                    if value:
                        segment_key_parts.append(f"{criterion}:{value}")
                    else:
                        segment_key_parts.append(f"{criterion}:unknown")
                
                segment_key = " | ".join(segment_key_parts)
                segments[segment_key].append(company)
            
            return dict(segments)
            
        except Exception as e:
            logger.error(f"Market segmentation failed: {e}", exc_info=True)
            return {}
    
    async def calculate_similarity_clusters(
        self,
        companies: List[CompanyData],
        cluster_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Calculate similarity clusters among companies"""
        
        if not HAS_SKLEARN or len(companies) < 3:
            # Fallback to simple grouping
            return await self._simple_clustering(companies)
        
        try:
            return await self._advanced_clustering(companies, cluster_count)
            
        except Exception as e:
            logger.error(f"Similarity clustering failed: {e}", exc_info=True)
            return await self._simple_clustering(companies)
    
    async def generate_insights(
        self,
        analytics: Analytics,
        companies: List[CompanyData]
    ) -> List[str]:
        """Generate actionable insights from analytics data"""
        
        insights = []
        
        try:
            # Industry concentration insights
            if analytics.industry_distribution:
                top_industry = max(analytics.industry_distribution.items(), key=lambda x: x[1])
                top_industry_pct = (top_industry[1] / analytics.total_companies) * 100
                
                if top_industry_pct > 50:
                    insights.append(
                        f"Market is highly concentrated in {top_industry[0]} "
                        f"({top_industry_pct:.1f}% of companies)"
                    )
                elif top_industry_pct < 20:
                    insights.append(
                        f"Market shows high diversity with {top_industry[0]} "
                        f"leading at only {top_industry_pct:.1f}%"
                    )
            
            # Size distribution insights
            if analytics.size_distribution:
                if 'startup' in analytics.size_distribution:
                    startup_pct = (analytics.size_distribution['startup'] / analytics.total_companies) * 100
                    if startup_pct > 60:
                        insights.append(
                            f"Market is dominated by early-stage companies "
                            f"({startup_pct:.1f}% startups)"
                        )
            
            # Geographic insights
            if analytics.location_distribution:
                location_count = len(analytics.location_distribution)
                if location_count > analytics.total_companies * 0.8:
                    insights.append("Companies are highly geographically distributed")
                elif location_count < analytics.total_companies * 0.3:
                    insights.append("Companies show geographic clustering")
            
            # Similarity insights
            if analytics.similarity_clusters and len(analytics.similarity_clusters) > 0:
                cluster_count = len(analytics.similarity_clusters)
                insights.append(
                    f"Market segments into {cluster_count} distinct similarity clusters"
                )
            
            # Market concentration insights
            if analytics.market_concentration:
                if analytics.market_concentration > 0.7:
                    insights.append("Market shows high concentration (potential monopolistic trends)")
                elif analytics.market_concentration < 0.3:
                    insights.append("Market is highly fragmented with many small players")
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}", exc_info=True)
            return ["Unable to generate insights due to processing error"]
    
    def _calculate_industry_distribution(self, companies: List[CompanyData]) -> Dict[str, int]:
        """Calculate distribution of companies by industry"""
        industries = [c.industry for c in companies if c.industry]
        return dict(Counter(industries))
    
    def _calculate_size_distribution(self, companies: List[CompanyData]) -> Dict[str, int]:
        """Calculate distribution of companies by size"""
        sizes = []
        for company in companies:
            # Try different size indicators
            if hasattr(company, 'company_size') and company.company_size:
                sizes.append(company.company_size)
            elif hasattr(company, 'employee_count') and company.employee_count:
                # Categorize by employee count
                if company.employee_count < 10:
                    sizes.append('startup')
                elif company.employee_count < 50:
                    sizes.append('small')
                elif company.employee_count < 250:
                    sizes.append('medium')
                else:
                    sizes.append('large')
            else:
                sizes.append('unknown')
        
        return dict(Counter(sizes))
    
    def _calculate_location_distribution(self, companies: List[CompanyData]) -> Dict[str, int]:
        """Calculate distribution of companies by location"""
        locations = [c.location for c in companies if c.location]
        return dict(Counter(locations))
    
    def _calculate_average_company_size(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate average company size"""
        sizes = []
        for company in companies:
            size = self._normalize_company_size(company)
            if size is not None:
                sizes.append(size)
        
        return statistics.mean(sizes) if sizes else None
    
    def _normalize_company_size(self, company: CompanyData) -> Optional[float]:
        """Normalize company size to a numeric value"""
        if hasattr(company, 'employee_count') and company.employee_count:
            return float(company.employee_count)
        elif hasattr(company, 'revenue') and company.revenue:
            return float(company.revenue)
        else:
            return None
    
    def _analyze_growth_trends(self, companies: List[CompanyData]) -> Dict[str, List[float]]:
        """Analyze growth trends across companies"""
        trends = {}
        
        # Group by year if founding year is available
        yearly_counts = defaultdict(int)
        for company in companies:
            if hasattr(company, 'founded_year') and company.founded_year:
                yearly_counts[company.founded_year] += 1
        
        if yearly_counts:
            years = sorted(yearly_counts.keys())
            counts = [yearly_counts[year] for year in years]
            trends['founding_trends'] = counts
        
        return trends
    
    def _analyze_temporal_patterns(self, companies: List[CompanyData]) -> Dict[str, Any]:
        """Analyze temporal patterns in company data"""
        patterns = {}
        
        # Analyze founding years
        founding_years = [getattr(c, 'founded_year', None) for c in companies]
        founding_years = [year for year in founding_years if year and year > 1900]
        
        if founding_years:
            patterns['earliest_founding'] = min(founding_years)
            patterns['latest_founding'] = max(founding_years)
            patterns['median_founding_year'] = statistics.median(founding_years)
            patterns['founding_year_spread'] = max(founding_years) - min(founding_years)
        
        return patterns
    
    async def _calculate_similarity_clusters(self, companies: List[CompanyData]) -> List[Dict[str, Any]]:
        """Calculate similarity clusters using advanced algorithms"""
        
        if not HAS_SKLEARN:
            return await self._simple_clustering(companies)
        
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            # Extract features for clustering
            features = []
            company_names = []
            
            for company in companies:
                feature_vector = []
                
                # Industry encoding (simple categorical)
                industries = list(set(c.industry for c in companies if c.industry))
                industry_encoding = [1 if company.industry == ind else 0 for ind in industries]
                feature_vector.extend(industry_encoding)
                
                # Size encoding
                size = self._normalize_company_size(company) or 0
                feature_vector.append(size)
                
                # Business model encoding
                business_models = list(set(getattr(c, 'business_model', '') for c in companies))
                bm_encoding = [1 if getattr(company, 'business_model', '') == bm else 0 for bm in business_models]
                feature_vector.extend(bm_encoding)
                
                features.append(feature_vector)
                company_names.append(company.name)
            
            if len(features) < 3:
                return await self._simple_clustering(companies)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Determine optimal number of clusters
            n_clusters = min(max(2, len(companies) // 5), 8)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Group companies by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append({
                    'company': companies[i],
                    'name': company_names[i]
                })
            
            # Convert to result format
            result_clusters = []
            for cluster_id, cluster_companies in clusters.items():
                result_clusters.append({
                    'cluster_id': int(cluster_id),
                    'size': len(cluster_companies),
                    'companies': [c['name'] for c in cluster_companies],
                    'characteristics': self._analyze_cluster_characteristics(
                        [c['company'] for c in cluster_companies]
                    )
                })
            
            return result_clusters
            
        except Exception as e:
            logger.warning(f"Advanced clustering failed, falling back to simple clustering: {e}")
            return await self._simple_clustering(companies)
    
    async def _simple_clustering(self, companies: List[CompanyData]) -> List[Dict[str, Any]]:
        """Simple clustering based on industry and business model"""
        
        clusters = defaultdict(list)
        
        for company in companies:
            # Create cluster key based on industry and business model
            industry = company.industry or 'unknown'
            business_model = getattr(company, 'business_model', 'unknown')
            cluster_key = f"{industry}_{business_model}"
            clusters[cluster_key].append(company)
        
        result_clusters = []
        for i, (cluster_key, cluster_companies) in enumerate(clusters.items()):
            result_clusters.append({
                'cluster_id': i,
                'size': len(cluster_companies),
                'companies': [c.name for c in cluster_companies],
                'characteristics': {
                    'primary_industry': cluster_companies[0].industry,
                    'business_model': getattr(cluster_companies[0], 'business_model', 'unknown'),
                    'cluster_basis': cluster_key
                }
            })
        
        return result_clusters
    
    def _analyze_cluster_characteristics(self, companies: List[CompanyData]) -> Dict[str, Any]:
        """Analyze characteristics of a company cluster"""
        
        characteristics = {}
        
        # Most common industry
        industries = [c.industry for c in companies if c.industry]
        if industries:
            characteristics['primary_industry'] = Counter(industries).most_common(1)[0][0]
        
        # Most common business model
        business_models = [getattr(c, 'business_model', '') for c in companies]
        if business_models:
            characteristics['primary_business_model'] = Counter(business_models).most_common(1)[0][0]
        
        # Average size
        sizes = [self._normalize_company_size(c) for c in companies]
        sizes = [s for s in sizes if s is not None]
        if sizes:
            characteristics['average_size'] = statistics.mean(sizes)
        
        # Geographic concentration
        locations = [c.location for c in companies if c.location]
        if locations:
            characteristics['primary_location'] = Counter(locations).most_common(1)[0][0]
        
        return characteristics
    
    def _calculate_average_similarity(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate average similarity between companies"""
        
        if not HAS_SKLEARN or len(companies) < 2:
            return None
        
        try:
            # This is a simplified similarity calculation
            # In practice, would use actual embeddings from vector database
            similarities = []
            
            for i, company1 in enumerate(companies):
                for j, company2 in enumerate(companies[i+1:], i+1):
                    # Simple similarity based on shared attributes
                    similarity = 0.0
                    
                    if company1.industry == company2.industry:
                        similarity += 0.4
                    
                    if getattr(company1, 'business_model', '') == getattr(company2, 'business_model', ''):
                        similarity += 0.3
                    
                    if company1.location == company2.location:
                        similarity += 0.2
                    
                    # Size similarity
                    size1 = self._normalize_company_size(company1)
                    size2 = self._normalize_company_size(company2)
                    if size1 and size2:
                        size_diff = abs(size1 - size2) / max(size1, size2)
                        similarity += 0.1 * (1 - size_diff)
                    
                    similarities.append(similarity)
            
            return statistics.mean(similarities) if similarities else None
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return None
    
    def _calculate_market_concentration(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate market concentration using Herfindahl-Hirschman Index"""
        
        if not companies:
            return None
        
        # Calculate based on industry distribution
        industry_counts = Counter(c.industry for c in companies if c.industry)
        total = len(companies)
        
        if not industry_counts:
            return None
        
        # HHI calculation
        hhi = sum((count / total) ** 2 for count in industry_counts.values())
        return hhi
    
    def _calculate_competitive_density(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate competitive density in the market"""
        
        if not companies:
            return None
        
        # Simple competitive density based on industry diversity
        unique_industries = len(set(c.industry for c in companies if c.industry))
        total_companies = len(companies)
        
        return unique_industries / total_companies if total_companies > 0 else None
    
    async def _generate_competitive_analysis(self, companies: List[CompanyData]) -> AnalyticsReport:
        """Generate competitive analysis report"""
        
        analytics = await self.generate_analytics(companies)
        
        # Create basic visualizations
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Industry Distribution",
                data=analytics.industry_distribution,
                chart_type="pie"
            ),
            Visualization(
                type=VisualizationType.CHARTS,
                title="Company Size Distribution",
                data=analytics.size_distribution,
                chart_type="bar"
            )
        ]
        
        insights = await self.generate_insights(analytics, companies)
        
        return AnalyticsReport(
            report_type=AnalysisType.COMPETITIVE_LANDSCAPE,
            title="Competitive Landscape Analysis",
            summary=f"Analysis of {len(companies)} companies across {analytics.industries_count} industries",
            analytics=analytics,
            visualizations=visualizations,
            key_insights=insights
        )
    
    async def _generate_trend_analysis(self, companies: List[CompanyData]) -> AnalyticsReport:
        """Generate trend analysis report"""
        
        analytics = await self.generate_analytics(companies)
        trends = await self.identify_trends(companies)
        
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Industry Trends",
                data=trends.get('industry_trends', {}),
                chart_type="line"
            )
        ]
        
        insights = [
            f"Analyzed trends across {len(companies)} companies",
            f"Identified {len(trends.get('industry_trends', {}))} industry categories",
            f"Geographic presence spans {len(analytics.location_distribution)} locations"
        ]
        
        return AnalyticsReport(
            report_type=AnalysisType.TRENDS,
            title="Market Trend Analysis",
            summary="Comprehensive analysis of market trends and patterns",
            analytics=analytics,
            visualizations=visualizations,
            key_insights=insights
        )
    
    async def _generate_growth_analysis(self, companies: List[CompanyData]) -> AnalyticsReport:
        """Generate growth pattern analysis report"""
        
        analytics = await self.generate_analytics(companies)
        
        # Analyze growth patterns
        growth_data = analytics.growth_trends
        
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Growth Patterns",
                data=growth_data,
                chart_type="line"
            )
        ]
        
        insights = [
            f"Analyzed growth patterns for {len(companies)} companies",
            "Identified key growth trends and inflection points"
        ]
        
        return AnalyticsReport(
            report_type=AnalysisType.GROWTH_PATTERNS,
            title="Growth Pattern Analysis",
            summary="Analysis of company growth patterns and trends",
            analytics=analytics,
            visualizations=visualizations,
            key_insights=insights
        )
    
    async def _generate_clustering_analysis(self, companies: List[CompanyData]) -> AnalyticsReport:
        """Generate similarity clustering analysis report"""
        
        analytics = await self.generate_analytics(companies)
        clusters = analytics.similarity_clusters
        
        visualizations = [
            Visualization(
                type=VisualizationType.NETWORK,
                title="Company Similarity Clusters",
                data={'clusters': clusters},
                chart_type="network"
            )
        ]
        
        insights = [
            f"Identified {len(clusters)} distinct company clusters",
            f"Average cluster size: {statistics.mean([c['size'] for c in clusters]) if clusters else 0:.1f} companies"
        ]
        
        return AnalyticsReport(
            report_type=AnalysisType.SIMILARITY_CLUSTERS,
            title="Company Similarity Analysis",
            summary="Analysis of company similarity patterns and clustering",
            analytics=analytics,
            visualizations=visualizations,
            key_insights=insights
        )
    
    async def _generate_summary_analysis(self, companies: List[CompanyData]) -> AnalyticsReport:
        """Generate summary analysis report"""
        
        analytics = await self.generate_analytics(companies)
        insights = await self.generate_insights(analytics, companies)
        
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Market Overview",
                data=analytics.industry_distribution,
                chart_type="pie"
            )
        ]
        
        return AnalyticsReport(
            report_type=AnalysisType.SUMMARY,
            title="Market Summary Analysis",
            summary=f"Comprehensive summary of {len(companies)} companies",
            analytics=analytics,
            visualizations=visualizations,
            key_insights=insights
        )
    
    def _analyze_competitive_positioning(self, companies: List[CompanyData]) -> Dict[str, Any]:
        """Analyze competitive positioning"""
        
        positioning = {
            'market_leaders': [],
            'challengers': [],
            'niche_players': [],
            'positioning_factors': []
        }
        
        # Simple positioning based on company size and industry presence
        size_threshold_large = 100  # employee count
        size_threshold_medium = 25
        
        for company in companies:
            employee_count = getattr(company, 'employee_count', 0) or 0
            
            if employee_count > size_threshold_large:
                positioning['market_leaders'].append(company.name)
            elif employee_count > size_threshold_medium:
                positioning['challengers'].append(company.name)
            else:
                positioning['niche_players'].append(company.name)
        
        positioning['positioning_factors'] = [
            'Company size (employee count)',
            'Industry presence',
            'Market share indicators'
        ]
        
        return positioning
    
    def _calculate_concentration_metrics(self, companies: List[CompanyData]) -> Dict[str, float]:
        """Calculate market concentration metrics"""
        
        metrics = {}
        
        # Industry concentration
        industry_counts = Counter(c.industry for c in companies if c.industry)
        if industry_counts:
            total = sum(industry_counts.values())
            hhi = sum((count / total) ** 2 for count in industry_counts.values())
            metrics['industry_hhi'] = hhi
            
            # CR4 (concentration ratio for top 4)
            top_4 = sum(count for _, count in industry_counts.most_common(4))
            metrics['industry_cr4'] = top_4 / total if total > 0 else 0
        
        # Geographic concentration
        location_counts = Counter(c.location for c in companies if c.location)
        if location_counts:
            total = sum(location_counts.values())
            geo_hhi = sum((count / total) ** 2 for count in location_counts.values())
            metrics['geographic_hhi'] = geo_hhi
        
        return metrics
    
    def _identify_market_opportunities(
        self, 
        companies: List[CompanyData], 
        segments: Dict[str, List[CompanyData]]
    ) -> List[Dict[str, Any]]:
        """Identify market opportunities"""
        
        opportunities = []
        
        # Underserved segments (segments with few companies)
        segment_sizes = {segment: len(companies) for segment, companies in segments.items()}
        avg_segment_size = statistics.mean(segment_sizes.values()) if segment_sizes else 0
        
        for segment, size in segment_sizes.items():
            if size < avg_segment_size * 0.5:  # Less than half the average
                opportunities.append({
                    'type': 'underserved_segment',
                    'segment': segment,
                    'current_players': size,
                    'opportunity_score': 1.0 - (size / avg_segment_size) if avg_segment_size > 0 else 0
                })
        
        # Geographic opportunities
        location_counts = Counter(c.location for c in companies if c.location)
        if location_counts:
            # Find locations with growing presence
            sorted_locations = location_counts.most_common()
            if len(sorted_locations) > 3:
                emerging_locations = sorted_locations[2:]  # Not top 2
                for location, count in emerging_locations[:3]:  # Top 3 emerging
                    opportunities.append({
                        'type': 'geographic_expansion',
                        'location': location,
                        'current_presence': count,
                        'opportunity_score': 0.7  # Fixed score for now
                    })
        
        return opportunities
    
    async def _create_competitive_visualizations(
        self, 
        companies: List[CompanyData]
    ) -> List[Visualization]:
        """Create visualizations for competitive analysis"""
        
        visualizations = []
        
        # Industry distribution pie chart
        industry_dist = self._calculate_industry_distribution(companies)
        if industry_dist:
            visualizations.append(Visualization(
                type=VisualizationType.CHARTS,
                title="Market Share by Industry",
                data=industry_dist,
                chart_type="pie",
                description="Distribution of companies across industries"
            ))
        
        # Company size distribution
        size_dist = self._calculate_size_distribution(companies)
        if size_dist:
            visualizations.append(Visualization(
                type=VisualizationType.CHARTS,
                title="Company Size Distribution",
                data=size_dist,
                chart_type="bar",
                description="Distribution of companies by size category"
            ))
        
        # Geographic distribution heatmap
        location_dist = self._calculate_location_distribution(companies)
        if location_dist:
            visualizations.append(Visualization(
                type=VisualizationType.HEATMAPS,
                title="Geographic Distribution",
                data=location_dist,
                description="Geographic concentration of companies"
            ))
        
        return visualizations