#!/usr/bin/env python3
"""
Core Domain Exceptions for Theodore v2
=====================================

Domain-specific exceptions that represent business rule violations
and core system failures in Theodore's clean architecture.
"""


class TheodoreError(Exception):
    """Base exception for all Theodore domain errors."""
    pass


class ConfigurationError(TheodoreError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(TheodoreError):
    """Raised when domain validation fails."""
    pass


class AIProviderError(TheodoreError):
    """Raised when AI provider operations fail."""
    pass


class EmbeddingProviderError(TheodoreError):
    """Raised when embedding provider operations fail."""
    pass


class VectorStorageError(TheodoreError):
    """Raised when vector storage operations fail."""
    pass


class WebScrapingError(TheodoreError):
    """Raised when web scraping operations fail."""
    pass


class ResearchError(TheodoreError):
    """Raised when research operations fail."""
    pass


class SimilarityError(TheodoreError):
    """Raised when similarity calculations fail."""
    pass


class MCPError(TheodoreError):
    """Raised when MCP operations fail."""
    pass


class ProgressTrackingError(TheodoreError):
    """Raised when progress tracking fails."""
    pass