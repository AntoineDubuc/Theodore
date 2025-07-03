#!/usr/bin/env python3
"""
Theodore v2 Analytics Engine Port

Port interface for comprehensive analytics and business intelligence functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ...domain.models.company import CompanyData
from ...domain.models.export import (
    Analytics, AnalyticsReport, AnalysisType, CompetitiveLandscapeReport
)


class AnalyticsEnginePort(ABC):
    """
    Port interface for comprehensive analytics engine
    
    Provides market analysis, competitive intelligence, and business insights
    from company data.
    """
    
    @abstractmethod
    async def generate_analytics(
        self,
        companies: List[CompanyData],
        config: Optional[Dict[str, Any]] = None
    ) -> Analytics:
        """
        Generate comprehensive analytics for company data
        
        Args:
            companies: List of company data to analyze
            config: Optional configuration for analytics generation
            
        Returns:
            Analytics object with computed insights
            
        Raises:
            AnalyticsError: If analytics generation fails
        """
        pass
    
    @abstractmethod
    async def generate_market_analysis(
        self,
        companies: List[CompanyData],
        analysis_type: AnalysisType
    ) -> AnalyticsReport:
        """
        Generate market analysis report
        
        Args:
            companies: Company data for analysis
            analysis_type: Type of analysis to perform
            
        Returns:
            Analytics report with market insights
        """
        pass
    
    @abstractmethod
    async def analyze_competitive_landscape(
        self,
        companies: List[CompanyData]
    ) -> CompetitiveLandscapeReport:
        """
        Analyze competitive landscape and market positioning
        
        Args:
            companies: Companies to analyze
            
        Returns:
            Competitive landscape report with positioning insights
        """
        pass
    
    @abstractmethod
    async def calculate_market_metrics(
        self,
        companies: List[CompanyData]
    ) -> Dict[str, float]:
        """
        Calculate key market metrics
        
        Args:
            companies: Companies for metric calculation
            
        Returns:
            Dictionary of calculated metrics
        """
        pass
    
    @abstractmethod
    async def identify_trends(
        self,
        companies: List[CompanyData],
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify market trends and patterns
        
        Args:
            companies: Company data for trend analysis
            time_period: Optional time period for analysis
            
        Returns:
            Dictionary containing trend data and insights
        """
        pass
    
    @abstractmethod
    async def segment_market(
        self,
        companies: List[CompanyData],
        segmentation_criteria: List[str]
    ) -> Dict[str, List[CompanyData]]:
        """
        Segment market based on specified criteria
        
        Args:
            companies: Companies to segment
            segmentation_criteria: Fields to use for segmentation
            
        Returns:
            Dictionary mapping segment names to company lists
        """
        pass
    
    @abstractmethod
    async def calculate_similarity_clusters(
        self,
        companies: List[CompanyData],
        cluster_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate similarity clusters among companies
        
        Args:
            companies: Companies to cluster
            cluster_count: Optional number of clusters to create
            
        Returns:
            List of cluster definitions with member companies
        """
        pass
    
    @abstractmethod
    async def generate_insights(
        self,
        analytics: Analytics,
        companies: List[CompanyData]
    ) -> List[str]:
        """
        Generate actionable insights from analytics data
        
        Args:
            analytics: Analytics data
            companies: Original company data
            
        Returns:
            List of insight strings
        """
        pass