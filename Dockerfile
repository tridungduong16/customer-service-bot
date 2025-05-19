# Use the base image with uv and Python 3.13
FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Set working directory
WORKDIR /app

# Install system packages + Node.js + npm + npx
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg gcc g++ python3-dev git \
      libfreetype6-dev libpng-dev \
 && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

# Check Node.js and npm versions (optional debug step)
RUN node -v && npm -v && npx --version

# Copy configuration and source code
COPY pyproject.toml uv.lock .env ./
COPY . .

# Create logs directory
RUN mkdir -p logs && chmod 777 logs

# Expose port
EXPOSE 8080

# Set PYTHONPATH
ENV PYTHONPATH=.

# Default command
CMD ["uv", "run", "python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
