# Firefly III CSV Importer (Home Assistant Add-on)

A Home Assistant add-on that provides a web UI to upload CSV files and import transactions into Firefly III via its API.

## Features

- Upload CSV files and map columns
- Supports withdrawal, deposit, and transfer types
- Creates missing accounts automatically
- Shows detailed import results, errors, and summaries
- Works with Home Assistant Ingress

## Configuration

Set these options in the add-on configuration:

- `firefly_url`: Base URL of Firefly III (e.g. `http://homeassistant.local:8080`)
- `firefly_token`: Personal Access Token from Firefly III
- `csv_max_size_mb`: Maximum CSV file size (default 10)
- `default_currency`: Default currency code (default USD)

## Usage

1. Open the add-on UI (Ingress).
2. Upload a CSV file.
3. Select the CSV format and map the columns.
4. Start the import and review the summary.

## Security Notes

- The token is never logged.
- CSV uploads are size-limited and type-checked.
- Inputs are validated before import.

## Development

Local run (outside Home Assistant):

```bash
export FIREFLY_URL=http://localhost:8080
export FIREFLY_TOKEN=your-token
python app.py
```

Then open `http://localhost:8099`.
