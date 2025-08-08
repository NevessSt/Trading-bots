import re
from typing import Dict, List, Any, Optional
from flask import request, jsonify
from functools import wraps
import bleach

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_api_key(api_key: str, exchange: str = None) -> bool:
        """Validate API key format"""
        if not api_key or len(api_key.strip()) == 0:
            return False
        
        # Basic length check
        if len(api_key) < 10 or len(api_key) > 200:
            return False
        
        # Exchange-specific validation
        if exchange:
            exchange = exchange.lower()
            if exchange == 'binance':
                return len(api_key) == 64 and api_key.isalnum()
            elif exchange == 'coinbase':
                return len(api_key) >= 32 and api_key.replace('-', '').isalnum()
            elif exchange == 'kraken':
                return len(api_key) >= 40 and all(c.isalnum() or c in '+/=' for c in api_key)
        
        # Generic validation - alphanumeric with some special chars
        return re.match(r'^[a-zA-Z0-9+/=_-]+$', api_key) is not None
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        
        # Remove HTML tags and limit length
        sanitized = bleach.clean(text, tags=[], strip=True)
        return sanitized[:max_length].strip()
    
    @staticmethod
    def validate_numeric_range(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric value within range"""
        try:
            num_value = float(value)
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_enum(value: str, allowed_values: List[str]) -> bool:
        """Validate value is in allowed enum"""
        return value in allowed_values

def validate_json_input(schema: Dict[str, Dict[str, Any]]):
    """Decorator to validate JSON input against schema"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            errors = {}
            validated_data = {}
            
            # Validate each field in schema
            for field, rules in schema.items():
                value = data.get(field)
                
                # Check required fields
                if rules.get('required', False) and value is None:
                    errors[field] = 'This field is required'
                    continue
                
                # Skip validation if field is optional and not provided
                if value is None:
                    continue
                
                # Type validation
                field_type = rules.get('type')
                if field_type == 'string':
                    if not isinstance(value, str):
                        errors[field] = 'Must be a string'
                        continue
                    
                    # String-specific validations
                    min_length = rules.get('min_length', 0)
                    max_length = rules.get('max_length', 1000)
                    
                    if len(value) < min_length:
                        errors[field] = f'Must be at least {min_length} characters'
                        continue
                    
                    if len(value) > max_length:
                        errors[field] = f'Must be no more than {max_length} characters'
                        continue
                    
                    # Email validation
                    if rules.get('format') == 'email':
                        if not InputValidator.validate_email(value):
                            errors[field] = 'Invalid email format'
                            continue
                    
                    # Sanitize string
                    validated_data[field] = InputValidator.sanitize_string(value, max_length)
                
                elif field_type == 'number':
                    if not isinstance(value, (int, float)):
                        errors[field] = 'Must be a number'
                        continue
                    
                    # Numeric range validation
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    
                    if not InputValidator.validate_numeric_range(value, min_val, max_val):
                        range_msg = []
                        if min_val is not None:
                            range_msg.append(f'minimum {min_val}')
                        if max_val is not None:
                            range_msg.append(f'maximum {max_val}')
                        errors[field] = f'Must be within range: {" and ".join(range_msg)}'
                        continue
                    
                    validated_data[field] = value
                
                elif field_type == 'boolean':
                    if not isinstance(value, bool):
                        errors[field] = 'Must be a boolean'
                        continue
                    
                    validated_data[field] = value
                
                elif field_type == 'array':
                    if not isinstance(value, list):
                        errors[field] = 'Must be an array'
                        continue
                    
                    validated_data[field] = value
                
                # Enum validation
                allowed_values = rules.get('enum')
                if allowed_values and not InputValidator.validate_enum(value, allowed_values):
                    errors[field] = f'Must be one of: {", ".join(allowed_values)}'
                    continue
            
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Add validated data to request
            request.validated_data = validated_data
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

# Common validation schemas
USER_REGISTRATION_SCHEMA = {
    'email': {
        'type': 'string',
        'required': True,
        'format': 'email',
        'max_length': 255
    },
    'password': {
        'type': 'string',
        'required': True,
        'min_length': 8,
        'max_length': 128
    },
    'first_name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 50
    },
    'last_name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 50
    }
}

USER_LOGIN_SCHEMA = {
    'email': {
        'type': 'string',
        'required': True,
        'format': 'email'
    },
    'password': {
        'type': 'string',
        'required': True,
        'min_length': 1
    }
}

API_KEY_SCHEMA = {
    'exchange': {
        'type': 'string',
        'required': True,
        'enum': ['binance', 'coinbase', 'kraken', 'bitfinex', 'bybit']
    },
    'api_key': {
        'type': 'string',
        'required': True,
        'min_length': 10,
        'max_length': 200
    },
    'api_secret': {
        'type': 'string',
        'required': True,
        'min_length': 10,
        'max_length': 200
    },
    'passphrase': {
        'type': 'string',
        'required': False,
        'max_length': 100
    },
    'is_testnet': {
        'type': 'boolean',
        'required': False
    }
}

BOT_CREATION_SCHEMA = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 100
    },
    'strategy': {
        'type': 'string',
        'required': True,
        'enum': ['grid', 'dca', 'momentum', 'mean_reversion']
    },
    'exchange': {
        'type': 'string',
        'required': True,
        'enum': ['binance', 'coinbase', 'kraken', 'bitfinex', 'bybit']
    },
    'symbol': {
        'type': 'string',
        'required': True,
        'min_length': 3,
        'max_length': 20
    },
    'investment_amount': {
        'type': 'number',
        'required': True,
        'min': 10,
        'max': 1000000
    },
    'risk_level': {
        'type': 'string',
        'required': True,
        'enum': ['low', 'medium', 'high']
    }
}