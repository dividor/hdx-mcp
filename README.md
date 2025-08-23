# HDX MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with seamless access to the [Humanitarian Data Exchange (HDX) API](https://data.humdata.org/hapi). This provides a wide array of humanitarian data as hosted on the [Humanitarian Data Exchange](https://data.humdata.org/)

This server automatically generates MCP tools from the HDX OpenAPI specification and includes custom tools for enhanced functionality.

## Available Tools (33 Total)

### 🔍 Metadata & Discovery (12 tools)
- `metadata_location_get` - Get countries/locations in HDX
- `metadata_admin1_get` - Get states/provinces
- `metadata_admin2_get` - Get districts/counties
- `metadata_data_availability_get` - **Check data coverage** (use first!)
- `metadata_dataset_get` - Get dataset information
- `metadata_resource_get` - Get resource details
- `metadata_org_get` - Get organizations
- `metadata_sector_get` - Get humanitarian sectors
- `metadata_currency_get` - Get currency info
- `metadata_org_type_get` - Get organization types
- `metadata_wfp_commodity_get` - Get WFP commodities
- `metadata_wfp_market_get` - Get WFP markets

### 🚨 Affected People (4 tools)
- `affected_people_refugees_get` - Get refugee/persons of concern data
- `affected_people_humanitarian_needs_get` - Get humanitarian needs data
- `affected_people_idps_get` - Get internally displaced persons data
- `affected_people_returnees_get` - Get returnee data

### 🌍 Demographics & Geography (1 tool)
- `geography_infrastructure_baseline_population_get` - Get population data

### 🌦️ Climate (1 tool)
- `climate_rainfall_get` - Get rainfall data

### 🤝 Coordination & Context (4 tools)
- `coordination_context_operational_presence_get` - Get operational presence
- `coordination_context_funding_get` - Get funding data
- `coordination_context_conflict_events_get` - Get conflict events
- `coordination_context_national_risk_get` - Get national risk data

### 🍽️ Food Security & Poverty (3 tools)
- `food_security_nutrition_poverty_food_security_get` - Get food security data
- `food_security_nutrition_poverty_food_prices_get` - Get food prices
- `food_security_nutrition_poverty_poverty_rate_get` - Get poverty rates

### 🔧 Utilities (2 tools)
- `encode_app_identifier_get` - Generate app identifier
- `util_version_get` - Get API version

### 🎯 Custom HDX Tools (3 tools)
- `hdx_server_info` - Get server information
- `hdx_get_dataset_info` - Get detailed dataset info
- `hdx_search_locations` - Search for locations



**⚠️ Critical**: Always use `metadata_data_availability_get` first to check data coverage - it varies significantly by country and administrative level.

### Caveats

The HDX API offers a very rich source of Humanitarian data, but it is complex. The coverage of data by regions differs per country, as showing in the table [here](https://data.humdata.org/hapi). The server prompt instructs calling LLMs to check data coverage, but it is worth noting that in this release aggregate queries such as 'What's the population of country X' or 'How many conflict events were there last year in country Y' will be challenging for countries which **only** have data at a granular level (eg Afghanistan conflict events). The LLM would have to sum this data, which of course may be error prone. To resolve this in future work, either the API can provide aggregate values or data needs to be extracted and processed.

## Quick Start

Get up and running in 2 minutes:

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone <repository-url>
cd hdx-mcp
uv sync --all-extras --dev

# 3. Configure your HDX API key
cp env.example .env
nano .env  # Edit HDX_API_KEY and HDX_APP_EMAIL

# 4. Run the server
uv run hdx-mcp-server
```

That's it! The server is now running and ready to serve HDX data via MCP.

## Installation

### Prerequisites

- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) package manager
- HDX API key (obtain from [HDX](https://data.humdata.org/))

### Setup Instructions

[UV](https://docs.astral.sh/uv/) is a fast Python package manager that automatically handles virtual environments and dependency management. No need to manually create or activate virtual environments - `uv` does this automatically!

1. **Install UV (if not already installed):**
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd hdx-mcp2
   ```

3. **Install dependencies:**
   ```bash
   # Install all dependencies including development tools
   uv sync --all-extras

   # Or install only production dependencies
   uv sync
   ```

4. **Configure your environment:**
   ```bash
   # Copy environment template
   cp env.example .env

   # Edit .env with your HDX API key and settings
   nano .env
   ```

   **Important Environment Variables:**
   - `HDX_API_KEY` - Your HDX API key (required)
   - `HDX_RATE_LIMIT_REQUESTS` - Max requests per period (default: 10)
   - `HDX_RATE_LIMIT_PERIOD` - Rate limit period in seconds (default: 60.0)
   - `HDX_TIMEOUT` - Request timeout in seconds (default: 30.0)

## Usage

### Running the Server

#### Option 1: Using UV (Development)

```bash
# Stdio transport (default) - for local MCP clients
uv run hdx-mcp-server

# HTTP transport - for remote access
uv run hdx-mcp-server --transport http

# With verbose logging
uv run hdx-mcp-server --verbose

# HTTP with custom configuration
uv run hdx-mcp-server --transport http --host 0.0.0.0 --port 9000 --verbose
```

#### Option 2: Using Docker (Recommended for Claude Desktop)

```bash
# Build the Docker image
docker build -t hdx-mcp-server .

# Run with stdio transport (for MCP clients)
docker run --rm -i --env-file .env hdx-mcp-server

# Run with HTTP transport
docker run --rm -p 8000:8000 --env-file .env hdx-mcp-server --transport http --host 0.0.0.0

# Using docker-compose (includes proper volume mounts)
docker-compose up
```

### Command Line Options

```
usage: uv run hdx-mcp-server [-h] [--transport {stdio,http}] [--host HOST] [--port PORT] [--verbose]

HDX MCP Server - Humanitarian Data Exchange API Server

options:
  -h, --help            show this help message and exit
  --transport {stdio,http}
                        Transport method to use (default: stdio)
  --host HOST           Host to bind HTTP server to (default: localhost)
  --port PORT           Port to bind HTTP server to (default: 8000)
  --verbose, -v         Enable verbose logging

Examples:
  uv run hdx-mcp-server                         # Run with stdio transport
  uv run hdx-mcp-server --transport http        # Run with HTTP transport
  uv run hdx-mcp-server --transport http --port 9000  # HTTP on custom port
```

## Using with Claude Desktop

To use this HDX MCP server with Claude Desktop, you need to configure it in Claude's MCP settings.

### Setup Steps

1. **Complete the basic setup above** - ensure the server works with `uv run hdx-mcp-server`

2. **Get the absolute path to your project:**
   ```bash
   cd /path/to/your/hdx-mcp2
   pwd  # Copy this path
   ```

3. **Configure Claude Desktop:**

   Open Claude Desktop settings and add to your MCP servers configuration:

   **Option A: Using Docker (Recommended)**
   ```json
   {
     "hdx-humanitarian-data": {
       "command": "docker",
       "args": ["run", "--rm", "-i", "--env-file", "/absolute/path/to/your/hdx-mcp2/.env", "hdx-mcp-server"]
     }
   }
   ```

   **Option B: Using UV**
   ```json
   {
     "hdx-humanitarian-data": {
       "command": "uv",
       "args": ["run", "hdx-mcp-server"],
       "cwd": "/absolute/path/to/your/hdx-mcp2"
     }
   }
   ```

   **Replace `/absolute/path/to/your/hdx-mcp2` with the actual path from step 2.**

4. **Ensure your `.env` file is configured** with your HDX API key:
   ```bash
   HDX_API_KEY=your_hdx_api_key_here
   HDX_BASE_URL=https://hapi.humdata.org
   ```

5. **Restart Claude Desktop** to load the new MCP server

### Verification

Once configured, you should see the HDX server appear in Claude's MCP servers list. You can test it by asking Claude to:

- "List available HDX tools"
- "Get information about Afghanistan using HDX data"
- "Search for refugee data in Syria"

### Troubleshooting

If Claude Desktop can't connect to the server:

1. **Check the path** - ensure the `cwd` path is correct and absolute
2. **Verify uv is available** - make sure `uv` is installed and in your PATH
3. **Test standalone** - verify `uv run hdx-mcp-server` works from the project directory
4. **Check logs** - Claude Desktop logs may show connection errors
5. **Verify environment** - ensure your `.env` file is in the project root with valid HDX API key

### Alternative: HTTP Transport

If stdio transport doesn't work, you can also run the server in HTTP mode and configure Claude to connect via HTTP:

1. **Start the server in HTTP mode:**
   ```bash
   uv run hdx-mcp-server --transport http --host 127.0.0.1 --port 9001
   ```

2. **Configure Claude Desktop for HTTP:**
   ```json
   {
     "hdx-humanitarian-data": {
       "url": "http://127.0.0.1:9001/mcp"
     }
   }
   ```

## Available Tools

The server provides **30 tools** automatically generated from the HDX HAPI OpenAPI specification, plus **3 custom tools** for enhanced functionality. All tools support pagination using `limit` and `offset` parameters.

### 🔍 Metadata & Discovery Tools

- **`metadata_dataset_get`** - Get information about data sources and datasets in HDX HAPI
- **`metadata_resource_get`** - Get information about data resource details and sources
- **`metadata_location_get`** - Get the list of locations (countries) included in HDX HAPI
- **`metadata_admin1_get`** - Get first-level subnational administrative divisions (states/provinces)
- **`metadata_admin2_get`** - Get second-level subnational administrative divisions (districts/counties)
- **`metadata_data_availability_get`** - **CRITICAL**: Get data availability for different geographic admin levels
- **`metadata_currency_get`** - Get information about currency classifications used in data
- **`metadata_org_get`** - Get the list of organizations represented in HDX HAPI data
- **`metadata_org_type_get`** - Get information about organization type classifications
- **`metadata_sector_get`** - Get humanitarian response sector classifications
- **`metadata_wfp_commodity_get`** - Get the list of WFP (World Food Programme) commodities
- **`metadata_wfp_market_get`** - Get the list of WFP market locations

### 🚨 Affected People & Humanitarian Needs

- **`affected_people_refugees_get`** - Get UNHCR refugee and persons of concern data
- **`affected_people_humanitarian_needs_get`** - Get humanitarian needs assessments and people in need data
- **`affected_people_idps_get`** - Get internally displaced persons (IDPs) data
- **`affected_people_returnees_get`** - Get data about returned displaced persons

### 🌍 Geography & Population

- **`geography_infrastructure_baseline_population_get`** - Get baseline population data by geographic area

### 🌦️ Climate & Environment

- **`climate_rainfall_get`** - Get rainfall measurement data by location and time period

### 🤝 Coordination & Context

- **`coordination_context_operational_presence_get`** - Get organizations present and their humanitarian sectors
- **`coordination_context_funding_get`** - Get humanitarian funding data and financial flows
- **`coordination_context_conflict_events_get`** - Get conflict event data and security incidents
- **`coordination_context_national_risk_get`** - Get national-level risk assessment data

### 🍽️ Food Security, Nutrition & Poverty

- **`food_security_nutrition_poverty_food_security_get`** - Get food security classification and analysis data
- **`food_security_nutrition_poverty_food_prices_get`** - Get food commodity prices from market monitoring
- **`food_security_nutrition_poverty_poverty_rate_get`** - Get poverty rate statistics and economic indicators

### 🔧 Utility Tools

- **`encode_app_identifier_get`** - Generate app identifier by encoding application name and email
- **`util_version_get`** - Display the API and SQL Alchemy versions

### 🎯 Custom HDX Tools

#### `hdx_server_info`
Get information about the HDX MCP server instance.

**Returns:**
```json
{
  "server_name": "HDX MCP Server",
  "version": "1.0.0",
  "base_url": "https://hapi.humdata.org/api/v2",
  "total_endpoints": 25,
  "available_tools": 28,
  "description": "MCP server for Humanitarian Data Exchange API"
}
```

#### `hdx_get_dataset_info`
Get detailed information about a specific HDX dataset.

**Parameters:**
- `dataset_hdx_id` (string): The HDX dataset identifier

**Example:**
```json
{
  "dataset_hdx_id": "dataset-123",
  "status": "success",
  "dataset": {
    "dataset_hdx_title": "Afghanistan - Baseline Population",
    "hdx_provider_name": "OCHA",
    "...": "..."
  }
}
```

#### `hdx_search_locations`
Search for locations (countries) in the HDX system.

**Parameters:**
- `name_pattern` (optional string): Pattern to match location names
- `has_hrp` (optional boolean): Filter for locations with Humanitarian Response Plans

**Example:**
```json
{
  "status": "success",
  "locations": [
    {
      "code": "AFG",
      "name": "Afghanistan",
      "has_hrp": true
    }
  ],
  "count": 1,
  "filters_applied": {
    "name_pattern": "Afghanistan",
    "has_hrp": true
  }
}
```

## Key Features & Data Coverage Notes

### 🎯 Data Coverage Verification
**CRITICAL**: Always use `metadata_data_availability_get` before querying specific data. Data coverage varies significantly by country and administrative level. Not all countries have data at all levels (country/state/district).

### 🔄 Universal Pagination
All tools support pagination with `limit` (default: 10, max: 100) and `offset` parameters for handling large datasets efficiently.

### 🏷️ Tool Categories and Tags

Tools are automatically categorized with relevant tags:

- **🔍 Metadata & Discovery**: `metadata`, `reference`, `discovery`
- **🚨 Affected People & Humanitarian**: `affected-people`, `humanitarian`, `displacement`
- **🌍 Geography & Population**: `geography`, `infrastructure`, `population`, `demographics`
- **🌦️ Climate & Environment**: `climate`, `environmental`, `weather`
- **🤝 Coordination & Context**: `coordination`, `humanitarian`, `context`, `security`
- **🍽️ Food Security & Poverty**: `food-security`, `nutrition`, `poverty`, `economics`
- **🔧 Utility & System**: `utility`, `system`, `admin`
- **🎯 Custom HDX**: `hdx-custom`, `enhanced`

All tools also include global tags: `hdx`, `humanitarian`, `data`

## Configuration

### Environment Variables

The server is configured via environment variables. Copy `env.example` to `.env` and customize:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HDX_API_KEY` | **Yes** | - | Your HDX API key |
| `HDX_BASE_URL` | No | `https://hapi.humdata.org/api/v2` | HDX API base URL |
| `HDX_OPENAPI_URL` | No | `https://hapi.humdata.org/openapi.json` | OpenAPI spec URL |
| `HDX_TIMEOUT` | No | `30.0` | HTTP request timeout (seconds) |
| `HDX_APP_NAME` | No | `hdx-mcp-server` | Application name for HDX |
| `HDX_APP_EMAIL` | No | `assistant@example.com` | Contact email for user of HDX API |
| `MCP_HOST` | No | `localhost` | Host for HTTP transport |
| `MCP_PORT` | No | `8000` | Port for HTTP transport |

### Complete Configuration Example

See `env.example` for a complete configuration template with detailed comments:

```bash
# View the configuration template
cat env.example

# Copy and edit for your environment
cp env.example .env
nano .env
```

### Excluded Endpoints

The server automatically excludes the following endpoints:
- `/api/v2/encode_app_identifier` - Internal utility for generating app identifiers

## Adding Custom Tools

To add your own tools alongside the auto-generated ones, modify the `_register_custom_tools` method in `hdx_mcp_server.py`:

```python
def _register_custom_tools(self):
    """Register custom tools alongside the OpenAPI-derived ones."""

    @self.mcp.tool("my_custom_tool")
    async def my_custom_tool(param1: str, param2: int = 10) -> Dict[str, Any]:
        """
        Description of my custom tool.

        Args:
            param1: Description of parameter 1
            param2: Description of parameter 2 with default value

        Returns:
            Dictionary containing the results
        """
        # Your custom tool implementation
        return {"result": "success", "data": param1}
```

## Development

### Development Setup with UV

```bash
# Install all dependencies including development tools
uv sync --all-extras --dev

# Install production dependencies only
uv sync

# Install pre-commit hooks (recommended)
uv run pre-commit install
```

### Development Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/security/      # Security tests

# Code quality checks
uv run black src/ tests/           # Format code
uv run isort src/ tests/           # Sort imports
uv run flake8 src/ tests/          # Lint code
uv run mypy src/                   # Type checking
uv run bandit -r src/              # Security scanning

# Run all quality checks
uv run pre-commit run --all-files

# Clean cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
```

### Project Structure

```
hdx-mcp-server/
├── src/hdx_mcp_server/     # Main source code
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # CLI entry point
│   └── server.py           # Main server implementation
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── security/          # Security tests
│   └── conftest.py        # Shared test fixtures
├── .github/workflows/     # GitHub Actions CI/CD
└── pyproject.toml         # Project configuration
```

### Testing

#### Running Tests

```bash
# All tests
uv run pytest

# Specific test categories
uv run pytest tests/unit/ -v              # Unit tests only
uv run pytest tests/integration/ -v       # Integration tests only
uv run pytest tests/security/ -v          # Security tests only

# With coverage reporting
uv run pytest --cov=src --cov-report=html
```

#### Test Categories

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test interactions with external APIs
- **Security Tests** (`tests/security/`): Test security features and protections

### Test Coverage

The test suite includes:
- **Unit Tests**: Server initialization, configuration, authentication
- **Integration Tests**: Real API interaction (when API key available)
- **Security Tests**: API key protection, input validation, error handling
- **Edge Case Tests**: Malformed specs, network errors, timeouts

### Manual Testing

Test the server manually with curl (HTTP transport):
```bash
# Start server
uv run hdx-mcp-server --transport http

# Test server info tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "hdx_server_info", "arguments": {}}}'
```

## Security Considerations

This server follows MCP security best practices:

### Authentication & Authorization
- ✅ API keys stored in environment variables, never hardcoded
- ✅ API keys not logged or exposed in error messages
- ✅ Proper HTTP client configuration with timeouts
- ✅ Base64 encoding for app identifiers as required by HDX

### Input Validation
- ✅ FastMCP handles input schema validation automatically
- ✅ Custom tools include proper type hints and validation
- ✅ Error handling prevents information leakage

### Network Security
- ✅ HTTPS-only communication with HDX API
- ✅ Configurable timeouts to prevent hanging connections
- ✅ Proper error handling for network failures

### Data Handling
- ✅ No persistent data storage
- ✅ Proper cleanup of HTTP connections
- ✅ Graceful shutdown handling

## Troubleshooting

### Common Issues

1. **"Required environment variable HDX_API_KEY is not set"**
   - Ensure you have copied `.env.example` to `.env`
   - Verify your HDX API key is correctly set in `.env`

2. **"Failed to load OpenAPI specification"**
   - Check your internet connection
   - Verify HDX API is accessible: `curl https://hapi.humdata.org/openapi.json`

3. **HTTP transport not accessible.**
   - Check if the port is already in use
   - Verify firewall settings if accessing remotely
   - Use `--host 0.0.0.0` for external access

4. **Authentication errors**
   - Verify your HDX API key is valid
   - Check if your account has necessary permissions

### Logging

Enable verbose logging for debugging:
```bash
uv run hdx-mcp-server --verbose
```

This will show detailed information about:
- Server initialization
- OpenAPI spec loading
- Tool registration
- HTTP requests and responses
- Error details

## Contributing

### Development Setup

1. **Install dependencies:**
   ```bash
   uv sync --all-extras    # Install all dependencies including dev tools
   uv run pre-commit install     # Install pre-commit hooks
   ```

2. **Development workflow:**
   ```bash
   uv run black src/ tests/      # Format code
   uv run flake8 src/ tests/     # Lint code
   uv run pytest                 # Run tests
   uv run pre-commit run --all-files  # Run all checks
   ```

### Code Quality & CI/CD

This project includes comprehensive quality controls:

#### Code Quality Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting with security and complexity extensions
- **mypy**: Type checking
- **bandit**: Security vulnerability scanning
- **pytest**: Testing with coverage reporting

#### GitHub Actions
- **CI Pipeline**: Tests on Python 3.8-3.12
- **Code Quality**: Automated formatting, linting, and type checking
- **Security Scanning**: Vulnerability detection and security tests
- **Integration Tests**: Full API integration testing

#### Pre-commit Hooks
Automatically run quality checks before each commit:
```bash
uv run pre-commit install    # One-time setup
git commit                   # Hooks run automatically
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

### Adding New Endpoints

New HDX API endpoints are automatically included when the OpenAPI specification is updated. No code changes are required.

### Adding Custom Tools

1. Add your tool function in the `_register_custom_tools` method
2. Include proper type hints and documentation
3. Add corresponding tests in `test_hdx_mcp_server.py`
4. Update this README with documentation for your tool

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Resources

- [HDX (Humanitarian Data Exchange)](https://data.humdata.org/)
- [HDX HAPI Documentation](https://hdx-hapi.readthedocs.io/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)

## Support

For issues related to:
- **This MCP server**: Open an issue in this repository
- **HDX API**: Consult [HDX HAPI documentation](https://hdx-hapi.readthedocs.io/)
- **MCP protocol**: See [MCP specification](https://modelcontextprotocol.io/)
- **FastMCP library**: Check [FastMCP documentation](https://gofastmcp.com/)

---

**Note**: This server requires a valid HDX API key. Please ensure you comply with HDX's terms of service and rate limiting guidelines when using this server.
