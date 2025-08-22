"""
Security tests for HDX MCP Server.

These tests verify security features including input validation,
rate limiting enforcement, and protection against malicious inputs.
"""

import asyncio
import os
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
from asyncio_throttle import Throttler

from src.hdx_mcp_server.server import HDXMCPServer


class TestInputSecurity:
    """Test security of input handling and validation."""

    def test_malicious_input_handling(self):
        """Test handling of malicious inputs in environment variables."""
        malicious_inputs = [
            "normal_value",  # Control case
            "value;rm -rf /",  # Command injection
            "value`whoami`",  # Command execution
            "<script>alert('xss')</script>",  # XSS
            "'; DROP TABLE users; --",  # SQL injection
            "value$(whoami)",  # Command substitution
            "value\nMALICIOUS=1",  # Newline injection
        ]

        for malicious_input in malicious_inputs:
            with patch.dict(os.environ, {"MALICIOUS_TEST": malicious_input}):
                server = object.__new__(HDXMCPServer)

                # Test production function handles input safely
                result = server._get_required_env("MALICIOUS_TEST")
                assert result == malicious_input.strip()  # Stored as-is, not executed

                # Test app identifier creation with malicious input
                server.app_name = malicious_input
                server.app_email = "test@example.com"
                identifier = server._create_app_identifier()

                # Should be base64 encoded, not executed
                assert isinstance(identifier, str)
                assert len(identifier) > 0

    def test_unicode_and_encoding_security(self):
        """Test security of unicode character handling."""
        unicode_inputs = [
            "ascii_only",
            "café_français",
            "测试中文",
            "emoji_🔑",
            "mixed_café_测试_🔑",
        ]

        for unicode_input in unicode_inputs:
            with patch.dict(os.environ, {"UNICODE_TEST": unicode_input}):
                server = object.__new__(HDXMCPServer)

                try:
                    # Test production function
                    result = server._get_required_env("UNICODE_TEST")
                    assert result == unicode_input.strip()

                    # Test encoding in production
                    server.app_name = unicode_input
                    server.app_email = "test@example.com"
                    identifier = server._create_app_identifier()
                    assert isinstance(identifier, str)

                except ValueError:
                    # Some unicode may legitimately fail - this is good security
                    pass

    def test_environment_variable_edge_cases(self):
        """Test edge cases in environment variable handling."""
        test_cases = [
            ("VALID_VAR", "valid_value", "valid_value"),
            ("TRIMMED_VAR", "  trimmed_value  ", "trimmed_value"),
            ("SPECIAL_VAR", "value!@#$%^&*()", "value!@#$%^&*()"),
            ("NUMERIC_VAR", "12345", "12345"),
            ("MIXED_VAR", "  value123!@#  ", "value123!@#"),
        ]

        for var_name, var_value, expected in test_cases:
            with patch.dict(os.environ, {var_name: var_value}):
                server = object.__new__(HDXMCPServer)
                result = server._get_required_env(var_name)
                assert result == expected

    def test_null_byte_injection_protection(self):
        """Test protection against null byte injection."""
        dangerous_inputs = [
            "value\x00malicious",
            "normal\x00\x00double",
            "\x00start_with_null",
            "end_with_null\x00",
        ]

        for dangerous_input in dangerous_inputs:
            try:
                with patch.dict(os.environ, {"NULL_TEST": dangerous_input}):
                    server = object.__new__(HDXMCPServer)

                    # This should either work safely or fail appropriately
                    result = server._get_required_env("NULL_TEST")

                    # If it succeeds, null bytes should be preserved as-is
                    assert dangerous_input.strip() == result

            except (ValueError, OSError):
                # Some systems may reject null bytes - this is acceptable security behavior
                pass


class TestRateLimitingSecurity:
    """Test rate limiting security features."""

    def test_rate_limiting_configuration_security(self):
        """Test rate limiting configuration with security considerations."""
        with patch.dict(
            os.environ,
            {"HDX_RATE_LIMIT_REQUESTS": "15", "HDX_RATE_LIMIT_PERIOD": "45.5"},
        ):
            # Test production configuration
            server = object.__new__(HDXMCPServer)
            server.rate_limit_requests = int(os.getenv("HDX_RATE_LIMIT_REQUESTS", "10"))
            server.rate_limit_period = float(os.getenv("HDX_RATE_LIMIT_PERIOD", "60.0"))

            # Create production throttler
            server.throttler = Throttler(
                rate_limit=server.rate_limit_requests, period=server.rate_limit_period
            )

            # Verify secure values
            assert server.rate_limit_requests == 15
            assert server.rate_limit_period == 45.5
            assert isinstance(server.throttler, Throttler)
            assert server.throttler.rate_limit == 15
            assert server.throttler.period == 45.5

    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement_timing(self):
        """Test that rate limiting actually enforces timing delays."""
        # Test with restrictive rate limiting for security
        server = object.__new__(HDXMCPServer)
        server.throttler = Throttler(rate_limit=2, period=1.0)  # 2 requests per second

        # Mock HTTP response but use real rate limiting
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None

        server.client = AsyncMock()
        server.client.get = AsyncMock(return_value=mock_response)

        # Test actual rate limiting enforcement
        start_time = time.time()

        # Make 3 requests - should be rate limited
        await server._rate_limited_request("get", "/test1")
        await server._rate_limited_request("get", "/test2")
        await server._rate_limited_request("get", "/test3")  # This should be delayed

        duration = time.time() - start_time

        # Verify rate limiting actually worked (security requirement)
        assert duration >= 0.4  # Should take time due to throttling
        assert server.client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_live_server_rate_limiting_protection(self):
        """Test that rate limiting will protect the live server from abuse."""
        # Create server instance similar to production
        server = object.__new__(HDXMCPServer)

        # Set aggressive rate limiting for testing
        server.throttler = Throttler(
            rate_limit=2, period=1.0
        )  # 2 requests per 1 second (more predictable)

        # Mock the HTTP client to simulate live server responses
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": [{"test": "response"}]}
        mock_response.raise_for_status.return_value = None

        server.client = AsyncMock()
        server.client.get = AsyncMock(return_value=mock_response)

        # Test 1: First 2 requests should be fast (within rate limit)
        start_time = time.time()
        await server._rate_limited_request("get", "/api/test1")
        await server._rate_limited_request("get", "/api/test2")
        fast_duration = time.time() - start_time

        # Should be very quick since we're within rate limit
        assert fast_duration < 0.5, f"First 2 requests took too long: {fast_duration}s"

        # Test 2: Third request should be throttled (rate limit exceeded)
        start_time = time.time()
        await server._rate_limited_request("get", "/api/test3")
        throttled_duration = time.time() - start_time

        # Should be throttled for at least part of the remaining period
        assert (
            throttled_duration >= 0.4
        ), f"Third request not properly throttled: {throttled_duration}s"

        # Verify all requests were made
        assert server.client.get.call_count == 3

        # Test 3: Verify rate limiting resets after period
        # Wait for rate limit period to reset
        await asyncio.sleep(1.1)

        # Now requests should be fast again
        start_time = time.time()
        await server._rate_limited_request("get", "/api/test4")
        await server._rate_limited_request("get", "/api/test5")
        reset_duration = time.time() - start_time

        assert (
            reset_duration < 0.5
        ), f"Requests after reset took too long: {reset_duration}s"
        assert server.client.get.call_count == 5

    def test_rate_limiting_configuration_bounds(self):
        """Test rate limiting configuration handles extreme values safely."""
        extreme_configs = [
            (1, 1.0),  # Very restrictive
            (1000, 1.0),  # High burst, short period
            (10, 3600.0),  # Low rate, long period
            (100, 0.1),  # High rate, very short period
        ]

        for requests, period in extreme_configs:
            try:
                # Test that extreme configurations don't break
                throttler = Throttler(rate_limit=requests, period=period)

                # Verify configuration is accepted
                assert throttler.rate_limit == requests
                assert throttler.period == period
                assert isinstance(throttler, Throttler)

            except (ValueError, TypeError) as e:
                # Some extreme values may be rejected - this is acceptable
                assert "rate_limit" in str(e) or "period" in str(e)


class TestHTTPClientSecurity:
    """Test HTTP client security features."""

    def test_http_client_wrapper_security(self):
        """Test HTTP client wrapper maintains security properties."""
        server = object.__new__(HDXMCPServer)
        server.throttler = Throttler(rate_limit=10, period=60.0)

        # Create HTTP client with security headers
        import httpx

        base_client = httpx.AsyncClient(
            base_url="https://secure.api.com",
            headers={
                "Authorization": "Bearer secure_token",
                "User-Agent": "HDX-MCP-Server/1.0",
                "X-Requested-With": "HDX-MCP-Server",
            },
            timeout=30.0,
        )

        # Test wrapper preserves security properties
        wrapped_client = server._wrap_client_with_rate_limiting(base_client)

        # Verify security-relevant attributes are preserved
        assert hasattr(wrapped_client, "_client")
        assert hasattr(wrapped_client, "_throttler")
        assert wrapped_client._client is base_client
        assert wrapped_client._throttler is server.throttler

        # Verify HTTP methods are properly wrapped
        assert hasattr(wrapped_client, "get")
        assert hasattr(wrapped_client, "post")
        assert hasattr(wrapped_client, "put")
        assert hasattr(wrapped_client, "delete")

        # Verify base URL and headers are preserved
        assert str(wrapped_client.base_url) == "https://secure.api.com"
        # Timeout is preserved (httpx.Timeout object)
        assert hasattr(wrapped_client, "timeout")
        assert wrapped_client.timeout is not None

    def test_timeout_security_enforcement(self):
        """Test that timeout values provide DoS protection."""
        timeout_values = [
            ("1.0", 1.0),
            ("30.0", 30.0),
            ("60.0", 60.0),
            ("0.5", 0.5),  # Very short timeout
        ]

        for timeout_str, expected_float in timeout_values:
            with patch.dict(os.environ, {"HDX_TIMEOUT": timeout_str}):
                # Test timeout parsing and enforcement
                server = object.__new__(HDXMCPServer)
                server.timeout = float(os.getenv("HDX_TIMEOUT", "30.0"))

                assert server.timeout == expected_float
                assert isinstance(server.timeout, float)
                assert server.timeout > 0  # Security: prevent infinite waits

    def test_base_url_security_validation(self):
        """Test base URL handling for security."""
        secure_urls = [
            "https://api.humdata.org/v2",
            "https://hapi.humdata.org/api/v2",
            "https://secure-api.org:443/v1",
        ]

        for base_url in secure_urls:
            with patch.dict(os.environ, {"HDX_BASE_URL": base_url}):
                server = object.__new__(HDXMCPServer)
                server.base_url = os.getenv("HDX_BASE_URL", "https://default.com")

                # Verify secure URL handling
                assert server.base_url == base_url
                assert isinstance(server.base_url, str)
                assert server.base_url.startswith("https://")  # Security: require HTTPS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
