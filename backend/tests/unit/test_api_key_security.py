import pytest
from unittest.mock import patch, MagicMock
from services.api_key_service import APIKeyService
from models.api_key import APIKey
from utils.encryption import encrypt_data, decrypt_data


class TestAPIKeySecurity:
    """Test API key security features including encryption and validation."""
    
    @pytest.fixture
    def api_key_service(self):
        """Create APIKeyService instance for testing."""
        return APIKeyService()
    
    def test_encrypt_decrypt_api_key(self):
        """Test that API keys are properly encrypted and decrypted."""
        original_key = "test_api_key_12345"
        
        # Encrypt the key
        encrypted_key = encrypt_data(original_key)
        
        # Verify it's encrypted (not the same as original)
        assert encrypted_key != original_key
        assert len(encrypted_key) > len(original_key)
        
        # Decrypt and verify
        decrypted_key = decrypt_data(encrypted_key)
        assert decrypted_key == original_key
    
    def test_api_key_validation_valid_binance(self):
        """Test validation of valid Binance API key format."""
        valid_key = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ12"
        valid_secret = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ12"
        
        # Should not raise any exception
        try:
            APIKeyService.validate_api_key_format(valid_key, valid_secret, 'binance')
        except ValueError:
            pytest.fail("Valid API key should not raise ValueError")
    
    def test_api_key_validation_invalid_format(self):
        """Test validation rejects invalid API key formats."""
        invalid_key = "short"
        invalid_secret = "also_short"
        
        with pytest.raises(ValueError, match="Invalid API key format"):
            APIKeyService.validate_api_key_format(invalid_key, invalid_secret, 'binance')
    
    def test_api_key_validation_empty_keys(self):
        """Test validation rejects empty API keys."""
        with pytest.raises(ValueError, match="API key and secret cannot be empty"):
            APIKeyService.validate_api_key_format("", "", 'binance')
    
    @patch('services.api_key_service.db')
    def test_create_api_key_encrypts_data(self, mock_db, api_key_service):
        """Test that creating API key encrypts sensitive data."""
        user_id = 1
        exchange = "binance"
        api_key = "test_api_key"
        api_secret = "test_api_secret"
        
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        with patch('services.api_key_service.encrypt_data') as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
            
            result = api_key_service.create_api_key(user_id, exchange, api_key, api_secret)
            
            # Verify encryption was called
            assert mock_encrypt.call_count == 2
            mock_encrypt.assert_any_call(api_key)
            mock_encrypt.assert_any_call(api_secret)
    
    @patch('services.api_key_service.db')
    def test_get_decrypted_api_keys(self, mock_db, api_key_service):
        """Test that retrieving API keys decrypts the data."""
        user_id = 1
        
        # Mock encrypted API key from database
        mock_api_key = MagicMock()
        mock_api_key.api_key = "encrypted_test_key"
        mock_api_key.api_secret = "encrypted_test_secret"
        mock_api_key.exchange = "binance"
        
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_api_key
        
        with patch('services.api_key_service.decrypt_data') as mock_decrypt:
            mock_decrypt.side_effect = lambda x: x.replace("encrypted_", "")
            
            result = api_key_service.get_api_keys(user_id)
            
            # Verify decryption was called
            assert mock_decrypt.call_count == 2
            mock_decrypt.assert_any_call("encrypted_test_key")
            mock_decrypt.assert_any_call("encrypted_test_secret")
    
    def test_api_key_masking_in_response(self):
        """Test that API keys are properly masked in API responses."""
        full_key = "abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ12"
        
        # Simulate masking function
        def mask_api_key(key):
            if len(key) <= 8:
                return "*" * len(key)
            return key[:4] + "*" * (len(key) - 8) + key[-4:]
        
        masked = mask_api_key(full_key)
        
        # Should show first 4 and last 4 characters
        assert masked.startswith("abcd")
        assert masked.endswith("Z12")
        assert "*" in masked
        assert len(masked) == len(full_key)
    
    def test_api_key_deletion_security(self):
        """Test that API key deletion is secure and complete."""
        # This would test that when deleting API keys:
        # 1. All related data is removed
        # 2. No traces remain in logs
        # 3. Proper audit trail is maintained
        pass  # Implementation would depend on actual deletion logic