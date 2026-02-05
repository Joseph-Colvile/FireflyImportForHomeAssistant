#!/usr/bin/with-contenv bashio
# Firefly III CSV Importer - Home Assistant Add-on Entry Point

set -e

# Log addon startup
bashio::log.info "Starting Firefly III CSV Importer"

# Get configuration from Home Assistant
if bashio::config.exists 'firefly_base_url'; then
    FIREFLY_BASE_URL=$(bashio::config 'firefly_base_url')
    export FIREFLY_BASE_URL
    bashio::log.info "Firefly III URL: $FIREFLY_BASE_URL"
else
    bashio::log.warning "Firefly III URL not configured"
fi

if bashio::config.exists 'firefly_token'; then
    FIREFLY_TOKEN=$(bashio::config 'firefly_token')
    export FIREFLY_TOKEN
    bashio::log.info "Firefly III token configured"
else
    bashio::log.warning "Firefly III token not configured"
fi

# Get log level
if bashio::config.exists 'log_level'; then
    LOG_LEVEL=$(bashio::config 'log_level')
    export LOG_LEVEL
else
    export LOG_LEVEL="info"
fi

bashio::log.info "Log level: $LOG_LEVEL"

# Create temp directory for uploads
mkdir -p /tmp/firefly_uploads
chmod 777 /tmp/firefly_uploads

# Start the application
bashio::log.info "Starting Flask application on port 8099"
exec python /app/app/main.py
