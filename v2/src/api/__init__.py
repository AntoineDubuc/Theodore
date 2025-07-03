#!/usr/bin/env python3
"""
Theodore v2 REST API Package

Comprehensive FastAPI-based REST API server for Theodore v2.
Provides enterprise-grade web interface with authentication, 
real-time updates, monitoring, and comprehensive security.
"""

__version__ = "2.0.0"
__author__ = "Theodore Development Team"

from .app import create_app
from .models import *
from .middleware import *
from .security import *

__all__ = [
    "create_app",
]