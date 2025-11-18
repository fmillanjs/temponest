# Stage 1: Builder - Install dependencies
# NOTE: Using Debian (slim) instead of Alpine because:
# - onnxruntime (required by chromadb) doesn't provide musllinux wheels
# - Building from source is too slow and unreliable
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to a virtual environment
COPY services/agents/requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    PIP_DEFAULT_TIMEOUT=300 pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies including Node.js for Claude Code
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code@latest \
    && npm cache clean --force

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (preserve directory structure)
COPY services/agents/app/ /app/app/

# Copy shared modules
COPY shared/ /app/shared/

# Create output directory
RUN mkdir -p /output

# Add shared modules to PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Create entrypoint script for Claude Code authentication
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Setup Claude Code authentication if tokens are provided\n\
if [ -n "$CLAUDE_CODE_ACCESS_TOKEN" ] && [ -n "$CLAUDE_CODE_REFRESH_TOKEN" ]; then\n\
    echo "Setting up Claude Code authentication..."\n\
    mkdir -p ~/.claude\n\
    \n\
    # Create .credentials.json with proper OAuth structure\n\
    cat > ~/.claude/.credentials.json <<EOF\n\
{\n\
  "claudeAiOauth": {\n\
    "accessToken": "$CLAUDE_CODE_ACCESS_TOKEN",\n\
    "refreshToken": "$CLAUDE_CODE_REFRESH_TOKEN",\n\
    "expiresAt": ${CLAUDE_CODE_EXPIRES_AT:-9999999999999},\n\
    "scopes": ["user:inference","user:profile","user:sessions:claude_code"],\n\
    "subscriptionType": "${CLAUDE_CODE_SUBSCRIPTION_TYPE:-max}",\n\
    "rateLimitTier": "${CLAUDE_CODE_RATE_LIMIT_TIER:-default_claude_max_20x}"\n\
  }\n\
}\n\
EOF\n\
    echo "Claude Code configured successfully"\n\
elif [ -n "$CLAUDE_CODE_TOKEN" ]; then\n\
    echo "WARNING: CLAUDE_CODE_TOKEN is deprecated. Please use CLAUDE_CODE_ACCESS_TOKEN and CLAUDE_CODE_REFRESH_TOKEN instead."\n\
fi\n\
\n\
# Start the application\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 9000\n\
' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
