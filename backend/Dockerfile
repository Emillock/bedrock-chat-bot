FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/python \
    UV_PYTHON_PREFERENCE=only-managed

# Install build dependencies and clean up in the same layer
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y clang git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only backend code
COPY backend/ .

# <<< ADD THE PYTHONPATH HERE so /app/src is on sys.path and `import utils` works
# point PYTHONPATH to the folder that contains utils.py
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Install Python dependencies
RUN uv sync --no-dev

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose 8000 port
EXPOSE 8000

# Recommended: use python -m uvicorn to avoid PATH/script issues. Remove --reload in prod.
CMD ["uv", "run", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]