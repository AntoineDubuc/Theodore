"""
Discovery utilities for Theodore CLI.

Provides result caching, similarity explanations, and discovery metrics.
"""

from .result_cache import DiscoveryResultCache
from .similarity_explainer import SimilarityExplainer

__all__ = ['DiscoveryResultCache', 'SimilarityExplainer']