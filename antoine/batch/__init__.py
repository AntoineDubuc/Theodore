"""
Antoine Batch Processing Module
==============================

This module provides batch processing capabilities for the antoine 4-phase pipeline,
enabling parallel processing of multiple companies while maintaining resource efficiency.
"""

from .batch_processor import AntoineBatchProcessor

__all__ = ['AntoineBatchProcessor']