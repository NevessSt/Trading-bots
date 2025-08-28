#!/usr/bin/env python3
"""
License Administration Tool
Provides command-line interface for managing licenses and revocations.
"""

import argparse
import json
import os
import requests
import sys
from datetime import datetime
from typing import Dict, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from license_server import LicenseServer

class LicenseAdmin:
    """License administration interface"""
    
    def __init__(self, server_url: str = None, api_key: str = None):
        self.server_url = server_url or os.environ.get('LICENSE_SERVER_URL', 'http://localhost:8080')
        self.api_key = api_key or os.environ.get('LICENSE_ADMIN_KEY', 'admin-key-123')
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def generate_license(self, machine_id: str, license_type: str = 'standard', 
                        days_valid: int = 365, features: List[str] = None) -> Dict:
        """Generate a new license"""
        if features is None:
            features = ['basic_trading', 'risk_management', 'market_data']
        
        payload = {
            'machine_id': machine_id,
            'license_type': license_type,
            'days_valid': days_valid,
            'features': features
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/generate",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def revoke_license(self, license_key: str, reason: str, revoked_by: str = None) -> Dict:
        """Revoke a license"""
        payload = {
            'license_key': license_key,
            'reason': reason,
            'revoked_by': revoked_by or 'admin-cli'
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/revoke",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_revocation_list(self) -> Dict:
        """Get list of revoked licenses"""
        try:
            response = requests.get(
                f"{self.server_url}/revocation-list",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_license_stats(self) -> Dict:
        """Get license statistics"""
        try:
            response = requests.get(
                f"{self.server_url}/stats",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_license(self, license_key: str, machine_id: str) -> Dict:
        """Validate a license"""
        payload = {
            'license_key': license_key,
            'machine_id': machine_id
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/validate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'valid': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def health_check(self) -> Dict:
        """Check license server health"""
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'status': 'unreachable',
                'error': str(e)
            }

def main():
    parser = argparse.ArgumentParser(description='License Administration Tool')
    parser.add_argument('--server-url', help='License server URL')
    parser.add_argument('--api-key', help='Admin API key')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate license command
    gen_parser = subparsers.add_parser('generate', help='Generate a new license')
    gen_parser.add_argument('machine_id', help='Machine ID for the license')
    gen_parser.add_argument('--type', default='standard', choices=['trial', 'standard', 'premium', 'enterprise'],
                           help='License type (default: standard)')
    gen_parser.add_argument('--days', type=int, default=365, help='Days valid (default: 365)')
    gen_parser.add_argument('--features', nargs='+', help='License features')
    
    # Revoke license command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke a license')
    revoke_parser.add_argument('license_key', help='License key to revoke')
    revoke_parser.add_argument('reason', help='Reason for revocation')
    revoke_parser.add_argument('--revoked-by', help='Who is revoking the license')
    
    # Validate license command
    validate_parser = subparsers.add_parser('validate', help='Validate a license')
    validate_parser.add_argument('license_key', help='License key to validate')
    validate_parser.add_argument('machine_id', help='Machine ID to validate against')
    
    # List revoked licenses command
    subparsers.add_parser('list-revoked', help='List revoked licenses')
    
    # Get statistics command
    subparsers.add_parser('stats', help='Get license statistics')
    
    # Health check command
    subparsers.add_parser('health', help='Check license server health')
    
    # Start local server command
    server_parser = subparsers.add_parser('start-server', help='Start local license server')
    server_parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    server_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle local server start
    if args.command == 'start-server':
        print(f"Starting license server on port {args.port}...")
        os.environ['LICENSE_SERVER_PORT'] = str(args.port)
        if args.debug:
            os.environ['FLASK_DEBUG'] = 'true'
        
        # Import and run the server
        from license_server import app
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
        return
    
    # Initialize admin client
    admin = LicenseAdmin(args.server_url, args.api_key)
    
    # Execute commands
    if args.command == 'generate':
        result = admin.generate_license(
            args.machine_id,
            args.type,
            args.days,
            args.features
        )
        
        if result.get('success'):
            print("✅ License generated successfully!")
            print(f"License Key: {result['license_key']}")
            print(f"Machine ID: {result['machine_id']}")
            print(f"License Type: {result['license_type']}")
            print(f"Expires in: {result['expires_in_days']} days")
        else:
            print(f"❌ Failed to generate license: {result.get('error')}")
    
    elif args.command == 'revoke':
        result = admin.revoke_license(args.license_key, args.reason, args.revoked_by)
        
        if result.get('success'):
            print("✅ License revoked successfully!")
            print(f"Message: {result['message']}")
        else:
            print(f"❌ Failed to revoke license: {result.get('error')}")
    
    elif args.command == 'validate':
        result = admin.validate_license(args.license_key, args.machine_id)
        
        if result.get('valid'):
            print("✅ License is valid!")
            print(f"Message: {result['message']}")
            if 'license_data' in result:
                data = result['license_data']
                print(f"License Type: {data.get('license_type')}")
                print(f"Expires At: {data.get('expires_at')}")
                print(f"Features: {', '.join(data.get('features', []))}")
        else:
            print("❌ License is invalid!")
            print(f"Reason: {result.get('message', result.get('error'))}")
    
    elif args.command == 'list-revoked':
        result = admin.get_revocation_list()
        
        if 'revoked_licenses' in result:
            revoked = result['revoked_licenses']
            print(f"📋 Found {result['count']} revoked licenses:")
            print()
            
            for license_info in revoked:
                print(f"License: {license_info['license_key']}")
                print(f"Revoked: {license_info['revoked_at']}")
                print(f"Reason: {license_info['reason']}")
                print(f"By: {license_info.get('revoked_by', 'Unknown')}")
                print("-" * 50)
        else:
            print(f"❌ Failed to get revocation list: {result.get('error')}")
    
    elif args.command == 'stats':
        result = admin.get_license_stats()
        
        if 'total_licenses' in result:
            print("📊 License Statistics:")
            print(f"Total Licenses: {result['total_licenses']}")
            print(f"Active Licenses: {result['active_licenses']}")
            print(f"Revoked Licenses: {result['revoked_licenses']}")
            print(f"Expired Licenses: {result['expired_licenses']}")
            print(f"Recent Checks (24h): {result['recent_checks']}")
            print(f"Last Updated: {result['last_updated']}")
        else:
            print(f"❌ Failed to get statistics: {result.get('error')}")
    
    elif args.command == 'health':
        result = admin.health_check()
        
        if result.get('status') == 'healthy':
            print("✅ License server is healthy!")
            print(f"Version: {result.get('version')}")
            print(f"Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ License server is {result.get('status', 'unknown')}")
            if 'error' in result:
                print(f"Error: {result['error']}")

if __name__ == '__main__':
    main()