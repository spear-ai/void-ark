FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

# System dependencies for ctypes-loaded shared libraries
RUN apt-get update && apt-get install -y \
    libc6 \
    libstdc++6 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv 
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency metadata first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

CMD ["uv", "run", "python", "main.py"]
