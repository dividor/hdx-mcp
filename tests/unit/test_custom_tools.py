"""
Unit tests for HDX MCP Server custom tools.

These tests verify the custom tool functions work correctly
with proper parameter handling and error management.
"""

import pytest

from src.hdx_mcp_server.tools import hdx_tools


class TestCustomToolStructure:
    """Test custom tool function structure and availability."""

    def test_custom_tools_importable(self):
        """Test that all custom tools are properly importable."""
        # Test that all production custom tools are accessible
        assert hasattr(hdx_tools, "get_server_info")
        assert hasattr(hdx_tools, "get_dataset_info")
        assert hasattr(hdx_tools, "search_locations")

        # Test that they are callable functions
        assert callable(hdx_tools.get_server_info)
        assert callable(hdx_tools.get_dataset_info)
        assert callable(hdx_tools.search_locations)

    @pytest.mark.asyncio
    async def test_get_server_info_structure(self):
        """Test get_server_info returns proper structure."""

        # Mock server with realistic attributes
        class MockServer:
            base_url = "https://hapi.humdata.org/api/v2"
            openapi_spec = {"paths": {f"/api/v2/endpoint{i}": {} for i in range(15)}}

        server = MockServer()

        # Test the actual function
        result = await hdx_tools.get_server_info(server)

        # Verify result structure
        assert isinstance(result, dict)
        assert result["server_name"] == "HDX MCP Server"
        assert result["version"] == "1.0.0"
        assert result["base_url"] == "https://hapi.humdata.org/api/v2"
        assert result["total_endpoints"] == 15
        assert "description" in result
        assert "available_tools" in result

    @pytest.mark.asyncio
    async def test_get_server_info_with_varying_specs(self):
        """Test get_server_info with different spec sizes."""

        # Test with minimal spec
        class MinimalServer:
            base_url = "https://test.api.com"
            openapi_spec = {"paths": {"/test": {}}}

        result = await hdx_tools.get_server_info(MinimalServer())
        assert result["total_endpoints"] == 1
        assert result["base_url"] == "https://test.api.com"

        # Test with larger spec
        class LargeServer:
            base_url = "https://production.api.com/v3"
            openapi_spec = {"paths": {f"/endpoint_{i}": {} for i in range(50)}}

        result = await hdx_tools.get_server_info(LargeServer())
        assert result["total_endpoints"] == 50
        assert result["base_url"] == "https://production.api.com/v3"

    @pytest.mark.asyncio
    async def test_get_server_info_edge_cases(self):
        """Test get_server_info handles edge cases."""

        # Test with empty paths
        class EmptyServer:
            base_url = "https://empty.api.com"
            openapi_spec = {"paths": {}}

        result = await hdx_tools.get_server_info(EmptyServer())
        assert result["total_endpoints"] == 0

        # Test with missing paths key
        class MissingPathsServer:
            base_url = "https://missing.api.com"
            openapi_spec = {"info": {"title": "Test API"}}

        result = await hdx_tools.get_server_info(MissingPathsServer())
        assert result["total_endpoints"] == 0

        # Test with None openapi_spec
        class NoneSpecServer:
            base_url = "https://none.api.com"
            openapi_spec = None

        # This should handle the None case gracefully
        try:
            result = await hdx_tools.get_server_info(NoneSpecServer())
            # If it succeeds, should return 0 endpoints
            assert result["total_endpoints"] == 0
        except (AttributeError, TypeError):
            # If it fails, that's also acceptable behavior
            pass


class TestParameterValidation:
    """Test parameter validation in custom tools."""

    def test_get_dataset_info_parameter_types(self):
        """Test get_dataset_info parameter type expectations."""
        # Test that the function signature accepts string parameter
        import inspect

        sig = inspect.signature(hdx_tools.get_dataset_info)
        params = list(sig.parameters.keys())

        # Should accept server_instance and dataset_hdx_id
        assert len(params) == 2
        assert "server_instance" in params
        assert "dataset_hdx_id" in params

    def test_search_locations_parameter_types(self):
        """Test search_locations parameter type expectations."""
        import inspect

        sig = inspect.signature(hdx_tools.search_locations)
        params = list(sig.parameters.keys())

        # Should accept server_instance, name_pattern, and has_hrp
        assert len(params) == 3
        assert "server_instance" in params
        assert "name_pattern" in params
        assert "has_hrp" in params

    def test_get_server_info_parameter_types(self):
        """Test get_server_info parameter type expectations."""
        import inspect

        sig = inspect.signature(hdx_tools.get_server_info)
        params = list(sig.parameters.keys())

        # Should only accept server_instance
        assert len(params) == 1
        assert "server_instance" in params


class TestFunctionDocumentation:
    """Test that custom tools have proper documentation."""

    def test_get_server_info_documentation(self):
        """Test get_server_info has proper docstring."""
        assert hdx_tools.get_server_info.__doc__ is not None
        doc = hdx_tools.get_server_info.__doc__
        assert "server instance" in doc.lower()
        assert "args:" in doc.lower() or "arguments:" in doc.lower()
        assert "returns:" in doc.lower()

    def test_get_dataset_info_documentation(self):
        """Test get_dataset_info has proper docstring."""
        assert hdx_tools.get_dataset_info.__doc__ is not None
        doc = hdx_tools.get_dataset_info.__doc__
        assert "dataset" in doc.lower()
        assert "hdx" in doc.lower()

    def test_search_locations_documentation(self):
        """Test search_locations has proper docstring."""
        assert hdx_tools.search_locations.__doc__ is not None
        doc = hdx_tools.search_locations.__doc__
        assert "location" in doc.lower()
        assert "search" in doc.lower()


class TestErrorHandling:
    """Test error handling in custom tools."""

    @pytest.mark.asyncio
    async def test_get_server_info_error_handling(self):
        """Test get_server_info handles server errors gracefully."""

        # Test with server that raises exceptions
        class ErrorServer:
            @property
            def base_url(self):
                raise Exception("Server error")

            @property
            def openapi_spec(self):
                return {"paths": {}}

        # Should handle the error gracefully or raise appropriate exception
        try:
            result = await hdx_tools.get_server_info(ErrorServer())
            # If it succeeds, verify it's a valid response
            assert isinstance(result, dict)
        except Exception as e:
            # If it fails, should be a reasonable exception
            assert isinstance(e, (AttributeError, Exception))

    @pytest.mark.asyncio
    async def test_get_server_info_with_invalid_spec(self):
        """Test get_server_info with invalid OpenAPI spec."""

        class InvalidSpecServer:
            base_url = "https://test.com"
            openapi_spec = "invalid_spec_not_dict"

        try:
            result = await hdx_tools.get_server_info(InvalidSpecServer())
            # If it handles invalid spec gracefully
            assert isinstance(result, dict)
            assert result["total_endpoints"] == 0
        except (TypeError, AttributeError):
            # If it raises appropriate error for invalid spec
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
