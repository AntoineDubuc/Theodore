#!/usr/bin/env python3
"""
Tests for Analytics Engine
"""

import pytest
from unittest.mock import patch

from src.infrastructure.adapters.io.analytics_engine import (
    AnalyticsEngine, AnalyticsError
)
from src.core.domain.models.company import CompanyData
from src.core.domain.models.export import AnalysisType


class TestAnalyticsEngine:
    """Test cases for AnalyticsEngine"""
    
    @pytest.fixture
    def analytics_engine(self):
        """Analytics engine instance"""
        return AnalyticsEngine()
    
    @pytest.fixture
    def sample_companies(self):
        """Sample company data with diverse characteristics"""
        return [
            CompanyData(
                name="TechCorp",
                industry="Technology",
                location="San Francisco",
                description="AI and machine learning company",
                employee_count=150,
                founded_year=2018
            ),
            CompanyData(
                name="FinanceInc", 
                industry="Finance",
                location="New York",
                description="Financial services provider",
                employee_count=500,
                founded_year=2010
            ),
            CompanyData(
                name="HealthCo",
                industry="Healthcare",
                location="Boston",
                description="Healthcare technology startup",
                employee_count=45,
                founded_year=2020
            ),
            CompanyData(
                name="StartupXYZ",
                industry="Technology",
                location="San Francisco",
                description="Web development and cloud services",
                employee_count=25,
                founded_year=2022
            ),
            CompanyData(
                name="BigBank",
                industry="Finance",
                location="Chicago",
                description="Commercial banking services",
                employee_count=1000,
                founded_year=1995
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_analytics_basic(self, analytics_engine, sample_companies):
        """Test basic analytics generation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        assert analytics.total_companies == 5
        assert analytics.industries_count == 3  # Technology, Finance, Healthcare
        assert 'Technology' in analytics.industry_distribution
        assert 'Finance' in analytics.industry_distribution
        assert 'Healthcare' in analytics.industry_distribution
        
        # Check industry distribution counts
        assert analytics.industry_distribution['Technology'] == 2
        assert analytics.industry_distribution['Finance'] == 2
        assert analytics.industry_distribution['Healthcare'] == 1
        
        # Check location distribution
        assert analytics.location_distribution['San Francisco'] == 2
        assert analytics.location_distribution['New York'] == 1
        assert analytics.location_distribution['Boston'] == 1
        assert analytics.location_distribution['Chicago'] == 1
    
    @pytest.mark.asyncio
    async def test_generate_analytics_empty_dataset(self, analytics_engine):
        """Test analytics generation with empty dataset"""
        
        analytics = await analytics_engine.generate_analytics([])
        
        assert analytics.total_companies == 0
        assert analytics.industries_count == 0
        assert analytics.industry_distribution == {}
        assert analytics.size_distribution == {}
        assert analytics.location_distribution == {}
    
    @pytest.mark.asyncio
    async def test_size_distribution_calculation(self, analytics_engine, sample_companies):
        """Test company size distribution calculation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        # Based on employee counts: 25, 45, 150, 500, 1000
        # startup (1-9): 0, small (10-49): 2, medium (50-249): 1, large (250+): 2
        assert analytics.size_distribution['small'] == 2  # 25, 45 employees
        assert analytics.size_distribution['medium'] == 1  # 150 employees
        assert analytics.size_distribution['large'] == 2  # 500, 1000 employees
    
    @pytest.mark.asyncio
    async def test_average_company_size_calculation(self, analytics_engine, sample_companies):
        """Test average company size calculation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        # Average of 25, 45, 150, 500, 1000 = 344
        expected_avg = (25 + 45 + 150 + 500 + 1000) / 5
        assert abs(analytics.average_company_size - expected_avg) < 0.1
    
    @pytest.mark.asyncio
    async def test_temporal_patterns_analysis(self, analytics_engine, sample_companies):
        """Test temporal patterns analysis"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        # Founding years: 1995, 2010, 2018, 2020, 2022
        assert analytics.temporal_patterns['earliest_founding'] == 1995
        assert analytics.temporal_patterns['latest_founding'] == 2022
        assert analytics.temporal_patterns['founding_year_spread'] == 27  # 2022 - 1995
    
    @pytest.mark.asyncio
    async def test_similarity_clustering_without_sklearn(self, analytics_engine, sample_companies):
        """Test similarity clustering fallback without sklearn"""
        
        with patch.object(analytics_engine, 'available_features', {'sklearn': False}):
            analytics = await analytics_engine.generate_analytics(sample_companies)
            
            # Should fall back to simple clustering
            assert len(analytics.similarity_clusters) > 0
            
            # Simple clustering should group by industry_businessmodel
            for cluster in analytics.similarity_clusters:
                assert 'cluster_id' in cluster
                assert 'size' in cluster
                assert 'companies' in cluster
                assert 'characteristics' in cluster
    
    @pytest.mark.asyncio
    async def test_similarity_clustering_with_sklearn(self, analytics_engine, sample_companies):
        """Test similarity clustering with sklearn (if available)"""
        
        if analytics_engine.available_features.get('sklearn', False):
            analytics = await analytics_engine.generate_analytics(sample_companies)
            
            # Should use advanced clustering
            assert len(analytics.similarity_clusters) > 0
            
            for cluster in analytics.similarity_clusters:
                assert isinstance(cluster['cluster_id'], int)
                assert cluster['size'] > 0
                assert len(cluster['companies']) == cluster['size']
                assert 'characteristics' in cluster
    
    @pytest.mark.asyncio
    async def test_market_concentration_calculation(self, analytics_engine, sample_companies):
        """Test market concentration (HHI) calculation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        # HHI calculation: (2/5)^2 + (2/5)^2 + (1/5)^2 = 0.16 + 0.16 + 0.04 = 0.36
        expected_hhi = (2/5)**2 + (2/5)**2 + (1/5)**2
        assert abs(analytics.market_concentration - expected_hhi) < 0.01
    
    @pytest.mark.asyncio
    async def test_competitive_density_calculation(self, analytics_engine, sample_companies):
        """Test competitive density calculation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        
        # 3 unique industries / 5 total companies = 0.6
        expected_density = 3 / 5
        assert abs(analytics.competitive_density - expected_density) < 0.01
    
    @pytest.mark.asyncio
    async def test_generate_market_analysis_competitive_landscape(self, analytics_engine, sample_companies):
        """Test competitive landscape analysis"""
        
        report = await analytics_engine.generate_market_analysis(
            sample_companies, AnalysisType.COMPETITIVE_LANDSCAPE
        )
        
        assert report.report_type == AnalysisType.COMPETITIVE_LANDSCAPE
        assert "Competitive Landscape Analysis" in report.title
        assert len(report.key_insights) > 0
        assert report.analytics is not None
        assert len(report.visualizations) > 0
    
    @pytest.mark.asyncio
    async def test_generate_market_analysis_trends(self, analytics_engine, sample_companies):
        """Test market trends analysis"""
        
        report = await analytics_engine.generate_market_analysis(
            sample_companies, AnalysisType.MARKET_TRENDS
        )
        
        assert report.report_type == AnalysisType.TRENDS
        assert "Trend Analysis" in report.title
        assert len(report.key_insights) > 0
        assert report.analytics is not None
    
    @pytest.mark.asyncio
    async def test_generate_market_analysis_growth_patterns(self, analytics_engine, sample_companies):
        """Test growth patterns analysis"""
        
        report = await analytics_engine.generate_market_analysis(
            sample_companies, AnalysisType.GROWTH_PATTERNS
        )
        
        assert report.report_type == AnalysisType.GROWTH_PATTERNS
        assert "Growth Pattern Analysis" in report.title
        assert len(report.key_insights) > 0
        assert report.analytics is not None
    
    @pytest.mark.asyncio
    async def test_generate_market_analysis_similarity_clusters(self, analytics_engine, sample_companies):
        """Test similarity clusters analysis"""
        
        report = await analytics_engine.generate_market_analysis(
            sample_companies, AnalysisType.SIMILARITY_CLUSTERS
        )
        
        assert report.report_type == AnalysisType.SIMILARITY_CLUSTERS
        assert "Similarity Analysis" in report.title
        assert len(report.key_insights) > 0
        assert report.analytics is not None
    
    @pytest.mark.asyncio
    async def test_analyze_competitive_landscape(self, analytics_engine, sample_companies):
        """Test comprehensive competitive landscape analysis"""
        
        landscape_report = await analytics_engine.analyze_competitive_landscape(sample_companies)
        
        assert landscape_report.companies_analyzed == 5
        assert landscape_report.market_coverage > 0
        assert len(landscape_report.market_segments) > 0
        assert landscape_report.competitive_positioning is not None
        assert landscape_report.market_concentration is not None
        assert len(landscape_report.opportunities) >= 0
        assert len(landscape_report.visualizations) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_market_metrics(self, analytics_engine, sample_companies):
        """Test market metrics calculation"""
        
        metrics = await analytics_engine.calculate_market_metrics(sample_companies)
        
        assert 'herfindahl_index' in metrics
        assert 'industry_diversity' in metrics
        assert 'size_variance' in metrics
        assert 'average_size' in metrics
        assert 'geographic_concentration' in metrics
        
        # Verify metric values are reasonable
        assert 0 <= metrics['herfindahl_index'] <= 1
        assert 0 <= metrics['industry_diversity'] <= 1
        assert metrics['size_variance'] >= 0
        assert metrics['average_size'] > 0
        assert 0 <= metrics['geographic_concentration'] <= 1
    
    @pytest.mark.asyncio
    async def test_identify_trends(self, analytics_engine, sample_companies):
        """Test trend identification"""
        
        trends = await analytics_engine.identify_trends(sample_companies)
        
        assert 'industry_trends' in trends
        assert 'size_trends' in trends
        assert 'geographic_trends' in trends
        assert 'growth_patterns' in trends
        
        # Check that we have meaningful trend data
        assert len(trends['industry_trends']) > 0
        assert len(trends['size_trends']) > 0
        assert len(trends['geographic_trends']) > 0
    
    @pytest.mark.asyncio
    async def test_segment_market(self, analytics_engine, sample_companies):
        """Test market segmentation"""
        
        segments = await analytics_engine.segment_market(
            sample_companies, ['industry', 'location']
        )
        
        assert len(segments) > 0
        
        # Verify segment structure
        for segment_key, companies in segments.items():
            assert 'industry:' in segment_key
            assert 'location:' in segment_key
            assert len(companies) > 0
            assert all(isinstance(company, CompanyData) for company in companies)
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_clusters_basic(self, analytics_engine, sample_companies):
        """Test similarity clusters calculation"""
        
        clusters = await analytics_engine.calculate_similarity_clusters(sample_companies)
        
        assert len(clusters) > 0
        
        for cluster in clusters:
            assert 'cluster_id' in cluster
            assert 'size' in cluster
            assert 'companies' in cluster
            assert 'characteristics' in cluster
            assert cluster['size'] > 0
            assert len(cluster['companies']) == cluster['size']
    
    @pytest.mark.asyncio
    async def test_generate_insights_comprehensive(self, analytics_engine, sample_companies):
        """Test comprehensive insights generation"""
        
        analytics = await analytics_engine.generate_analytics(sample_companies)
        insights = await analytics_engine.generate_insights(analytics, sample_companies)
        
        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)
        
        # Should contain insights about concentration, diversity, etc.
        insights_text = ' '.join(insights).lower()
        assert any(keyword in insights_text for keyword in [
            'market', 'concentration', 'diversity', 'companies', 'industry'
        ])
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analytics_generation(self, analytics_engine):
        """Test error handling in analytics generation"""
        
        # Test with malformed data that might cause errors
        malformed_companies = [
            CompanyData(name="Test", industry=None, location=None),
            # This might cause issues in some calculations
        ]
        
        # Should not raise an exception, but handle gracefully
        analytics = await analytics_engine.generate_analytics(malformed_companies)
        
        assert analytics.total_companies == 1
        assert analytics.industries_count == 0  # No valid industries
    
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, analytics_engine):
        """Test performance with larger dataset"""
        
        # Create a larger dataset
        large_dataset = []
        industries = ['Tech', 'Finance', 'Healthcare', 'Manufacturing', 'Retail']
        locations = ['SF', 'NYC', 'LA', 'Chicago', 'Boston']
        
        for i in range(100):
            large_dataset.append(CompanyData(
                name=f"Company {i}",
                industry=industries[i % len(industries)],
                location=locations[i % len(locations)],
                employee_count=10 + (i * 5),
                founded_year=2000 + (i % 23)
            ))
        
        analytics = await analytics_engine.generate_analytics(large_dataset)
        
        assert analytics.total_companies == 100
        assert analytics.industries_count == 5
        assert len(analytics.industry_distribution) == 5
        assert len(analytics.location_distribution) == 5
    
    @pytest.mark.asyncio
    async def test_clustering_with_insufficient_data(self, analytics_engine):
        """Test clustering behavior with insufficient data"""
        
        # Only 2 companies - should fall back to simple clustering
        small_dataset = [
            CompanyData(name="A", industry="Tech", location="SF"),
            CompanyData(name="B", industry="Finance", location="NYC")
        ]
        
        analytics = await analytics_engine.generate_analytics(small_dataset)
        
        # Should still produce some clustering results
        assert len(analytics.similarity_clusters) >= 0
        
        if analytics.similarity_clusters:
            total_companies_in_clusters = sum(
                cluster['size'] for cluster in analytics.similarity_clusters
            )
            assert total_companies_in_clusters == 2


class TestAnalyticsEngineEdgeCases:
    """Test edge cases and error conditions for AnalyticsEngine"""
    
    @pytest.fixture
    def analytics_engine(self):
        return AnalyticsEngine()
    
    @pytest.mark.asyncio
    async def test_companies_with_missing_data(self, analytics_engine):
        """Test analytics with companies missing various data fields"""
        
        incomplete_companies = [
            CompanyData(name="Complete", industry="Tech", location="SF", employee_count=100),
            CompanyData(name="NoIndustry", location="NYC", employee_count=50),
            CompanyData(name="NoLocation", industry="Finance", employee_count=200),
            CompanyData(name="NoEmployees", industry="Healthcare", location="Boston"),
            CompanyData(name="OnlyName")  # Minimal data
        ]
        
        analytics = await analytics_engine.generate_analytics(incomplete_companies)
        
        assert analytics.total_companies == 5
        
        # Should handle missing data gracefully
        assert analytics.industries_count == 3  # Only 3 companies have industry
        assert len(analytics.location_distribution) == 3  # Only 3 companies have location
        
        # Size distribution should handle missing employee counts
        assert 'unknown' in analytics.size_distribution
    
    @pytest.mark.asyncio
    async def test_companies_with_extreme_values(self, analytics_engine):
        """Test analytics with extreme or unusual values"""
        
        extreme_companies = [
            CompanyData(
                name="VeryOld", 
                industry="Manufacturing", 
                location="Detroit",
                employee_count=1000000,  # Very large
                founded_year=1800  # Very old
            ),
            CompanyData(
                name="VeryNew",
                industry="AI",
                location="Austin", 
                employee_count=1,  # Very small
                founded_year=2024  # Very recent
            ),
            CompanyData(
                name="Normal",
                industry="Tech",
                location="SF",
                employee_count=100,
                founded_year=2010
            )
        ]
        
        analytics = await analytics_engine.generate_analytics(extreme_companies)
        
        assert analytics.total_companies == 3
        
        # Should handle extreme values without crashing
        assert analytics.temporal_patterns['founding_year_spread'] == 224  # 2024 - 1800
        assert analytics.average_company_size is not None
    
    @pytest.mark.asyncio
    async def test_duplicate_companies(self, analytics_engine):
        """Test analytics with duplicate company data"""
        
        base_company = CompanyData(
            name="DuplicateTest",
            industry="Tech", 
            location="SF",
            employee_count=100
        )
        
        # Create duplicates
        duplicate_companies = [base_company] * 5
        
        analytics = await analytics_engine.generate_analytics(duplicate_companies)
        
        assert analytics.total_companies == 5
        assert analytics.industries_count == 1
        assert analytics.industry_distribution['Tech'] == 5
        assert analytics.location_distribution['SF'] == 5
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, analytics_engine):
        """Test analytics with unicode and special characters"""
        
        unicode_companies = [
            CompanyData(
                name="Café Technologies",
                industry="Food & Beverage",
                location="São Paulo",
                description="Café management with AI"
            ),
            CompanyData(
                name="北京科技",
                industry="Technology",
                location="北京",
                description="Chinese tech company"
            ),
            CompanyData(
                name="Entreprise français",
                industry="Consulting", 
                location="Paris",
                description="French consulting firm"
            )
        ]
        
        analytics = await analytics_engine.generate_analytics(unicode_companies)
        
        assert analytics.total_companies == 3
        assert analytics.industries_count == 3
        
        # Should handle unicode characters in distributions
        assert "São Paulo" in analytics.location_distribution
        assert "北京" in analytics.location_distribution
        assert "Paris" in analytics.location_distribution