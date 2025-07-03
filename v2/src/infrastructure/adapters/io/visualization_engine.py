#!/usr/bin/env python3
"""
Theodore v2 Visualization Engine Implementation

Comprehensive visualization engine for charts, dashboards, and interactive visualizations.
"""

import asyncio
import json
import base64
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
import statistics
from collections import Counter

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from ....core.ports.io.visualization_engine_port import VisualizationEnginePort
from ....core.domain.models.company import CompanyData
from ....core.domain.models.export import (
    Visualization, VisualizationType, VisualizationConfig,
    InteractiveDashboard, DashboardType
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class VisualizationError(Exception):
    """Visualization operation error"""
    pass


class UnsupportedVisualizationError(VisualizationError):
    """Unsupported visualization type error"""
    pass


class VisualizationEngine(VisualizationEnginePort):
    """
    Comprehensive visualization engine
    
    Provides:
    - Chart generation (bar, pie, line, scatter, heatmap)
    - Interactive dashboards
    - Network visualizations
    - Geographic visualizations
    - Export capabilities
    """
    
    def __init__(self):
        self.available_features = {
            'matplotlib': HAS_MATPLOTLIB,
            'plotly': HAS_PLOTLY,
            'networkx': HAS_NETWORKX
        }
        
        # Chart type mappings
        self.chart_types = {
            'bar': self._create_bar_chart,
            'pie': self._create_pie_chart,
            'line': self._create_line_chart,
            'scatter': self._create_scatter_chart,
            'heatmap': self._create_heatmap_chart,
            'histogram': self._create_histogram_chart,
            'box': self._create_box_chart
        }
    
    async def create_visualizations(
        self,
        companies: List[CompanyData],
        config: Optional[Dict[str, Any]] = None
    ) -> List[Visualization]:
        """Create comprehensive visualizations for company data"""
        
        if not companies:
            return []
        
        config = config or {}
        visualizations = []
        
        try:
            logger.info(f"Creating visualizations for {len(companies)} companies")
            
            # Industry distribution pie chart
            industry_viz = await self._create_industry_distribution(companies)
            if industry_viz:
                visualizations.append(industry_viz)
            
            # Company size distribution bar chart
            size_viz = await self._create_size_distribution(companies)
            if size_viz:
                visualizations.append(size_viz)
            
            # Geographic distribution heatmap
            geo_viz = await self._create_geographic_distribution(companies)
            if geo_viz:
                visualizations.append(geo_viz)
            
            # Business model analysis
            business_model_viz = await self._create_business_model_analysis(companies)
            if business_model_viz:
                visualizations.append(business_model_viz)
            
            # Founding year trends (if data available)
            trends_viz = await self._create_founding_trends(companies)
            if trends_viz:
                visualizations.append(trends_viz)
            
            # Technology stack analysis (if data available)
            tech_viz = await self._create_technology_analysis(companies)
            if tech_viz:
                visualizations.append(tech_viz)
            
            logger.info(f"Created {len(visualizations)} visualizations successfully")
            return visualizations
            
        except Exception as e:
            logger.error(f"Visualization creation failed: {e}", exc_info=True)
            raise VisualizationError(f"Failed to create visualizations: {e}") from e
    
    async def create_chart(
        self,
        data: Dict[str, Any],
        chart_type: str,
        title: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Visualization:
        """Create a specific chart visualization"""
        
        if chart_type not in self.chart_types:
            supported = list(self.chart_types.keys())
            raise UnsupportedVisualizationError(
                f"Chart type '{chart_type}' not supported. Available: {supported}"
            )
        
        config = config or {}
        
        try:
            chart_function = self.chart_types[chart_type]
            return await chart_function(data, title, config)
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}", exc_info=True)
            raise VisualizationError(f"Failed to create {chart_type} chart: {e}") from e
    
    async def create_interactive_dashboard(
        self,
        companies: List[CompanyData],
        dashboard_type: DashboardType
    ) -> InteractiveDashboard:
        """Create interactive dashboard with real-time capabilities"""
        
        try:
            if dashboard_type == DashboardType.EXECUTIVE_SUMMARY:
                return await self._create_executive_dashboard(companies)
            elif dashboard_type == DashboardType.MARKET_ANALYSIS:
                return await self._create_market_analysis_dashboard(companies)
            elif dashboard_type == DashboardType.COMPETITIVE_INTELLIGENCE:
                return await self._create_competitive_dashboard(companies)
            else:
                return await self._create_overview_dashboard(companies)
                
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}", exc_info=True)
            raise VisualizationError(f"Failed to create dashboard: {e}") from e
    
    async def create_network_visualization(
        self,
        companies: List[CompanyData],
        relationship_data: Dict[str, Any]
    ) -> Visualization:
        """Create network/graph visualization showing relationships"""
        
        if not HAS_NETWORKX:
            logger.warning("NetworkX not available, creating simplified network visualization")
            return await self._create_simple_network(companies, relationship_data)
        
        try:
            return await self._create_advanced_network(companies, relationship_data)
            
        except Exception as e:
            logger.error(f"Network visualization failed: {e}", exc_info=True)
            return await self._create_simple_network(companies, relationship_data)
    
    async def create_heatmap(
        self,
        data: Dict[str, Any],
        title: str,
        x_axis: str,
        y_axis: str
    ) -> Visualization:
        """Create heatmap visualization"""
        
        config = {
            'x_axis_label': x_axis,
            'y_axis_label': y_axis
        }
        
        return await self._create_heatmap_chart(data, title, config)
    
    async def create_geographic_visualization(
        self,
        companies: List[CompanyData],
        map_type: str = "distribution"
    ) -> Visualization:
        """Create geographic visualization of company locations"""
        
        try:
            if map_type == "distribution":
                return await self._create_geographic_distribution(companies)
            elif map_type == "concentration":
                return await self._create_geographic_concentration(companies)
            else:
                return await self._create_geographic_distribution(companies)
                
        except Exception as e:
            logger.error(f"Geographic visualization failed: {e}", exc_info=True)
            raise VisualizationError(f"Failed to create geographic visualization: {e}") from e
    
    async def export_visualization(
        self,
        visualization: Visualization,
        output_path: str,
        format: str = "png"
    ) -> str:
        """Export visualization to file"""
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "html" and visualization.interactive_data:
                # Export interactive visualization as HTML
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(visualization.interactive_data)
            elif format.lower() == "json":
                # Export visualization data as JSON
                viz_data = {
                    'title': visualization.title,
                    'type': visualization.type.value,
                    'data': visualization.data,
                    'description': visualization.description,
                    'chart_type': getattr(visualization, 'chart_type', None)
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(viz_data, f, indent=2, default=str)
            else:
                # For other formats, save the encoded image data
                if hasattr(visualization, 'image_data') and visualization.image_data:
                    # Decode base64 image data
                    image_data = base64.b64decode(visualization.image_data)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                else:
                    # Create a simple text representation
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"Visualization: {visualization.title}\n")
                        f.write(f"Type: {visualization.type.value}\n")
                        f.write(f"Description: {visualization.description}\n")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Visualization export failed: {e}", exc_info=True)
            raise VisualizationError(f"Failed to export visualization: {e}") from e
    
    async def get_supported_chart_types(self) -> List[str]:
        """Get list of supported chart types"""
        return list(self.chart_types.keys())
    
    async def validate_visualization_config(
        self,
        config: VisualizationConfig
    ) -> bool:
        """Validate visualization configuration"""
        try:
            # Basic validation
            if not config.title or not config.chart_type:
                return False
            
            # Check if chart type is supported
            if config.chart_type not in self.chart_types:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False
    
    async def _create_industry_distribution(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create industry distribution pie chart"""
        
        industries = [c.industry for c in companies if c.industry]
        if not industries:
            return None
        
        industry_counts = dict(Counter(industries))
        
        return await self.create_chart(
            data=industry_counts,
            chart_type="pie",
            title="Industry Distribution",
            config={
                'description': f"Distribution of {len(companies)} companies across industries"
            }
        )
    
    async def _create_size_distribution(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create company size distribution bar chart"""
        
        sizes = []
        for company in companies:
            if hasattr(company, 'employee_count') and company.employee_count:
                if company.employee_count < 10:
                    sizes.append('Startup (1-9)')
                elif company.employee_count < 50:
                    sizes.append('Small (10-49)')
                elif company.employee_count < 250:
                    sizes.append('Medium (50-249)')
                else:
                    sizes.append('Large (250+)')
            elif hasattr(company, 'company_size') and company.company_size:
                sizes.append(company.company_size)
            else:
                sizes.append('Unknown')
        
        if not sizes:
            return None
        
        size_counts = dict(Counter(sizes))
        
        return await self.create_chart(
            data=size_counts,
            chart_type="bar",
            title="Company Size Distribution",
            config={
                'description': f"Size distribution of {len(companies)} companies"
            }
        )
    
    async def _create_geographic_distribution(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create geographic distribution heatmap"""
        
        locations = [c.location for c in companies if c.location]
        if not locations:
            return None
        
        location_counts = dict(Counter(locations))
        
        return await self.create_chart(
            data=location_counts,
            chart_type="bar",
            title="Geographic Distribution",
            config={
                'description': f"Geographic distribution of {len(companies)} companies",
                'chart_style': 'horizontal'
            }
        )
    
    async def _create_business_model_analysis(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create business model analysis chart"""
        
        business_models = [getattr(c, 'business_model', 'Unknown') for c in companies]
        business_models = [bm for bm in business_models if bm and bm != 'Unknown']
        
        if not business_models:
            return None
        
        model_counts = dict(Counter(business_models))
        
        return await self.create_chart(
            data=model_counts,
            chart_type="pie",
            title="Business Model Distribution",
            config={
                'description': f"Business model analysis of {len(companies)} companies"
            }
        )
    
    async def _create_founding_trends(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create founding year trends line chart"""
        
        founding_years = [getattr(c, 'founded_year', None) for c in companies]
        founding_years = [year for year in founding_years if year and year > 1950]
        
        if len(founding_years) < 3:
            return None
        
        # Group by decade
        decades = {}
        for year in founding_years:
            decade = (year // 10) * 10
            decades[f"{decade}s"] = decades.get(f"{decade}s", 0) + 1
        
        return await self.create_chart(
            data=decades,
            chart_type="line",
            title="Company Founding Trends by Decade",
            config={
                'description': f"Founding trends for {len(founding_years)} companies with known founding years"
            }
        )
    
    async def _create_technology_analysis(self, companies: List[CompanyData]) -> Optional[Visualization]:
        """Create technology stack analysis"""
        
        # This would require technology data - placeholder for now
        tech_data = {
            'Web Technologies': len([c for c in companies if 'web' in str(c.description).lower()]),
            'Mobile': len([c for c in companies if 'mobile' in str(c.description).lower()]),
            'AI/ML': len([c for c in companies if any(term in str(c.description).lower() 
                         for term in ['ai', 'artificial intelligence', 'machine learning', 'ml'])]),
            'Cloud': len([c for c in companies if 'cloud' in str(c.description).lower()]),
            'SaaS': len([c for c in companies if 'saas' in str(c.description).lower()])
        }
        
        # Only create if we have meaningful data
        if sum(tech_data.values()) < len(companies) * 0.1:
            return None
        
        return await self.create_chart(
            data=tech_data,
            chart_type="bar",
            title="Technology Focus Areas",
            config={
                'description': f"Technology focus analysis based on company descriptions"
            }
        )
    
    async def _create_bar_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create bar chart visualization"""
        
        # Create simple text-based visualization for now
        # In production, would use matplotlib/plotly
        
        chart_data = {
            'labels': list(data.keys()),
            'values': list(data.values()),
            'chart_type': 'bar'
        }
        
        # Create simple ASCII bar chart representation
        max_val = max(data.values()) if data.values() else 1
        chart_text = f"{title}\n" + "=" * len(title) + "\n\n"
        
        for label, value in data.items():
            bar_length = int((value / max_val) * 40)
            bar = "█" * bar_length
            chart_text += f"{label:20} {bar} {value}\n"
        
        return Visualization(
            type=VisualizationType.CHARTS,
            title=title,
            data=chart_data,
            chart_type="bar",
            description=config.get('description', f"Bar chart showing {title}"),
            chart_config=config,
            text_representation=chart_text
        )
    
    async def _create_pie_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create pie chart visualization"""
        
        chart_data = {
            'labels': list(data.keys()),
            'values': list(data.values()),
            'chart_type': 'pie'
        }
        
        # Create simple text representation
        total = sum(data.values())
        chart_text = f"{title}\n" + "=" * len(title) + "\n\n"
        
        for label, value in data.items():
            percentage = (value / total) * 100 if total > 0 else 0
            chart_text += f"{label:20} {value:5} ({percentage:5.1f}%)\n"
        
        return Visualization(
            type=VisualizationType.CHARTS,
            title=title,
            data=chart_data,
            chart_type="pie",
            description=config.get('description', f"Pie chart showing {title}"),
            chart_config=config,
            text_representation=chart_text
        )
    
    async def _create_line_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create line chart visualization"""
        
        chart_data = {
            'labels': list(data.keys()),
            'values': list(data.values()),
            'chart_type': 'line'
        }
        
        # Create simple text representation
        values = list(data.values())
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        
        chart_text = f"{title}\n" + "=" * len(title) + "\n\n"
        
        for label, value in data.items():
            # Normalize value for display
            normalized = int(((value - min_val) / (max_val - min_val)) * 20) if max_val > min_val else 10
            line = " " * normalized + "●"
            chart_text += f"{label:15} {line} {value}\n"
        
        return Visualization(
            type=VisualizationType.CHARTS,
            title=title,
            data=chart_data,
            chart_type="line",
            description=config.get('description', f"Line chart showing {title}"),
            chart_config=config,
            text_representation=chart_text
        )
    
    async def _create_scatter_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create scatter plot visualization"""
        
        return await self._create_bar_chart(data, title, config)  # Fallback to bar chart
    
    async def _create_heatmap_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create heatmap visualization"""
        
        chart_data = {
            'data': data,
            'chart_type': 'heatmap'
        }
        
        # Create simple text representation
        chart_text = f"{title}\n" + "=" * len(title) + "\n\n"
        chart_text += "Heatmap data visualization (detailed view requires visualization tools)\n"
        
        for key, value in data.items():
            chart_text += f"{key}: {value}\n"
        
        return Visualization(
            type=VisualizationType.HEATMAPS,
            title=title,
            data=chart_data,
            description=config.get('description', f"Heatmap showing {title}"),
            chart_config=config,
            text_representation=chart_text
        )
    
    async def _create_histogram_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create histogram visualization"""
        
        return await self._create_bar_chart(data, title, config)  # Similar to bar chart
    
    async def _create_box_chart(
        self, 
        data: Dict[str, Any], 
        title: str, 
        config: Dict[str, Any]
    ) -> Visualization:
        """Create box plot visualization"""
        
        return await self._create_bar_chart(data, title, config)  # Fallback to bar chart
    
    async def _create_executive_dashboard(self, companies: List[CompanyData]) -> InteractiveDashboard:
        """Create executive summary dashboard"""
        
        # Create key visualizations for executive view
        visualizations = []
        
        # Industry overview
        industry_viz = await self._create_industry_distribution(companies)
        if industry_viz:
            visualizations.append(industry_viz)
        
        # Size distribution
        size_viz = await self._create_size_distribution(companies)
        if size_viz:
            visualizations.append(size_viz)
        
        # Key metrics
        metrics = {
            'total_companies': len(companies),
            'unique_industries': len(set(c.industry for c in companies if c.industry)),
            'geographic_spread': len(set(c.location for c in companies if c.location)),
            'avg_founded_year': self._calculate_avg_founding_year(companies)
        }
        
        return InteractiveDashboard(
            dashboard_type=DashboardType.EXECUTIVE_SUMMARY,
            title="Executive Summary Dashboard",
            description="High-level overview of company portfolio",
            visualizations=visualizations,
            metrics=metrics,
            layout_config={'columns': 2, 'responsive': True}
        )
    
    async def _create_market_analysis_dashboard(self, companies: List[CompanyData]) -> InteractiveDashboard:
        """Create market analysis dashboard"""
        
        visualizations = []
        
        # Market distribution
        industry_viz = await self._create_industry_distribution(companies)
        if industry_viz:
            visualizations.append(industry_viz)
        
        # Geographic distribution
        geo_viz = await self._create_geographic_distribution(companies)
        if geo_viz:
            visualizations.append(geo_viz)
        
        # Business model analysis
        bm_viz = await self._create_business_model_analysis(companies)
        if bm_viz:
            visualizations.append(bm_viz)
        
        # Market metrics
        metrics = {
            'market_concentration': self._calculate_market_concentration(companies),
            'geographic_diversity': len(set(c.location for c in companies if c.location)),
            'industry_diversity': len(set(c.industry for c in companies if c.industry)),
            'size_distribution_score': self._calculate_size_diversity(companies)
        }
        
        return InteractiveDashboard(
            dashboard_type=DashboardType.MARKET_ANALYSIS,
            title="Market Analysis Dashboard",
            description="Comprehensive market landscape analysis",
            visualizations=visualizations,
            metrics=metrics,
            layout_config={'columns': 3, 'responsive': True}
        )
    
    async def _create_competitive_dashboard(self, companies: List[CompanyData]) -> InteractiveDashboard:
        """Create competitive intelligence dashboard"""
        
        visualizations = []
        
        # Competitive landscape
        size_viz = await self._create_size_distribution(companies)
        if size_viz:
            visualizations.append(size_viz)
        
        # Technology focus
        tech_viz = await self._create_technology_analysis(companies)
        if tech_viz:
            visualizations.append(tech_viz)
        
        # Competitive metrics
        metrics = {
            'total_competitors': len(companies),
            'size_categories': len(set(self._categorize_size(c) for c in companies)),
            'technology_diversity': self._calculate_tech_diversity(companies),
            'competitive_intensity': len(companies) / max(1, len(set(c.industry for c in companies if c.industry)))
        }
        
        return InteractiveDashboard(
            dashboard_type=DashboardType.COMPETITIVE_INTELLIGENCE,
            title="Competitive Intelligence Dashboard",
            description="Competitive landscape and positioning analysis",
            visualizations=visualizations,
            metrics=metrics,
            layout_config={'columns': 2, 'responsive': True, 'real_time': True}
        )
    
    async def _create_overview_dashboard(self, companies: List[CompanyData]) -> InteractiveDashboard:
        """Create general overview dashboard"""
        
        visualizations = await self.create_visualizations(companies)
        
        metrics = {
            'total_companies': len(companies),
            'data_completeness': self._calculate_data_completeness(companies),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        return InteractiveDashboard(
            dashboard_type=DashboardType.OVERVIEW,
            title="Company Portfolio Overview",
            description="Comprehensive overview of all company data",
            visualizations=visualizations,
            metrics=metrics,
            layout_config={'columns': 3, 'responsive': True}
        )
    
    async def _create_simple_network(
        self, 
        companies: List[CompanyData], 
        relationship_data: Dict[str, Any]
    ) -> Visualization:
        """Create simple network visualization without NetworkX"""
        
        # Create basic network representation
        network_data = {
            'nodes': [{'id': c.name, 'industry': c.industry} for c in companies],
            'edges': relationship_data.get('connections', []),
            'chart_type': 'network'
        }
        
        # Create text representation
        chart_text = "Company Network Visualization\n"
        chart_text += "=" * 30 + "\n\n"
        chart_text += f"Nodes: {len(companies)} companies\n"
        chart_text += f"Connections: {len(relationship_data.get('connections', []))}\n\n"
        
        # Group by industry
        industries = {}
        for company in companies:
            industry = company.industry or 'Unknown'
            industries[industry] = industries.get(industry, 0) + 1
        
        for industry, count in industries.items():
            chart_text += f"{industry}: {count} companies\n"
        
        return Visualization(
            type=VisualizationType.NETWORK,
            title="Company Relationship Network",
            data=network_data,
            description="Network visualization of company relationships",
            text_representation=chart_text
        )
    
    async def _create_advanced_network(
        self, 
        companies: List[CompanyData], 
        relationship_data: Dict[str, Any]
    ) -> Visualization:
        """Create advanced network visualization with NetworkX"""
        
        import networkx as nx
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes
        for company in companies:
            G.add_node(company.name, industry=company.industry or 'Unknown')
        
        # Add edges from relationship data
        connections = relationship_data.get('connections', [])
        for connection in connections:
            if 'source' in connection and 'target' in connection:
                G.add_edge(connection['source'], connection['target'])
        
        # Calculate network metrics
        network_metrics = {
            'nodes': len(G.nodes()),
            'edges': len(G.edges()),
            'density': nx.density(G),
            'components': nx.number_connected_components(G)
        }
        
        # Create visualization data
        network_data = {
            'nodes': [{'id': node, **attrs} for node, attrs in G.nodes(data=True)],
            'edges': [{'source': u, 'target': v} for u, v in G.edges()],
            'metrics': network_metrics,
            'chart_type': 'network'
        }
        
        return Visualization(
            type=VisualizationType.NETWORK,
            title="Advanced Company Network",
            data=network_data,
            description=f"Network analysis of {len(companies)} companies with {len(connections)} connections"
        )
    
    async def _create_geographic_concentration(self, companies: List[CompanyData]) -> Visualization:
        """Create geographic concentration analysis"""
        
        return await self._create_geographic_distribution(companies)
    
    def _calculate_avg_founding_year(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate average founding year"""
        years = [getattr(c, 'founded_year', None) for c in companies]
        years = [year for year in years if year and year > 1900]
        return statistics.mean(years) if years else None
    
    def _calculate_market_concentration(self, companies: List[CompanyData]) -> float:
        """Calculate market concentration (HHI)"""
        industries = [c.industry for c in companies if c.industry]
        if not industries:
            return 0.0
        
        industry_counts = Counter(industries)
        total = len(industries)
        hhi = sum((count / total) ** 2 for count in industry_counts.values())
        return hhi
    
    def _calculate_size_diversity(self, companies: List[CompanyData]) -> float:
        """Calculate size distribution diversity"""
        sizes = [self._categorize_size(c) for c in companies]
        unique_sizes = len(set(sizes))
        total_sizes = len(sizes)
        return unique_sizes / total_sizes if total_sizes > 0 else 0.0
    
    def _categorize_size(self, company: CompanyData) -> str:
        """Categorize company size"""
        if hasattr(company, 'employee_count') and company.employee_count:
            if company.employee_count < 10:
                return 'startup'
            elif company.employee_count < 50:
                return 'small'
            elif company.employee_count < 250:
                return 'medium'
            else:
                return 'large'
        return 'unknown'
    
    def _calculate_tech_diversity(self, companies: List[CompanyData]) -> float:
        """Calculate technology diversity score"""
        # Simple heuristic based on description keywords
        tech_keywords = ['ai', 'ml', 'web', 'mobile', 'cloud', 'saas', 'blockchain']
        tech_mentions = 0
        
        for company in companies:
            description = str(company.description).lower() if company.description else ''
            tech_mentions += sum(1 for keyword in tech_keywords if keyword in description)
        
        return tech_mentions / len(companies) if companies else 0.0
    
    def _calculate_data_completeness(self, companies: List[CompanyData]) -> float:
        """Calculate data completeness percentage"""
        if not companies:
            return 0.0
        
        total_fields = 0
        completed_fields = 0
        
        key_fields = ['name', 'industry', 'location', 'description']
        
        for company in companies:
            for field in key_fields:
                total_fields += 1
                if hasattr(company, field) and getattr(company, field):
                    completed_fields += 1
        
        return (completed_fields / total_fields) * 100 if total_fields > 0 else 0.0