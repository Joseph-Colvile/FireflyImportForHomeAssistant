ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    linux-headers \
    jq

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies in a venv to avoid PEP 668 restrictions
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --no-cache-dir -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# Copy application files
COPY app.py .
COPY templates templates/
COPY static static/
COPY run.sh /run.sh

RUN chmod a+x /run.sh

# Home Assistant add-ons run as root by default to access /data/options.json

# Expose port
EXPOSE 8099

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8099/health')"

# Run application
CMD ["/run.sh"]
