"""
Testing Overrides for Theodore v2 Container.

Simplified placeholder for initial CLI testing.
Will be implemented with full testing overrides later.
"""

from typing import Dict, Any, List


class TestingOverrides:
    """Provides testing overrides for container dependencies - simplified for CLI testing."""
    
    @staticmethod
    def get_default_overrides() -> Dict[str, Any]:
        """Get default testing overrides."""
        return {
            # Basic overrides for CLI testing
            "logging.level": "WARNING",
            "monitoring.enabled": False
        }