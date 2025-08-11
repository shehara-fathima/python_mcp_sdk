
"""
Routers package for FastAPI MCP server.

Contains specialized routers for different model types and functionalities.
"""

from . import codegen_router, debugger_router

__all__ = ["codegen_router", "debugger_router"]
