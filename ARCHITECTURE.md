# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Home Assistant                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │     Firefly III CSV Importer Add-on                    │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │         Web Interface (Port 8099)                │  │  │
│  │  │  ┌─ Frontend (HTML/CSS/JS)                       │  │  │
│  │  │  │ ├─ Configuration Section                      │  │  │
│  │  │  │ ├─ Upload Section                             │  │  │
│  │  │  │ ├─ Preview & Validation                       │  │  │
│  │  │  │ ├─ Import Progress                            │  │  │
│  │  │  │ └─ Results Display                            │  │  │
│  │  │  └─ Backend (Flask)                              │  │  │
│  │  │     ├─ Config Routes (/api/config)               │  │  │
│  │  │     ├─ Upload Routes (/api/upload)               │  │  │
│  │  │     ├─ Import Routes (/api/import)               │  │  │
│  │  │     └─ Session Routes (/api/sessions)            │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                          │                               │  │
│  │  ┌────────────────────────┴────────────────────────┐   │  │
│  │  │      Core Business Logic                        │   │  │
│  │  │  ┌──────────────────────────────────────────┐  │   │  │
│  │  │  │  CSV Parser (csv_parser.py)              │  │   │  │
│  │  │  │  ├─ Multiple format support              │  │   │  │
│  │  │  │  ├─ Column mapping                       │  │   │  │
│  │  │  │  ├─ Data validation                      │  │   │  │
│  │  │  │  └─ Error reporting                      │  │   │  │
│  │  │  └──────────────────────────────────────────┘  │   │  │
│  │  │  ┌──────────────────────────────────────────┐  │   │  │
│  │  │  │  Firefly III Client (firefly_client.py) │  │   │  │
│  │  │  │  ├─ Connection management                │  │   │  │
│  │  │  │  ├─ Account operations                   │  │   │  │
│  │  │  │  ├─ Transaction operations               │  │   │  │
│  │  │  │  ├─ Error handling                       │  │   │  │
│  │  │  │  └─ Caching                              │  │   │  │
│  │  │  └──────────────────────────────────────────┘  │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │                          │                             │  │
│  │                          └─────────────────────────────  │  │
│  │                                                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
└──────────────────────────┼────────────────────────────────────┘
                           │
                           │ HTTP REST API
                           ▼
                  ┌─────────────────────┐
                  │   Firefly III       │
                  │                     │
                  │  ┌───────────────┐  │
                  │  │  Accounts API │  │
                  │  └───────────────┘  │
                  │  ┌───────────────┐  │
                  │  │ Transactions  │  │
                  │  │      API      │  │
                  │  └───────────────┘  │
                  │  ┌───────────────┐  │
                  │  │   Database    │  │
                  │  │  (PostgreSQL  │  │
                  │  │  or MySQL)    │  │
                  │  └───────────────┘  │
                  └─────────────────────┘
```

## Component Architecture

### 1. Frontend Layer (index.html)

**Responsibilities:**
- Display web user interface
- Handle user interactions
- Manage form validation on client side
- Display real-time feedback and results

**Key Sections:**
- Configuration Panel: Store Firefly III credentials
- Upload Section: CSV file selection and format choice
- Preview Section: Show parsed data and validation results
- Progress Section: Real-time import progress tracking
- Results Section: Final import statistics and error reporting

**Technologies:**
- Vanilla JavaScript (no external frameworks)
- Responsive HTML5
- CSS3 with flexbox/grid

### 2. Backend Layer (main.py)

**Framework:** Flask 2.3.3

**Responsibilities:**
- Handle HTTP requests/responses
- Validate file uploads
- Coordinate CSV parsing and API calls
- Manage import sessions
- Error handling and logging

**Key Routes:**
```
GET/POST /                    # Serve index.html
GET/POST /api/config          # Manage Firefly III config
POST     /api/upload          # Upload and validate CSV
POST     /api/import/<id>     # Start import process
GET      /api/sessions/<id>   # Get session status
```

**Session Management:**
- Store upload sessions in memory dictionary
- Each session has: rows, format, status, filepath, results
- Sessions include: created_at for cleanup

### 3. CSV Processing (csv_parser.py)

**Class:** CSVParser

**Format Support:**
- **Generic:** Standard 5-column format with optional fields
- **Bank:** Bank export with Date, Description, Amount
- **PocketSmith:** PocketSmith with Payee, Category, Memo

**Processing Pipeline:**
1. **Delimiter Detection:** Automatically detect CSV delimiter (comma, semicolon, tab, pipe)
2. **Column Mapping:** Map source columns to standard fields
3. **Parsing:** Read CSV into dictionaries
4. **Validation:** 
   - Check required fields present
   - Validate date formats
   - Validate amount formats
   - Report errors with row numbers
5. **Normalization:** Convert types (strings to floats, dates to standard format)

**Supported Date Formats:**
- YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD, DD-MM-YYYY, MM-DD-YYYY

**Supported Amount Formats:**
- Positive/negative: 45.50, -45.50
- With currency: $45.50, €45,50
- With thousands: 1,000.50, -1,000.50

### 4. Firefly III Integration (firefly_client.py)

**Class:** FireflyClient

**API Operations:**

#### Connection Management
- `test_connection()` - Verify API access
- Session management with retry logic
- Automatic Bearer token authentication

#### Account Operations
- `get_account(id)` - Retrieve account by ID
- `find_account_by_name(name, type)` - Search for account
- `create_account(name, type, currency)` - Create new account
- `get_or_create_account(name, type)` - Get or create with caching
- `list_accounts(type)` - List all accounts

#### Transaction Operations
- `create_transaction(data)` - Create transaction
- Multiple transaction types: withdrawal, deposit, transfer

#### Caching
- Account name lookup cache to reduce API calls
- Cache key format: "{name}_{type}"

#### Error Handling
- Parse Firefly III error responses
- Return meaningful error messages
- Log all errors for debugging

**Retry Strategy:**
- 3 total attempts
- Exponential backoff (0.5s initial delay)
- Retry on: 500, 502, 504 errors

### 5. Data Flow

#### Upload Flow
```
1. User selects CSV file
   ↓
2. /api/upload receives multipart/form-data
   ↓
3. File saved to /tmp with secure filename
   ↓
4. CSVParser.parse() reads and maps columns
   ↓
5. CSVParser.validate_rows() checks data
   ↓
6. Session created with parsed data
   ↓
7. Response with preview and validation results
```

#### Import Flow
```
1. User clicks "Start Import"
   ↓
2. /api/import/<session_id> called
   ↓
3. For each row in session:
   ├─ Get or create source account
   ├─ Get or create destination account
   ├─ Normalize transaction data
   ├─ Call Firefly III API
   ├─ Track success/error
   └─ Continue on error (don't abort)
   ↓
4. Return results with:
   ├─ accounts_created count
   ├─ transactions_created count
   ├─ rows_skipped count
   ├─ errors array with details
   └─ accounts array
   ↓
5. Cleanup: Delete temporary CSV file
```

## Security Architecture

### Input Validation
- File type validation (only .csv)
- File size limit (10MB)
- Delimiter auto-detection (safe parsing)
- Data type validation (dates, amounts)

### Token Security
- Personal Access Token never logged
- Token stored as environment variable only
- Not included in error messages or responses
- Not displayed in UI after configuration

### Data Handling
- Temporary files in /tmp
- Files deleted after import
- No persistent storage of CSV data
- Sanitized input in all API responses

### API Security
- Bearer token authentication for Firefly III
- HTTPS recommended (when deployed)
- CORS handling for Ingress integration
- No credential exposure in logs

## Configuration Schema

```yaml
config.yaml:
  firefly_base_url: string (URL)
  firefly_token: password (hidden)
  log_level: select (debug|info|warning|error)

addon.json:
  options: schema definitions
  schema: type definitions
  healthcheck: container health monitoring
  ingress: UI integration setup
```

## Deployment Architecture

### Home Assistant Add-on
- Docker container with Python 3.9-slim base image
- Non-root user (appuser) for security
- Health check every 30 seconds
- Automatic restart on failure
- Ingress integration for UI access

### Environment Variables
```
FIREFLY_BASE_URL   # Firefly III URL
FIREFLY_TOKEN      # API token
PORT                # Server port (default 8099)
LOG_LEVEL          # Logging verbosity
PYTHONUNBUFFERED   # Unbuffered Python output
```

### Port Mapping
- Internal: 8099 (Flask app)
- External: 8099 (Home Assistant ingress)
- Health check on /

### Volume Mounting
- /tmp/firefly_uploads - Temporary file storage

## Error Handling Strategy

### CSV Validation Errors
- Report specific row numbers
- List all errors found (up to 10)
- Allow partial recovery

### API Errors
- Parse Firefly III error responses
- Return meaningful messages
- Log for debugging
- Continue on error (don't abort entire import)

### Network Errors
- Retry with exponential backoff
- Timeout after 3 attempts
- Report connection errors to UI

### System Errors
- Log full error details
- Return sanitized error message to user
- 500 error on unexpected failures

## Performance Considerations

### Optimization
- Account lookup caching (reduce API calls)
- Batch file processing
- Streaming CSV parsing
- Session-based state management

### Limitations
- Max file size: 10MB
- Recommended max transactions per import: 1000
- API rate limiting: depends on Firefly III configuration
- Processing speed: 10-20 tx/second (API dependent)

### Scalability
- Can handle multiple concurrent upload sessions
- Memory-based session storage (no persistence)
- Can be deployed with load balancer
- Stateless design allows horizontal scaling

## Testing Strategy

### Unit Tests (Recommended)
- CSV parsing with various formats
- Data validation rules
- API client methods
- Error handling

### Integration Tests
- Full upload workflow
- Import with real Firefly III
- Error scenarios
- Session management

### Manual Testing
- Multiple CSV formats
- Edge cases (empty files, missing columns)
- Network failures
- Large file uploads

## Future Enhancements

### Possible Improvements
- Database persistence for sessions
- Scheduled imports
- Template management
- Advanced column mapping UI
- Batch duplicate detection
- Transaction editing before import
- API rate limiting configuration
- Export functionality

### Architecture Support
- Currently modular (api.py reserved)
- Easy to add new CSV formats
- Plugin architecture for formatters
- Extensible error handling
