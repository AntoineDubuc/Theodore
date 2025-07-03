#!/usr/bin/env python3
"""
Theodore v2 API Routers

FastAPI routers for different API endpoints.
"""

from . import auth, research, discovery, batch, plugins, system, websocket

__all__ = [
    "auth",
    "research", 
    "discovery",
    "batch",
    "plugins",
    "system",
    "websocket",
]