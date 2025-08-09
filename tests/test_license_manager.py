import pytest
import os
import tempfile
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add backend to path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from auth.license_manager import LicenseManager, LicenseError, generate_test_license

class TestLicenseManager:
    """Test suite for LicenseManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.license_file = os.path.join(self.temp_dir, 'license.json')
        self.manager = LicenseManager(license_file_path=self.license_file)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test LicenseManager initialization."""
        assert self.manager.license_file_path == self.license_file
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
        assert license_info.get('error') == 'No license found'
    
    def test_generate_test_license(self):
        """Test generating a test license."""
        license_key = generate_test_license(
            user_email="test@example.com",
            days_valid=30
        )
        
        assert license_key is not None
        assert isinstance(license_key, str)
        assert len(license_key) > 0
        
        # Verify the license key can be decoded
        license_data_json = base64.b64decode(license_key).decode('utf-8')
        license_data = json.loads(license_data_json)
        assert license_data['user_email'] == "test@example.com"
        assert 'signature' in license_data
    
    def test_activate_license_success(self):
        """Test successful license activation."""
        # Generate a valid test license
        license_key = generate_test_license(
            user_email='test@example.com',
            days_valid=30
        )
        
        result = self.manager.activate_license(
            license_key=license_key,
            user_email='test@example.com'
        )
        
        assert result['success'] is True
        assert 'license_id' in result
        assert 'expiry_date' in result
        assert 'features' in result
        
        # Verify license is now activated
        license_info = self.manager.get_license_info()
        assert license_info.get('valid') is True
        assert license_info.get('user_email') == 'test@example.com'
    
    def test_activate_license_invalid(self):
        """Test activation with invalid license key."""
        result = self.manager.activate_license(
            license_key='invalid-key',
            user_email='test@example.com'
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert result['error'] == 'Invalid license key format'
        
        # Verify license is still not activated
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
    
    def test_offline_license_validation(self):
        """Test offline license validation."""
        # First activate a license
        license_key = generate_test_license(
            user_email='test@example.com',
            days_valid=30
        )
        
        result = self.manager.activate_license(
            license_key=license_key,
            user_email='test@example.com'
        )
        assert result['success'] is True
        
        # Test offline validation
        license_info = self.manager.validate_license()
        assert license_info.get('valid') is True
        assert license_info.get('user_email') == 'test@example.com'
        assert 'features' in license_info
        
        # Test feature checking
        assert self.manager.has_feature('live_trading')
        assert self.manager.has_feature('backtesting')
        assert not self.manager.has_feature('nonexistent_feature')
    
    def test_expired_license(self):
        """Test handling of expired license."""
        # Generate an expired test license
        license_key = generate_test_license(
            user_email='test@example.com',
            days_valid=-1  # Expired license
        )
        
        result = self.manager.activate_license(
            license_key=license_key,
            user_email='test@example.com'
        )
        
        assert result['success'] is False
        assert 'expired' in result['error'].lower()
        
        # Verify license is not activated
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
        assert not self.manager.has_feature('live_trading')
    
    def test_deactivate_license(self):
        """Test license deactivation."""
        # First activate a license
        license_key = generate_test_license(
            user_email='test@example.com',
            days_valid=30
        )
        
        result = self.manager.activate_license(
            license_key=license_key,
            user_email='test@example.com'
        )
        assert result['success'] is True
        
        # Verify license is activated
        license_info = self.manager.get_license_info()
        assert license_info.get('valid') is True
        
        # Deactivate the license
        result = self.manager.deactivate_license()
        assert result is True
        
        # Verify license is deactivated
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
    
    def test_get_license_info(self):
        """Test getting license information."""
        # First activate a license
        license_key = generate_test_license(
            user_email='test@example.com',
            days_valid=30
        )
        
        result = self.manager.activate_license(
            license_key=license_key,
            user_email='test@example.com'
        )
        assert result['success'] is True
        
        # Get license info
        info = self.manager.get_license_info()
        
        assert info.get('valid') is True
        assert info.get('user_email') == 'test@example.com'
        assert 'license_id' in info
        assert 'expiry_date' in info
        assert 'features' in info
        assert 'days_remaining' in info
    
    def test_demo_mode_features(self):
        """Test demo mode functionality."""
        # Without any license, should not be valid
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
        assert license_info.get('error') == 'No license found'
        
        # Demo mode should have no features
        assert not self.manager.has_feature('live_trading')
        assert not self.manager.has_feature('backtesting')
    
    def test_corrupted_license_file(self):
        """Test handling of corrupted license file."""
        # Create a corrupted license file
        with open(self.license_file, 'w') as f:
            f.write('invalid json content')
        
        # Should handle gracefully and return no license found
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)
        assert 'error' in license_info
    
    def test_network_error_handling(self):
        """Test handling of network errors during activation."""
        # Test with malformed license key that would cause an exception
        result = self.manager.activate_license(
            license_key='malformed-base64-!@#$%',
            user_email='test@example.com'
        )
        
        assert result['success'] is False
        assert 'error' in result
        
        # Verify license is not activated
        license_info = self.manager.get_license_info()
        assert not license_info.get('valid', False)

if __name__ == '__main__':
    pytest.main([__file__])