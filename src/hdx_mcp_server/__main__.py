"""
Entry point for running the HDX MCP Server as a module.

Usage:
    python -m hdx_mcp_server
    python -m hdx_mcp_server --transport http
    python -m hdx_mcp_server --help
"""

import sys

from .server import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
