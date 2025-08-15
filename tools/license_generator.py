#!/usr/bin/env python3
"""
License Generator for TradingBot Pro
Generates and manages software licenses with hardware binding and expiration
"""

import os
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import platform
import uuid
import psutil
import subprocess

class LicenseType:
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    DEVELOPER = "developer"
    LIFETIME = "lifetime"

class LicenseStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"

class LicenseGenerator:
    def __init__(self, master_key: str = None):
        self.master_key = master_key or self._generate_master_key()
        self.cipher_suite = self._initialize_cipher()
        self.private_key, self.public_key = self._generate_rsa_keys()
        
        # License templates
        self.license_templates = {
            LicenseType.TRIAL: {
                'duration_days': 14,
                'max_strategies': 2,
                'max_api_keys': 1,
                'trading_enabled': True,
                'backtesting_enabled': True,
                'advanced_features': False,
                'support_level': 'community'
            },
            LicenseType.BASIC: {
                'duration_days': 30,
                'max_strategies': 5,
                'max_api_keys': 2,
                'trading_enabled': True,
                'backtesting_enabled': True,
                'advanced_features': False,
                'support_level': 'email'
            },
            LicenseType.PRO: {
                'duration_days': 365,
                'max_strategies': 20,
                'max_api_keys': 5,
                'trading_enabled': True,
                'backtesting_enabled': True,
                'advanced_features': True,
                'support_level': 'priority'
            },
            LicenseType.ENTERPRISE: {
                'duration_days': 365,
                'max_strategies': -1,  # Unlimited
                'max_api_keys': -1,    # Unlimited
                'trading_enabled': True,
                'backtesting_enabled': True,
                'advanced_features': True,
                'support_level': 'dedicated'
            },
            LicenseType.LIFETIME: {
                'duration_days': -1,   # Never expires
                'max_strategies': -1,  # Unlimited
                'max_api_keys': -1,    # Unlimited
                'trading_enabled': True,
                'backtesting_enabled': True,
                'advanced_features': True,
                'support_level': 'lifetime'
            }
        }
    
    def _generate_master_key(self) -> str:
        """Generate a master encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize encryption cipher"""
        key = base64.urlsafe_b64decode(self.master_key.encode())
        return Fernet(key)
    
    def _generate_rsa_keys(self):
        """Generate RSA key pair for license signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def get_machine_fingerprint(self) -> str:
        """Generate unique machine fingerprint"""
        try:
            # Collect system information
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'node': platform.node(),
            }
            
            # Add MAC address
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0, 2*6, 2)][::-1])
                system_info['mac'] = mac
            except:
                pass
            
            # Add CPU info
            try:
                system_info['cpu_count'] = psutil.cpu_count()
            except:
                pass
            
            # Add disk serial (Windows)
            try:
                if platform.system() == 'Windows':
                    result = subprocess.run(
                        ['wmic', 'diskdrive', 'get', 'serialnumber'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            system_info['disk_serial'] = lines[1].strip()
            except:
                pass
            
            # Create fingerprint hash
            fingerprint_data = json.dumps(system_info, sort_keys=True)
            fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            return fingerprint_hash[:16]  # Use first 16 characters
            
        except Exception as e:
            # Fallback to basic fingerprint
            fallback_data = f"{platform.platform()}-{platform.node()}-{uuid.getnode()}"
            return hashlib.sha256(fallback_data.encode()).hexdigest()[:16]
    
    def generate_license_key(self) -> str:
        """Generate a unique license key"""
        # Format: XXXX-XXXX-XXXX-XXXX
        key_parts = []
        for _ in range(4):
            part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4))
            key_parts.append(part)
        
        return '-'.join(key_parts)
    
    def create_license(self, 
                      license_type: str,
                      customer_email: str,
                      customer_name: str = None,
                      custom_duration: int = None,
                      custom_features: Dict = None,
                      hardware_binding: bool = True) -> Dict:
        """Create a new license"""
        
        if license_type not in self.license_templates:
            raise ValueError(f"Invalid license type: {license_type}")
        
        # Get template
        template = self.license_templates[license_type].copy()
        
        # Apply custom settings
        if custom_duration:
            template['duration_days'] = custom_duration
        if custom_features:
            template.update(custom_features)
        
        # Generate license data
        license_key = self.generate_license_key()
        issue_date = datetime.utcnow()
        
        # Calculate expiration
        if template['duration_days'] == -1:
            expiration_date = None  # Never expires
        else:
            expiration_date = issue_date + timedelta(days=template['duration_days'])
        
        # Get machine fingerprint if hardware binding is enabled
        machine_fingerprint = self.get_machine_fingerprint() if hardware_binding else None
        
        license_data = {
            'license_key': license_key,
            'license_type': license_type,
            'customer_email': customer_email,
            'customer_name': customer_name,
            'issue_date': issue_date.isoformat(),
            'expiration_date': expiration_date.isoformat() if expiration_date else None,
            'status': LicenseStatus.ACTIVE,
            'machine_fingerprint': machine_fingerprint,
            'features': template,
            'activation_count': 0,
            'max_activations': 1 if hardware_binding else 3,
            'metadata': {
                'generator_version': '1.0',
                'created_by': 'TradingBot Pro License Generator'
            }
        }
        
        # Sign the license
        signature = self._sign_license(license_data)
        license_data['signature'] = signature
        
        # Encrypt the license
        encrypted_license = self._encrypt_license(license_data)
        
        return {
            'license_key': license_key,
            'license_data': license_data,
            'encrypted_license': encrypted_license,
            'public_key': self._serialize_public_key()
        }
    
    def _sign_license(self, license_data: Dict) -> str:
        """Sign license data with RSA private key"""
        # Create signature payload (exclude signature field)
        sign_data = {k: v for k, v in license_data.items() if k != 'signature'}
        payload = json.dumps(sign_data, sort_keys=True).encode()
        
        # Sign with RSA private key
        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode()
    
    def _encrypt_license(self, license_data: Dict) -> str:
        """Encrypt license data"""
        license_json = json.dumps(license_data)
        encrypted_data = self.cipher_suite.encrypt(license_json.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def _serialize_public_key(self) -> str:
        """Serialize public key for distribution"""
        pem = self.public_key.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()
    
    def verify_license(self, encrypted_license: str, public_key_pem: str = None) -> Dict:
        """Verify and decrypt license"""
        try:
            # Decrypt license
            encrypted_data = base64.b64decode(encrypted_license.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data.decode())
            
            # Verify signature
            if public_key_pem:
                public_key = serialization.load_pem_public_key(public_key_pem.encode())
            else:
                public_key = self.public_key
            
            signature = base64.b64decode(license_data['signature'].encode())
            sign_data = {k: v for k, v in license_data.items() if k != 'signature'}
            payload = json.dumps(sign_data, sort_keys=True).encode()
            
            try:
                public_key.verify(
                    signature,
                    payload,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                signature_valid = True
            except:
                signature_valid = False
            
            # Check expiration
            expired = False
            if license_data.get('expiration_date'):
                expiration = datetime.fromisoformat(license_data['expiration_date'])
                expired = datetime.utcnow() > expiration
            
            # Check hardware binding
            hardware_match = True
            if license_data.get('machine_fingerprint'):
                current_fingerprint = self.get_machine_fingerprint()
                hardware_match = license_data['machine_fingerprint'] == current_fingerprint
            
            return {
                'valid': signature_valid and not expired and hardware_match,
                'license_data': license_data,
                'signature_valid': signature_valid,
                'expired': expired,
                'hardware_match': hardware_match,
                'status': license_data.get('status', LicenseStatus.ACTIVE)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'license_data': None
            }
    
    def activate_license(self, license_key: str, encrypted_license: str) -> Dict:
        """Activate a license on current machine"""
        try:
            # Verify license
            verification = self.verify_license(encrypted_license)
            
            if not verification['valid']:
                return {
                    'success': False,
                    'error': 'Invalid license',
                    'details': verification
                }
            
            license_data = verification['license_data']
            
            # Check if license key matches
            if license_data['license_key'] != license_key:
                return {
                    'success': False,
                    'error': 'License key mismatch'
                }
            
            # Check activation count
            if license_data['activation_count'] >= license_data['max_activations']:
                return {
                    'success': False,
                    'error': 'Maximum activations exceeded'
                }
            
            # Update activation count
            license_data['activation_count'] += 1
            license_data['last_activation'] = datetime.utcnow().isoformat()
            license_data['activated_machine'] = self.get_machine_fingerprint()
            
            # Re-encrypt updated license
            updated_license = self._encrypt_license(license_data)
            
            # Save activation info
            activation_info = {
                'license_key': license_key,
                'activation_date': license_data['last_activation'],
                'machine_fingerprint': license_data['activated_machine'],
                'license_type': license_data['license_type'],
                'features': license_data['features']
            }
            
            return {
                'success': True,
                'activation_info': activation_info,
                'updated_license': updated_license
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def revoke_license(self, license_key: str, encrypted_license: str) -> Dict:
        """Revoke a license"""
        try:
            verification = self.verify_license(encrypted_license)
            
            if not verification['valid']:
                return {
                    'success': False,
                    'error': 'Invalid license'
                }
            
            license_data = verification['license_data']
            
            if license_data['license_key'] != license_key:
                return {
                    'success': False,
                    'error': 'License key mismatch'
                }
            
            # Update status
            license_data['status'] = LicenseStatus.REVOKED
            license_data['revocation_date'] = datetime.utcnow().isoformat()
            
            # Re-encrypt
            updated_license = self._encrypt_license(license_data)
            
            return {
                'success': True,
                'message': 'License revoked successfully',
                'updated_license': updated_license
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extend_license(self, license_key: str, encrypted_license: str, additional_days: int) -> Dict:
        """Extend license expiration"""
        try:
            verification = self.verify_license(encrypted_license)
            
            if not verification['valid']:
                return {
                    'success': False,
                    'error': 'Invalid license'
                }
            
            license_data = verification['license_data']
            
            if license_data['license_key'] != license_key:
                return {
                    'success': False,
                    'error': 'License key mismatch'
                }
            
            # Extend expiration
            if license_data.get('expiration_date'):
                current_expiration = datetime.fromisoformat(license_data['expiration_date'])
                new_expiration = current_expiration + timedelta(days=additional_days)
                license_data['expiration_date'] = new_expiration.isoformat()
            else:
                # If no expiration, set one
                new_expiration = datetime.utcnow() + timedelta(days=additional_days)
                license_data['expiration_date'] = new_expiration.isoformat()
            
            license_data['extension_date'] = datetime.utcnow().isoformat()
            license_data['extended_days'] = additional_days
            
            # Re-sign and encrypt
            signature = self._sign_license(license_data)
            license_data['signature'] = signature
            updated_license = self._encrypt_license(license_data)
            
            return {
                'success': True,
                'message': f'License extended by {additional_days} days',
                'new_expiration': license_data['expiration_date'],
                'updated_license': updated_license
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_batch_licenses(self, 
                               license_type: str,
                               count: int,
                               customer_prefix: str = "customer") -> List[Dict]:
        """Generate multiple licenses at once"""
        licenses = []
        
        for i in range(count):
            customer_email = f"{customer_prefix}_{i+1}@example.com"
            customer_name = f"{customer_prefix.title()} {i+1}"
            
            try:
                license_info = self.create_license(
                    license_type=license_type,
                    customer_email=customer_email,
                    customer_name=customer_name,
                    hardware_binding=False  # Batch licenses typically don't use hardware binding
                )
                licenses.append(license_info)
            except Exception as e:
                licenses.append({
                    'error': str(e),
                    'customer_email': customer_email
                })
        
        return licenses
    
    def export_license_info(self, license_data: Dict, format: str = 'json') -> str:
        """Export license information in various formats"""
        if format.lower() == 'json':
            return json.dumps(license_data, indent=2)
        
        elif format.lower() == 'text':
            info = []
            info.append(f"License Key: {license_data['license_key']}")
            info.append(f"Type: {license_data['license_type']}")
            info.append(f"Customer: {license_data['customer_name']} ({license_data['customer_email']})")
            info.append(f"Issue Date: {license_data['issue_date']}")
            info.append(f"Expiration: {license_data['expiration_date'] or 'Never'}")
            info.append(f"Status: {license_data['status']}")
            info.append(f"Hardware Binding: {'Yes' if license_data['machine_fingerprint'] else 'No'}")
            
            features = license_data['features']
            info.append("\nFeatures:")
            info.append(f"  Max Strategies: {features['max_strategies'] if features['max_strategies'] != -1 else 'Unlimited'}")
            info.append(f"  Max API Keys: {features['max_api_keys'] if features['max_api_keys'] != -1 else 'Unlimited'}")
            info.append(f"  Trading: {'Enabled' if features['trading_enabled'] else 'Disabled'}")
            info.append(f"  Backtesting: {'Enabled' if features['backtesting_enabled'] else 'Disabled'}")
            info.append(f"  Advanced Features: {'Enabled' if features['advanced_features'] else 'Disabled'}")
            info.append(f"  Support Level: {features['support_level']}")
            
            return '\n'.join(info)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def save_license_to_file(self, license_info: Dict, filename: str = None):
        """Save license to file"""
        if not filename:
            filename = f"license_{license_info['license_key']}.lic"
        
        license_file_data = {
            'license_key': license_info['license_key'],
            'encrypted_license': license_info['encrypted_license'],
            'public_key': license_info['public_key'],
            'created_date': datetime.utcnow().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(license_file_data, f, indent=2)
        
        return filename
    
    def load_license_from_file(self, filename: str) -> Dict:
        """Load license from file"""
        with open(filename, 'r') as f:
            license_file_data = json.load(f)
        
        return license_file_data

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Pro License Generator')
    parser.add_argument('action', choices=['create', 'verify', 'activate', 'revoke', 'extend', 'batch'])
    parser.add_argument('--type', help='License type')
    parser.add_argument('--email', help='Customer email')
    parser.add_argument('--name', help='Customer name')
    parser.add_argument('--key', help='License key')
    parser.add_argument('--license-file', help='License file path')
    parser.add_argument('--days', type=int, help='Days for extension')
    parser.add_argument('--count', type=int, help='Number of licenses for batch generation')
    parser.add_argument('--output', help='Output file')
    
    args = parser.parse_args()
    
    generator = LicenseGenerator()
    
    if args.action == 'create':
        if not args.type or not args.email:
            print("Type and email are required for license creation")
            exit(1)
        
        license_info = generator.create_license(
            license_type=args.type,
            customer_email=args.email,
            customer_name=args.name
        )
        
        filename = generator.save_license_to_file(license_info, args.output)
        print(f"License created and saved to {filename}")
        print(f"License Key: {license_info['license_key']}")
    
    elif args.action == 'verify':
        if not args.license_file:
            print("License file is required for verification")
            exit(1)
        
        license_data = generator.load_license_from_file(args.license_file)
        verification = generator.verify_license(
            license_data['encrypted_license'],
            license_data['public_key']
        )
        
        print(json.dumps(verification, indent=2))
    
    elif args.action == 'batch':
        if not args.type or not args.count:
            print("Type and count are required for batch generation")
            exit(1)
        
        licenses = generator.generate_batch_licenses(args.type, args.count)
        
        output_file = args.output or f"batch_licenses_{args.type}_{args.count}.json"
        with open(output_file, 'w') as f:
            json.dump(licenses, f, indent=2)
        
        print(f"Generated {len(licenses)} licenses and saved to {output_file}")
    
    else:
        print(f"Action {args.action} not fully implemented in CLI")