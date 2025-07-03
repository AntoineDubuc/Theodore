#!/usr/bin/env python3
"""
Theodore v2 Report Engine Port

Port interface for report generation and template management functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ...domain.models.company import CompanyData
from ...domain.models.export import (
    ReportTemplate, GeneratedReport, Analytics, Visualization
)


class ReportEnginePort(ABC):
    """
    Port interface for comprehensive report generation engine
    
    Provides template-based report generation with analytics
    and visualization integration.
    """
    
    @abstractmethod
    async def generate_report(
        self,
        template_name: str,
        companies: List[CompanyData],
        parameters: Dict[str, Any],
        analytics: Optional[Analytics] = None,
        visualizations: Optional[List[Visualization]] = None
    ) -> GeneratedReport:
        """
        Generate report from template with data and parameters
        
        Args:
            template_name: Name of report template to use
            companies: Company data for report
            parameters: Template parameters
            analytics: Optional analytics data
            visualizations: Optional visualizations to include
            
        Returns:
            Generated report object
            
        Raises:
            ReportError: If report generation fails
            TemplateNotFoundError: If template doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_template(self, template_name: str) -> Optional[ReportTemplate]:
        """
        Get report template by name
        
        Args:
            template_name: Name of template to retrieve
            
        Returns:
            Report template if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_templates(self) -> List[ReportTemplate]:
        """
        Get list of available report templates
        
        Returns:
            List of available report templates
        """
        pass
    
    @abstractmethod
    async def create_template(self, template: ReportTemplate) -> bool:
        """
        Create new report template
        
        Args:
            template: Template definition to create
            
        Returns:
            True if template was created successfully
            
        Raises:
            TemplateError: If template creation fails
        """
        pass
    
    @abstractmethod
    async def update_template(
        self, 
        template_name: str, 
        template: ReportTemplate
    ) -> bool:
        """
        Update existing report template
        
        Args:
            template_name: Name of template to update
            template: Updated template definition
            
        Returns:
            True if template was updated successfully
        """
        pass
    
    @abstractmethod
    async def delete_template(self, template_name: str) -> bool:
        """
        Delete report template
        
        Args:
            template_name: Name of template to delete
            
        Returns:
            True if template was deleted successfully
        """
        pass
    
    @abstractmethod
    async def validate_template(self, template: ReportTemplate) -> bool:
        """
        Validate report template structure and syntax
        
        Args:
            template: Template to validate
            
        Returns:
            True if template is valid
            
        Raises:
            TemplateValidationError: If template is invalid
        """
        pass
    
    @abstractmethod
    async def render_preview(
        self,
        template_name: str,
        sample_data: List[CompanyData],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate preview of report without full processing
        
        Args:
            template_name: Template to preview
            sample_data: Sample data for preview
            parameters: Template parameters
            
        Returns:
            Preview content as string
        """
        pass
    
    @abstractmethod
    async def get_template_parameters(self, template_name: str) -> List[Dict[str, Any]]:
        """
        Get required parameters for a template
        
        Args:
            template_name: Template to get parameters for
            
        Returns:
            List of parameter definitions
        """
        pass
    
    @abstractmethod
    async def export_report(
        self,
        report: GeneratedReport,
        output_path: str,
        format: Optional[str] = None
    ) -> str:
        """
        Export generated report to file
        
        Args:
            report: Generated report to export
            output_path: Output file path
            format: Optional format override
            
        Returns:
            Path to exported file
        """
        pass