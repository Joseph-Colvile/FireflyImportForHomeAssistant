# Development Guide

## Project Setup

### Prerequisites
- Python 3.9 or later
- pip package manager
- Git
- Docker (optional, for containerized development)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/firefly-csv-importer.git
   cd firefly-csv-importer
   ```

2. **Create Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your Firefly III configuration
   ```

5. **Run the application:**
   ```bash
   python app/main.py
   ```

6. **Access the UI:**
   - Open `http://localhost:8099` in your browser

### Docker Development

1. **Build image:**
   ```bash
   docker build -t firefly-csv-importer:dev .
   ```

2. **Run container:**
   ```bash
   docker run -p 8099:8099 \
     -e FIREFLY_BASE_URL=http://host.docker.internal:8080 \
     -e FIREFLY_TOKEN=your_token \
     -v $(pwd):/app \
     firefly-csv-importer:dev
   ```

## Code Structure

```
app/
├── main.py           # Flask app & routes (500+ lines)
├── csv_parser.py     # CSV parsing logic (250+ lines)
├── firefly_client.py # Firefly III API client (300+ lines)
├── api.py            # Extensible route module (reserved)
├── templates/
│   └── index.html    # Web UI (400+ lines)
└── static/
    └── styles.css    # Styling (500+ lines)
```

## Adding New CSV Formats

### Step 1: Define Format in csv_parser.py

```python
FORMATS = {
    'your_format': {
        'columns': ['col1', 'col2', 'col3'],
        'required': ['col1', 'col2'],
        'optional': ['col3'],
        'mapper': {
            'col1': 'date',
            'col2': 'amount',
            'col3': 'description'
        }
    }
}
```

### Step 2: Add to UI (index.html)

```javascript
const formatDescriptions = {
    'your_format': 'Your format description'
};
```

And in the select dropdown:
```html
<option value="your_format">Your Format</option>
```

### Step 3: Update Documentation

- Add to README.md
- Add example CSV to examples/ folder
- Update API_EXAMPLES.md

### Example: Custom Bank Format

```python
'mybank': {
    'columns': ['Transaction Date', 'Reference', 'Debit', 'Credit', 'Balance'],
    'required': ['Transaction Date', 'Reference'],
    'optional': ['Debit', 'Credit', 'Balance'],
    'mapper': {
        'Transaction Date': 'date',
        'Reference': 'description',
        'Debit': 'amount',  # Will be negative
        'Credit': 'amount',  # Will be positive
    }
}
```

## Extending the API

### Add New Endpoint

1. **In main.py:**

```python
@app.route('/api/new-endpoint', methods=['GET', 'POST'])
@require_config
def new_endpoint():
    """New endpoint documentation"""
    data = request.get_json()
    
    try:
        # Your logic here
        return jsonify({'result': 'success'})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

2. **Update frontend:**

```javascript
async function callNewEndpoint() {
    const response = await fetch('/api/new-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({/* data */})
    });
    const result = await response.json();
}
```

## Firefly III API Integration

### Getting API Documentation

1. Open Firefly III
2. Go to `/api/` endpoint
3. Swagger UI shows all available endpoints
4. Authentication uses Bearer tokens

### Common API Calls

```python
# Get all accounts
GET /api/v1/accounts

# Get specific account
GET /api/v1/accounts/{id}

# Create transaction
POST /api/v1/transactions
```

### Testing Firefly III Connection

```bash
# Test with curl
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8080/api/v1/about

# In Python
import requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8080/api/v1/about', headers=headers)
print(response.json())
```

## Testing

### Manual Testing Checklist

- [ ] Upload valid CSV in all formats
- [ ] Upload invalid CSV (missing columns, bad dates)
- [ ] Test with different amount formats
- [ ] Test with special characters in description
- [ ] Test duplicate external_id detection
- [ ] Test account creation
- [ ] Test with empty categories/tags
- [ ] Test file size limit (>10MB)
- [ ] Test configuration update
- [ ] Test connection failure handling

### Unit Test Example

```python
import unittest
from app.csv_parser import CSVParser

class TestCSVParser(unittest.TestCase):
    def test_parse_generic_format(self):
        parser = CSVParser('test_generic.csv')
        rows = parser.parse('generic')
        self.assertEqual(len(rows), 10)
        self.assertIn('date', rows[0])
    
    def test_validate_required_fields(self):
        rows = [{'date': '2024-01-01', 'amount': '100'}]
        result = parser.validate_rows(rows, 'generic')
        self.assertFalse(result['valid'])
        self.assertTrue(len(result['errors']) > 0)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test Example

```python
def test_full_import_workflow():
    # Configure
    client = FireflyClient(base_url, token)
    assert client.test_connection()['success']
    
    # Upload
    response = app.post('/api/upload', data={'file': test_csv})
    assert response.status_code == 200
    session_id = response.json['session_id']
    
    # Import
    response = app.post(f'/api/import/{session_id}')
    assert response.status_code == 200
    assert response.json['transactions_created'] > 0
```

## Debugging

### Enable Debug Logging

1. **In .env:**
   ```
   LOG_LEVEL=debug
   FLASK_DEBUG=1
   ```

2. **Run with debug:**
   ```bash
   python -m flask --app app.main run --debug
   ```

3. **Check logs:**
   ```bash
   tail -f app.log
   ```

### Common Issues

**Issue:** Column mapping not working
- Check format definition in FORMATS
- Verify mapper keys match CSV headers exactly (case-sensitive)
- Print parsed rows to debug

**Issue:** API call fails
- Check Firefly III URL and token
- Verify network connectivity
- Check Firefly III logs
- Test with curl first

**Issue:** Memory issues
- Reduce batch size
- Clear old sessions
- Monitor temp file cleanup

## Code Style

### Python
- Follow PEP 8
- Use type hints where possible
- Document complex functions
- Use meaningful variable names

### JavaScript
- Use const/let (no var)
- Use async/await
- Add error handling
- Comment complex logic

### CSS
- Use CSS variables for colors
- Mobile-first responsive design
- Semantic HTML
- Consistent spacing

## Version Management

### Semantic Versioning
- MAJOR.MINOR.PATCH
- Update version in:
  - addon.json
  - config.yaml
  - README.md (Changelog)

### Release Process
1. Update version numbers
2. Update CHANGELOG.md
3. Tag in git: `git tag v1.0.0`
4. Push: `git push origin --tags`
5. Create GitHub release with notes

## Documentation Standards

### Code Comments
```python
def validate_amount(amount_str):
    """
    Validate amount string format.
    
    Args:
        amount_str: String containing amount (may include currency symbol)
    
    Returns:
        bool: True if valid, False otherwise
    
    Examples:
        >>> validate_amount("45.50")
        True
        >>> validate_amount("$1,000.00")
        True
    """
```

### Function Documentation
- Include docstring for all functions
- Document parameters and return values
- Include example usage
- Document exceptions raised

### README Sections
- Overview and features
- Installation instructions
- Configuration steps
- Usage examples
- API documentation
- Troubleshooting
- Development info

## Performance Optimization

### Tips
- Cache account lookups (already implemented)
- Use connection pooling (requests session)
- Minimize API calls
- Optimize CSV parsing
- Compress responses

### Monitoring
- Log API response times
- Track memory usage
- Monitor error rates
- Count processed transactions

### Benchmarking
```python
import time

start = time.time()
# Code to benchmark
duration = time.time() - start
logger.info(f"Operation took {duration:.2f}s")
```

## Security Best Practices

### Code Security
- Never log sensitive data (tokens, passwords)
- Validate all user input
- Use parameterized queries
- Sanitize file uploads
- Update dependencies regularly

### Secrets Management
- Never commit .env files
- Use environment variables
- Rotate tokens periodically
- Never display tokens in UI
- Log redacted versions only

### Dependency Management
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

## Building and Deploying

### Build for Release

```bash
# Build Docker image
docker build -t firefly-csv-importer:1.0.0 .

# Tag for registry
docker tag firefly-csv-importer:1.0.0 ghcr.io/yourusername/addon-firefly-csv-importer:1.0.0

# Push to registry
docker push ghcr.io/yourusername/addon-firefly-csv-importer:1.0.0
```

### Deploy to Home Assistant

1. Update addon.json with new version
2. Commit to repository
3. Tag release in git
4. Home Assistant users will see update available

## Troubleshooting Development

### Virtual Environment Issues
```bash
# Recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall package
pip install --force-reinstall -r requirements.txt
```

### Port Already in Use
```bash
# Find process using port 8099
lsof -i :8099
# Kill process
kill -9 <PID>
```

## Contributing

### Pull Request Process
1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Test thoroughly
5. Commit with clear messages
6. Push to branch
7. Create pull request
8. Respond to review comments

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Comments are clear
- [ ] No debug code left
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Performance considered
- [ ] Security reviewed

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Firefly III API](https://api-docs.firefly-iii.org/)
- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons/)
- [Python Best Practices](https://peps.python.org/pep-0008/)

---

Happy developing! 🚀
