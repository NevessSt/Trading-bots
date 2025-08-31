"""OAuth2 authentication routes."""

from flask import Blueprint, request, jsonify, redirect, url_for, current_app
from urllib.parse import urlencode

from services.oauth_service import OAuthService
from services.logging_service import get_logger, LogCategory
from services.error_handler import handle_errors, ErrorCategory
from middleware.security_middleware import rate_limit, validate_content_type, log_request, cors_headers

# Create blueprint
oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')

# Initialize services
oauth_service = OAuthService()
logger = get_logger(LogCategory.API)


@oauth_bp.route('/providers', methods=['GET'])
@cors_headers
def get_oauth_providers():
    """Get list of available OAuth providers."""
    providers = {
        'google': {
            'name': 'Google',
            'enabled': bool(current_app.config.get('GOOGLE_CLIENT_ID')),
            'icon': 'google',
            'color': '#4285f4'
        },
        'github': {
            'name': 'GitHub',
            'enabled': bool(current_app.config.get('GITHUB_CLIENT_ID')),
            'icon': 'github',
            'color': '#333'
        },
        'microsoft': {
            'name': 'Microsoft',
            'enabled': bool(current_app.config.get('MICROSOFT_CLIENT_ID')),
            'icon': 'microsoft',
            'color': '#00a1f1'
        }
    }
    
    # Filter only enabled providers
    enabled_providers = {k: v for k, v in providers.items() if v['enabled']}
    
    return jsonify({
        'providers': enabled_providers
    }), 200


@oauth_bp.route('/<provider>/authorize', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
def oauth_authorize(provider):
    """Initiate OAuth2 authorization flow."""
    try:
        # Get redirect URI from query params or use default
        redirect_uri = request.args.get('redirect_uri') or url_for(
            'oauth.oauth_callback', 
            provider=provider, 
            _external=True
        )
        
        # Generate authorization URL
        auth_url = oauth_service.get_authorization_url(provider, redirect_uri)
        
        # Return URL for frontend to redirect to
        return jsonify({
            'authorization_url': auth_url
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"OAuth authorization error for {provider}: {e}")
        return jsonify({'error': 'Authorization failed'}), 500


@oauth_bp.route('/<provider>/callback', methods=['GET'])
@rate_limit(max_requests=20, window_seconds=300)  # 20 callbacks per 5 minutes
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
def oauth_callback(provider):
    """Handle OAuth2 callback and complete authentication."""
    try:
        # Get authorization code and state from query params
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.warning(f"OAuth error for {provider}: {error}")
            return jsonify({
                'error': f'OAuth authorization failed: {error}'
            }), 400
        
        if not code or not state:
            return jsonify({
                'error': 'Missing authorization code or state parameter'
            }), 400
        
        # Get redirect URI
        redirect_uri = url_for('oauth.oauth_callback', provider=provider, _external=True)
        
        # Handle OAuth callback
        result = oauth_service.handle_callback(provider, code, state, redirect_uri)
        
        # For web applications, you might want to redirect to frontend with tokens
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        
        # Create query parameters for frontend
        params = {
            'access_token': result['tokens']['access_token'],
            'refresh_token': result['tokens']['refresh_token'],
            'user_id': result['user']['id']
        }
        
        # Redirect to frontend with tokens
        return redirect(f"{frontend_url}/auth/callback?{urlencode(params)}")
        
    except ValueError as e:
        logger.warning(f"OAuth callback validation error for {provider}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {e}")
        return jsonify({'error': 'Authentication failed'}), 500


@oauth_bp.route('/<provider>/callback/api', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=300)
@validate_content_type()
@log_request
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
def oauth_callback_api(provider):
    """Handle OAuth2 callback via API (for mobile/SPA applications)."""
    try:
        data = request.get_json()
        code = data.get('code')
        state = data.get('state')
        redirect_uri = data.get('redirect_uri')
        
        if not code or not state:
            return jsonify({
                'error': 'Missing authorization code or state parameter'
            }), 400
        
        if not redirect_uri:
            redirect_uri = url_for('oauth.oauth_callback', provider=provider, _external=True)
        
        # Handle OAuth callback
        result = oauth_service.handle_callback(provider, code, state, redirect_uri)
        
        return jsonify({
            'message': 'OAuth authentication successful',
            'user': result['user'],
            'access_token': result['tokens']['access_token'],
            'refresh_token': result['tokens']['refresh_token']
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"OAuth API callback error for {provider}: {e}")
        return jsonify({'error': 'Authentication failed'}), 500


@oauth_bp.route('/unlink', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300)
@validate_content_type()
@log_request
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
def unlink_oauth_provider():
    """Unlink OAuth provider from user account."""
    from flask_jwt_extended import jwt_required, get_jwt_identity
    from models import User
    
    try:
        # Get current user
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Unlink OAuth provider
        success = oauth_service.unlink_oauth_provider(user)
        
        if success:
            return jsonify({
                'message': 'OAuth provider unlinked successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to unlink OAuth provider'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"OAuth unlink error: {e}")
        return jsonify({'error': 'Failed to unlink OAuth provider'}), 500


@oauth_bp.route('/cleanup', methods=['POST'])
@rate_limit(max_requests=1, window_seconds=60)
@cors_headers
def cleanup_oauth_states():
    """Clean up expired OAuth states (admin endpoint)."""
    try:
        cleaned_count = oauth_service.cleanup_expired_states()
        
        return jsonify({
            'message': f'Cleaned up {cleaned_count} expired OAuth states'
        }), 200
        
    except Exception as e:
        logger.error(f"OAuth cleanup error: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500


# Error handlers
@oauth_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify({'error': 'Bad request'}), 400


@oauth_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors."""
    return jsonify({'error': 'Unauthorized'}), 401


@oauth_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"OAuth internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500