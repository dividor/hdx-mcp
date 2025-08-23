"""
HDX MCP Server - Custom Tools.

This module contains custom tool implementations for HDX-specific functionality.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def get_server_info(server_instance) -> Dict[str, Any]:
    """
    Get information about the HDX MCP server instance.

    Args:
        server_instance: The HDXMCPServer instance

    Returns:
        Dictionary containing server information
    """
    return {
        "server_name": "HDX MCP Server",
        "version": "1.0.0",
        "base_url": server_instance.base_url,
        "total_endpoints": len(server_instance.openapi_spec.get("paths", {})),
        "available_tools": "Multiple tools available (see tools/list)",
        "description": "MCP server for Humanitarian Data Exchange API",
    }


async def get_dataset_info(server_instance, dataset_hdx_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific HDX dataset.

    Args:
        server_instance: The HDXMCPServer instance
        dataset_hdx_id: The HDX dataset identifier

    Returns:
        Dictionary containing dataset information
    """
    try:
        # Use rate-limited request to protect HDX API
        response = await server_instance._rate_limited_request(
            "get", "/metadata/dataset", params={"dataset_hdx_id": dataset_hdx_id}
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("data"):
            return {
                "error": "Dataset not found",
                "dataset_hdx_id": dataset_hdx_id,
            }

        return {
            "status": "success",
            "dataset": data["data"][0] if data["data"] else None,
            "dataset_hdx_id": dataset_hdx_id,
        }
    except Exception as e:
        logger.error(f"Error fetching dataset info for {dataset_hdx_id}: {e}")
        return {
            "error": "Failed to fetch dataset information",
            "dataset_hdx_id": dataset_hdx_id,
        }


async def search_locations(
    server_instance, name_pattern: Optional[str] = None, has_hrp: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Search for locations (countries) in the HDX system.

    Args:
        server_instance: The HDXMCPServer instance
        name_pattern: Optional pattern to match location names
        has_hrp: Optional filter for locations with Humanitarian Response Plans

    Returns:
        Dictionary containing matching locations
    """
    try:
        params = {}
        if name_pattern:
            params["name"] = name_pattern
        if has_hrp is not None:
            params["has_hrp"] = str(has_hrp).lower()

        response = await server_instance._rate_limited_request(
            "get", "/metadata/location", params=params
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "success",
            "locations": data.get("data", []),
            "count": len(data.get("data", [])),
            "filters_applied": {
                "name_pattern": name_pattern,
                "has_hrp": has_hrp,
            },
        }
    except Exception as e:
        logger.error(
            f"Error searching locations with filters {name_pattern}, {has_hrp}: {e}"
        )
        return {
            "error": "Failed to search locations",
            "filters_applied": {
                "name_pattern": name_pattern,
                "has_hrp": has_hrp,
            },
        }
