#!/usr/bin/env python3
"""
Theodore v2 Export Engine Port

Port interface for data export functionality with multiple format support.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from ...domain.models.company import CompanyData
from ...domain.models.export import (
    ExportResult, OutputConfig, Visualization
)


class ExportEnginePort(ABC):
    """
    Port interface for comprehensive export engine
    
    Supports multiple export formats with streaming capabilities
    and visualization integration.
    """
    
    @abstractmethod
    async def export(
        self,
        data: List[CompanyData],
        config: OutputConfig,
        visualizations: Optional[List[Visualization]] = None
    ) -> ExportResult:
        """
        Export data using specified configuration
        
        Args:
            data: Company data to export
            config: Export configuration including format and options
            visualizations: Optional visualizations to include
            
        Returns:
            Export result with file information and metadata
            
        Raises:
            ExportError: If export operation fails
        """
        pass
    
    @abstractmethod
    async def validate_export_config(self, config: OutputConfig) -> bool:
        """
        Validate export configuration
        
        Args:
            config: Export configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValidationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats
        
        Returns:
            List of supported format names
        """
        pass
    
    @abstractmethod
    async def estimate_export_size(
        self,
        data: List[CompanyData],
        config: OutputConfig
    ) -> int:
        """
        Estimate export file size in bytes
        
        Args:
            data: Company data to export
            config: Export configuration
            
        Returns:
            Estimated file size in bytes
        """
        pass
    
    @abstractmethod
    async def cleanup_temp_files(self, export_result: ExportResult) -> None:
        """
        Clean up temporary files created during export
        
        Args:
            export_result: Export result containing file paths to clean
        """
        pass