#!/usr/bin/env python3
"""
Theodore v2 Visualization Engine Port

Port interface for data visualization and dashboard creation functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ...domain.models.company import CompanyData
from ...domain.models.export import (
    Visualization, VisualizationType, VisualizationConfig,
    InteractiveDashboard, DashboardType
)


class VisualizationEnginePort(ABC):
    """
    Port interface for comprehensive visualization engine
    
    Provides chart generation, dashboard creation, and interactive
    visualization capabilities.
    """
    
    @abstractmethod
    async def create_visualizations(
        self,
        companies: List[CompanyData],
        config: Optional[Dict[str, Any]] = None
    ) -> List[Visualization]:
        """
        Create visualizations for company data
        
        Args:
            companies: Company data to visualize
            config: Optional visualization configuration
            
        Returns:
            List of generated visualizations
            
        Raises:
            VisualizationError: If visualization creation fails
        """
        pass
    
    @abstractmethod
    async def create_chart(
        self,
        data: Dict[str, Any],
        chart_type: str,
        title: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Visualization:
        """
        Create a specific chart visualization
        
        Args:
            data: Chart data
            chart_type: Type of chart (bar, pie, line, etc.)
            title: Chart title
            config: Optional chart configuration
            
        Returns:
            Chart visualization object
        """
        pass
    
    @abstractmethod
    async def create_interactive_dashboard(
        self,
        companies: List[CompanyData],
        dashboard_type: DashboardType
    ) -> InteractiveDashboard:
        """
        Create interactive dashboard with real-time capabilities
        
        Args:
            companies: Company data for dashboard
            dashboard_type: Type of dashboard to create
            
        Returns:
            Interactive dashboard object
        """
        pass
    
    @abstractmethod
    async def create_network_visualization(
        self,
        companies: List[CompanyData],
        relationship_data: Dict[str, Any]
    ) -> Visualization:
        """
        Create network/graph visualization showing relationships
        
        Args:
            companies: Companies to include in network
            relationship_data: Relationship/similarity data
            
        Returns:
            Network visualization object
        """
        pass
    
    @abstractmethod
    async def create_heatmap(
        self,
        data: Dict[str, Any],
        title: str,
        x_axis: str,
        y_axis: str
    ) -> Visualization:
        """
        Create heatmap visualization
        
        Args:
            data: Heatmap data
            title: Heatmap title
            x_axis: X-axis label
            y_axis: Y-axis label
            
        Returns:
            Heatmap visualization object
        """
        pass
    
    @abstractmethod
    async def create_geographic_visualization(
        self,
        companies: List[CompanyData],
        map_type: str = "distribution"
    ) -> Visualization:
        """
        Create geographic visualization of company locations
        
        Args:
            companies: Companies with location data
            map_type: Type of geographic visualization
            
        Returns:
            Geographic visualization object
        """
        pass
    
    @abstractmethod
    async def export_visualization(
        self,
        visualization: Visualization,
        output_path: str,
        format: str = "png"
    ) -> str:
        """
        Export visualization to file
        
        Args:
            visualization: Visualization to export
            output_path: Output file path
            format: Export format (png, svg, pdf, html)
            
        Returns:
            Path to exported file
        """
        pass
    
    @abstractmethod
    async def get_supported_chart_types(self) -> List[str]:
        """
        Get list of supported chart types
        
        Returns:
            List of supported chart type names
        """
        pass
    
    @abstractmethod
    async def validate_visualization_config(
        self,
        config: VisualizationConfig
    ) -> bool:
        """
        Validate visualization configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        pass