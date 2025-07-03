"""
Pinecone vector storage adapter for Theodore.

This module provides a comprehensive Pinecone implementation of the VectorStorage interface,
supporting enterprise-grade vector operations with advanced features.
"""

from .adapter import PineconeVectorStorage
from .config import PineconeConfig
from .client import PineconeClient
from .index import PineconeIndexManager
from .batch import PineconeBatchProcessor
from .query import PineconeQueryEngine
from .monitor import PineconeMonitor

__all__ = [
    "PineconeVectorStorage",
    "PineconeConfig", 
    "PineconeClient",
    "PineconeIndexManager",
    "PineconeBatchProcessor",
    "PineconeQueryEngine",
    "PineconeMonitor"
]

__version__ = "2.0.0"