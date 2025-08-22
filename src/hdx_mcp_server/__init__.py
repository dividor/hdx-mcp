"""
HDX MCP Server - A Model Context Protocol server for the Humanitarian Data Exchange API.

This package provides a comprehensive MCP server that automatically generates tools
from the HDX HAPI OpenAPI specification and includes custom tools for enhanced
functionality.

The server is organized into the following modules:
- server: Core server implementation and OpenAPI integration
- tools: Custom tool implementations for HDX-specific functionality
- prompts: Guidance prompts for AI assistants using the server
- resources: Resource handlers for external data sources (future expansion)
"""

from .server import HDXMCPServer, main

__version__ = "1.0.0"
__author__ = "HDX MCP Server Team"
__email__ = "support@example.com"

__all__ = ["HDXMCPServer", "main"]
