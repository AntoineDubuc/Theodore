"""
CLI Formatters for Theodore v2.

Provides specialized formatting for discovery results, similarity scores,
and interactive displays.
"""

from .similarity import SimilarityResultFormatter
from .discovery_table import RichDiscoveryTableFormatter
from .comparison import ComparisonFormatter

__all__ = [
    'SimilarityResultFormatter',
    'RichDiscoveryTableFormatter',
    'ComparisonFormatter'
]