"""
Firefly III API Client
Handles all API interactions with Firefly III
"""

import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class FireflyClient:
    """Client for interacting with Firefly III API"""
    
    def __init__(self, base_url, token):
        """
        Initialize Firefly III client
        
        Args:
            base_url: Base URL of Firefly III (e.g., http://homeassistant.local:8080)
            token: Personal Access Token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = self._create_session()
        self.account_cache = {}  # Cache for account lookups
    
    def _create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        # Set default headers
        session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Add retry strategy
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def test_connection(self):
        """
        Test connection to Firefly III
        
        Returns:
            Dictionary with success status and error message if failed
        """
        try:
            response = self.session.get(f'{self.base_url}/api/v1/about')
            
            if response.status_code == 200:
                logger.info("Successfully connected to Firefly III")
                return {'success': True}
            else:
                error_msg = f"Connection failed: {response.status_code}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_account(self, account_id):
        """
        Get account by ID
        
        Args:
            account_id: Firefly III account ID
        
        Returns:
            Account data or None if not found
        """
        try:
            response = self.session.get(f'{self.base_url}/api/v1/accounts/{account_id}')
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting account {account_id}: {str(e)}")
            return None
    
    def find_account_by_name(self, name, account_type='asset'):
        """
        Find account by name
        
        Args:
            name: Account name
            account_type: Type of account (asset, expense, revenue, etc.)
        
        Returns:
            Account ID or None if not found
        """
        # Check cache first
        cache_key = f"{name}_{account_type}"
        if cache_key in self.account_cache:
            return self.account_cache[cache_key]
        
        try:
            params = {
                'filter[name]': name,
                'filter[type]': account_type
            }
            response = self.session.get(
                f'{self.base_url}/api/v1/accounts',
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('data', [])
                
                if accounts:
                    account_id = accounts[0]['id']
                    self.account_cache[cache_key] = account_id
                    return account_id
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding account '{name}': {str(e)}")
            return None
    
    def create_account(self, name, account_type='asset', currency='USD'):
        """
        Create a new account
        
        Args:
            name: Account name
            account_type: Type of account (asset, expense, revenue, etc.)
            currency: Currency code
        
        Returns:
            Dictionary with success, id, and error (if failed)
        """
        try:
            payload = {
                'name': name,
                'type': account_type,
                'currency_code': currency,
                'active': True
            }
            
            response = self.session.post(
                f'{self.base_url}/api/v1/accounts',
                json=payload
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                account_id = data.get('data', {}).get('id')
                logger.info(f"Created account '{name}' with ID {account_id}")
                
                # Cache the new account
                cache_key = f"{name}_{account_type}"
                self.account_cache[cache_key] = account_id
                
                return {
                    'success': True,
                    'id': account_id,
                    'name': name,
                    'created': True
                }
            else:
                error_msg = self._parse_error_response(response)
                logger.error(f"Failed to create account '{name}': {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_or_create_account(self, name, account_type='asset', currency='USD'):
        """
        Get account by name or create if not exists
        
        Args:
            name: Account name
            account_type: Type of account
            currency: Currency code
        
        Returns:
            Dictionary with id, name, and created flag
        """
        # Try to find existing account
        account_id = self.find_account_by_name(name, account_type)
        
        if account_id:
            return {
                'id': account_id,
                'name': name,
                'created': False
            }
        
        # Create new account if not found
        result = self.create_account(name, account_type, currency)
        
        if result['success']:
            return {
                'id': result['id'],
                'name': name,
                'created': True
            }
        else:
            raise Exception(result['error'])
    
    def create_transaction(self, transaction_data):
        """
        Create a transaction
        
        Args:
            transaction_data: Transaction payload
        
        Returns:
            Dictionary with success status and error if failed
        """
        try:
            response = self.session.post(
                f'{self.base_url}/api/v1/transactions',
                json=transaction_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                transaction_id = data.get('data', {}).get('id')
                logger.info(f"Created transaction with ID {transaction_id}")
                return {'success': True, 'id': transaction_id}
            else:
                error_msg = self._parse_error_response(response)
                logger.error(f"Failed to create transaction: {error_msg}")
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def list_accounts(self, account_type=None):
        """
        List all accounts
        
        Args:
            account_type: Optional account type filter
        
        Returns:
            List of accounts
        """
        try:
            params = {}
            if account_type:
                params['filter[type]'] = account_type
            
            response = self.session.get(
                f'{self.base_url}/api/v1/accounts',
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            
            return []
        
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []
    
    def _parse_error_response(self, response):
        """
        Parse error response from Firefly III API
        
        Args:
            response: Response object
        
        Returns:
            Error message string
        """
        try:
            error_data = response.json()
            
            # Check for validation errors
            if 'errors' in error_data:
                errors = error_data['errors']
                if isinstance(errors, dict):
                    error_msg = '; '.join([
                        f"{key}: {', '.join(msgs) if isinstance(msgs, list) else msgs}"
                        for key, msgs in errors.items()
                    ])
                    return error_msg
            
            # Check for message field
            if 'message' in error_data:
                return error_data['message']
            
            # Check for exception field
            if 'exception' in error_data:
                return error_data['exception']
            
            return f"HTTP {response.status_code}"
        
        except:
            return f"HTTP {response.status_code}: {response.text[:200]}"
