#!/usr/bin/env python3
"""
Theodore v2 Report Engine Implementation

Comprehensive report generation engine with template management and automated scheduling.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import shutil

try:
    from jinja2 import Environment, FileSystemLoader, Template, TemplateError
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

from ....core.ports.io.report_engine_port import ReportEnginePort
from ....core.domain.models.company import CompanyData
from ....core.domain.models.export import (
    ReportTemplate, GeneratedReport, Analytics, Visualization,
    ReportFormat, ScheduleType
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ReportError(Exception):
    """Report generation error"""
    pass


class TemplateNotFoundError(ReportError):
    """Template not found error"""
    pass


class TemplateValidationError(ReportError):
    """Template validation error"""
    pass


class ReportEngine(ReportEnginePort):
    """
    Comprehensive report generation engine
    
    Provides:
    - Template-based report generation
    - Multiple output formats (HTML, PDF, Markdown, JSON)
    - Template management and validation
    - Report scheduling and automation
    - Analytics and visualization integration
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = Path(templates_dir) if templates_dir else Path("templates/reports")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment if available
        if HAS_JINJA2:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=True
            )
        else:
            self.jinja_env = None
        
        # Built-in templates
        self._create_default_templates()
        
        # Report cache
        self.report_cache = {}
    
    async def generate_report(
        self,
        template_name: str,
        companies: List[CompanyData],
        parameters: Dict[str, Any],
        analytics: Optional[Analytics] = None,
        visualizations: Optional[List[Visualization]] = None
    ) -> GeneratedReport:
        """Generate report from template with data and parameters"""
        
        try:
            logger.info(f"Generating report with template '{template_name}' for {len(companies)} companies")
            
            # Get template
            template = await self.get_template(template_name)
            if not template:
                raise TemplateNotFoundError(f"Template '{template_name}' not found")
            
            # Prepare template data
            template_data = await self._prepare_template_data(
                companies, parameters, analytics, visualizations
            )
            
            # Render report content
            content = await self._render_template(template, template_data)
            
            # Process content based on output format
            final_content = await self._process_content(content, template.output_format)
            
            # Create generated report
            report = GeneratedReport(
                template_name=template_name,
                title=parameters.get('title', template.name),
                content=final_content,
                format=template.output_format,
                generated_at=datetime.now(timezone.utc),
                companies_count=len(companies),
                parameters=parameters,
                analytics=analytics,
                visualizations=visualizations or [],
                metadata={
                    'template_version': template.version,
                    'generation_time': datetime.now(timezone.utc).isoformat(),
                    'data_sources': ['companies', 'analytics', 'visualizations']
                }
            )
            
            # Cache report if enabled
            if template.cache_enabled:
                cache_key = self._generate_cache_key(template_name, companies, parameters)
                self.report_cache[cache_key] = report
            
            logger.info(
                f"Report generated successfully",
                extra={
                    "template": template_name,
                    "companies_count": len(companies),
                    "format": template.output_format.value,
                    "content_length": len(final_content)
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            raise ReportError(f"Failed to generate report: {e}") from e
    
    async def get_template(self, template_name: str) -> Optional[ReportTemplate]:
        """Get report template by name"""
        
        template_path = self.templates_dir / f"{template_name}.json"
        if not template_path.exists():
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            return ReportTemplate(**template_data)
            
        except Exception as e:
            logger.error(f"Failed to load template '{template_name}': {e}")
            return None
    
    async def list_templates(self) -> List[ReportTemplate]:
        """Get list of available report templates"""
        
        templates = []
        
        for template_file in self.templates_dir.glob("*.json"):
            template_name = template_file.stem
            template = await self.get_template(template_name)
            if template:
                templates.append(template)
        
        return templates
    
    async def create_template(self, template: ReportTemplate) -> bool:
        """Create new report template"""
        
        try:
            # Validate template
            if not await self.validate_template(template):
                raise TemplateValidationError("Template validation failed")
            
            # Save template to file
            template_path = self.templates_dir / f"{template.name}.json"
            template_data = template.dict()
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, default=str)
            
            # Create template file if it has custom content
            if template.template_content:
                content_path = self.templates_dir / f"{template.name}.html"
                with open(content_path, 'w', encoding='utf-8') as f:
                    f.write(template.template_content)
            
            logger.info(f"Template '{template.name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Template creation failed: {e}", exc_info=True)
            return False
    
    async def update_template(
        self, 
        template_name: str, 
        template: ReportTemplate
    ) -> bool:
        """Update existing report template"""
        
        try:
            # Check if template exists
            existing = await self.get_template(template_name)
            if not existing:
                return False
            
            # Update template name to match
            template.name = template_name
            
            # Validate updated template
            if not await self.validate_template(template):
                raise TemplateValidationError("Template validation failed")
            
            # Save updated template
            return await self.create_template(template)
            
        except Exception as e:
            logger.error(f"Template update failed: {e}", exc_info=True)
            return False
    
    async def delete_template(self, template_name: str) -> bool:
        """Delete report template"""
        
        try:
            template_path = self.templates_dir / f"{template_name}.json"
            content_path = self.templates_dir / f"{template_name}.html"
            
            deleted = False
            
            if template_path.exists():
                template_path.unlink()
                deleted = True
            
            if content_path.exists():
                content_path.unlink()
            
            if deleted:
                logger.info(f"Template '{template_name}' deleted successfully")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Template deletion failed: {e}", exc_info=True)
            return False
    
    async def validate_template(self, template: ReportTemplate) -> bool:
        """Validate report template structure and syntax"""
        
        try:
            # Basic validation
            if not template.name or not template.description:
                logger.error("Template missing required fields (name, description)")
                return False
            
            # Validate template content if using Jinja2
            if template.template_content and HAS_JINJA2:
                try:
                    Template(template.template_content)
                except TemplateError as e:
                    logger.error(f"Template syntax error: {e}")
                    return False
            
            # Validate parameters
            for param in template.parameters:
                if not param.get('name') or not param.get('type'):
                    logger.error("Template parameter missing name or type")
                    return False
            
            # Validate sections
            for section in template.sections:
                if not section.get('name') or not section.get('content'):
                    logger.error("Template section missing name or content")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return False
    
    async def render_preview(
        self,
        template_name: str,
        sample_data: List[CompanyData],
        parameters: Dict[str, Any]
    ) -> str:
        """Generate preview of report without full processing"""
        
        try:
            # Limit sample data for preview
            preview_data = sample_data[:5] if len(sample_data) > 5 else sample_data
            
            # Generate report with limited data
            report = await self.generate_report(
                template_name=template_name,
                companies=preview_data,
                parameters=parameters
            )
            
            # Return truncated content for preview
            content = report.content
            if len(content) > 2000:
                content = content[:2000] + "\n\n... [Preview truncated] ..."
            
            return content
            
        except Exception as e:
            logger.error(f"Preview generation failed: {e}", exc_info=True)
            return f"Preview generation failed: {str(e)}"
    
    async def get_template_parameters(self, template_name: str) -> List[Dict[str, Any]]:
        """Get required parameters for a template"""
        
        template = await self.get_template(template_name)
        if not template:
            return []
        
        return template.parameters
    
    async def export_report(
        self,
        report: GeneratedReport,
        output_path: str,
        format: Optional[str] = None
    ) -> str:
        """Export generated report to file"""
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_format = format or report.format.value
            
            if export_format.lower() == 'html':
                await self._export_html(report, output_path)
            elif export_format.lower() == 'pdf':
                await self._export_pdf(report, output_path)
            elif export_format.lower() == 'markdown':
                await self._export_markdown(report, output_path)
            elif export_format.lower() == 'json':
                await self._export_json(report, output_path)
            else:
                # Default to text export
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report.content)
            
            logger.info(f"Report exported to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Report export failed: {e}", exc_info=True)
            raise ReportError(f"Failed to export report: {e}") from e
    
    async def _prepare_template_data(
        self,
        companies: List[CompanyData],
        parameters: Dict[str, Any],
        analytics: Optional[Analytics] = None,
        visualizations: Optional[List[Visualization]] = None
    ) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        
        # Base template data
        template_data = {
            'companies': [c.dict() for c in companies],
            'companies_count': len(companies),
            'parameters': parameters,
            'generation_date': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            'analytics': analytics.dict() if analytics else None,
            'visualizations': [v.dict() for v in visualizations] if visualizations else [],
        }
        
        # Add summary statistics
        template_data['summary'] = {
            'total_companies': len(companies),
            'unique_industries': len(set(c.industry for c in companies if c.industry)),
            'unique_locations': len(set(c.location for c in companies if c.location)),
            'avg_founding_year': self._calculate_avg_founding_year(companies),
            'data_completeness': self._calculate_data_completeness(companies)
        }
        
        # Add industry breakdown
        industries = [c.industry for c in companies if c.industry]
        template_data['industry_breakdown'] = dict(
            sorted(
                Counter(industries).items(),
                key=lambda x: x[1],
                reverse=True
            )
        )
        
        # Add location breakdown
        locations = [c.location for c in companies if c.location]
        template_data['location_breakdown'] = dict(
            sorted(
                Counter(locations).items(),
                key=lambda x: x[1],
                reverse=True
            )
        )
        
        return template_data
    
    async def _render_template(
        self, 
        template: ReportTemplate, 
        data: Dict[str, Any]
    ) -> str:
        """Render template with data"""
        
        if template.template_content and HAS_JINJA2:
            # Use custom Jinja2 template
            jinja_template = Template(template.template_content)
            return jinja_template.render(**data)
        elif HAS_JINJA2:
            # Use template file
            try:
                jinja_template = self.jinja_env.get_template(f"{template.name}.html")
                return jinja_template.render(**data)
            except:
                pass
        
        # Fallback to simple template rendering
        return await self._render_simple_template(template, data)
    
    async def _render_simple_template(
        self, 
        template: ReportTemplate, 
        data: Dict[str, Any]
    ) -> str:
        """Render template using simple string replacement"""
        
        content = f"# {template.name}\n\n"
        content += f"{template.description}\n\n"
        content += f"Generated: {data['generation_date']}\n\n"
        
        # Add summary section
        content += "## Summary\n\n"
        content += f"- Total Companies: {data['companies_count']}\n"
        content += f"- Unique Industries: {data['summary']['unique_industries']}\n"
        content += f"- Unique Locations: {data['summary']['unique_locations']}\n"
        if data['summary']['avg_founding_year']:
            content += f"- Average Founding Year: {data['summary']['avg_founding_year']:.0f}\n"
        content += f"- Data Completeness: {data['summary']['data_completeness']:.1f}%\n\n"
        
        # Add industry breakdown
        if data['industry_breakdown']:
            content += "## Industry Distribution\n\n"
            for industry, count in list(data['industry_breakdown'].items())[:10]:
                percentage = (count / data['companies_count']) * 100
                content += f"- {industry}: {count} companies ({percentage:.1f}%)\n"
            content += "\n"
        
        # Add location breakdown
        if data['location_breakdown']:
            content += "## Geographic Distribution\n\n"
            for location, count in list(data['location_breakdown'].items())[:10]:
                percentage = (count / data['companies_count']) * 100
                content += f"- {location}: {count} companies ({percentage:.1f}%)\n"
            content += "\n"
        
        # Add company details section
        content += "## Company Details\n\n"
        for i, company in enumerate(data['companies'][:20], 1):  # Limit to first 20
            content += f"### {i}. {company.get('name', 'Unknown')}\n"
            if company.get('industry'):
                content += f"- Industry: {company['industry']}\n"
            if company.get('location'):
                content += f"- Location: {company['location']}\n"
            if company.get('description'):
                desc = company['description'][:200] + "..." if len(company['description']) > 200 else company['description']
                content += f"- Description: {desc}\n"
            content += "\n"
        
        if len(data['companies']) > 20:
            content += f"... and {len(data['companies']) - 20} more companies\n\n"
        
        # Add analytics section if available
        if data.get('analytics'):
            content += "## Analytics\n\n"
            analytics = data['analytics']
            if analytics.get('market_concentration'):
                content += f"- Market Concentration (HHI): {analytics['market_concentration']:.3f}\n"
            if analytics.get('average_similarity'):
                content += f"- Average Similarity: {analytics['average_similarity']:.3f}\n"
            if analytics.get('competitive_density'):
                content += f"- Competitive Density: {analytics['competitive_density']:.3f}\n"
            content += "\n"
        
        # Add visualizations section if available
        if data.get('visualizations'):
            content += "## Visualizations\n\n"
            for viz in data['visualizations']:
                content += f"- {viz.get('title', 'Unnamed Visualization')}\n"
                if viz.get('description'):
                    content += f"  {viz['description']}\n"
            content += "\n"
        
        return content
    
    async def _process_content(self, content: str, output_format: ReportFormat) -> str:
        """Process content based on output format"""
        
        if output_format == ReportFormat.HTML:
            return await self._convert_to_html(content)
        elif output_format == ReportFormat.MARKDOWN:
            return content  # Already in markdown format
        elif output_format == ReportFormat.JSON:
            return await self._convert_to_json(content)
        else:
            return content
    
    async def _convert_to_html(self, content: str) -> str:
        """Convert content to HTML"""
        
        if HAS_MARKDOWN:
            # Convert markdown to HTML
            html_content = markdown.markdown(content, extensions=['tables', 'toc'])
            
            # Wrap in basic HTML structure
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Theodore Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 20px; border-left: 4px solid #007acc; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
            """
        else:
            # Simple HTML conversion
            html_content = content.replace('\n\n', '</p><p>')
            html_content = html_content.replace('\n', '<br>')
            html_content = html_content.replace('# ', '<h1>').replace('\n', '</h1>\n')
            html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>\n')
            html_content = html_content.replace('### ', '<h3>').replace('\n', '</h3>\n')
            
            return f"<html><body><p>{html_content}</p></body></html>"
    
    async def _convert_to_json(self, content: str) -> str:
        """Convert content to JSON"""
        
        # Simple JSON structure
        json_data = {
            'content': content,
            'format': 'markdown',
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    async def _export_html(self, report: GeneratedReport, output_path: Path) -> None:
        """Export report as HTML"""
        
        if report.format == ReportFormat.HTML:
            content = report.content
        else:
            content = await self._convert_to_html(report.content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _export_pdf(self, report: GeneratedReport, output_path: Path) -> None:
        """Export report as PDF"""
        
        # For now, save as HTML and suggest using browser to print to PDF
        html_path = output_path.with_suffix('.html')
        await self._export_html(report, html_path)
        
        # Create a simple text version as fallback
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PDF Export Notice:\n")
            f.write("==================\n\n")
            f.write(f"HTML version saved as: {html_path}\n")
            f.write("Open the HTML file in a browser and print to PDF for best results.\n\n")
            f.write("Report Content:\n")
            f.write("===============\n\n")
            f.write(report.content)
    
    async def _export_markdown(self, report: GeneratedReport, output_path: Path) -> None:
        """Export report as Markdown"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report.content)
    
    async def _export_json(self, report: GeneratedReport, output_path: Path) -> None:
        """Export report as JSON"""
        
        report_data = {
            'template_name': report.template_name,
            'title': report.title,
            'content': report.content,
            'format': report.format.value,
            'generated_at': report.generated_at.isoformat(),
            'companies_count': report.companies_count,
            'parameters': report.parameters,
            'metadata': report.metadata
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)
    
    def _generate_cache_key(
        self, 
        template_name: str, 
        companies: List[CompanyData], 
        parameters: Dict[str, Any]
    ) -> str:
        """Generate cache key for report"""
        
        # Simple cache key based on template and data
        company_hash = hash(tuple(c.name for c in companies))
        param_hash = hash(str(sorted(parameters.items())))
        
        return f"{template_name}_{company_hash}_{param_hash}"
    
    def _calculate_avg_founding_year(self, companies: List[CompanyData]) -> Optional[float]:
        """Calculate average founding year"""
        years = [getattr(c, 'founded_year', None) for c in companies]
        years = [year for year in years if year and year > 1900]
        return sum(years) / len(years) if years else None
    
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
    
    def _create_default_templates(self) -> None:
        """Create default report templates"""
        
        # Executive Summary Template
        executive_template = ReportTemplate(
            name="executive_summary",
            description="Executive summary report with key metrics and insights",
            output_format=ReportFormat.HTML,
            sections=[
                {
                    "name": "summary",
                    "title": "Executive Summary",
                    "content": "High-level overview of company portfolio"
                },
                {
                    "name": "metrics",
                    "title": "Key Metrics", 
                    "content": "Important business metrics and KPIs"
                },
                {
                    "name": "insights",
                    "title": "Key Insights",
                    "content": "Strategic insights and recommendations"
                }
            ],
            parameters=[
                {
                    "name": "title",
                    "type": "string",
                    "description": "Report title",
                    "default": "Executive Summary Report"
                }
            ]
        )
        
        # Market Analysis Template
        market_template = ReportTemplate(
            name="market_analysis",
            description="Comprehensive market analysis report",
            output_format=ReportFormat.HTML,
            sections=[
                {
                    "name": "overview",
                    "title": "Market Overview",
                    "content": "General market landscape analysis"
                },
                {
                    "name": "segmentation",
                    "title": "Market Segmentation",
                    "content": "Industry and geographic segmentation"
                },
                {
                    "name": "competition",
                    "title": "Competitive Analysis",
                    "content": "Competitive landscape and positioning"
                }
            ],
            parameters=[
                {
                    "name": "title",
                    "type": "string", 
                    "description": "Report title",
                    "default": "Market Analysis Report"
                },
                {
                    "name": "focus_industry",
                    "type": "string",
                    "description": "Industry to focus analysis on",
                    "default": ""
                }
            ]
        )
        
        # Company Profile Template
        profile_template = ReportTemplate(
            name="company_profiles",
            description="Detailed company profiles report",
            output_format=ReportFormat.MARKDOWN,
            sections=[
                {
                    "name": "profiles",
                    "title": "Company Profiles",
                    "content": "Detailed profiles of each company"
                }
            ],
            parameters=[
                {
                    "name": "title",
                    "type": "string",
                    "description": "Report title", 
                    "default": "Company Profiles Report"
                },
                {
                    "name": "max_companies",
                    "type": "integer",
                    "description": "Maximum number of companies to include",
                    "default": 50
                }
            ]
        )
        
        # Save default templates
        default_templates = [executive_template, market_template, profile_template]
        
        for template in default_templates:
            template_path = self.templates_dir / f"{template.name}.json"
            if not template_path.exists():
                try:
                    with open(template_path, 'w', encoding='utf-8') as f:
                        json.dump(template.dict(), f, indent=2, default=str)
                except Exception as e:
                    logger.error(f"Failed to create default template {template.name}: {e}")


# Import Counter for industry/location breakdown
from collections import Counter