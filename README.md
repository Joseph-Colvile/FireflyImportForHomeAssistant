# Firefly III CSV Importer

A Home Assistant add-on that provides a simple web UI for importing transactions from CSV files into Firefly III.

## Features

✨ **Easy to Use**
- Simple web interface accessible through Home Assistant
- Support for multiple CSV formats (Bank, PocketSmith, Generic)
- Real-time validation and error reporting

🔐 **Secure**
- Personal Access Token authentication with Firefly III
- No token storage in logs
- Validated input sanitization

📊 **Flexible**
- Automatic account creation if not exists
- Support for transaction categories, tags, and notes
- Deduplication via external_id
- Transaction type support: withdrawal, deposit, transfer

📈 **Comprehensive**
- Detailed import results and error reporting
- Preview before import
- Session management for tracking imports

## Installation

### Option 1: Manual Installation

1. **Copy the add-on folder:**
   ```bash
   cd ~/.homeassistant/addons/
   git clone https://github.com/yourusername/firefly-csv-importer
   ```

2. **Restart Home Assistant supervisor:**
   - Settings → System → Supervisor → Click the refresh icon

3. **Install the add-on:**
   - Go to Settings → Add-ons → Click "Create addon folder" (if needed)
   - Refresh the page
   - Look for "Firefly III CSV Importer" in the add-on store
   - Click "Install"

### Option 2: Via Add-on Store (if published)

1. Settings → Add-ons & Integrations
2. Search for "Firefly III CSV Importer"
3. Click Install

## Configuration

### Initial Setup

1. **Open the add-on:**
   - Settings → Add-ons → Firefly III CSV Importer
   - Click "Open Web UI"

2. **Configure Firefly III:**
   - Enter your Firefly III base URL (e.g., `http://homeassistant.local:8080`)
   - Enter your Personal Access Token
   - Click "Save Configuration"

3. **The add-on will test the connection and confirm success**

### Getting Your Personal Access Token

1. Open Firefly III
2. Go to Settings → Profile
3. Scroll to "Personal Access Tokens"
4. Click "Create New Token"
5. Enter a name (e.g., "CSV Importer")
6. Copy the token and save it in the add-on configuration

## Usage

### Step 1: Prepare Your CSV File

Choose your CSV format:

#### Generic Format (Recommended)
```csv
date,amount,description,source_account,destination_account,type,category,tags,notes,external_id
2024-01-15,-45.50,Grocery Store,Checking,Groceries,withdrawal,Groceries,food;weekly,Whole Foods,WF001
2024-01-16,3000.00,Salary,Salary,Checking,deposit,Salary,income,January salary,SAL001
```

**Required columns:** `date`, `amount`, `description`, `source_account`, `destination_account`
**Optional columns:** `type`, `category`, `tags`, `notes`, `external_id`

#### Bank Format
```csv
Date,Description,Amount,Balance,Category
2024-01-15,Grocery Store,-45.50,1954.50,Groceries
2024-01-16,Salary,3000.00,4954.50,Income
```

**Required columns:** `Date`, `Description`, `Amount`
**Optional columns:** `Balance`, `Category`, `Tags`

#### PocketSmith Format
```csv
Date,Payee,Category,Memo,Amount,Account
2024-01-15,Whole Foods,Groceries,Weekly shopping,-45.50,Checking
2024-01-16,Employer,Income,Monthly salary,3000.00,Checking
```

**Required columns:** `Date`, `Amount`
**Optional columns:** `Payee`, `Category`, `Memo`, `Account`

### Step 2: Upload and Validate

1. Click "Select CSV File" and choose your prepared CSV file
2. Select the appropriate CSV format
3. Click "Upload & Validate"
4. Review the validation results and preview

### Step 3: Import

1. If validation passes, click "Start Import"
2. Monitor the import progress
3. Review the results:
   - Transactions created
   - Accounts created
   - Rows skipped
   - Errors encountered

## Supported CSV Formats

### Date Formats
- `YYYY-MM-DD` (2024-01-15)
- `DD/MM/YYYY` (15/01/2024)
- `MM/DD/YYYY` (01/15/2024)
- `YYYY/MM/DD` (2024/01/15)
- `DD-MM-YYYY` (15-01-2024)
- `MM-DD-YYYY` (01-15-2024)

### Amount Formats
- Positive/negative numbers: `45.50`, `-45.50`
- With currency symbols: `$45.50`, `€45,50`
- With commas: `1,000.50`, `-1,000.50`

### Transaction Types
- `withdrawal` - Money out from source to destination
- `deposit` - Money in from source to destination
- `transfer` - Transfer between accounts

## Example CSV Files

The add-on includes example CSV files in the `examples/` directory:

- `sample_bank.csv` - Bank format example
- `sample_pocketsmith.csv` - PocketSmith format example
- `sample_generic.csv` - Generic format example

You can download these files and use them as templates for your own CSV files.

## API Documentation

The add-on exposes a RESTful API. See [API_EXAMPLES.md](API_EXAMPLES.md) for detailed documentation including:

- Configuration endpoints
- Upload and validation
- Import processing
- Session management
- Error handling
- Example API calls

## Troubleshooting

### "Connection failed" Error

**Issue:** Cannot connect to Firefly III
**Solutions:**
- Verify the base URL is correct (check spelling and port)
- Ensure Firefly III is running
- Check firewall rules
- Verify network connectivity from Home Assistant to Firefly III

### "Invalid token" Error

**Issue:** Personal Access Token is invalid or expired
**Solutions:**
- Generate a new Personal Access Token in Firefly III
- Copy the entire token (no extra spaces)
- Ensure the token has API access permissions

### "CSV validation failed" Errors

**Issue:** CSV file format issues
**Solutions:**
- Verify required columns are present
- Check date format matches one of the supported formats
- Ensure amounts are numeric (can include $ symbol)
- Verify file encoding is UTF-8
- Try another CSV format option

### "File too large" Error

**Issue:** CSV file exceeds 10MB limit
**Solutions:**
- Split the CSV file into smaller parts
- Remove unnecessary columns
- Filter to a smaller date range

### Accounts Not Created

**Issue:** Expected accounts were not created
**Solutions:**
- Verify account names in source and destination columns
- Ensure account type is appropriate (asset for bank accounts, expense for expenses)
- Check Firefly III permissions for your token

### Duplicate Transactions

**Issue:** Same transactions imported multiple times
**Solutions:**
- Use the `external_id` column for deduplication
- Ensure `external_id` is unique for each transaction
- Firefly III uses `external_id` to detect duplicates

## Features in Detail

### Column Mapping

The importer automatically maps columns based on the selected format:

- **Bank Format:** Maps bank export columns to standard transaction fields
- **PocketSmith Format:** Converts PocketSmith columns to Firefly III format
- **Generic Format:** Direct mapping with consistent column names

### Automatic Account Creation

If an account doesn't exist in Firefly III:
- Asset accounts are created for source accounts
- Expense accounts are created for destination accounts
- Accounts are created with the provided name and type

### Error Handling

The importer provides detailed error reporting:
- Row-by-row error messages
- Summary of skipped rows
- Firefly III API error details
- Validation errors before import

### Session Management

Each import session is tracked with:
- Session ID
- Import status
- Row count and preview
- Final results and statistics

## Development

### Project Structure

```
firefly-importer/
├── README.md
├── Dockerfile
├── config.yaml
├── run.sh
├── requirements.txt
├── app/
│   ├── main.py          # Flask application
│   ├── csv_parser.py    # CSV parsing and validation
│   ├── firefly_client.py # Firefly III API client
│   ├── templates/
│   │   └── index.html   # Web UI
│   └── static/
│       └── styles.css   # UI styles
├── examples/
│   ├── sample_bank.csv
│   ├── sample_pocketsmith.csv
│   └── sample_generic.csv
└── API_EXAMPLES.md      # API documentation
```

### Building Docker Image

```bash
docker build -t firefly-csv-importer .
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FIREFLY_BASE_URL=http://localhost:8080
export FIREFLY_TOKEN=your_token_here

# Run the application
python app/main.py
```

Access the UI at `http://localhost:8099`

### Adding New CSV Formats

1. Edit `app/csv_parser.py`
2. Add format to `FORMATS` dictionary
3. Define columns, required fields, and mapper
4. Update `index.html` with format option
5. Update documentation

## Configuration

Add-on configuration options:

- `firefly_base_url` - Base URL of Firefly III instance
- `firefly_token` - Personal Access Token
- `log_level` - Logging level (debug, info, warning, error)

## Logs

View add-on logs in Home Assistant:
- Settings → Add-ons → Firefly III CSV Importer → Logs

## Performance

- **Maximum file size:** 10MB
- **Recommended transaction count per import:** < 1000
- **Processing speed:** ~10-20 transactions per second (depends on API response time)

## Security Considerations

- Personal Access Token is never stored in logs
- CSV files are uploaded to temporary storage and deleted after processing
- All input is validated and sanitized
- API calls use Bearer token authentication
- Sensitive data is not exposed in error messages

## Support

For issues and feature requests:
- GitHub Issues: https://github.com/yourusername/firefly-csv-importer/issues
- Documentation: See [API_EXAMPLES.md](API_EXAMPLES.md)

## License

MIT License - See LICENSE file for details

## Credits

- [Firefly III](https://www.firefly-iii.org/) - Personal finance management
- [Home Assistant](https://www.home-assistant.io/) - Home automation platform
- Community contributors

## Changelog

### Version 1.0.0
- Initial release
- Support for Bank, PocketSmith, and Generic CSV formats
- Web UI with drag-and-drop upload
- Real-time validation and error reporting
- Automatic account creation
- Session management
- Comprehensive API documentation
- Example CSV files

---

**Happy importing! 🎉**
