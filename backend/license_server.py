#!/usr/bin/env python3
"""
License Server - Remote License Management
Provides remote license validation, revocation, and management capabilities.
"""

import hashlib
import hmac
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LicenseServer:
    """Remote license management server"""
    
    def __init__(self, db_path: str = "license_server.db", secret_key: str = None):
        self.db_path = db_path
        self.secret_key = secret_key or os.environ.get('LICENSE_SERVER_SECRET', 'default-license-secret')
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the license database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    license_key TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    revoked_at TEXT NULL,
                    revoked_reason TEXT NULL,
                    last_check TEXT NULL,
                    check_count INTEGER DEFAULT 0,
                    features TEXT NOT NULL,
                    metadata TEXT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS revocation_list (
                    license_key TEXT PRIMARY KEY,
                    revoked_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    revoked_by TEXT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS license_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    check_time TEXT NOT NULL,
                    ip_address TEXT NULL,
                    user_agent TEXT NULL,
                    status TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def generate_license_key(self, machine_id: str, license_type: str, 
                           days_valid: int = 365, features: List[str] = None) -> str:
        """Generate a new license key"""
        if features is None:
            features = ['basic_trading', 'risk_management', 'market_data']
        
        license_data = {
            'machine_id': machine_id,
            'license_type': license_type,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=days_valid)).isoformat(),
            'features': features,
            'version': '1.0'
        }
        
        # Create license key from data
        license_json = json.dumps(license_data, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            license_json.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        license_key = f"{license_json}|{signature}"
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO licenses 
                (license_key, machine_id, license_type, created_at, expires_at, features)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                license_key,
                machine_id,
                license_type,
                license_data['created_at'],
                license_data['expires_at'],
                json.dumps(features)
            ))
            conn.commit()
        
        return license_key
    
    def validate_license_remote(self, license_key: str, machine_id: str, 
                              ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Validate license remotely and check revocation status"""
        try:
            # Parse license key
            if '|' not in license_key:
                return False, "Invalid license key format", None
            
            license_json, signature = license_key.rsplit('|', 1)
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                license_json.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid license signature", None
            
            # Parse license data
            license_data = json.loads(license_json)
            
            # Check if license exists in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM licenses WHERE license_key = ?",
                    (license_key,)
                )
                db_license = cursor.fetchone()
                
                if not db_license:
                    return False, "License not found in database", None
                
                # Check if license is active
                if not db_license[5]:  # is_active column
                    return False, "License has been deactivated", None
                
                # Check revocation list
                cursor = conn.execute(
                    "SELECT * FROM revocation_list WHERE license_key = ?",
                    (license_key,)
                )
                revoked = cursor.fetchone()
                
                if revoked:
                    return False, f"License revoked: {revoked[2]}", None
            
            # Validate machine ID
            if license_data['machine_id'] != machine_id:
                self._log_license_check(license_key, machine_id, ip_address, "MACHINE_MISMATCH")
                return False, "License not valid for this machine", None
            
            # Check expiration
            expires_at = datetime.fromisoformat(license_data['expires_at'])
            if datetime.utcnow() > expires_at:
                self._log_license_check(license_key, machine_id, ip_address, "EXPIRED")
                return False, "License has expired", None
            
            # Update last check time
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE licenses 
                    SET last_check = ?, check_count = check_count + 1
                    WHERE license_key = ?
                """, (datetime.utcnow().isoformat(), license_key))
                conn.commit()
            
            # Log successful check
            self._log_license_check(license_key, machine_id, ip_address, "VALID")
            
            return True, "License is valid", license_data
            
        except Exception as e:
            logger.error(f"License validation error: {e}")
            return False, f"Validation error: {str(e)}", None
    
    def revoke_license(self, license_key: str, reason: str, revoked_by: str = None) -> bool:
        """Revoke a license"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Add to revocation list
                conn.execute("""
                    INSERT OR REPLACE INTO revocation_list 
                    (license_key, revoked_at, reason, revoked_by)
                    VALUES (?, ?, ?, ?)
                """, (
                    license_key,
                    datetime.utcnow().isoformat(),
                    reason,
                    revoked_by
                ))
                
                # Update license status
                conn.execute("""
                    UPDATE licenses 
                    SET is_active = 0, revoked_at = ?, revoked_reason = ?
                    WHERE license_key = ?
                """, (
                    datetime.utcnow().isoformat(),
                    reason,
                    license_key
                ))
                
                conn.commit()
                
            logger.info(f"License revoked: {license_key[:20]}... Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking license: {e}")
            return False
    
    def get_revocation_list(self) -> List[Dict]:
        """Get list of revoked licenses"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT license_key, revoked_at, reason, revoked_by
                    FROM revocation_list
                    ORDER BY revoked_at DESC
                """)
                
                revoked_licenses = []
                for row in cursor.fetchall():
                    revoked_licenses.append({
                        'license_key': row[0][:20] + '...',  # Truncate for security
                        'revoked_at': row[1],
                        'reason': row[2],
                        'revoked_by': row[3]
                    })
                
                return revoked_licenses
                
        except Exception as e:
            logger.error(f"Error getting revocation list: {e}")
            return []
    
    def get_license_stats(self) -> Dict:
        """Get license statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total licenses
                cursor = conn.execute("SELECT COUNT(*) FROM licenses")
                total_licenses = cursor.fetchone()[0]
                
                # Active licenses
                cursor = conn.execute("SELECT COUNT(*) FROM licenses WHERE is_active = 1")
                active_licenses = cursor.fetchone()[0]
                
                # Revoked licenses
                cursor = conn.execute("SELECT COUNT(*) FROM revocation_list")
                revoked_licenses = cursor.fetchone()[0]
                
                # Expired licenses
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM licenses 
                    WHERE expires_at < ? AND is_active = 1
                """, (datetime.utcnow().isoformat(),))
                expired_licenses = cursor.fetchone()[0]
                
                # Recent checks (last 24 hours)
                yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM license_checks 
                    WHERE check_time > ?
                """, (yesterday,))
                recent_checks = cursor.fetchone()[0]
                
                return {
                    'total_licenses': total_licenses,
                    'active_licenses': active_licenses,
                    'revoked_licenses': revoked_licenses,
                    'expired_licenses': expired_licenses,
                    'recent_checks': recent_checks,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting license stats: {e}")
            return {}
    
    def _log_license_check(self, license_key: str, machine_id: str, 
                          ip_address: str, status: str):
        """Log license check attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO license_checks 
                    (license_key, machine_id, check_time, ip_address, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    license_key,
                    machine_id,
                    datetime.utcnow().isoformat(),
                    ip_address,
                    status
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging license check: {e}")

# Flask application for license server
app = Flask(__name__)
license_server = LicenseServer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0'
    })

@app.route('/validate', methods=['POST'])
def validate_license():
    """Validate license endpoint"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        machine_id = data.get('machine_id')
        
        if not license_key or not machine_id:
            return jsonify({
                'valid': False,
                'message': 'Missing license_key or machine_id'
            }), 400
        
        ip_address = request.remote_addr
        is_valid, message, license_data = license_server.validate_license_remote(
            license_key, machine_id, ip_address
        )
        
        response = {
            'valid': is_valid,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if is_valid and license_data:
            response['license_data'] = {
                'license_type': license_data.get('license_type'),
                'expires_at': license_data.get('expires_at'),
                'features': license_data.get('features', [])
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Validation endpoint error: {e}")
        return jsonify({
            'valid': False,
            'message': 'Internal server error'
        }), 500

@app.route('/revoke', methods=['POST'])
def revoke_license():
    """Revoke license endpoint (admin only)"""
    try:
        # Simple API key authentication (replace with proper auth)
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('LICENSE_ADMIN_KEY', 'admin-key-123'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        license_key = data.get('license_key')
        reason = data.get('reason', 'No reason provided')
        revoked_by = data.get('revoked_by', 'API')
        
        if not license_key:
            return jsonify({'error': 'Missing license_key'}), 400
        
        success = license_server.revoke_license(license_key, reason, revoked_by)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'License revoked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to revoke license'
            }), 500
            
    except Exception as e:
        logger.error(f"Revoke endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/revocation-list', methods=['GET'])
def get_revocation_list():
    """Get revocation list endpoint"""
    try:
        revoked_licenses = license_server.get_revocation_list()
        return jsonify({
            'revoked_licenses': revoked_licenses,
            'count': len(revoked_licenses),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Revocation list endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get license statistics endpoint"""
    try:
        stats = license_server.get_license_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/generate', methods=['POST'])
def generate_license():
    """Generate new license endpoint (admin only)"""
    try:
        # Simple API key authentication
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('LICENSE_ADMIN_KEY', 'admin-key-123'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        machine_id = data.get('machine_id')
        license_type = data.get('license_type', 'standard')
        days_valid = data.get('days_valid', 365)
        features = data.get('features')
        
        if not machine_id:
            return jsonify({'error': 'Missing machine_id'}), 400
        
        license_key = license_server.generate_license_key(
            machine_id, license_type, days_valid, features
        )
        
        return jsonify({
            'success': True,
            'license_key': license_key,
            'machine_id': machine_id,
            'license_type': license_type,
            'expires_in_days': days_valid
        })
        
    except Exception as e:
        logger.error(f"Generate endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the license server
    port = int(os.environ.get('LICENSE_SERVER_PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting License Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)