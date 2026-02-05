# Firefly III CSV Importer API Documentation

## Overview
The Firefly III CSV Importer provides a RESTful API for uploading, validating, and importing transactions into Firefly III.

## Base URL
```
http://localhost:8099/api
```

## Endpoints

### 1. Configuration

#### Get Configuration Status
```
GET /api/config
```

**Response:**
```json
{
  "firefly_url": "http://homeassistant.local:8080",
  "token_configured": true,
  "csv_formats": ["bank", "pocketsmith", "generic"]
}
```

#### Set Configuration
```
POST /api/config
Content-Type: application/json
```

**Request Body:**
```json
{
  "firefly_url": "http://homeassistant.local:8080",
  "firefly_token": "your-personal-access-token"
}
```

**Success Response (200):**
```json
{
  "message": "Configuration updated successfully"
}
```

**Error Response (400):**
```json
{
  "error": "Connection failed",
  "details": "Unable to reach Firefly III at the provided URL"
}
```

---

### 2. Upload & Validate CSV

#### Upload CSV File
```
POST /api/upload
Content-Type: multipart/form-data
```

**Request Parameters:**
- `file` (required): CSV file (max 10MB)
- `format` (optional): CSV format - one of: `generic`, `bank`, `pocketsmith` (default: `generic`)

**Success Response (200):**
```json
{
  "session_id": "2024-01-20T15:30:45.123456",
  "row_count": 10,
  "preview": [
    {
      "date": "2024-01-15",
      "amount": "-45.50",
      "description": "Grocery Store",
      "source_account": "Checking",
      "destination_account": "Groceries"
    }
  ],
  "validation": {
    "valid": true,
    "errors": [],
    "error_count": 0
  }
}
```

**Error Response (400):**
```json
{
  "error": "CSV validation failed",
  "details": [
    "Row 2: Missing required field 'amount'",
    "Row 3: Invalid date format '2024/13/01'"
  ]
}
```

---

### 3. Import Transactions

#### Start Import
```
POST /api/import/{session_id}
```

**Path Parameters:**
- `session_id`: Session ID from upload response

**Success Response (200):**
```json
{
  "accounts_created": 2,
  "transactions_created": 10,
  "rows_skipped": 0,
  "errors": [],
  "accounts": [
    "Groceries",
    "Utilities"
  ]
}
```

**Partial Failure Response (200):**
```json
{
  "accounts_created": 1,
  "transactions_created": 8,
  "rows_skipped": 2,
  "errors": [
    {
      "row": 5,
      "message": "Invalid amount format"
    },
    {
      "row": 9,
      "message": "Duplicate transaction detected"
    }
  ],
  "accounts": [
    "Utilities"
  ]
}
```

---

### 4. Session Status

#### Get Session Details
```
GET /api/sessions/{session_id}
```

**Path Parameters:**
- `session_id`: Session ID from upload response

**Response (200):**
```json
{
  "status": "completed",
  "format": "generic",
  "results": {
    "accounts_created": 2,
    "transactions_created": 10,
    "rows_skipped": 0,
    "errors": [],
    "accounts": ["Groceries", "Utilities"]
  }
}
```

---

## CSV Formats

### Generic Format
**Required columns:**
- `date`: Transaction date (YYYY-MM-DD)
- `amount`: Transaction amount
- `description`: Transaction description
- `source_account`: Source account name
- `destination_account`: Destination account name

**Optional columns:**
- `type`: Transaction type (withdrawal, deposit, transfer)
- `category`: Category name
- `tags`: Comma-separated tags
- `notes`: Additional notes
- `external_id`: External transaction ID

### Bank Format
**Required columns:**
- `Date`: Transaction date
- `Description`: Transaction description
- `Amount`: Transaction amount

**Optional columns:**
- `Balance`: Account balance after transaction
- `Category`: Transaction category
- `Tags`: Transaction tags

### PocketSmith Format
**Required columns:**
- `Date`: Transaction date
- `Amount`: Transaction amount

**Optional columns:**
- `Payee`: Payee name
- `Category`: Transaction category
- `Memo`: Transaction memo
- `Account`: Account name

---

## Firefly III API Integration Examples

### Create Account
```
POST http://homeassistant.local:8080/api/v1/accounts
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Groceries",
  "type": "expense",
  "currency_code": "USD",
  "active": true
}
```

### Get Account by Name
```
GET http://homeassistant.local:8080/api/v1/accounts?filter[name]=Checking&filter[type]=asset
Authorization: Bearer YOUR_TOKEN
```

### Create Transaction
```
POST http://homeassistant.local:8080/api/v1/transactions
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "transactions": [
    {
      "type": "withdrawal",
      "date": "2024-01-15",
      "amount": "45.50",
      "description": "Grocery Store",
      "source_id": "1",
      "destination_id": "5",
      "category_name": "Groceries",
      "tags": ["food", "weekly"],
      "external_id": "GROCERY_2024_001"
    }
  ]
}
```

### Response - Success
```json
{
  "data": {
    "type": "transactions",
    "id": "12345",
    "attributes": {
      "created_at": "2024-01-15T12:00:00Z",
      "updated_at": "2024-01-15T12:00:00Z",
      "user_id": 1,
      "group_title": null,
      "transactions": [
        {
          "type": "withdrawal",
          "date": "2024-01-15",
          "amount": "45.50",
          "description": "Grocery Store"
        }
      ]
    }
  }
}
```

### Response - Error
```json
{
  "message": "The given data was invalid.",
  "errors": {
    "transactions.0.source_id": [
      "This field is required."
    ],
    "transactions.0.destination_id": [
      "This field is required."
    ]
  }
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message",
  "details": "Additional information if available"
}
```

### Common Error Codes

| Code | Message | Solution |
|------|---------|----------|
| 400 | Configuration not set | Call POST /api/config first |
| 400 | Invalid CSV file | Check file format and encoding |
| 413 | File too large | Max file size is 10MB |
| 404 | Session not found | Session may have expired |
| 500 | Firefly III connection error | Check URL and token |

---

## Rate Limiting

- No rate limiting implemented
- Recommend keeping file uploads under 10MB
- Avoid importing more than 1000 transactions at once

---

## Authentication

All API endpoints require proper Firefly III configuration:

```javascript
// Set configuration before using other endpoints
await fetch('/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    firefly_url: 'http://homeassistant.local:8080',
    firefly_token: 'your_token_here'
  })
});
```

---

## Example Workflow

```javascript
// 1. Configure Firefly III
const configResponse = await fetch('/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    firefly_url: 'http://homeassistant.local:8080',
    firefly_token: 'token123'
  })
});

// 2. Upload and validate CSV
const formData = new FormData();
formData.append('file', csvFile);
formData.append('format', 'generic');

const uploadResponse = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const { session_id } = await uploadResponse.json();

// 3. Start import
const importResponse = await fetch(`/api/import/${session_id}`, {
  method: 'POST'
});

const results = await importResponse.json();
console.log(`Created ${results.transactions_created} transactions`);
```
