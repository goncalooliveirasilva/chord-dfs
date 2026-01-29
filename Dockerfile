FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ src/
COPY main.py .

# Create storage directory
RUN mkdir -p /app/storage

# Set storage path for container
ENV CHORD_STORAGE_PATH=/app/storage

# Expose port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "python", "main.py"]
