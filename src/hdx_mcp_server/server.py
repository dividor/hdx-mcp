#!/usr/bin/env python3
"""
HDX MCP Server - An MCP server for the Humanitarian Data Exchange API

This server provides MCP tools for interacting with the HDX HAPI (Humanitarian API).
It automatically generates tools from the OpenAPI specification and allows for
custom tool additions.

Author: Assistant
License: MIT
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import httpx
from asyncio_throttle import Throttler
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from .prompts import data_coverage_guidance, hdx_usage_instructions, population_guidance

# Import custom modules
from .tools import hdx_tools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default constants (can be overridden by environment variables)
DEFAULT_HDX_OPENAPI_URL = "https://hapi.humdata.org/openapi.json"
DEFAULT_BASE_URL = "https://hapi.humdata.org/api/v2"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000


class HDXMCPServer:
    """HDX MCP Server implementation with OpenAPI integration and custom tools."""

    def __init__(self):
        """Initialize the HDX MCP Server."""
        self.api_key = self._get_required_env("HDX_API_KEY")
        self.base_url = os.getenv("HDX_BASE_URL", DEFAULT_BASE_URL)
        self.openapi_url = os.getenv("HDX_OPENAPI_URL", DEFAULT_HDX_OPENAPI_URL)
        self.host = os.getenv("MCP_HOST", DEFAULT_HOST)
        self.port = int(os.getenv("MCP_PORT", DEFAULT_PORT))
        self.app_name = os.getenv("HDX_APP_NAME", "hdx-mcp-server")
        self.app_email = os.getenv("HDX_APP_EMAIL", "assistant@example.com")
        self.timeout = float(os.getenv("HDX_TIMEOUT", "30.0"))

        # Rate limiting configuration
        self.rate_limit_requests = int(os.getenv("HDX_RATE_LIMIT_REQUESTS", "10"))
        self.rate_limit_period = float(os.getenv("HDX_RATE_LIMIT_PERIOD", "60.0"))

        # Initialize rate limiter
        self.throttler = Throttler(
            rate_limit=self.rate_limit_requests, period=self.rate_limit_period
        )

        # Initialize HTTP client with authentication
        self.client = self._create_http_client()

        # Load OpenAPI specification
        self.openapi_spec = self._load_openapi_spec()

        # Enable experimental OpenAPI parser for better schema handling
        os.environ["FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER"] = "true"

        # Create FastMCP server with custom route mappings and simplified tool names
        self.mcp = self._create_mcp_server()

        # Register custom tools
        self._register_custom_tools()

    def _get_required_env(self, key: str) -> str:
        """Get a required environment variable or raise an error."""
        value = os.getenv(key)
        if not value or not value.strip():
            raise ValueError(f"Required environment variable {key} is not set")
        return value.strip()

    def _create_http_client(self) -> httpx.AsyncClient:
        """Create an authenticated HTTP client for HDX API calls."""
        headers = {
            "X-HDX-HAPI-APP-IDENTIFIER": self.api_key,  # Use the API key directly
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Create a rate-limited HTTP client wrapper
        base_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
            params={"app_identifier": self._create_app_identifier()},
        )

        # Wrap the client to add rate limiting to all requests
        return self._wrap_client_with_rate_limiting(base_client)

    def _wrap_client_with_rate_limiting(self, client: httpx.AsyncClient) -> Any:
        """Wrap an HTTP client with rate limiting for all requests."""

        class RateLimitedClient:
            """HTTP client wrapper that applies rate limiting to all requests."""

            def __init__(self, base_client: httpx.AsyncClient, throttler: Throttler):
                self._client = base_client
                self._throttler = throttler

                # Forward all attributes to the base client
                for attr in dir(base_client):
                    if not attr.startswith("_") and not hasattr(self, attr):
                        setattr(self, attr, getattr(base_client, attr))

            async def _rate_limited_method(self, method_name: str, *args, **kwargs):
                """Apply rate limiting to any HTTP method."""
                async with self._throttler:
                    logger.debug(f"Rate-limited {method_name.upper()} request")
                    method = getattr(self._client, method_name)
                    return await method(*args, **kwargs)

            # Create rate-limited versions of all HTTP methods
            async def get(self, *args, **kwargs):
                return await self._rate_limited_method("get", *args, **kwargs)

            async def post(self, *args, **kwargs):
                return await self._rate_limited_method("post", *args, **kwargs)

            async def put(self, *args, **kwargs):
                return await self._rate_limited_method("put", *args, **kwargs)

            async def patch(self, *args, **kwargs):
                return await self._rate_limited_method("patch", *args, **kwargs)

            async def delete(self, *args, **kwargs):
                return await self._rate_limited_method("delete", *args, **kwargs)

            async def head(self, *args, **kwargs):
                return await self._rate_limited_method("head", *args, **kwargs)

            async def options(self, *args, **kwargs):
                return await self._rate_limited_method("options", *args, **kwargs)

            async def request(self, *args, **kwargs):
                return await self._rate_limited_method("request", *args, **kwargs)

            async def aclose(self):
                """Close the underlying client."""
                return await self._client.aclose()

            def __getattr__(self, name):
                """Forward any other attributes to the base client."""
                return getattr(self._client, name)

        return RateLimitedClient(client, self.throttler)

    def _create_app_identifier(self) -> str:
        """Create a base64 encoded app identifier for HDX API."""
        import base64

        app_info = f"{self.app_name}:{self.app_email}"
        return base64.b64encode(app_info.encode()).decode()

    async def _rate_limited_request(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Make a rate-limited HTTP request to protect the HDX API."""
        async with self.throttler:
            logger.debug(f"Rate-limited {method.upper()} request to {url}")
            response = await getattr(self.client, method.lower())(url, **kwargs)
            return response

    def _load_openapi_spec(self) -> Dict[str, Any]:
        """Load the OpenAPI specification from HDX."""
        try:
            logger.info(f"Loading HDX OpenAPI specification from {self.openapi_url}...")
            response = httpx.get(self.openapi_url, timeout=self.timeout)
            response.raise_for_status()
            spec = response.json()

            # Fix schema reference issues in the HDX OpenAPI spec
            spec = self._fix_openapi_schema_references(spec)

            # Simplify operation IDs to get clean tool names
            spec = self._simplify_operation_ids(spec)

            # Update parameter descriptions to reference MCP tools
            spec = self._update_parameter_descriptions(spec)

            # Add administrative level guidance to relevant operations
            spec = self._add_admin_level_guidance(spec)

            logger.info(
                f"Loaded OpenAPI spec with {len(spec.get('paths', {}))} endpoints"
            )
            return spec
        except Exception as e:
            logger.error(f"Failed to load OpenAPI specification: {e}")
            raise

    def _fix_openapi_schema_references(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix schema reference issues by resolving all $ref inline while preserving schema info.

        This prevents FastMCP from encountering incomplete $defs by expanding all component
        schema references directly into the response schemas, preserving all useful information.
        """
        import copy

        # Make a deep copy to avoid modifying the original
        fixed_spec = copy.deepcopy(spec)

        # Get all schema definitions from components/schemas
        schemas = fixed_spec.get("components", {}).get("schemas", {})
        logger.debug(f"Available schemas for inlining: {list(schemas.keys())}")

        def resolve_ref(ref_path: str) -> Dict[str, Any]:
            """Resolve a $ref path to the actual schema definition."""
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.replace("#/components/schemas/", "")
                if schema_name in schemas:
                    resolved = copy.deepcopy(schemas[schema_name])
                    logger.debug(f"Resolved reference: {schema_name}")
                    return resolved
                else:
                    logger.warning(
                        f"⚠️ Schema {schema_name} not found in components/schemas"
                    )
                    return {}
            return {}

        def resolve_refs_recursively(obj: Any, depth: int = 0) -> Any:
            """Recursively resolve all $ref references in any object while preserving
            enum values."""
            if depth > 10:  # Prevent infinite recursion
                logger.warning("⚠️ Max recursion depth reached in schema resolution")
                return obj

            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_path = obj["$ref"]
                    resolved_schema = resolve_ref(ref_path)
                    if resolved_schema:
                        # Create inline schema that preserves all important information
                        inline_schema = copy.deepcopy(resolved_schema)

                        # If the original object has additional properties (like
                        # description), merge them
                        for key, value in obj.items():
                            if key != "$ref":
                                inline_schema[key] = value

                        # Special handling for enum schemas to ensure they're preserved
                        if "enum" in resolved_schema:
                            schema_name = (
                                ref_path.split("/")[-1] if "/" in ref_path else ref_path
                            )
                            logger.debug(
                                f"📋 Preserved enum schema {schema_name} with "
                                f"{len(resolved_schema['enum'])} values: {resolved_schema['enum']}"
                            )

                        # Recursively resolve any nested refs in the resolved schema
                        return resolve_refs_recursively(inline_schema, depth + 1)
                    else:
                        # Keep the $ref if we can't resolve it
                        return obj
                elif "anyOf" in obj and isinstance(obj["anyOf"], list):
                    # Special handling for anyOf with $ref elements
                    resolved_any_of = []
                    for item in obj["anyOf"]:
                        resolved_item = resolve_refs_recursively(item, depth + 1)
                        resolved_any_of.append(resolved_item)

                    # Create a new object with the resolved anyOf
                    resolved_obj = obj.copy()
                    resolved_obj["anyOf"] = resolved_any_of

                    # Check if any of the anyOf items was an enum schema and log it
                    for item in resolved_any_of:
                        if isinstance(item, dict) and "enum" in item:
                            enum_name = item.get("title", "unknown enum")
                            logger.debug(
                                f"📋 Found enum in anyOf: {enum_name} with "
                                f"{len(item['enum'])} values: {item['enum']}"
                            )

                    return resolved_obj
                elif "oneOf" in obj and isinstance(obj["oneOf"], list):
                    # Special handling for oneOf with $ref elements (similar to anyOf)
                    resolved_one_of = []
                    for item in obj["oneOf"]:
                        resolved_item = resolve_refs_recursively(item, depth + 1)
                        resolved_one_of.append(resolved_item)

                    # Create a new object with the resolved oneOf
                    resolved_obj = obj.copy()
                    resolved_obj["oneOf"] = resolved_one_of

                    # Check if any of the oneOf items was an enum schema and log it
                    for item in resolved_one_of:
                        if isinstance(item, dict) and "enum" in item:
                            enum_name = item.get("title", "unknown enum")
                            logger.debug(
                                f"📋 Found enum in oneOf: {enum_name} with "
                                f"{len(item['enum'])} values: {item['enum']}"
                            )

                    return resolved_obj
                elif "allOf" in obj and isinstance(obj["allOf"], list):
                    # Special handling for allOf with $ref elements (similar to anyOf)
                    resolved_all_of = []
                    for item in obj["allOf"]:
                        resolved_item = resolve_refs_recursively(item, depth + 1)
                        resolved_all_of.append(resolved_item)

                    # Create a new object with the resolved allOf
                    resolved_obj = obj.copy()
                    resolved_obj["allOf"] = resolved_all_of

                    return resolved_obj
                else:
                    # Process each key-value pair
                    resolved_obj = {}
                    for key, value in obj.items():
                        resolved_obj[key] = resolve_refs_recursively(value, depth + 1)
                    return resolved_obj
            elif isinstance(obj, list):
                # Process each item in the list
                return [resolve_refs_recursively(item, depth + 1) for item in obj]
            else:
                # Return primitive values as-is
                return obj

        # Process all schemas in paths to resolve all references and set default limits
        schemas_processed = 0

        for path, path_data in fixed_spec.get("paths", {}).items():
            for method, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                # Process parameter schemas and update default limit values
                parameters = method_data.get("parameters", [])
                for param in parameters:
                    if isinstance(param, dict):
                        # Update default values for common parameters
                        param_name = param.get("name")
                        if param_name == "limit":
                            # Set default limit to 10 instead of the original value
                            if "schema" in param:
                                param["schema"]["default"] = 10
                                logger.debug(
                                    f"📊 Set default limit to 10 for {method.upper()} {path}"
                                )
                        elif param_name == "age_range":
                            # Set default age_range to 'all'
                            if "schema" in param:
                                param["schema"]["default"] = "all"
                                logger.debug(
                                    f"👥 Set default age_range to 'all' for {method.upper()} {path}"
                                )
                        elif param_name == "gender":
                            # Set default gender to 'all'
                            if "schema" in param:
                                param["schema"]["default"] = "all"
                                logger.debug(
                                    f"⚧ Set default gender to 'all' for {method.upper()} {path}"
                                )

                        # Resolve $ref references in parameter schemas
                        if "schema" in param:
                            original_schema = param["schema"]
                            resolved_schema = resolve_refs_recursively(original_schema)
                            param["schema"] = resolved_schema
                            schemas_processed += 1

                            # Log enum resolution in parameters
                            if isinstance(resolved_schema, dict):
                                if "enum" in resolved_schema:
                                    param_name = param.get("name", "unknown")
                                    logger.debug(
                                        f"📋 Resolved enum in parameter '{param_name}': "
                                        f"{resolved_schema['enum']}"
                                    )
                                elif "anyOf" in resolved_schema:
                                    for any_of_item in resolved_schema.get("anyOf", []):
                                        if (
                                            isinstance(any_of_item, dict)
                                            and "enum" in any_of_item
                                        ):
                                            param_name = param.get("name", "unknown")
                                            enum_title = any_of_item.get(
                                                "title", "unknown enum"
                                            )
                                            logger.debug(
                                                f"📋 Resolved enum in parameter "
                                                f"'{param_name}' anyOf: {enum_title} = "
                                                f"{any_of_item['enum']}"
                                            )

                # Process response schemas
                responses = method_data.get("responses", {})
                for response_code, response in responses.items():
                    if not isinstance(response, dict):
                        continue

                    content = response.get("content", {})
                    for _media_type, media_type_data in content.items():
                        if "schema" in media_type_data:
                            original_schema = media_type_data["schema"]
                            resolved_schema = resolve_refs_recursively(original_schema)
                            media_type_data["schema"] = resolved_schema
                            schemas_processed += 1
                            logger.debug(
                                f"📋 Resolved refs in response: {method.upper()} {path} - "
                                f"{response_code}"
                            )

                # Process request body schemas
                request_body = method_data.get("requestBody", {})
                if isinstance(request_body, dict):
                    content = request_body.get("content", {})
                    for _media_type, media_type_data in content.items():
                        if "schema" in media_type_data:
                            original_schema = media_type_data["schema"]
                            resolved_schema = resolve_refs_recursively(original_schema)
                            media_type_data["schema"] = resolved_schema
                            schemas_processed += 1
                            logger.debug(
                                f"📋 Resolved refs in request: {method.upper()} {path}"
                            )

        logger.info(
            f"✅ Resolved all schema references inline and set default limits to 10 - "
            f"processed {schemas_processed} schemas"
        )
        return fixed_spec

    def _simplify_operation_ids(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify operationId fields in the OpenAPI spec to generate clean tool names."""
        import copy

        # Make a deep copy to avoid modifying the original
        simplified_spec = copy.deepcopy(spec)

        # Mapping of path patterns to simplified operation IDs
        path_to_operation_id = {
            # Affected People endpoints
            "/api/v2/affected-people/refugees-persons-of-concern": "affected_people_refugees_get",
            "/api/v2/affected-people/humanitarian-needs": "affected_people_humanitarian_needs_get",
            "/api/v2/affected-people/idps": "affected_people_idps_get",
            "/api/v2/affected-people/returnees": "affected_people_returnees_get",
            # Coordination Context endpoints
            "/api/v2/coordination-context/operational-presence": (
                "coordination_operational_presence_get"
            ),
            "/api/v2/coordination-context/funding": "coordination_funding_get",
            "/api/v2/coordination-context/conflict-events": "coordination_conflict_events_get",
            "/api/v2/coordination-context/national-risk": "coordination_national_risk_get",
            # Food Security endpoints
            "/api/v2/food-security-nutrition-poverty/food-security": "food_security_get",
            "/api/v2/food-security-nutrition-poverty/food-prices-market-monitor": "food_prices_get",
            "/api/v2/food-security-nutrition-poverty/poverty-rate": "poverty_rate_get",
            # Geography endpoints
            "/api/v2/geography-infrastructure/baseline-population": "baseline_population_get",
            # Climate endpoints
            "/api/v2/climate/rainfall": "climate_rainfall_get",
            # Metadata endpoints
            "/api/v2/metadata/dataset": "metadata_dataset_get",
            "/api/v2/metadata/resource": "metadata_resource_get",
            "/api/v2/metadata/location": "metadata_location_get",
            "/api/v2/metadata/admin1": "metadata_admin1_get",
            "/api/v2/metadata/admin2": "metadata_admin2_get",
            "/api/v2/metadata/currency": "metadata_currency_get",
            "/api/v2/metadata/org": "metadata_org_get",
            "/api/v2/metadata/org-type": "metadata_org_type_get",
            "/api/v2/metadata/sector": "metadata_sector_get",
            "/api/v2/metadata/wfp-commodity": "metadata_wfp_commodity_get",
            "/api/v2/metadata/wfp-market": "metadata_wfp_market_get",
            "/api/v2/metadata/data-availability": "metadata_data_availability_get",
            # Utility endpoints
            "/api/v2/util/version": "util_version_get",
        }

        operations_updated = 0

        # Process all paths in the OpenAPI spec
        for path, path_data in simplified_spec.get("paths", {}).items():
            if path in path_to_operation_id:
                new_operation_id = path_to_operation_id[path]

                # Update operationId for all HTTP methods on this path
                for method, method_data in path_data.items():
                    if isinstance(method_data, dict) and "operationId" in method_data:
                        old_operation_id = method_data["operationId"]
                        method_data["operationId"] = new_operation_id
                        operations_updated += 1
                        logger.debug(
                            f"Updated operationId: {path} {method.upper()} - "
                            f"{old_operation_id} -> {new_operation_id}"
                        )

        logger.info(
            f"Simplified {operations_updated} operation IDs for cleaner tool names"
        )
        return simplified_spec

    def _update_parameter_descriptions(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update parameter descriptions to reference MCP tools instead of external URLs."""
        import copy
        import re

        # Make a deep copy to avoid modifying the original
        updated_spec = copy.deepcopy(spec)

        # Define regex patterns and their replacements for comprehensive matching
        description_patterns = [
            # Location references
            (
                r'See the <a href="/docs#/Metadata/get_locations?_api_v'
                r'[12]_metadata_location_get" target="_blank">location endpoint</a> for details\.?',
                "Use the metadata_location_get tool to get available location codes and names.",
            ),
            # Admin1 references
            (
                r'See the <a href="/docs#/Metadata/get_admin1_api_v'
                r'[12]_metadata_admin1_get" target="_blank">admin1 endpoint</a> for details\.?',
                "Use the metadata_admin1_get tool to get available admin1 codes and names.",
            ),
            # Admin2 references
            (
                r'See the <a href="/docs#/Metadata/get_admin2_api_v'
                r'[12]_metadata_admin2_get" target="_blank">admin2 endpoint</a> for details\.?',
                "Use the metadata_admin2_get tool to get available admin2 codes and names.",
            ),
            # Organization type references
            (
                r'See the <a href="/docs#/Metadata/get_org_type_api_v'
                r'[12]_metadata_org_type_get" target="_blank">org type endpoint</a> for details\.?',
                "Use the metadata_org_type_get tool to get available "
                "organization type codes and descriptions.",
            ),
            # Organization references
            (
                r'See the <a href="/docs#/Metadata/get_orgs?_api_v'
                r'[12]_metadata_org_get" target="_blank">org endpoint</a> for details\.?',
                "Use the metadata_org_get tool to get available organization codes and names.",
            ),
            # Sector references
            (
                r'See the <a href="/docs#/Metadata/get_sectors?_api_v'
                r'[12]_metadata_sector_get" target="_blank">sector endpoint</a> for details\.?',
                "Use the metadata_sector_get tool to get available sector codes and names.",
            ),
            # Currency references
            (
                r'See the <a href="/docs#/Metadata/get_currencies?_api_v'
                r'[12]_metadata_currency_get" target="_blank">currency endpoint</a> for details\.?',
                "Use the metadata_currency_get tool to get available currency codes.",
            ),
            # WFP Commodity references
            (
                r'See the <a href="/docs#/Metadata/get_wfp_commodities?_api_v[12]_'
                r'metadata_wfp_commodity_get" target="_blank">wfp commodity endpoint</a> '
                r"for details\.?",
                "Use the metadata_wfp_commodity_get tool to get available "
                "WFP commodity codes and names.",
            ),
            # WFP Market references
            (
                r'See the <a href="/docs#/Metadata/get_wfp_markets?_api_v[12]_'
                r'metadata_wfp_market_get" target="_blank">wfp market endpoint</a> '
                r"for details\.?",
                "Use the metadata_wfp_market_get tool to get available WFP market codes and names.",
            ),
            # Dataset references
            (
                r'See the <a href="/docs#/Metadata/get_datasets?_api_v'
                r'[12]_metadata_dataset_get" target="_blank">dataset endpoint</a> for details\.?',
                "Use the metadata_dataset_get tool to get available dataset information.",
            ),
            # Resource references
            (
                r'See the <a href="/docs#/Metadata/get_resources?_api_v'
                r'[12]_metadata_resource_get" target="_blank">resource endpoint</a> for details\.?',
                "Use the metadata_resource_get tool to get available resource information.",
            ),
            # Generic endpoint references (catch remaining cases)
            (r"location endpoint", "metadata_location_get tool"),
            (r"admin1 endpoint", "metadata_admin1_get tool"),
            (r"admin2 endpoint", "metadata_admin2_get tool"),
            (r"org type endpoint", "metadata_org_type_get tool"),
            (r"org endpoint", "metadata_org_get tool"),
            (r"sector endpoint", "metadata_sector_get tool"),
            (r"currency endpoint", "metadata_currency_get tool"),
            (r"wfp commodity endpoint", "metadata_wfp_commodity_get tool"),
            (r"wfp market endpoint", "metadata_wfp_market_get tool"),
            (r"dataset endpoint", "metadata_dataset_get tool"),
            (r"resource endpoint", "metadata_resource_get tool"),
        ]

        descriptions_updated = 0

        # Helper function to update descriptions recursively in any schema
        def update_descriptions_recursive(obj, path_info=""):
            if isinstance(obj, dict):
                if "description" in obj and isinstance(obj["description"], str):
                    original_desc = obj["description"]
                    updated_desc = original_desc

                    # Apply all regex pattern replacements
                    for pattern, replacement in description_patterns:
                        try:
                            if re.search(pattern, updated_desc):
                                new_desc = re.sub(pattern, replacement, updated_desc)
                                if new_desc != updated_desc:
                                    updated_desc = new_desc
                                    nonlocal descriptions_updated
                                    descriptions_updated += 1
                                    logger.info(
                                        f"✅ Updated description in {path_info}: "
                                        f"'{pattern[:50]}...' -> MCP tool reference"
                                    )
                        except (TypeError, AttributeError):
                            logger.debug(
                                f"Skipping regex update for non-string description at "
                                f"{path_info}: {type(updated_desc)}"
                            )
                            continue

                    # Update the description if it changed
                    if updated_desc != original_desc:
                        obj["description"] = updated_desc

                # Recursively process all nested objects
                for key, value in obj.items():
                    update_descriptions_recursive(
                        value, f"{path_info}.{key}" if path_info else key
                    )

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    update_descriptions_recursive(
                        item, f"{path_info}[{i}]" if path_info else f"[{i}]"
                    )

        # Process all paths, parameters, request bodies, and response schemas
        for path, path_data in updated_spec.get("paths", {}).items():
            for method, method_data in path_data.items():
                if not isinstance(method_data, dict):
                    continue

                # Update all descriptions in the entire method definition recursively
                update_descriptions_recursive(method_data, f"{path}.{method}")

        # Also process components/schemas if they exist
        if "components" in updated_spec and "schemas" in updated_spec["components"]:
            update_descriptions_recursive(
                updated_spec["components"]["schemas"], "components.schemas"
            )

        logger.info(
            f"Updated {descriptions_updated} parameter descriptions to reference MCP tools"
        )
        return updated_spec

    def _add_admin_level_guidance(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add administrative level guidance to relevant operations.

        This adds critical guidance about checking data availability and using
        the lowest available administrative level for efficient aggregation queries.
        """
        import copy

        enhanced_spec = copy.deepcopy(spec)
        guidance_added = 0

        # Define operations that benefit from admin level guidance
        admin_level_endpoints = [
            "affected-people",
            "baseline-population",
            "humanitarian-needs",
            "refugees",
            "idps",
            "returnees",
            "population",
            "food-security",
            "nutrition",
            "poverty",
            "conflict",
            "funding",
        ]

        # Define location-related endpoints that need data coverage warnings
        location_endpoints = [
            "location",
            "admin1",
            "admin2",
        ]

        admin_level_guidance = (
            "\n\n🎯 **CRITICAL - Data Coverage Warning**: "
            "Data coverage is only determined by the metadata_data_availability_get tool. "
            "Just because a country is in the system doesn't mean it has data. "
            "ALWAYS verify data availability before making data queries. "
            "\n\n🎯 **CRITICAL - Administrative Level Efficiency**: "
            "Before making aggregate queries (totals, country-wide statistics), "
            "ALWAYS check data availability using metadata_data_availability_get for the target country. "
            "Use the LOWEST available admin level (0=country, 1=state, "
            "2=district) to avoid downloading excessive granular data. "
            "For country totals, use admin level 0 if available, "
            "otherwise level 1. "
            "Never query admin level 2 for simple aggregations when level 0/1 is sufficient."
        )

        location_guidance = (
            "\n\n⚠️ **CRITICAL - Data Coverage Warning**: "
            "Data coverage is only determined by the metadata_data_availability_get tool. "
            "Just because a country appears in location metadata doesn't mean it has actual data. "
            "ALWAYS verify data availability using metadata_data_availability_get before making data queries."
        )

        # Universal pagination guidance for ALL tools
        pagination_guidance = (
            "\n\n🔄 **Pagination**: You can page through results using `limit` and `offset` parameters "
            "(limit=records per page, offset=starting position)."
        )

        # Add guidance to relevant operations
        for path, path_data in enhanced_spec.get("paths", {}).items():
            # Skip the app identifier endpoint
            if "app-identifier" in path:
                continue

            for method, operation in path_data.items():
                if isinstance(operation, dict) and "summary" in operation:
                    operation_updated = False

                    # Add admin level guidance to data endpoints
                    if any(endpoint in path for endpoint in admin_level_endpoints):
                        if admin_level_guidance not in operation["summary"]:
                            operation["summary"] = (
                                operation["summary"] + admin_level_guidance
                            )
                            guidance_added += 1
                            operation_updated = True
                            logger.debug(
                                f"Added admin level guidance to {method.upper()} {path}"
                            )

                    # Add location guidance to location metadata endpoints
                    elif any(endpoint in path for endpoint in location_endpoints):
                        if location_guidance not in operation["summary"]:
                            operation["summary"] = (
                                operation["summary"] + location_guidance
                            )
                            guidance_added += 1
                            operation_updated = True
                            logger.debug(
                                f"Added location guidance to {method.upper()} {path}"
                            )

                    # Add pagination guidance to ALL operations
                    if pagination_guidance not in operation["summary"]:
                        operation["summary"] = (
                            operation["summary"] + pagination_guidance
                        )
                        if not operation_updated:
                            guidance_added += 1
                        logger.debug(
                            f"Added pagination guidance to {method.upper()} {path}"
                        )

                elif isinstance(operation, dict) and "description" in operation:
                    # Add location guidance to the description if no summary (for
                    # location endpoints)
                    if any(endpoint in path for endpoint in location_endpoints):
                        if location_guidance not in operation["description"]:
                            operation["description"] = (
                                operation["description"] + location_guidance
                            )
                            guidance_added += 1
                            logger.debug(
                                f"Added location guidance to {method.upper()} {path}"
                            )

                    # Add pagination guidance to description if no summary
                    if pagination_guidance not in operation["description"]:
                        operation["description"] = (
                            operation["description"] + pagination_guidance
                        )
                        logger.debug(
                            f"Added pagination guidance to {method.upper()} {path}"
                        )

        logger.info(
            f"Added administrative level, data coverage, "
            f"and pagination guidance to {guidance_added} operations"
        )
        return enhanced_spec

    def _create_route_mappings(self) -> List[RouteMap]:
        """Create custom route mappings to exclude app identifier endpoint."""
        return [
            # Exclude the app identifier generation endpoint
            RouteMap(
                pattern=r".*/encode_app_identifier$",
                mcp_type=MCPType.EXCLUDE,
                mcp_tags={"excluded", "utility"},
            ),
            # All other endpoints become tools with appropriate tags
            RouteMap(
                pattern=r".*/metadata/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"metadata", "reference"},
            ),
            RouteMap(
                pattern=r".*/affected-people/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"affected-people", "humanitarian"},
            ),
            RouteMap(
                pattern=r".*/climate/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"climate", "environmental"},
            ),
            RouteMap(
                pattern=r".*/coordination-context/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"coordination", "humanitarian"},
            ),
            RouteMap(
                pattern=r".*/food-security-nutrition-poverty/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"food-security", "nutrition", "poverty"},
            ),
            RouteMap(
                pattern=r".*/geography-infrastructure/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"geography", "infrastructure", "population"},
            ),
            RouteMap(
                pattern=r".*/util/.*",
                mcp_type=MCPType.TOOL,
                mcp_tags={"utility", "system"},
            ),
        ]

    def _customize_mcp_components(self, route, component):
        """
        Customize MCP components to remove app_identifier from tool schemas.

        This function is called for each MCP component created from the OpenAPI spec.
        We use it to remove the app_identifier parameter from tool input schemas
        since it's automatically provided by the HTTP client.
        """
        try:
            if (
                hasattr(component, "__class__")
                and "Tool" in component.__class__.__name__
            ):
                # The tool parameters are in the 'parameters' attribute for OpenAPI
                # tools
                if hasattr(component, "parameters") and component.parameters:
                    properties = component.parameters.get("properties", {})
                    if "app_identifier" in properties:
                        del properties["app_identifier"]
                        logger.debug(
                            f"✅ Removed app_identifier from tool schema: {component.name}"
                        )

                    # Also remove from required fields if present
                    required = component.parameters.get("required", [])
                    if "app_identifier" in required:
                        required.remove("app_identifier")
                        component.parameters["required"] = required
                        logger.debug(
                            f"✅ Removed app_identifier from required fields: {component.name}"
                        )

                # Add detailed debug logging for schema validation issues
                tool_name = getattr(component, "name", "unknown")
                logger.debug(f"🔧 Customized tool: {tool_name}")

                # Log response schema information for debugging
                if hasattr(component, "_response_schema"):
                    logger.debug(f"📋 Tool {tool_name} has response schema")
                elif hasattr(component, "response_schema"):
                    logger.debug(f"📋 Tool {tool_name} has response_schema attribute")
                else:
                    logger.debug(
                        f"⚠️  Tool {tool_name} has no response schema attribute"
                    )
        except Exception as e:
            logger.warning(
                f"Error customizing component {getattr(component, 'name', 'unknown')}: {e}"
            )

    def _create_mcp_server(self) -> FastMCP:
        """Create the FastMCP server with OpenAPI integration."""
        try:
            logger.info("Creating FastMCP server with HDX OpenAPI integration...")

            mcp = FastMCP.from_openapi(
                openapi_spec=self.openapi_spec,
                client=self.client,
                name="HDX Humanitarian Data Exchange Server",
                route_maps=self._create_route_mappings(),
                tags={"hdx", "humanitarian", "data"},
                mcp_component_fn=self._customize_mcp_components,
            )

            logger.info("FastMCP server created successfully")
            return mcp

        except Exception as e:
            logger.error(f"Failed to create FastMCP server: {e}")
            raise

    def _register_custom_tools(self):
        """Register custom tools alongside the OpenAPI-derived ones."""
        self._register_tools()
        self._register_prompts()
        logger.info("Custom tools and prompts registered successfully")

    def _register_tools(self):
        """Register custom tools from the tools module."""

        @self.mcp.tool("hdx_server_info")
        async def get_server_info() -> Dict[str, Any]:
            """Get information about the HDX MCP server instance."""
            return await hdx_tools.get_server_info(self)

        @self.mcp.tool("hdx_get_dataset_info")
        async def get_dataset_info(dataset_hdx_id: str) -> Dict[str, Any]:
            """
            Get detailed information about a specific HDX dataset.

            Args:
                dataset_hdx_id: The HDX dataset identifier

            Returns:
                Dictionary containing dataset information
            """
            return await hdx_tools.get_dataset_info(self, dataset_hdx_id)

        @self.mcp.tool("hdx_search_locations")
        async def search_locations(
            name_pattern: Optional[str] = None, has_hrp: Optional[bool] = None
        ) -> Dict[str, Any]:
            """
            Search for locations (countries) in the HDX system.

            Args:
                name_pattern: Optional pattern to match location names
                has_hrp: Optional filter for locations with Humanitarian Response Plans

            Returns:
                Dictionary containing matching locations
            """
            return await hdx_tools.search_locations(self, name_pattern, has_hrp)

    def _register_prompts(self):
        """Register custom prompts from the prompts module."""

        @self.mcp.prompt("population_data_guidance")
        async def population_data_guidance_prompt() -> str:
            """
            Guidance for querying population data from HDX.

            Provides information about available population-related tools and data availability considerations.
            """
            return await population_guidance.population_data_guidance()

        @self.mcp.prompt("hdx_usage_instructions")
        async def hdx_usage_instructions_prompt() -> str:
            """
            Instructions for using HDX tools effectively.

            Provides guidance on handling disaggregated data, pagination,
                and parameter optimization.
            """
            return await hdx_usage_instructions.hdx_usage_instructions()

        @self.mcp.prompt("data_coverage_guidance")
        async def data_coverage_guidance_prompt() -> str:
            """
            Critical guidance for understanding and verifying data coverage in HDX.

            Explains how data availability varies by country, administrative level, and data type.
            Emphasizes mandatory use of metadata_data_availability_get for verification.
            """
            return await data_coverage_guidance.data_coverage_guidance()

    def run_stdio(self):
        """Run the server using stdio transport."""
        logger.info("Starting HDX MCP Server with stdio transport...")
        # FastMCP's run method handles its own event loop
        self.mcp.run(transport="stdio")

    def run_http(self):
        """Run the server using HTTP transport."""
        logger.info(
            f"Starting HDX MCP Server with HTTP transport on {self.host}:{self.port}"
        )
        # FastMCP's run method handles its own event loop
        self.mcp.run(transport="http", host=self.host, port=self.port)

    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down HDX MCP Server...")
        if self.client:
            await self.client.aclose()


def main():
    """Main entry point for the HDX MCP Server."""
    parser = argparse.ArgumentParser(
        description="HDX MCP Server - Humanitarian Data Exchange API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hdx_mcp_server.py                    # Run with stdio transport
  python hdx_mcp_server.py --transport http   # Run with HTTP transport
  python hdx_mcp_server.py --transport http --port 9000  # HTTP on custom port
        """,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind HTTP server to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind HTTP server to (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Create and configure server
        server = HDXMCPServer()

        # Override host/port if provided via command line
        if args.host != DEFAULT_HOST:
            server.host = args.host
        if args.port != DEFAULT_PORT:
            server.port = args.port

        # Run server with selected transport
        if args.transport == "http":
            server.run_http()
        else:
            server.run_stdio()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if "server" in locals():
            # Shutdown doesn't need to be awaited since run() handles the event loop
            pass


if __name__ == "__main__":
    # Handle direct execution
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
