"""
Firefly III CSV Importer - Flask Web Application
Main entry point for the Home Assistant add-on
"""

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from functools import wraps
import os
import logging
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_parser import CSVParser
from firefly_client import FireflyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/firefly_uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global state for import session
import_sessions = {}

def require_config(f):
    """Decorator to check if Firefly III config is set"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        base_url = os.getenv('FIREFLY_BASE_URL')
        token = os.getenv('FIREFLY_TOKEN')
        if not base_url or not token:
            return jsonify({'error': 'Firefly III not configured'}), 400
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration status"""
    base_url = os.getenv('FIREFLY_BASE_URL', '')
    token_set = bool(os.getenv('FIREFLY_TOKEN'))
    
    return jsonify({
        'firefly_url': base_url,
        'token_configured': token_set,
        'csv_formats': ['bank', 'pocketsmith', 'generic']
    })

@app.route('/api/config', methods=['POST'])
def set_config():
    """Update Firefly III configuration"""
    data = request.get_json()
    
    if not data.get('firefly_url') or not data.get('firefly_token'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Set environment variables
    os.environ['FIREFLY_BASE_URL'] = data['firefly_url']
    os.environ['FIREFLY_TOKEN'] = data['firefly_token']
    
    # Test connection
    client = FireflyClient(data['firefly_url'], data['firefly_token'])
    test_result = client.test_connection()
    
    if not test_result['success']:
        return jsonify({'error': test_result.get('error', 'Connection failed')}), 400
    
    return jsonify({'message': 'Configuration updated successfully'})

@app.route('/api/upload', methods=['POST'])
@require_config
def upload_csv():
    """Handle CSV file upload and validation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    csv_format = request.form.get('format', 'generic')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are supported'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse CSV
        parser = CSVParser(filepath)
        rows = parser.parse(csv_format)
        
        # Validate rows
        validation = parser.validate_rows(rows, csv_format)
        
        if not validation['valid']:
            return jsonify({
                'error': 'CSV validation failed',
                'details': validation['errors']
            }), 400
        
        # Create session
        session_id = datetime.now().isoformat()
        import_sessions[session_id] = {
            'rows': rows,
            'format': csv_format,
            'filepath': filepath,
            'status': 'validated',
            'created_at': datetime.now()
        }
        
        return jsonify({
            'session_id': session_id,
            'row_count': len(rows),
            'preview': rows[:5],  # Preview first 5 rows
            'validation': validation
        })
    
    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import/<session_id>', methods=['POST'])
@require_config
def import_transactions(session_id):
    """Import transactions from validated CSV"""
    if session_id not in import_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = import_sessions[session_id]
    client = FireflyClient(
        os.getenv('FIREFLY_BASE_URL'),
        os.getenv('FIREFLY_TOKEN')
    )
    
    try:
        results = {
            'accounts_created': 0,
            'transactions_created': 0,
            'rows_skipped': 0,
            'errors': [],
            'accounts': []
        }
        
        # Process each row
        for idx, row in enumerate(session['rows']):
            try:
                # Create/get accounts
                source_account = client.get_or_create_account(
                    row.get('source_account', 'Uncategorized'),
                    'asset'
                )
                
                if source_account.get('created'):
                    results['accounts_created'] += 1
                    results['accounts'].append(source_account['name'])
                
                dest_account = client.get_or_create_account(
                    row.get('destination_account', 'Expenses'),
                    'expense'
                )
                
                if dest_account.get('created'):
                    results['accounts_created'] += 1
                    results['accounts'].append(dest_account['name'])
                
                # Create transaction
                transaction_data = {
                    'transactions': [{
                        'type': row.get('type', 'withdrawal'),
                        'date': row.get('date'),
                        'amount': row.get('amount'),
                        'description': row.get('description'),
                        'source_id': source_account['id'],
                        'destination_id': dest_account['id'],
                        'category_name': row.get('category'),
                        'tags': row.get('tags', '').split(',') if row.get('tags') else [],
                        'external_id': row.get('external_id'),
                        'notes': row.get('notes')
                    }]
                }
                
                # Remove None values
                transaction_data['transactions'][0] = {
                    k: v for k, v in transaction_data['transactions'][0].items()
                    if v is not None
                }
                
                result = client.create_transaction(transaction_data)
                
                if result.get('success'):
                    results['transactions_created'] += 1
                else:
                    results['errors'].append({
                        'row': idx + 1,
                        'message': result.get('error', 'Unknown error')
                    })
                    results['rows_skipped'] += 1
            
            except Exception as e:
                logger.error(f"Error processing row {idx + 1}: {str(e)}")
                results['errors'].append({
                    'row': idx + 1,
                    'message': str(e)
                })
                results['rows_skipped'] += 1
        
        session['status'] = 'completed'
        session['results'] = results
        
        logger.info(f"Import completed: {results['transactions_created']} transactions, {results['accounts_created']} accounts")
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Error importing transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup
        if os.path.exists(session['filepath']):
            os.remove(session['filepath'])

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get import session details"""
    if session_id not in import_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = import_sessions[session_id]
    return jsonify({
        'status': session['status'],
        'format': session['format'],
        'results': session.get('results', {})
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File too large (max 10MB)'}), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Get port from environment or default
    port = int(os.getenv('PORT', 8099))
    
    logger.info(f"Starting Firefly III CSV Importer on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
