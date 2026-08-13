# Financial OS API — multi-stage container build
# The same image is used for both the API (public ingress) and the worker (private).
# The entrypoint is overridden in Cloud Run service configuration to separate concerns.
#
# Security: no long-lived service account keys are baked into the image.
# Runtime identity is provided by Cloud Run's Workload Identity (CICD-01).

# ── Stage 1: dependency installation ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy dependency manifests first to leverage Docker layer cache.
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install the package and its runtime dependencies into a complete virtual
# environment so console entry points (uvicorn and alembic) reach the runtime.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade "pip>=26.1.2,<27" && \
    /opt/venv/bin/pip install --no-cache-dir .

# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Financial OS API"
LABEL org.opencontainers.image.description="Private receipt capture service — Wave 1"

# Non-root user for security (principle of least privilege).
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy the complete environment, including console entry points.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Copy application entry point and migration assets.
COPY contracts/ /app/contracts/
ENV FINANCIAL_OS_CONTRACTS_DIR=/app/contracts
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY apps/api/main.py /app/main.py

# Cloud Run delivers the PORT environment variable.
ENV PORT=8080

# Run as non-root.
USER appuser

# Health check — used by Cloud Run readiness probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health/live')"

EXPOSE ${PORT}

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info"]
