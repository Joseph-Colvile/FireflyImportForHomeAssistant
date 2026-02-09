#!/usr/bin/env python3
"""
Firefly III CSV Importer - Flask Backend
Handles CSV upload, validation, and transaction import to Firefly III
"""

import os
import logging
import csv
import io
from datetime import datetime
from typing import Dict, Tuple, Optional
import requests
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')


class IngressPathMiddleware:
    """Support Home Assistant Ingress by honoring X-Ingress-Path."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        ingress_path = environ.get('HTTP_X_INGRESS_PATH', '')
        if ingress_path:
            environ['SCRIPT_NAME'] = ingress_path
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(ingress_path):
                environ['PATH_INFO'] = path_info[len(ingress_path):] or '/'
        return self.wsgi_app(environ, start_response)


app.wsgi_app = IngressPathMiddleware(app.wsgi_app)

# Configuration
FIREFLY_URL = os.environ.get('FIREFLY_URL', '').rstrip('/')
FIREFLY_TOKEN = os.environ.get('FIREFLY_TOKEN', '')
CSV_MAX_SIZE_MB = int(os.environ.get('CSV_MAX_SIZE_MB', 10))
DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'USD')

# File upload configuration
UPLOAD_FOLDER = '/tmp/firefly_uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_CONTENT_LENGTH = CSV_MAX_SIZE_MB * 1024 * 1024  # Convert MB to bytes

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_config():
    """Verify Firefly III configuration"""
    if not FIREFLY_URL or not FIREFLY_TOKEN:
        return False, "Firefly III configuration not complete"
    return True, "Configuration valid"


def make_firefly_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Tuple[bool, Dict]:
    """
    Make authenticated request to Firefly III API
    Returns: (success: bool, response_data: dict)
    """
    url = f"{FIREFLY_URL}/api/v1{endpoint}"
    headers = {
        'Authorization': f'Bearer {FIREFLY_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            resp = requests.post(url, json=data, headers=headers, params=params, timeout=10)
        elif method == 'PUT':
            resp = requests.put(url, json=data, headers=headers, params=params, timeout=10)
        else:
            return False, {'error': f'Unknown HTTP method: {method}'}
        
        if resp.status_code in [200, 201]:
            try:
                return True, resp.json()
            except ValueError:
                return True, {'success': True}
        else:
            try:
                error_data = resp.json()
                return False, error_data
            except ValueError:
                return False, {'error': f'HTTP {resp.status_code}: {resp.text}'}
    
    except requests.exceptions.Timeout:
        return False, {'error': 'Request timeout - Firefly III server not responding'}
    except requests.exceptions.ConnectionError:
        return False, {'error': f'Cannot connect to Firefly III at {FIREFLY_URL}'}
    except Exception as e:
        logger.error(f"API request error: {e}")
        return False, {'error': f'API request failed: {str(e)}'}


def get_or_create_account(account_name: str, account_type: str, currency: str = DEFAULT_CURRENCY) -> Tuple[bool, int, str]:
    """
    Get account by name or create if not exists
    Returns: (success: bool, account_id: int, message: str)
    """
    if not account_name or not account_name.strip():
        return False, 0, "Account name cannot be empty"
    
    account_name = account_name.strip()
    
    # Search for existing account
    success, response = make_firefly_request('GET', '/accounts', params={'type': account_type})
    
    if success and 'data' in response:
        for account in response['data']:
            if account['attributes']['name'].lower() == account_name.lower():
                return True, account['id'], f"Found existing account: {account_name}"
    
    # Account doesn't exist, create it
    create_data = {
        'name': account_name,
        'type': account_type,
        'currency_code': currency,
        'account_number': None,
        'iban': None,
        'bic': None,
        'virtual_balance': '0'
    }
    
    success, response = make_firefly_request('POST', '/accounts', data=create_data)
    
    if success and 'data' in response:
        account_id = response['data']['id']
        logger.info(f"Created account '{account_name}' with ID {account_id}")
        return True, account_id, f"Created account: {account_name}"
    else:
        error_msg = response.get('error', response.get('message', 'Unknown error'))
        logger.error(f"Failed to create account '{account_name}': {error_msg}")
        return False, 0, f"Failed to create account: {error_msg}"


def create_transaction(transaction_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create transaction in Firefly III
    Returns: (success: bool, message: str, transaction_data: dict or None)
    """
    success, response = make_firefly_request('POST', '/transactions', data=transaction_data)
    
    if success:
        if 'data' in response:
            transaction_id = response['data'][0]['id'] if isinstance(response['data'], list) else response['data']['id']
            return True, f"Transaction created with ID {transaction_id}", response.get('data')
        return True, "Transaction created successfully", None
    else:
        error_msg = response.get('error', response.get('message', 'Unknown error'))
        return False, error_msg, None


@app.before_request
def check_config():
    """Check configuration on each request"""
    if request.path.startswith('/api/') and request.path != '/api/health':
        valid, msg = validate_config()
        if not valid:
            return jsonify({'error': msg, 'configured': False}), 400


@app.route('/health')
def health():
    """Health check endpoint for Docker"""
    return jsonify({'status': 'ok'}), 200


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/config')
def get_config():
    """Get current configuration (without sensitive data)"""
    valid, msg = validate_config()
    return jsonify({
        'configured': valid,
        'firefly_url': FIREFLY_URL,
        'default_currency': DEFAULT_CURRENCY,
        'max_upload_size_mb': CSV_MAX_SIZE_MB
    })


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test connection to Firefly III API"""
    success, response = make_firefly_request('GET', '/user')
    
    if success:
        user_email = response.get('data', {}).get('attributes', {}).get('email', 'Unknown')
        return jsonify({
            'success': True,
            'message': f'Connected to Firefly III',
            'user': user_email
        })
    else:
        return jsonify({
            'success': False,
            'error': response.get('error', 'Connection failed')
        }), 400


@app.route('/api/parse-csv', methods=['POST'])
def parse_csv():
    """Parse CSV file and return preview"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    
    try:
        # Read and decode CSV
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        if not csv_reader.fieldnames:
            return jsonify({'error': 'CSV file is empty'}), 400
        
        rows = list(csv_reader)
        
        return jsonify({
            'success': True,
            'columns': csv_reader.fieldnames,
            'preview': rows[:5],
            'total_rows': len(rows),
            'all_rows': rows
        })
    
    except UnicodeDecodeError:
        return jsonify({'error': 'File encoding error. Please use UTF-8 encoded CSV.'}), 400
    except Exception as e:
        logger.error(f"CSV parsing error: {e}")
        return jsonify({'error': f'Failed to parse CSV: {str(e)}'}), 400


@app.route('/api/import-transactions', methods=['POST'])
def import_transactions():
    """Import transactions into Firefly III"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    rows = data.get('rows', [])
    mapping = data.get('mapping', {})
    
    if not rows:
        return jsonify({'error': 'No rows to import'}), 400
    
    # Validate mapping has required fields
    required_fields = ['date', 'amount', 'description', 'source_account', 'destination_account']
    for field in required_fields:
        if field not in mapping or not mapping[field]:
            return jsonify({'error': f'Mapping missing required field: {field}'}), 400
    
    # Process import
    results = {
        'imported': 0,
        'skipped': 0,
        'errors': [],
        'accounts_created': [],
        'transactions': []
    }
    
    processed_accounts = {}  # Cache for account lookups
    
    for row_idx, row in enumerate(rows, 1):
        try:
            # Extract mapped values
            date_str = row.get(mapping['date'], '').strip()
            amount_str = row.get(mapping['amount'], '').strip()
            description = row.get(mapping['description'], '').strip()
            source_account = row.get(mapping['source_account'], '').strip()
            destination_account = row.get(mapping['destination_account'], '').strip()
            category = row.get(mapping.get('category', ''), '').strip() if mapping.get('category') else None
            tags = row.get(mapping.get('tags', ''), '').strip() if mapping.get('tags') else None
            notes = row.get(mapping.get('notes', ''), '').strip() if mapping.get('notes') else None
            external_id = row.get(mapping.get('external_id', ''), '').strip() if mapping.get('external_id') else None
            transaction_type = row.get(mapping.get('type', ''), 'withdrawal').strip().lower()
            
            # Validate required fields
            if not all([date_str, amount_str, description, source_account, destination_account]):
                results['errors'].append({
                    'row': row_idx,
                    'reason': 'Missing required field'
                })
                results['skipped'] += 1
                continue
            
            # Validate and parse date
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date_iso = date_obj.isoformat()
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    date_iso = date_obj.isoformat()
                except ValueError:
                    results['errors'].append({
                        'row': row_idx,
                        'reason': f'Invalid date format: {date_str}'
                    })
                    results['skipped'] += 1
                    continue
            
            # Validate and parse amount
            try:
                amount = float(amount_str.replace(',', '').replace('$', '').replace('€', '').strip())
                if amount == 0:
                    results['errors'].append({
                        'row': row_idx,
                        'reason': 'Amount cannot be zero'
                    })
                    results['skipped'] += 1
                    continue
            except ValueError:
                results['errors'].append({
                    'row': row_idx,
                    'reason': f'Invalid amount: {amount_str}'
                })
                results['skipped'] += 1
                continue
            
            # Determine account types and get/create accounts
            amount_abs = abs(amount)
            
            # Determine transaction type
            if transaction_type.lower() in ['withdrawal', 'expense']:
                source_type = 'asset'
                dest_type = 'expense'
                final_type = 'withdrawal'
            elif transaction_type.lower() in ['deposit', 'income']:
                source_type = 'revenue'
                dest_type = 'asset'
                final_type = 'deposit'
            elif transaction_type.lower() == 'transfer':
                source_type = 'asset'
                dest_type = 'asset'
                final_type = 'transfer'
            else:
                source_type = 'asset'
                dest_type = 'expense'
                final_type = 'withdrawal'
            
            # Get or create source account
            cache_key = (source_account, source_type)
            if cache_key not in processed_accounts:
                success, acc_id, msg = get_or_create_account(source_account, source_type)
                if not success:
                    results['errors'].append({
                        'row': row_idx,
                        'reason': f'Source account error: {msg}'
                    })
                    results['skipped'] += 1
                    continue
                processed_accounts[cache_key] = acc_id
                if 'created' in msg.lower():
                    results['accounts_created'].append(source_account)
            
            source_id = processed_accounts[cache_key]
            
            # Get or create destination account
            cache_key = (destination_account, dest_type)
            if cache_key not in processed_accounts:
                success, acc_id, msg = get_or_create_account(destination_account, dest_type)
                if not success:
                    results['errors'].append({
                        'row': row_idx,
                        'reason': f'Destination account error: {msg}'
                    })
                    results['skipped'] += 1
                    continue
                processed_accounts[cache_key] = acc_id
                if 'created' in msg.lower():
                    results['accounts_created'].append(destination_account)
            
            dest_id = processed_accounts[cache_key]
            
            # Build transaction data
            transaction = {
                'error_if_duplicate_hash': 'ignore',
                'transactions': [
                    {
                        'type': final_type,
                        'date': date_iso,
                        'amount': str(amount_abs),
                        'description': description,
                        'source_id': str(source_id),
                        'destination_id': str(dest_id),
                        'currency_code': DEFAULT_CURRENCY
                    }
                ]
            }
            
            # Add optional fields
            if notes:
                transaction['transactions'][0]['notes'] = notes
            if external_id:
                transaction['transactions'][0]['external_id'] = external_id
            if tags:
                transaction['transactions'][0]['tags'] = [t.strip() for t in tags.split(',')]
            if category:
                transaction['transactions'][0]['category_name'] = category
            
            # Create transaction
            success, msg, trans_data = create_transaction(transaction)
            
            if success:
                results['imported'] += 1
                results['transactions'].append({
                    'row': row_idx,
                    'description': description,
                    'amount': amount,
                    'date': date_iso
                })
            else:
                results['errors'].append({
                    'row': row_idx,
                    'reason': msg
                })
                results['skipped'] += 1
        
        except Exception as e:
            logger.error(f"Error processing row {row_idx}: {e}")
            results['errors'].append({
                'row': row_idx,
                'reason': f'Processing error: {str(e)}'
            })
            results['skipped'] += 1
    
    # Remove duplicates from accounts_created
    results['accounts_created'] = list(set(results['accounts_created']))
    
    return jsonify({
        'success': True,
        'results': results,
        'summary': {
            'total_rows': len(rows),
            'imported': results['imported'],
            'skipped': results['skipped'],
            'accounts_created': len(results['accounts_created']),
            'success_rate': f"{(results['imported'] / len(rows) * 100):.1f}%" if rows else "0%"
        }
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': f'File is too large. Maximum size is {CSV_MAX_SIZE_MB}MB'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Starting Firefly III CSV Importer")
    logger.info(f"Firefly III URL: {FIREFLY_URL}")
    logger.info(f"Max upload size: {CSV_MAX_SIZE_MB}MB")
    
    # Run Flask app
    # Use 0.0.0.0 to listen on all interfaces (required for Docker/Home Assistant)
    app.run(host='0.0.0.0', port=8099, debug=False, threaded=True)
