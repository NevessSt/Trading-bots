#!/usr/bin/env python3
"""
Tenant Middleware for Flask Applications
Handles tenant identification, routing, and context management.
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from flask import Flask, request, g, jsonify, abort
from functools import wraps

from .tenant_manager import TenantManager, tenant_context, TenantStatus
from .billing import BillingManager

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """Flask middleware for multi-tenant support"""
    
    def __init__(self, app: Flask = None, tenant_manager: TenantManager = None):
        self.tenant_manager = tenant_manager or TenantManager()
        self.billing_manager = BillingManager()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_appcontext)
        
        # Add tenant-aware error handlers
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        
        logger.info("TenantMiddleware initialized")
    
    def before_request(self):
        """Process request before routing"""
        # Skip tenant resolution for certain paths
        if self._should_skip_tenant_resolution():
            return
        
        # Identify tenant
        tenant_id = self._identify_tenant()
        if not tenant_id:
            return jsonify({"error": "Tenant not found"}), 404
        
        # Get tenant configuration
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        # Check tenant status
        if tenant.status != TenantStatus.ACTIVE.value:
            if tenant.status == TenantStatus.SUSPENDED.value:
                return jsonify({"error": "Tenant suspended"}), 403
            elif tenant.status == TenantStatus.INACTIVE.value:
                return jsonify({"error": "Tenant inactive"}), 403
        
        # Set tenant context
        tenant_config = self.tenant_manager.get_tenant_config(tenant_id)
        tenant_context.set_tenant(tenant_id, tenant_config)
        
        # Store in Flask's g object for easy access
        g.tenant_id = tenant_id
        g.tenant = tenant
        g.tenant_config = tenant_config
        
        # Check rate limits
        if not self._check_rate_limits(tenant_config):
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        # Record usage
        self.tenant_manager.record_tenant_usage(tenant_id, "api_requests", 1)
    
    def after_request(self, response):
        """Process response after request"""
        # Add tenant-specific headers
        if hasattr(g, 'tenant_id'):
            response.headers['X-Tenant-ID'] = g.tenant_id
        
        return response
    
    def teardown_appcontext(self, exception):
        """Clean up tenant context"""
        tenant_context.clear()
    
    def _should_skip_tenant_resolution(self) -> bool:
        """Check if tenant resolution should be skipped for this request"""
        skip_paths = [
            '/health',
            '/metrics',
            '/api/billing/webhook',  # Stripe webhooks
            '/api/admin',            # Admin endpoints
            '/static',               # Static files
            '/favicon.ico'
        ]
        
        path = request.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _identify_tenant(self) -> Optional[str]:
        """Identify tenant from request"""
        # Method 1: Subdomain-based routing
        tenant_id = self._get_tenant_from_subdomain()
        if tenant_id:
            return tenant_id
        
        # Method 2: Custom domain routing
        tenant_id = self._get_tenant_from_domain()
        if tenant_id:
            return tenant_id
        
        # Method 3: Header-based routing
        tenant_id = self._get_tenant_from_header()
        if tenant_id:
            return tenant_id
        
        # Method 4: Path-based routing
        tenant_id = self._get_tenant_from_path()
        if tenant_id:
            return tenant_id
        
        return None
    
    def _get_tenant_from_subdomain(self) -> Optional[str]:
        """Extract tenant ID from subdomain"""
        host = request.headers.get('Host', '')
        if not host:
            return None
        
        # Parse subdomain (e.g., tenant1.tradingbot.com -> tenant1)
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.tld
            subdomain = parts[0]
            
            # Skip common subdomains
            if subdomain in ['www', 'api', 'admin', 'app']:
                return None
            
            return subdomain
        
        return None
    
    def _get_tenant_from_domain(self) -> Optional[str]:
        """Extract tenant ID from custom domain"""
        host = request.headers.get('Host', '')
        if not host:
            return None
        
        # Look up tenant by domain
        tenant = self.tenant_manager.get_tenant_by_domain(host)
        return tenant.tenant_id if tenant else None
    
    def _get_tenant_from_header(self) -> Optional[str]:
        """Extract tenant ID from custom header"""
        return request.headers.get('X-Tenant-ID')
    
    def _get_tenant_from_path(self) -> Optional[str]:
        """Extract tenant ID from URL path"""
        # Pattern: /tenant/{tenant_id}/...
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'tenant':
            return path_parts[1]
        
        return None
    
    def _check_rate_limits(self, tenant_config) -> bool:
        """Check if request is within rate limits"""
        if not tenant_config or not tenant_config.api_rate_limits:
            return True
        
        # This is a simplified rate limiting check
        # In production, you'd use Redis or similar for distributed rate limiting
        
        # For now, just log the rate limit check
        logger.debug(f"Rate limit check for tenant {tenant_config.tenant_id}")
        return True
    
    def handle_forbidden(self, error):
        """Handle 403 errors with tenant context"""
        return jsonify({
            "error": "Forbidden",
            "message": "Access denied for this tenant",
            "tenant_id": getattr(g, 'tenant_id', None)
        }), 403
    
    def handle_not_found(self, error):
        """Handle 404 errors with tenant context"""
        return jsonify({
            "error": "Not Found",
            "message": "Resource not found",
            "tenant_id": getattr(g, 'tenant_id', None)
        }), 404

# Decorators for tenant-aware routes
def require_tenant(f):
    """Decorator to ensure tenant context is available"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id'):
            abort(400, description="Tenant context required")
        return f(*args, **kwargs)
    return decorated_function

def require_tenant_user(permission: str = None):
    """Decorator to require tenant user with optional permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant_id'):
                abort(400, description="Tenant context required")
            
            # Get user ID from request (you'll need to implement your auth system)
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                abort(401, description="User authentication required")
            
            # Check tenant access
            tenant_manager = TenantManager()
            has_access = tenant_manager.check_user_access(
                g.tenant_id, user_id, permission
            )
            
            if not has_access:
                abort(403, description="Insufficient tenant permissions")
            
            g.user_id = user_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_tenant_admin(f):
    """Decorator to require tenant admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id'):
            abort(400, description="Tenant context required")
        
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            abort(401, description="User authentication required")
        
        tenant_manager = TenantManager()
        
        # Check if user is admin for this tenant
        session = tenant_manager.MasterSession()
        try:
            from .tenant_manager import TenantUser
            tenant_user = session.query(TenantUser).filter(
                TenantUser.tenant_id == g.tenant_id,
                TenantUser.user_id == user_id,
                TenantUser.role == "admin",
                TenantUser.is_active == True
            ).first()
            
            if not tenant_user:
                abort(403, description="Tenant admin access required")
            
            g.user_id = user_id
            return f(*args, **kwargs)
        finally:
            session.close()
    
    return decorated_function

def check_feature_flag(feature_name: str):
    """Decorator to check if feature is enabled for tenant"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant_config'):
                abort(400, description="Tenant context required")
            
            feature_flags = g.tenant_config.feature_flags or {}
            if not feature_flags.get(feature_name, False):
                abort(403, description=f"Feature '{feature_name}' not available")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_resource_limit(resource_name: str, current_usage: int):
    """Decorator to check resource limits"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant_config'):
                abort(400, description="Tenant context required")
            
            resource_limits = g.tenant_config.resource_limits or {}
            limit = resource_limits.get(resource_name, 0)
            
            if limit > 0 and current_usage >= limit:
                abort(403, description=f"Resource limit exceeded for '{resource_name}'")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Utility functions for tenant-aware operations
def get_tenant_database_session():
    """Get database session for current tenant"""
    if not hasattr(g, 'tenant_id'):
        raise ValueError("No tenant context available")
    
    tenant_manager = TenantManager()
    return tenant_manager.get_tenant_db_session(g.tenant_id)

def get_tenant_storage_path() -> str:
    """Get storage path for current tenant"""
    if not hasattr(g, 'tenant_config'):
        raise ValueError("No tenant context available")
    
    return g.tenant_config.storage_path

def record_tenant_usage(metric_name: str, value: int = 1):
    """Record usage for current tenant"""
    if not hasattr(g, 'tenant_id'):
        return
    
    tenant_manager = TenantManager()
    tenant_manager.record_tenant_usage(g.tenant_id, metric_name, value)

# Flask routes for tenant management
def create_tenant_routes(app: Flask):
    """Create tenant management routes"""
    tenant_manager = TenantManager()
    
    @app.route('/api/admin/tenants', methods=['GET'])
    def list_tenants():
        """List all tenants (admin only)"""
        # Add admin authentication here
        tenants = tenant_manager.list_tenants()
        return jsonify([
            {
                'tenant_id': t.tenant_id,
                'name': t.name,
                'domain': t.domain,
                'status': t.status,
                'plan_type': t.plan_type,
                'created_at': t.created_at.isoformat(),
                'last_accessed': t.last_accessed.isoformat() if t.last_accessed else None
            }
            for t in tenants
        ])
    
    @app.route('/api/admin/tenants', methods=['POST'])
    def create_tenant():
        """Create new tenant (admin only)"""
        data = request.get_json()
        
        try:
            tenant = tenant_manager.create_tenant(
                tenant_id=data['tenant_id'],
                name=data['name'],
                domain=data['domain'],
                plan_type=data.get('plan_type', 'starter'),
                custom_config=data.get('custom_config')
            )
            
            return jsonify({
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'domain': tenant.domain,
                'status': tenant.status,
                'database_url': tenant.database_url,
                'storage_path': tenant.storage_path
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/admin/tenants/<tenant_id>', methods=['PUT'])
    def update_tenant(tenant_id: str):
        """Update tenant configuration (admin only)"""
        data = request.get_json()
        
        success = tenant_manager.update_tenant_config(tenant_id, data)
        if success:
            return jsonify({'message': 'Tenant updated successfully'})
        else:
            return jsonify({'error': 'Failed to update tenant'}), 400
    
    @app.route('/api/admin/tenants/<tenant_id>/status', methods=['PUT'])
    def update_tenant_status(tenant_id: str):
        """Update tenant status (admin only)"""
        data = request.get_json()
        status = TenantStatus(data['status'])
        
        success = tenant_manager.update_tenant_status(tenant_id, status)
        if success:
            return jsonify({'message': 'Tenant status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update tenant status'}), 400
    
    @app.route('/api/admin/tenants/<tenant_id>/users', methods=['GET'])
    def get_tenant_users(tenant_id: str):
        """Get tenant users (admin only)"""
        users = tenant_manager.get_tenant_users(tenant_id)
        return jsonify([
            {
                'user_id': u.user_id,
                'role': u.role,
                'permissions': u.permissions,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat(),
                'last_login': u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ])
    
    @app.route('/api/admin/tenants/<tenant_id>/users', methods=['POST'])
    def add_tenant_user(tenant_id: str):
        """Add user to tenant (admin only)"""
        data = request.get_json()
        
        success = tenant_manager.add_tenant_user(
            tenant_id=tenant_id,
            user_id=data['user_id'],
            role=data.get('role', 'user'),
            permissions=data.get('permissions', [])
        )
        
        if success:
            return jsonify({'message': 'User added to tenant successfully'}), 201
        else:
            return jsonify({'error': 'Failed to add user to tenant'}), 400
    
    @app.route('/api/tenant/info', methods=['GET'])
    @require_tenant
    def get_tenant_info():
        """Get current tenant information"""
        return jsonify({
            'tenant_id': g.tenant.tenant_id,
            'name': g.tenant.name,
            'domain': g.tenant.domain,
            'plan_type': g.tenant.plan_type,
            'feature_flags': g.tenant.feature_flags,
            'resource_limits': g.tenant.resource_limits
        })
    
    @app.route('/api/tenant/usage', methods=['GET'])
    @require_tenant
    def get_tenant_usage():
        """Get current tenant usage"""
        usage = tenant_manager.get_tenant_usage(g.tenant_id, limit=50)
        return jsonify([
            {
                'metric_name': u.metric_name,
                'metric_value': u.metric_value,
                'timestamp': u.timestamp.isoformat(),
                'period': u.period
            }
            for u in usage
        ])

if __name__ == '__main__':
    # Test the middleware
    app = Flask(__name__)
    middleware = TenantMiddleware(app)
    
    @app.route('/test')
    @require_tenant
    def test_route():
        return jsonify({
            'message': 'Hello from tenant!',
            'tenant_id': g.tenant_id,
            'tenant_name': g.tenant.name
        })
    
    print("Tenant middleware test app ready")