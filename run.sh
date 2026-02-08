#!/usr/bin/env bash
set -e

# Home Assistant Firefly III CSV Importer Add-on
# This script initializes and runs the Flask application

# Set up logging
exec 1> >(logger -s -t firefly-csv-importer)
exec 2>&1

echo "Starting Firefly III CSV Importer..."

# Get configuration from Home Assistant config.yaml
CONFIG_PATH=/data/options.json

if [ ! -f "$CONFIG_PATH" ]; then
    echo "ERROR: Configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Export environment variables from config
export FIREFLY_URL=$(jq -r '.firefly_url // ""' $CONFIG_PATH)
export FIREFLY_TOKEN=$(jq -r '.firefly_token // ""' $CONFIG_PATH)
export CSV_MAX_SIZE_MB=$(jq -r '.csv_max_size_mb // 10' $CONFIG_PATH)
export DEFAULT_CURRENCY=$(jq -r '.default_currency // "USD"' $CONFIG_PATH)
export FLASK_ENV=production

# Validate required configuration
if [ -z "$FIREFLY_URL" ] || [ "$FIREFLY_URL" == "null" ]; then
    echo "ERROR: FIREFLY_URL not configured"
    exit 1
fi

if [ -z "$FIREFLY_TOKEN" ] || [ "$FIREFLY_TOKEN" == "null" ]; then
    echo "ERROR: FIREFLY_TOKEN not configured"
    exit 1
fi

echo "Configuration loaded successfully"
echo "Firefly III URL: $FIREFLY_URL"
echo "CSV Max Size: ${CSV_MAX_SIZE_MB}MB"
echo "Default Currency: $DEFAULT_CURRENCY"

# Run the Flask application
cd /app
python -u app.py

echo "Firefly III CSV Importer stopped"
