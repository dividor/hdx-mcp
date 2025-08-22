"""
Shared test fixtures and configuration for HDX MCP Server tests.

This module contains pytest fixtures that are shared across all test modules.
"""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "HDX_API_KEY": "test_api_key_12345",
            "HDX_BASE_URL": "https://test.hapi.humdata.org/api/v2",
            "HDX_OPENAPI_URL": "https://test.hapi.humdata.org/openapi.json",
            "HDX_TIMEOUT": "15.0",
            "HDX_RATE_LIMIT_REQUESTS": "10",
            "HDX_RATE_LIMIT_PERIOD": "60.0",
            "HDX_APP_NAME": "test-app",
            "HDX_APP_EMAIL": "test@example.com",
            "MCP_HOST": "testhost",
            "MCP_PORT": "9999",
        },
    ):
        yield


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "HDX HAPI Test", "version": "1.0.0"},
        "paths": {
            "/api/v2/metadata/location": {
                "get": {
                    "operationId": "get_locations_test",
                    "tags": ["Metadata"],
                    "summary": "Test location endpoint",
                    "parameters": [
                        {
                            "name": "app_identifier",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            },
            "/api/v2/encode_app_identifier": {
                "get": {
                    "operationId": "get_encoded_identifier",
                    "tags": ["Util"],
                    "summary": "Generate app identifier",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            },
            "/api/v2/affected-people/idps": {
                "get": {
                    "operationId": "get_idps_test",
                    "tags": ["Affected People"],
                    "summary": "Test IDPs endpoint",
                    "parameters": [
                        {
                            "name": "app_identifier",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            },
        },
    }


@pytest.fixture
def mock_httpx_responses():
    """Mock httpx responses for API calls."""
    return {
        "openapi_spec": {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        },
        "dataset_info": {
            "data": [
                {
                    "dataset_hdx_id": "test-dataset-123",
                    "dataset_hdx_title": "Test Dataset",
                    "hdx_provider_name": "Test Provider",
                }
            ]
        },
        "locations": {
            "data": [{"code": "AFG", "name": "Afghanistan", "has_hrp": True}]
        },
    }
