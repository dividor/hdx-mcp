"""
HDX MCP Server - Prompts Module.

This module contains prompt implementations for the HDX MCP server.
Prompts provide guidance and context for AI assistants using the server.
"""

from . import data_coverage_guidance, hdx_usage_instructions, population_guidance

__all__ = [
    "population_guidance",
    "hdx_usage_instructions",
    "data_coverage_guidance",
]
