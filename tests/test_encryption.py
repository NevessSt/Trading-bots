import pytest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add backend to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from utils.encryption import EncryptionManager, EncryptionError

class TestEncryptionManager:
    """Test suite for EncryptionManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, 'encryption.key')
        
        # Create test encryption manager
        self.manager = EncryptionManager(key_file_path=self.key_file)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_key_generation(self):
        """Test encryption key generation"""
        # Key should be generated automatically
        assert os.path.exists(self.key_file)
        
        # Key file should contain Fernet key
        with open(self.key_file, 'rb') as f:
            key_data = f.read()
        
        assert len(key_data) > 0
        
        # Should be a valid Fernet key (44 bytes when base64 encoded)
        try:
            from cryptography.fernet import Fernet
            # Try to create a Fernet instance with the key
            Fernet(key_data)
            assert len(key_data) == 44  # Fernet keys are 44 bytes when base64 encoded
        except Exception:
            pytest.fail("Key file does not contain valid Fernet key")
    
    def test_string_encryption_decryption(self):
        """Test basic string encryption and decryption"""
        test_string = "This is a test string with special chars: !@#$%^&*()"
        
        # Encrypt
        encrypted = self.manager.encrypt(test_string)
        assert encrypted != test_string
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = self.manager.decrypt(encrypted)
        assert decrypted == test_string
    
    def test_empty_string_encryption(self):
        """Test encryption of empty string"""
        empty_string = ""
        
        encrypted = self.manager.encrypt(empty_string)
        decrypted = self.manager.decrypt(encrypted)
        
        assert decrypted == empty_string
    
    def test_unicode_string_encryption(self):
        """Test encryption of unicode strings"""
        unicode_string = "Hello 世界 🌍 émojis and ñoñó"
        
        encrypted = self.manager.encrypt(unicode_string)
        decrypted = self.manager.decrypt(encrypted)
        
        assert decrypted == unicode_string
    
    def test_dictionary_encryption_decryption(self):
        """Test dictionary encryption and decryption"""
        test_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'nested': {
                'inner_key': 'inner_value'
            }
        }
        
        # Encrypt the dictionary
        encrypted = self.manager.encrypt_dict(test_dict)
        assert encrypted != str(test_dict)
        assert isinstance(encrypted, str)
        
        # Decrypt the dictionary
        decrypted = self.manager.decrypt_dict(encrypted)
        assert decrypted == test_dict
    
    def test_api_credentials_encryption(self):
        """Test API credentials encryption with passphrase"""
        api_key = 'test_api_key_12345'
        api_secret = 'test_secret_67890'
        passphrase = 'test_passphrase'
        
        # Encrypt API credentials
        encrypted = self.manager.encrypt_api_credentials(api_key, api_secret, passphrase)
        assert isinstance(encrypted, dict)
        assert 'api_key' in encrypted
        assert 'api_secret' in encrypted
        assert 'passphrase' in encrypted
        
        # All values should be encrypted (different from original)
        assert encrypted['api_key'] != api_key
        assert encrypted['api_secret'] != api_secret
        assert encrypted['passphrase'] != passphrase
        
        # Decrypt API credentials
        decrypted = self.manager.decrypt_api_credentials(encrypted)
        expected = {
            'api_key': api_key,
            'api_secret': api_secret,
            'passphrase': passphrase
        }
        assert decrypted == expected
    
    def test_api_credentials_without_passphrase(self):
        """Test API credentials encryption without passphrase"""
        api_key = 'binance_api_key_123'
        api_secret = 'binance_secret_456'
        
        # Encrypt API credentials without passphrase
        encrypted = self.manager.encrypt_api_credentials(api_key, api_secret)
        assert isinstance(encrypted, dict)
        assert 'api_key' in encrypted
        assert 'api_secret' in encrypted
        assert 'passphrase' not in encrypted
        
        # Decrypt API credentials
        decrypted = self.manager.decrypt_api_credentials(encrypted)
        expected = {
            'api_key': api_key,
            'api_secret': api_secret
        }
        assert decrypted == expected
    
    def test_invalid_encrypted_data(self):
        """Test handling of invalid encrypted data"""
        invalid_data = "this_is_not_encrypted_data"
        
        with pytest.raises(EncryptionError):
            self.manager.decrypt(invalid_data)
        
        with pytest.raises(EncryptionError):
            self.manager.decrypt_dict(invalid_data)
    
    def test_corrupted_encrypted_data(self):
        """Test handling of corrupted encrypted data"""
        # Create valid encrypted data first
        test_string = "test data"
        encrypted = self.manager.encrypt(test_string)
        
        # Corrupt the data
        corrupted = encrypted[:-5] + "xxxxx"
        
        with pytest.raises(EncryptionError):
            self.manager.decrypt(corrupted)
    
    def test_key_persistence(self):
        """Test that encryption key persists across instances"""
        test_string = "persistence test"
        
        # Encrypt with first instance
        encrypted = self.manager.encrypt(test_string)
        
        # Create new instance with same key file
        new_manager = EncryptionManager(key_file_path=self.key_file)
        
        # Should be able to decrypt with new instance
        decrypted = new_manager.decrypt(encrypted)
        assert decrypted == test_string
    
    def test_different_keys_incompatible(self):
        """Test that data encrypted with one key cannot be decrypted with another"""
        test_string = "incompatibility test"
        
        # Encrypt with first manager
        encrypted = self.manager.encrypt(test_string)
        
        # Create manager with different key file
        different_key_file = os.path.join(self.temp_dir, 'different.key')
        different_manager = EncryptionManager(key_file_path=different_key_file)
        
        # Should not be able to decrypt
        with pytest.raises(EncryptionError):
            different_manager.decrypt(encrypted)
    
    def test_large_data_encryption(self):
        """Test encryption of large data"""
        # Create large string (1MB)
        large_string = "A" * (1024 * 1024)
        
        encrypted = self.manager.encrypt(large_string)
        decrypted = self.manager.decrypt(encrypted)
        
        assert decrypted == large_string
    
    def test_special_characters_in_credentials(self):
        """Test API credentials with special characters"""
        credentials = {
            'api_key': 'key_with_special_chars_!@#$%^&*()',
            'api_secret': 'secret/with+slashes=and+plus',
            'passphrase': 'phrase with spaces and émojis 🔑'
        }
        
        encrypted = self.manager.encrypt_api_credentials(
            credentials['api_key'], 
            credentials['api_secret'], 
            credentials['passphrase']
        )
        decrypted = self.manager.decrypt_api_credentials(encrypted)
        
        assert decrypted == credentials
    
    def test_none_values_handling(self):
        """Test handling of None and empty values"""
        # Should handle empty string gracefully
        encrypted_empty = self.manager.encrypt('')
        assert encrypted_empty == ''
        
        decrypted_empty = self.manager.decrypt('')
        assert decrypted_empty == ''
    
    def test_global_encryption_manager(self):
        """Test that encryption manager works consistently"""
        # Test encryption/decryption consistency
        test_data = "global test data"
        encrypted = self.manager.encrypt(test_data)
        decrypted = self.manager.decrypt(encrypted)
        assert decrypted == test_data

if __name__ == '__main__':
    pytest.main([__file__])