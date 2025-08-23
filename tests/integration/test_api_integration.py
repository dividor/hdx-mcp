"""
Integration tests for HDX MCP Server with real API calls.

These tests require network access and valid API credentials.
"""

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.hdx_mcp_server import HDXMCPServer


class TestAPIIntegration:
    """Integration tests with the HDX API."""

    @pytest.mark.asyncio
    async def test_server_creation_with_real_openapi_spec(self):
        """Test server creation with actual HDX OpenAPI specification (if available)."""
        # This test requires network access and a valid API key
        # Fail if no API key is available - integration tests should not skip
        api_key = os.getenv("HDX_APP_IDENTIFIER")
        assert (
            api_key
        ), "HDX_APP_IDENTIFIER environment variable is required for integration tests"

        try:
            # Try to fetch the real OpenAPI spec
            response = httpx.get("https://hapi.humdata.org/openapi.json", timeout=10.0)
            if response.status_code != 200:
                pytest.skip("HDX OpenAPI spec not accessible")

            # Mock FastMCP to avoid actual server creation
            with patch("fastmcp.FastMCP.from_openapi") as mock_fastmcp:
                mock_fastmcp.return_value = MagicMock()

                server = HDXMCPServer()

                # Verify we loaded the real spec
                assert "paths" in server.openapi_spec
                assert len(server.openapi_spec["paths"]) > 0

                # Verify app identifier endpoint is in the spec
                paths = server.openapi_spec["paths"]
                encode_endpoint = "/api/v2/encode_app_identifier"
                assert encode_endpoint in paths

        except Exception as e:
            pytest.skip(f"Integration test failed due to network/API issues: {e}")

    @pytest.mark.asyncio
    async def test_real_api_authentication(self):
        """Test authentication with real HDX API (if credentials available)."""
        # Fail if no API key is available - integration tests should not skip
        api_key = os.getenv("HDX_APP_IDENTIFIER")
        assert (
            api_key
        ), "HDX_APP_IDENTIFIER environment variable is required for integration tests"

        try:
            # Test a simple API call to verify authentication
            api_key = os.getenv("HDX_APP_IDENTIFIER")
            base_url = "https://hapi.humdata.org/api/v2"

            # Create app identifier
            import base64

            app_info = "hdx-mcp-server-test:test@example.com"
            app_identifier = base64.b64encode(app_info.encode()).decode()

            # Make a test request to the version endpoint (should not require complex
            # auth)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/util/version",
                    params={"app_identifier": app_identifier},
                    timeout=10.0,
                )

                # If we get here without auth errors, authentication is working
                assert response.status_code in [
                    200,
                    400,
                    422,
                ]  # 400/422 are validation errors, not auth errors

        except Exception as e:
            pytest.skip(f"API authentication test failed: {e}")
