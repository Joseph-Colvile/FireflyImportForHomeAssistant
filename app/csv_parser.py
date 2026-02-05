"""
CSV Parser for Firefly III CSV Importer
Supports multiple CSV formats and column mapping
"""

import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVParser:
    """Parse and validate CSV files for transaction import"""
    
    # Define CSV format mappings
    FORMATS = {
        'generic': {
            'columns': ['date', 'amount', 'description', 'source_account', 'destination_account'],
            'required': ['date', 'amount', 'description', 'source_account', 'destination_account'],
            'optional': ['type', 'category', 'tags', 'notes', 'external_id']
        },
        'bank': {
            'columns': ['Date', 'Description', 'Amount', 'Balance'],
            'required': ['Date', 'Description', 'Amount'],
            'optional': ['Balance', 'Category', 'Tags'],
            'mapper': {
                'Date': 'date',
                'Description': 'description',
                'Amount': 'amount',
                'Category': 'category',
                'Tags': 'tags'
            }
        },
        'pocketsmith': {
            'columns': ['Date', 'Payee', 'Category', 'Memo', 'Amount', 'Account'],
            'required': ['Date', 'Amount'],
            'optional': ['Payee', 'Category', 'Memo', 'Account'],
            'mapper': {
                'Date': 'date',
                'Payee': 'source_account',
                'Category': 'category',
                'Memo': 'description',
                'Amount': 'amount',
                'Account': 'destination_account'
            }
        }
    }
    
    def __init__(self, filepath):
        """Initialize the CSV parser"""
        self.filepath = filepath
    
    def parse(self, format_type='generic'):
        """
        Parse CSV file and return rows as dictionaries
        
        Args:
            format_type: Type of CSV format (generic, bank, pocketsmith)
        
        Returns:
            List of dictionaries with transaction data
        """
        if format_type not in self.FORMATS:
            raise ValueError(f"Unsupported format: {format_type}")
        
        try:
            rows = []
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = self._detect_delimiter(sample)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                if reader.fieldnames is None:
                    raise ValueError("CSV file is empty or invalid")
                
                format_config = self.FORMATS[format_type]
                mapper = format_config.get('mapper', {})
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    # Map columns if mapper is defined
                    if mapper:
                        mapped_row = {}
                        for old_key, new_key in mapper.items():
                            if old_key in row:
                                mapped_row[new_key] = row[old_key]
                        rows.append(mapped_row)
                    else:
                        rows.append(row)
                
                logger.info(f"Parsed {len(rows)} rows from {format_type} CSV")
                return rows
        
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise
    
    def validate_rows(self, rows, format_type='generic'):
        """
        Validate rows against format requirements
        
        Args:
            rows: List of row dictionaries
            format_type: Type of CSV format
        
        Returns:
            Dictionary with validation result and details
        """
        if format_type not in self.FORMATS:
            return {'valid': False, 'errors': [f"Unsupported format: {format_type}"]}
        
        if not rows:
            return {'valid': False, 'errors': ['CSV file is empty']}
        
        format_config = self.FORMATS[format_type]
        required = format_config['required']
        errors = []
        
        # Check each row
        for idx, row in enumerate(rows, start=2):  # Start at row 2 (after header)
            for field in required:
                if not row.get(field) or str(row.get(field)).strip() == '':
                    errors.append(f"Row {idx}: Missing required field '{field}'")
            
            # Validate date format if present
            if row.get('date'):
                if not self._validate_date(row['date']):
                    errors.append(f"Row {idx}: Invalid date format '{row['date']}'")
            
            # Validate amount format if present
            if row.get('amount'):
                if not self._validate_amount(row['amount']):
                    errors.append(f"Row {idx}: Invalid amount '{row['amount']}'")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors[:10],  # Return first 10 errors
            'error_count': len(errors)
        }
    
    def _detect_delimiter(self, sample):
        """Detect CSV delimiter"""
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            return dialect.delimiter
        except:
            return ','
    
    def _validate_date(self, date_str):
        """Validate date string"""
        if not date_str:
            return False
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(str(date_str).strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _validate_amount(self, amount_str):
        """Validate amount string"""
        if not amount_str:
            return False
        
        try:
            # Remove common currency symbols and spaces
            clean_amount = str(amount_str).strip().replace('$', '').replace('€', '').replace('£', '')
            float(clean_amount)
            return True
        except ValueError:
            return False
    
    def normalize_row(self, row):
        """
        Normalize a row for API submission
        
        Args:
            row: Row dictionary
        
        Returns:
            Normalized row with proper types
        """
        return {
            'date': str(row.get('date', '')).strip(),
            'amount': float(str(row.get('amount', 0)).replace('$', '').replace(',', '')),
            'description': str(row.get('description', '')).strip(),
            'source_account': str(row.get('source_account', 'Uncategorized')).strip(),
            'destination_account': str(row.get('destination_account', 'Expenses')).strip(),
            'type': str(row.get('type', 'withdrawal')).strip(),
            'category': str(row.get('category', '')).strip() or None,
            'tags': str(row.get('tags', '')).strip() or None,
            'notes': str(row.get('notes', '')).strip() or None,
            'external_id': str(row.get('external_id', '')).strip() or None
        }
