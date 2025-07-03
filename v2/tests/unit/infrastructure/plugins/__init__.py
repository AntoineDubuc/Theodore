#!/usr/bin/env python3
"""
Theodore v2 Plugin System Tests
"""

# Import all test modules for easy test discovery
from . import (
    test_plugin_base,
    test_plugin_registry,
    test_plugin_loader,
    test_plugin_sandbox,
    test_plugin_manager,
    test_plugin_discovery
)

__all__ = [
    'test_plugin_base',
    'test_plugin_registry', 
    'test_plugin_loader',
    'test_plugin_sandbox',
    'test_plugin_manager',
    'test_plugin_discovery'
]