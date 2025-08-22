"""
Integration tests for HDX tools to ensure they work with real API endpoints.

These tests verify that tools can successfully communicate with the HDX API
and return expected data structures.
"""

import os

import pytest
from asyncio_throttle import Throttler

from src.hdx_mcp_server.server import HDXMCPServer
from src.hdx_mcp_server.tools import hdx_tools


@pytest.mark.asyncio
class TestHDXToolsIntegration:
    """Integration tests for HDX MCP tools."""

    @pytest.fixture(autouse=True)
    async def setup_server(self):
        """Set up minimal server instance for testing."""
        # Ensure we have required environment variables
        api_key = os.getenv("HDX_API_KEY")
        assert (
            api_key
        ), "HDX_API_KEY environment variable is required for integration tests"

        # Create minimal server instance
        self.server = object.__new__(HDXMCPServer)
        self.server.api_key = api_key
        self.server.base_url = "https://hapi.humdata.org/api/v2"
        self.server.app_name = os.getenv("HDX_APP_NAME", "hdx-mcp-server")
        self.server.app_email = os.getenv("HDX_APP_EMAIL", "test@example.com")
        self.server.timeout = 30.0

        # Initialize rate limiting
        self.server.throttler = Throttler(rate_limit=10, period=60.0)

        # Create HTTP client
        self.server.client = self.server._create_http_client()

    async def teardown(self):
        """Clean up after tests."""
        if hasattr(self.server, "client"):
            await self.server.client.aclose()

    async def test_search_locations_fixed(self):
        """Test that search_locations now works correctly after parameter fix."""
        result = await hdx_tools.search_locations(self.server, name_pattern="Iraq")

        assert "status" in result
        assert result["status"] == "success"
        assert "locations" in result
        assert "count" in result
        assert result["count"] > 0

        # Verify we got Iraq in the results
        iraq_found = any(loc.get("code") == "IRQ" for loc in result["locations"])
        assert iraq_found, "Iraq should be found in search results"

    async def test_search_locations_no_filter(self):
        """Test search_locations without filters returns multiple results."""
        result = await hdx_tools.search_locations(self.server)

        assert "status" in result
        assert result["status"] == "success"
        assert "locations" in result
        assert "count" in result
        assert result["count"] > 50  # Should return many countries

    async def test_get_server_info(self):
        """Test get_server_info custom tool."""
        # Mock the openapi_spec for this test
        self.server.openapi_spec = {"paths": {f"/test{i}": {} for i in range(27)}}

        result = await hdx_tools.get_server_info(self.server)

        assert "server_name" in result
        assert "version" in result
        assert "base_url" in result
        assert "total_endpoints" in result
        assert result["server_name"] == "HDX MCP Server"
        assert result["total_endpoints"] == 27

    async def test_metadata_location_endpoint(self):
        """Test basic metadata/location endpoint access."""
        response = await self.server._rate_limited_request(
            "get", "/metadata/location", params={"limit": 3}
        )
        response.raise_for_status()
        data = response.json()

        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 3
        if data["data"]:
            location = data["data"][0]
            assert "code" in location
            assert "name" in location

    async def test_metadata_data_availability_endpoint(self):
        """Test metadata/data-availability endpoint - critical for data coverage."""
        response = await self.server._rate_limited_request(
            "get", "/metadata/data-availability", params={"limit": 5}
        )
        response.raise_for_status()
        data = response.json()

        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_affected_people_refugees_endpoint(self):
        """Test affected-people/refugees-persons-of-concern endpoint."""
        response = await self.server._rate_limited_request(
            "get", "/affected-people/refugees-persons-of-concern", params={"limit": 5}
        )
        response.raise_for_status()
        data = response.json()

        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_baseline_population_endpoint(self):
        """Test geography-infrastructure/baseline-population endpoint."""
        response = await self.server._rate_limited_request(
            "get", "/geography-infrastructure/baseline-population", params={"limit": 5}
        )
        response.raise_for_status()
        data = response.json()

        assert "data" in data
        assert isinstance(data["data"], list)

    async def test_app_identifier_is_correctly_encoded(self):
        """Test that app_identifier is properly base64 encoded."""
        # Make a request and verify it works (proper encoding)
        response = await self.server._rate_limited_request(
            "get", "/metadata/location", params={"limit": 1}
        )
        response.raise_for_status()

        # If we get here without a 401/403, the app_identifier is working
        assert response.status_code == 200
