"""
Unit tests for HDX MCP Server core functions.

These tests verify individual server functions in isolation,
testing the actual production code without external dependencies.
"""

import base64
import os
from unittest.mock import patch

import pytest
from asyncio_throttle import Throttler

from src.hdx_mcp_server.server import HDXMCPServer


class TestEnvironmentHandling:
    """Test environment variable handling functions."""

    def test_get_required_env_validation(self):
        """Test _get_required_env with various input scenarios."""
        server = object.__new__(HDXMCPServer)

        # Test valid environment variable
        with patch.dict(os.environ, {"TEST_KEY": "valid_value"}):
            result = server._get_required_env("TEST_KEY")
            assert result == "valid_value"

        # Test trimming whitespace (production behavior)
        with patch.dict(os.environ, {"WHITESPACE_KEY": "  trimmed  "}):
            result = server._get_required_env("WHITESPACE_KEY")
            assert result == "trimmed"

        # Test missing variable raises ValueError
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Required environment variable MISSING is not set"
            ):
                server._get_required_env("MISSING")

        # Test empty string raises ValueError
        with patch.dict(os.environ, {"EMPTY": ""}):
            with pytest.raises(
                ValueError, match="Required environment variable EMPTY is not set"
            ):
                server._get_required_env("EMPTY")

        # Test whitespace-only string raises ValueError
        with patch.dict(os.environ, {"WHITESPACE_ONLY": "   \t\n  "}):
            with pytest.raises(
                ValueError,
                match="Required environment variable WHITESPACE_ONLY is not set",
            ):
                server._get_required_env("WHITESPACE_ONLY")

    def test_create_app_identifier(self):
        """Test _create_app_identifier for API authentication."""
        server = object.__new__(HDXMCPServer)

        # Test normal case
        server.app_name = "test-app"
        server.app_email = "user@example.com"
        result = server._create_app_identifier()

        expected = base64.b64encode("test-app:user@example.com".encode()).decode()
        assert result == expected

        # Test with special characters (production scenario)
        server.app_name = "app-with-special!@#"
        server.app_email = "user+tag@domain.co.uk"
        result = server._create_app_identifier()

        expected = base64.b64encode(
            "app-with-special!@#:user+tag@domain.co.uk".encode()
        ).decode()
        assert result == expected

        # Test unicode handling
        server.app_name = "app-测试"
        server.app_email = "user@example.com"
        result = server._create_app_identifier()

        expected = base64.b64encode("app-测试:user@example.com".encode()).decode()
        assert result == expected


class TestOpenAPIProcessing:
    """Test OpenAPI specification processing functions."""

    def test_fix_openapi_schema_references(self):
        """Test _fix_openapi_schema_references with parameter defaults."""
        server = object.__new__(HDXMCPServer)

        # Test with realistic schema structure including parameters
        test_spec = {
            "components": {
                "schemas": {
                    "LocationResponse": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "admin1": {"$ref": "#/components/schemas/Admin1"},
                        },
                    },
                    "Admin1": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                }
            },
            "paths": {
                "/api/v2/metadata/location": {
                    "get": {
                        "parameters": [
                            {
                                "name": "limit",
                                "schema": {"type": "integer", "default": 10000},
                            },
                            {"name": "age_range", "schema": {"type": "string"}},
                            {"name": "gender", "schema": {"type": "string"}},
                        ],
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/LocationResponse"
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }

        # Test the actual production function
        result = server._fix_openapi_schema_references(test_spec)

        # Verify structure preservation
        assert "components" in result
        assert "schemas" in result["components"]
        assert "LocationResponse" in result["components"]["schemas"]
        assert "/api/v2/metadata/location" in result["paths"]

        # Verify parameter defaults are set correctly
        params = result["paths"]["/api/v2/metadata/location"]["get"]["parameters"]
        limit_param = next(p for p in params if p["name"] == "limit")
        age_param = next(p for p in params if p["name"] == "age_range")
        gender_param = next(p for p in params if p["name"] == "gender")

        # Verify production defaults
        assert limit_param["schema"]["default"] == 10
        assert age_param["schema"]["default"] == "all"
        assert gender_param["schema"]["default"] == "all"

    def test_simplify_operation_ids(self):
        """Test _simplify_operation_ids creates clean tool names."""
        server = object.__new__(HDXMCPServer)

        test_spec = {
            "paths": {
                "/api/v2/affected-people/idps": {
                    "get": {
                        "operationId": "long_generated_operation_id_affected_people_idps"
                    }
                },
                "/api/v2/metadata/location": {
                    "get": {"operationId": "very_long_metadata_location_operation_id"}
                },
                "/api/v2/unmapped/endpoint": {
                    "get": {"operationId": "should_remain_unchanged"}
                },
            }
        }

        # Test the actual production function
        result = server._simplify_operation_ids(test_spec)

        # Verify mapped paths get simplified
        assert (
            result["paths"]["/api/v2/affected-people/idps"]["get"]["operationId"]
            == "affected_people_idps_get"
        )
        assert (
            result["paths"]["/api/v2/metadata/location"]["get"]["operationId"]
            == "metadata_location_get"
        )

        # Verify unmapped paths remain unchanged
        assert (
            result["paths"]["/api/v2/unmapped/endpoint"]["get"]["operationId"]
            == "should_remain_unchanged"
        )

    def test_update_parameter_descriptions(self):
        """Test _update_parameter_descriptions modifies descriptions."""
        server = object.__new__(HDXMCPServer)

        test_spec = {
            "paths": {
                "/api/v2/test": {
                    "get": {
                        "parameters": [
                            {
                                "name": "limit",
                                "description": "See https://hdx-hapi.readthedocs.io/en/latest/ "
                                "for details",
                                "schema": {"type": "integer", "default": 10000},
                            },
                            {
                                "name": "admin_level",
                                "description": "Administrative level (0=country, "
                                "1=admin1, 2=admin2)",
                                "schema": {"type": "integer"},
                            },
                        ]
                    }
                }
            }
        }

        # Test the actual production function
        result = server._update_parameter_descriptions(test_spec)

        params = result["paths"]["/api/v2/test"]["get"]["parameters"]
        limit_param = next(p for p in params if p["name"] == "limit")
        admin_param = next(p for p in params if p["name"] == "admin_level")

        # Note: _update_parameter_descriptions doesn't change defaults
        assert limit_param["schema"]["default"] == 10000

        # Verify non-URL descriptions are preserved
        assert "Administrative level" in admin_param["description"]

    def test_add_admin_level_guidance(self):
        """Test _add_admin_level_guidance adds user guidance."""
        server = object.__new__(HDXMCPServer)

        test_spec = {
            "paths": {
                "/api/v2/affected-people/idps": {
                    "get": {
                        "operationId": "affected_people_idps_get",
                        "summary": "Get IDP data",
                    }
                },
                "/api/v2/baseline-population": {
                    "get": {
                        "operationId": "baseline_population_get",
                        "summary": "Get population data",
                    }
                },
                "/api/v2/metadata/location": {
                    "get": {
                        "operationId": "metadata_location_get",
                        "summary": "Get locations",
                    }
                },
            }
        }

        # Test the actual production function
        result = server._add_admin_level_guidance(test_spec)

        # Verify guidance is added to data endpoints but not metadata
        idps_summary = result["paths"]["/api/v2/affected-people/idps"]["get"]["summary"]
        pop_summary = result["paths"]["/api/v2/baseline-population"]["get"]["summary"]
        location_summary = result["paths"]["/api/v2/metadata/location"]["get"][
            "summary"
        ]

        assert "CRITICAL - Administrative Level Efficiency" in idps_summary
        assert "metadata_data_availability_get" in idps_summary
        assert "CRITICAL - Administrative Level Efficiency" in pop_summary
        assert (
            "CRITICAL - Data Coverage Warning" in location_summary
        )  # location endpoints now include data coverage warnings
        assert "Just because a country appears in location metadata" in location_summary

        # Test pagination guidance is added to ALL operations
        assert "Pagination" in idps_summary
        assert "limit` and `offset` parameters" in idps_summary
        assert "Pagination" in pop_summary
        assert "limit` and `offset` parameters" in pop_summary
        assert "Pagination" in location_summary
        assert "limit` and `offset` parameters" in location_summary

    def test_create_route_mappings(self):
        """Test _create_route_mappings creates proper MCP structure."""
        server = object.__new__(HDXMCPServer)

        # Test the actual production function
        route_maps = server._create_route_mappings()

        # Verify it returns valid RouteMap objects
        from fastmcp.server.openapi import RouteMap

        assert isinstance(route_maps, list)
        assert len(route_maps) > 0

        for route_map in route_maps:
            assert isinstance(route_map, RouteMap)
            assert hasattr(route_map, "pattern")
            assert isinstance(route_map.pattern, str)

        # Verify specific patterns exist
        patterns = [rm.pattern for rm in route_maps]
        assert any("affected-people" in pattern for pattern in patterns)
        assert any("metadata" in pattern for pattern in patterns)


class TestRateLimitingComponents:
    """Test rate limiting component creation and configuration."""

    def test_wrap_client_with_rate_limiting(self):
        """Test _wrap_client_with_rate_limiting creates proper wrapper."""
        server = object.__new__(HDXMCPServer)
        server.throttler = Throttler(rate_limit=5, period=60.0)

        # Create actual HTTP client
        import httpx

        base_client = httpx.AsyncClient(
            base_url="https://test.api.com",
            headers={"Authorization": "Bearer test"},
            timeout=30.0,
        )

        # Test the actual production function
        wrapped_client = server._wrap_client_with_rate_limiting(base_client)

        # Verify wrapper has required properties
        assert hasattr(wrapped_client, "get")
        assert hasattr(wrapped_client, "post")
        assert hasattr(wrapped_client, "_client")
        assert hasattr(wrapped_client, "_throttler")
        assert wrapped_client._client is base_client
        assert wrapped_client._throttler is server.throttler

        # Test attribute forwarding
        assert str(wrapped_client.base_url) == str(base_client.base_url)
        assert wrapped_client.timeout == base_client.timeout

    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration setup."""
        test_configs = [
            (1, 60.0),
            (10, 30.0),
            (50, 120.0),
            (100, 3600.0),
        ]

        for requests, period in test_configs:
            # Test production throttler creation
            throttler = Throttler(rate_limit=requests, period=period)

            # Verify configuration
            assert throttler.rate_limit == requests
            assert throttler.period == period
            assert isinstance(throttler, Throttler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
