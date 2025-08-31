from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets
from datetime import datetime, timedelta

from .logging_service import get_logger, LogCategory
from .error_handler import handle_errors, ErrorCategory


class EncryptionLevel(Enum):
    """Encryption security levels"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


class KeyType(Enum):
    """Types of keys that can be encrypted"""
    API_KEY = "api_key"
    SECRET_KEY = "secret_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    WEBHOOK_SECRET = "webhook_secret"
    ENCRYPTION_KEY = "encryption_key"
    OTHER = "other"


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata"""
    encrypted_value: str
    key_type: KeyType
    encryption_level: EncryptionLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.logger = get_logger(LogCategory.SECURITY)
        self._master_key = master_key or self._get_or_create_master_key()
        self._fernet_instances = {}
        self._initialize_encryption_instances()
        
    def _get_or_create_master_key(self) -> str:
        """Get or create master encryption key"""
        key_file = os.path.join(os.path.dirname(__file__), '..', '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read().decode()
        else:
            # Generate new master key
            key = Fernet.generate_key().decode()
            with open(key_file, 'w') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict file permissions
            self.logger.info("Generated new master encryption key", extra={
                "key_file": key_file,
                "permissions": "0o600"
            })
            return key
    
    def _initialize_encryption_instances(self):
        """Initialize Fernet instances for different encryption levels"""
        try:
            # Basic encryption - single iteration
            self._fernet_instances[EncryptionLevel.BASIC] = Fernet(self._master_key.encode())
            
            # Standard encryption - derived key with salt
            salt = b'trading_bot_salt_standard'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
            self._fernet_instances[EncryptionLevel.STANDARD] = Fernet(key)
            
            # High encryption - more iterations
            salt_high = b'trading_bot_salt_high_security'
            kdf_high = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_high,
                iterations=500000,
            )
            key_high = base64.urlsafe_b64encode(kdf_high.derive(self._master_key.encode()))
            self._fernet_instances[EncryptionLevel.HIGH] = Fernet(key_high)
            
            # Maximum encryption - highest iterations
            salt_max = b'trading_bot_salt_maximum_security'
            kdf_max = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_max,
                iterations=1000000,
            )
            key_max = base64.urlsafe_b64encode(kdf_max.derive(self._master_key.encode()))
            self._fernet_instances[EncryptionLevel.MAXIMUM] = Fernet(key_max)
            
            self.logger.info("Initialized encryption instances for all security levels")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption instances: {e}")
            raise
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def encrypt_data(self, 
                    data: str, 
                    key_type: KeyType = KeyType.OTHER,
                    encryption_level: EncryptionLevel = EncryptionLevel.STANDARD,
                    expires_in_days: Optional[int] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> EncryptedData:
        """Encrypt sensitive data"""
        try:
            fernet = self._fernet_instances[encryption_level]
            encrypted_bytes = fernet.encrypt(data.encode())
            encrypted_value = base64.urlsafe_b64encode(encrypted_bytes).decode()
            
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            encrypted_data = EncryptedData(
                encrypted_value=encrypted_value,
                key_type=key_type,
                encryption_level=encryption_level,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            self.logger.info(f"Encrypted {key_type.value} data", extra={
                "key_type": key_type.value,
                "encryption_level": encryption_level.value,
                "expires_at": expires_at.isoformat() if expires_at else None
            })
            
            return encrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {e}", extra={
                "key_type": key_type.value,
                "encryption_level": encryption_level.value
            })
            raise
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def decrypt_data(self, encrypted_data: EncryptedData) -> str:
        """Decrypt sensitive data"""
        try:
            # Check if data has expired
            if encrypted_data.expires_at and datetime.utcnow() > encrypted_data.expires_at:
                raise ValueError(f"Encrypted data has expired at {encrypted_data.expires_at}")
            
            fernet = self._fernet_instances[encrypted_data.encryption_level]
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encrypted_value.encode())
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            decrypted_data = decrypted_bytes.decode()
            
            self.logger.info(f"Decrypted {encrypted_data.key_type.value} data", extra={
                "key_type": encrypted_data.key_type.value,
                "encryption_level": encrypted_data.encryption_level.value
            })
            
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}", extra={
                "key_type": encrypted_data.key_type.value,
                "encryption_level": encrypted_data.encryption_level.value
            })
            raise
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def encrypt_api_keys(self, api_keys: Dict[str, str]) -> Dict[str, EncryptedData]:
        """Encrypt multiple API keys"""
        encrypted_keys = {}
        
        for key_name, key_value in api_keys.items():
            key_type = KeyType.API_KEY if 'api' in key_name.lower() else KeyType.SECRET_KEY
            encrypted_keys[key_name] = self.encrypt_data(
                data=key_value,
                key_type=key_type,
                encryption_level=EncryptionLevel.HIGH
            )
        
        self.logger.info(f"Encrypted {len(api_keys)} API keys")
        return encrypted_keys
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def decrypt_api_keys(self, encrypted_keys: Dict[str, EncryptedData]) -> Dict[str, str]:
        """Decrypt multiple API keys"""
        decrypted_keys = {}
        
        for key_name, encrypted_data in encrypted_keys.items():
            decrypted_keys[key_name] = self.decrypt_data(encrypted_data)
        
        self.logger.info(f"Decrypted {len(encrypted_keys)} API keys")
        return decrypted_keys
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        hashed = base64.urlsafe_b64encode(kdf.derive(password.encode())).decode()
        
        self.logger.info("Password hashed successfully")
        return hashed, salt
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            new_hash, _ = self.hash_password(password, salt)
            is_valid = secrets.compare_digest(hashed_password, new_hash)
            
            self.logger.info(f"Password verification: {'success' if is_valid else 'failed'}")
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        token = secrets.token_urlsafe(length)
        self.logger.info(f"Generated secure token of length {length}")
        return token
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def save_encrypted_config(self, config_data: Dict[str, Any], file_path: str):
        """Save encrypted configuration to file"""
        try:
            # Encrypt the entire config as JSON
            config_json = json.dumps(config_data)
            encrypted_config = self.encrypt_data(
                data=config_json,
                key_type=KeyType.OTHER,
                encryption_level=EncryptionLevel.HIGH,
                metadata={"file_path": file_path, "config_type": "application_config"}
            )
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump({
                    "encrypted_value": encrypted_config.encrypted_value,
                    "key_type": encrypted_config.key_type.value,
                    "encryption_level": encrypted_config.encryption_level.value,
                    "created_at": encrypted_config.created_at.isoformat(),
                    "expires_at": encrypted_config.expires_at.isoformat() if encrypted_config.expires_at else None,
                    "metadata": encrypted_config.metadata
                }, f, indent=2)
            
            os.chmod(file_path, 0o600)  # Restrict file permissions
            self.logger.info(f"Saved encrypted configuration to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save encrypted config: {e}")
            raise
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def load_encrypted_config(self, file_path: str) -> Dict[str, Any]:
        """Load and decrypt configuration from file"""
        try:
            with open(file_path, 'r') as f:
                encrypted_data_dict = json.load(f)
            
            # Reconstruct EncryptedData object
            encrypted_data = EncryptedData(
                encrypted_value=encrypted_data_dict["encrypted_value"],
                key_type=KeyType(encrypted_data_dict["key_type"]),
                encryption_level=EncryptionLevel(encrypted_data_dict["encryption_level"]),
                created_at=datetime.fromisoformat(encrypted_data_dict["created_at"]),
                expires_at=datetime.fromisoformat(encrypted_data_dict["expires_at"]) if encrypted_data_dict["expires_at"] else None,
                metadata=encrypted_data_dict.get("metadata", {})
            )
            
            # Decrypt and parse JSON
            decrypted_json = self.decrypt_data(encrypted_data)
            config_data = json.loads(decrypted_json)
            
            self.logger.info(f"Loaded encrypted configuration from {file_path}")
            return config_data
            
        except Exception as e:
            self.logger.error(f"Failed to load encrypted config: {e}")
            raise
    
    def rotate_master_key(self, new_master_key: Optional[str] = None):
        """Rotate the master encryption key"""
        try:
            old_master_key = self._master_key
            self._master_key = new_master_key or Fernet.generate_key().decode()
            
            # Re-initialize encryption instances
            self._initialize_encryption_instances()
            
            # Update key file
            key_file = os.path.join(os.path.dirname(__file__), '..', '.encryption_key')
            with open(key_file, 'w') as f:
                f.write(self._master_key)
            
            self.logger.info("Master encryption key rotated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate master key: {e}")
            # Restore old key on failure
            self._master_key = old_master_key
            self._initialize_encryption_instances()
            raise


# Global encryption service instance
_encryption_service = None


def get_encryption_service(master_key: Optional[str] = None) -> EncryptionService:
    """Get global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(master_key)
    return _encryption_service


def encrypt_env_file(env_file_path: str, output_file_path: str):
    """Encrypt an entire .env file"""
    encryption_service = get_encryption_service()
    
    try:
        # Read .env file
        with open(env_file_path, 'r') as f:
            env_content = f.read()
        
        # Parse environment variables
        env_vars = {}
        for line in env_content.strip().split('\n'):
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        # Encrypt sensitive variables
        encrypted_vars = {}
        sensitive_keys = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'PRIVATE']
        
        for key, value in env_vars.items():
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                key_type = KeyType.API_KEY if 'API' in key.upper() else KeyType.SECRET_KEY
                encrypted_vars[key] = encryption_service.encrypt_data(
                    data=value,
                    key_type=key_type,
                    encryption_level=EncryptionLevel.HIGH
                )
            else:
                encrypted_vars[key] = value
        
        # Save encrypted configuration
        encryption_service.save_encrypted_config(encrypted_vars, output_file_path)
        
        logger = get_logger(LogCategory.SECURITY)
        logger.info(f"Encrypted .env file from {env_file_path} to {output_file_path}")
        
    except Exception as e:
        logger = get_logger(LogCategory.SECURITY)
        logger.error(f"Failed to encrypt .env file: {e}")
        raise


def decrypt_env_file(encrypted_file_path: str, output_file_path: str):
    """Decrypt an encrypted .env file"""
    encryption_service = get_encryption_service()
    
    try:
        # Load encrypted configuration
        encrypted_vars = encryption_service.load_encrypted_config(encrypted_file_path)
        
        # Decrypt variables and create .env content
        env_lines = []
        for key, value in encrypted_vars.items():
            if isinstance(value, dict) and 'encrypted_value' in value:
                # This is an encrypted value, decrypt it
                encrypted_data = EncryptedData(
                    encrypted_value=value['encrypted_value'],
                    key_type=KeyType(value['key_type']),
                    encryption_level=EncryptionLevel(value['encryption_level']),
                    created_at=datetime.fromisoformat(value['created_at']),
                    expires_at=datetime.fromisoformat(value['expires_at']) if value['expires_at'] else None,
                    metadata=value.get('metadata', {})
                )
                decrypted_value = encryption_service.decrypt_data(encrypted_data)
                env_lines.append(f"{key}={decrypted_value}")
            else:
                # This is a plain value
                env_lines.append(f"{key}={value}")
        
        # Write to output file
        with open(output_file_path, 'w') as f:
            f.write('\n'.join(env_lines))
        
        os.chmod(output_file_path, 0o600)  # Restrict file permissions
        
        logger = get_logger(LogCategory.SECURITY)
        logger.info(f"Decrypted .env file from {encrypted_file_path} to {output_file_path}")
        
    except Exception as e:
        logger = get_logger(LogCategory.SECURITY)
        logger.error(f"Failed to decrypt .env file: {e}")
        raise