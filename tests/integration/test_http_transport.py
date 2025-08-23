#!/usr/bin/env python3
"""Integration tests for HTTP transport functionality."""

import json
import subprocess
import time
from contextlib import contextmanager

import pytest
import requests


@pytest.fixture(scope="module")
def http_server():
    """Start HTTP server for testing."""
    import os

    # Start the server in a subprocess
    env = os.environ.copy()
    env.update(
        {
            "HDX_APP_IDENTIFIER": "test-key",
            "HDX_BASE_URL": "https://hapi.humdata.org",
            "HDX_OPENAPI_URL": "https://hapi.humdata.org/openapi.json",
            "HDX_HOST": "127.0.0.1",
            "HDX_PORT": "9001",  # Different port to avoid conflicts
        }
    )

    process = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-m",
            "hdx_mcp_server",
            "--transport",
            "http",
            "--host",
            "127.0.0.1",
            "--port",
            "9001",
        ],
        env=env,
    )

    # Wait for server to start
    time.sleep(5)

    yield "http://127.0.0.1:9001/mcp"

    # Clean up
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@contextmanager
def mcp_session(base_url: str):
    """Context manager for MCP HTTP session with proper initialization."""
    # Initialize session
    init_response = requests.post(
        base_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        },
    )

    session_id = init_response.headers.get("mcp-session-id")
    assert session_id, "Failed to get session ID"

    # Send initialized notification
    requests.post(
        base_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
        },
        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    )

    # Wait for initialization
    time.sleep(2)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": session_id,
    }

    try:
        yield headers
    finally:
        pass  # Session cleanup if needed


@pytest.mark.integration
class TestHTTPTransport:
    """Integration tests for HTTP transport."""

    def test_tools_list(self, http_server):
        """Test that tools list works via HTTP."""
        with mcp_session(http_server) as headers:
            response = requests.post(
                http_server,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "list-tools",
                    "method": "tools/list",
                    "params": {},
                },
            )

            assert response.status_code == 200
            # Should contain our expected tools
            response_text = response.text
            assert "hdx_server_info" in response_text
            assert "hdx_get_dataset_info" in response_text

    def test_simple_tool_call(self, http_server):
        """Test simple tool call works."""
        with mcp_session(http_server) as headers:
            response = requests.post(
                http_server,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "dataset-test",
                    "method": "tools/call",
                    "params": {
                        "name": "hdx_get_dataset_info",
                        "arguments": {"dataset_hdx_id": "test-dataset"},
                    },
                },
            )

            assert response.status_code == 200

            # Parse SSE response
            lines = response.text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    json_data = line[6:]
                    try:
                        parsed = json.loads(json_data)
                        if "result" in parsed and not parsed["result"].get(
                            "isError", False
                        ):
                            content = parsed["result"]["content"][0]["text"]
                            data = json.loads(content)
                            # Should return either success or error, but with proper
                            # structure
                            assert "dataset_hdx_id" in data
                            return
                    except Exception:
                        continue

            pytest.fail("Tool call did not return expected result")

    def test_hdx_server_info_call(self, http_server):
        """Test hdx_server_info tool call works."""
        with mcp_session(http_server) as headers:
            response = requests.post(
                http_server,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-hdx-info",
                    "method": "tools/call",
                    "params": {"name": "hdx_server_info", "arguments": {}},
                },
            )

            assert response.status_code == 200

            # Parse SSE response
            lines = response.text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    json_data = line[6:]
                    try:
                        parsed = json.loads(json_data)
                        if "result" in parsed:
                            result = parsed["result"]
                            if result.get("isError", False):
                                error_text = result["content"][0]["text"]
                                pytest.fail(f"Tool call failed: {error_text}")
                            else:
                                content = result["content"][0]["text"]
                                # Should contain server information
                                assert (
                                    "HDX MCP Server" in content
                                    or "api_version" in content
                                )
                                return
                    except Exception:
                        continue

            pytest.fail("hdx_server_info tool did not return expected result")

    def test_hdx_search_locations_call(self, http_server):
        """Test hdx_search_locations tool call works."""
        with mcp_session(http_server) as headers:
            response = requests.post(
                http_server,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "test-search-locations",
                    "method": "tools/call",
                    "params": {"name": "hdx_search_locations", "arguments": {}},
                },
            )

            assert response.status_code == 200

            # Parse SSE response
            lines = response.text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    json_data = line[6:]
                    try:
                        parsed = json.loads(json_data)
                        if "result" in parsed:
                            result = parsed["result"]
                            if result.get("isError", False):
                                error_text = result["content"][0]["text"]
                                pytest.fail(f"Tool call failed: {error_text}")
                            else:
                                # Check if response contains location data
                                content_text = result["content"][0]["text"]
                                data = json.loads(content_text)
                                assert (
                                    "status" in data
                                    or "locations" in data
                                    or "error" in data
                                )
                                return
                    except Exception:
                        continue

            pytest.fail("hdx_search_locations tool did not return expected result")
