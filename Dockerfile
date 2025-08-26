# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app


# Install system dependencies
#RUN apt-get update && apt-get install -y \
#    curl \
#    git \
#    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY env.example ./
COPY requirements.txt ./
COPY LICENSE ./
COPY README.md ./

# Create .env file with placeholder (will be overridden by volume mount)
RUN cp env.example .env

# Install dependencies using uv
RUN uv sync --no-dev

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ ! -f .env ]; then\n\
    echo "Warning: .env file not found, using env.example as template"\n\
    cp env.example .env\n\
fi\n\
\n\
exec uv run python -m hdx_mcp_server "$@"' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Expose stdio for MCP
ENTRYPOINT ["/app/entrypoint.sh"]

# Default to stdio transport
CMD []
