from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.license_manager import LicenseManager, require_license, generate_test_license
from auth.decorators import admin_required
import logging

license_bp = Blueprint('license', __name__, url_prefix='/api/license')
logger = logging.getLogger(__name__)

@license_bp.route('/activate', methods=['POST'])
@jwt_required()
def activate_license():
    """
    Activate a license with the provided license key.
    """
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        user_email = data.get('user_email')
        
        if not license_key or not user_email:
            return jsonify({
                'error': 'License key and user email are required'
            }), 400
        
        license_manager = LicenseManager()
        result = license_manager.activate_license(license_key, user_email)
        
        if result['success']:
            logger.info(f"License activated successfully for user: {user_email}")
            return jsonify({
                'message': 'License activated successfully',
                'license_info': {
                    'license_id': result['license_id'],
                    'expiry_date': result['expiry_date'],
                    'features': result['features']
                }
            }), 200
        else:
            logger.warning(f"License activation failed for user {user_email}: {result['error']}")
            return jsonify({
                'error': result['error'],
                'details': result.get('details')
            }), 400
            
    except Exception as e:
        logger.error(f"License activation error: {str(e)}")
        return jsonify({
            'error': 'License activation failed',
            'details': str(e)
        }), 500

@license_bp.route('/status', methods=['GET'])
@jwt_required()
def get_license_status():
    """
    Get current license status and information.
    """
    try:
        license_manager = LicenseManager()
        license_info = license_manager.get_license_info()
        
        if license_info.get('valid', False):
            return jsonify({
                'valid': True,
                'license_info': {
                    'license_id': license_info['license_id'],
                    'user_email': license_info['user_email'],
                    'expiry_date': license_info['expiry_date'],
                    'features': license_info['features'],
                    'activated_at': license_info.get('activated_at'),
                    'days_remaining': license_info.get('days_remaining')
                }
            }), 200
        else:
            return jsonify({
                'valid': False,
                'error': license_info.get('error', 'No valid license found')
            }), 200
            
    except Exception as e:
        logger.error(f"License status check error: {str(e)}")
        return jsonify({
            'error': 'Failed to check license status',
            'details': str(e)
        }), 500

@license_bp.route('/features', methods=['GET'])
@jwt_required()
def get_available_features():
    """
    Get list of available features based on current license.
    """
    try:
        license_manager = LicenseManager()
        license_info = license_manager.get_license_info()
        
        if license_info.get('valid', False):
            features = license_info.get('features', [])
            
            # Define feature descriptions
            feature_descriptions = {
                'live_trading': 'Live trading with real money',
                'backtesting': 'Historical strategy backtesting',
                'real_time_data': 'Real-time market data streaming',
                'advanced_strategies': 'Advanced trading strategies',
                'portfolio_management': 'Portfolio management tools',
                'risk_management': 'Advanced risk management',
                'api_access': 'Full API access',
                'unlimited_bots': 'Unlimited trading bots'
            }
            
            available_features = [
                {
                    'name': feature,
                    'description': feature_descriptions.get(feature, 'Feature description not available'),
                    'enabled': True
                }
                for feature in features
            ]
            
            return jsonify({
                'features': available_features,
                'total_features': len(available_features)
            }), 200
        else:
            return jsonify({
                'error': 'No valid license found',
                'features': []
            }), 403
            
    except Exception as e:
        logger.error(f"Feature check error: {str(e)}")
        return jsonify({
            'error': 'Failed to check available features',
            'details': str(e)
        }), 500

@license_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_license():
    """
    Deactivate the current license.
    """
    try:
        license_manager = LicenseManager()
        success = license_manager.deactivate_license()
        
        if success:
            logger.info(f"License deactivated by user: {get_jwt_identity()}")
            return jsonify({
                'message': 'License deactivated successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to deactivate license'
            }), 500
            
    except Exception as e:
        logger.error(f"License deactivation error: {str(e)}")
        return jsonify({
            'error': 'License deactivation failed',
            'details': str(e)
        }), 500

@license_bp.route('/validate-feature/<feature_name>', methods=['GET'])
@jwt_required()
def validate_feature(feature_name):
    """
    Validate if a specific feature is available in the current license.
    """
    try:
        license_manager = LicenseManager()
        has_feature = license_manager.has_feature(feature_name)
        
        return jsonify({
            'feature': feature_name,
            'available': has_feature
        }), 200
        
    except Exception as e:
        logger.error(f"Feature validation error: {str(e)}")
        return jsonify({
            'error': 'Feature validation failed',
            'details': str(e)
        }), 500

# Admin routes for license management
@license_bp.route('/admin/generate-test', methods=['POST'])
@jwt_required()
@admin_required
def generate_test_license_key():
    """
    Generate a test license key (admin only).
    """
    try:
        data = request.get_json()
        user_email = data.get('user_email')
        days_valid = data.get('days_valid', 30)
        
        if not user_email:
            return jsonify({
                'error': 'User email is required'
            }), 400
        
        license_key = generate_test_license(user_email, days_valid)
        
        logger.info(f"Test license generated for {user_email} by admin: {get_jwt_identity()}")
        
        return jsonify({
            'message': 'Test license generated successfully',
            'license_key': license_key,
            'user_email': user_email,
            'days_valid': days_valid
        }), 200
        
    except Exception as e:
        logger.error(f"Test license generation error: {str(e)}")
        return jsonify({
            'error': 'Failed to generate test license',
            'details': str(e)
        }), 500

@license_bp.route('/admin/info', methods=['GET'])
@jwt_required()
@admin_required
def get_license_admin_info():
    """
    Get detailed license information for admin purposes.
    """
    try:
        license_manager = LicenseManager()
        license_info = license_manager.get_license_info()
        
        # Include additional admin-only information
        admin_info = {
            'license_status': license_info,
            'license_file_exists': license_manager._load_license() is not None,
            'license_file_path': license_manager.license_file_path
        }
        
        return jsonify(admin_info), 200
        
    except Exception as e:
        logger.error(f"Admin license info error: {str(e)}")
        return jsonify({
            'error': 'Failed to get admin license info',
            'details': str(e)
        }), 500

# Middleware to check license for protected routes
@license_bp.before_app_request
def check_license_for_trading():
    """
    Check license for trading-related endpoints.
    """
    if request.endpoint and 'trading' in request.endpoint:
        license_manager = LicenseManager()
        if not license_manager.has_feature('live_trading'):
            return jsonify({
                'error': 'Live trading feature not available in current license'
            }), 403

# Error handlers
@license_bp.errorhandler(403)
def license_forbidden(error):
    return jsonify({
        'error': 'License validation failed',
        'message': 'Valid license required to access this feature'
    }), 403

@license_bp.errorhandler(500)
def license_server_error(error):
    return jsonify({
        'error': 'License service error',
        'message': 'Please try again later'
    }), 500