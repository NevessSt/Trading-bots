import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Handles encryption and decryption of sensitive data like API keys.
    Uses AES encryption via Fernet (symmetric encryption).
    """
    
    def __init__(self, key_file_path: str = None):
        self.key_file_path = key_file_path or os.path.join(
            os.path.dirname(__file__), '..', 'config', 'encryption.key'
        )
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """
        Initialize the encryption system with the master key.
        """
        try:
            # Try to load existing key
            if os.path.exists(self.key_file_path):
                with open(self.key_file_path, 'rb') as f:
                    key = f.read()
                    # If it's the old format (not base64), convert it
                    if len(key) != 44:  # Fernet keys are 44 bytes when base64 encoded
                        key = self._derive_key_from_password(key)
                    else:
                        # Validate it's a proper Fernet key
                        try:
                            Fernet(key)
                        except Exception:
                            # If invalid, derive a new key from the old one
                            key = self._derive_key_from_password(key)
            else:
                # Generate new key
                key = Fernet.generate_key()
                self._save_key(key)
            
            self._fernet = Fernet(key)
            logger.info("Encryption system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            # Fallback: generate a new key
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
            self._save_key(key)
    
    def _derive_key_from_password(self, password: bytes) -> bytes:
        """
        Derive a Fernet key from a password using PBKDF2.
        """
        # Use a fixed salt for consistency (in production, consider using a random salt)
        salt = b'trading_bot_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _save_key(self, key: bytes):
        """
        Save the encryption key to file.
        """
        try:
            os.makedirs(os.path.dirname(self.key_file_path), exist_ok=True)
            with open(self.key_file_path, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(self.key_file_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to save encryption key: {str(e)}")
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string and return base64 encoded result.
        
        Args:
            data: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            if not data:
                return ''
            
            encrypted_data = self._fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a base64 encoded encrypted string.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        try:
            if not encrypted_data:
                return ''
            
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary by converting to JSON first.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64 encoded encrypted JSON string
        """
        try:
            json_data = json.dumps(data, sort_keys=True)
            return self.encrypt(json_data)
        except Exception as e:
            logger.error(f"Dictionary encryption failed: {str(e)}")
            raise EncryptionError(f"Failed to encrypt dictionary: {str(e)}")
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt an encrypted JSON string back to dictionary.
        
        Args:
            encrypted_data: Base64 encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        try:
            json_data = self.decrypt(encrypted_data)
            return json.loads(json_data)
        except Exception as e:
            logger.error(f"Dictionary decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt dictionary: {str(e)}")
    
    def encrypt_api_credentials(self, api_key: str, api_secret: str, 
                              passphrase: str = None) -> Dict[str, str]:
        """
        Encrypt API credentials and return encrypted data.
        
        Args:
            api_key: API key to encrypt
            api_secret: API secret to encrypt
            passphrase: Optional passphrase to encrypt
            
        Returns:
            Dictionary with encrypted credentials
        """
        try:
            credentials = {
                'api_key': self.encrypt(api_key),
                'api_secret': self.encrypt(api_secret)
            }
            
            if passphrase:
                credentials['passphrase'] = self.encrypt(passphrase)
            
            return credentials
            
        except Exception as e:
            logger.error(f"API credentials encryption failed: {str(e)}")
            raise EncryptionError(f"Failed to encrypt API credentials: {str(e)}")
    
    def decrypt_api_credentials(self, encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt API credentials.
        
        Args:
            encrypted_credentials: Dictionary with encrypted credentials
            
        Returns:
            Dictionary with decrypted credentials
        """
        try:
            credentials = {
                'api_key': self.decrypt(encrypted_credentials['api_key']),
                'api_secret': self.decrypt(encrypted_credentials['api_secret'])
            }
            
            if 'passphrase' in encrypted_credentials:
                credentials['passphrase'] = self.decrypt(encrypted_credentials['passphrase'])
            
            return credentials
            
        except Exception as e:
            logger.error(f"API credentials decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt API credentials: {str(e)}")
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if a string appears to be encrypted (base64 encoded).
        
        Args:
            data: String to check
            
        Returns:
            True if data appears encrypted, False otherwise
        """
        try:
            if not data:
                return False
            
            # Try to decode as base64
            base64.b64decode(data)
            
            # Check if it looks like Fernet encrypted data
            # Fernet tokens start with specific bytes when base64 decoded
            decoded = base64.b64decode(data.encode('utf-8'))
            return len(decoded) > 16  # Fernet tokens are at least 16 bytes
            
        except Exception:
            return False
    
    def rotate_key(self, new_key: bytes = None) -> bool:
        """
        Rotate the encryption key. This would require re-encrypting all data.
        
        Args:
            new_key: New encryption key (optional, generates one if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if new_key is None:
                new_key = Fernet.generate_key()
            
            # Save the new key
            self._save_key(new_key)
            
            # Update the Fernet instance
            self._fernet = Fernet(new_key)
            
            logger.info("Encryption key rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return False


class EncryptionError(Exception):
    """
    Custom exception for encryption-related errors.
    """
    pass


# Global encryption manager instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance (singleton pattern).
    
    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


# Convenience functions
def encrypt_string(data: str) -> str:
    """
    Encrypt a string using the global encryption manager.
    """
    return get_encryption_manager().encrypt(data)


def decrypt_string(encrypted_data: str) -> str:
    """
    Decrypt a string using the global encryption manager.
    """
    return get_encryption_manager().decrypt(encrypted_data)


def encrypt_api_credentials(api_key: str, api_secret: str, passphrase: str = None) -> Dict[str, str]:
    """
    Encrypt API credentials using the global encryption manager.
    """
    return get_encryption_manager().encrypt_api_credentials(api_key, api_secret, passphrase)


def decrypt_api_credentials(encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
    """
    Decrypt API credentials using the global encryption manager.
    """
    return get_encryption_manager().decrypt_api_credentials(encrypted_credentials)