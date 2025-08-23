from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.license_manager import LicenseManager
from models.user import User
from database import db
from datetime import datetime, timedelta

license_bp = Blueprint('license', __name__)

@license_bp.route('/activate', methods=['POST'])
@jwt_required()
def activate_license():
    """Activate a license key for the current user"""
    try:
        data = request.get_json()
        if not data or 'license_key' not in data:
            return jsonify({'error': 'License key is required'}), 400
        
        license_key = data['license_key'].strip()
        if not license_key:
            return jsonify({'error': 'License key cannot be empty'}), 400
        
        user_id = get_jwt_identity()
        
        # Activate the license
        success, message = LicenseManager.activate_license(user_id, license_key)
        
        if success:
            # Get updated license info
            license_info, _ = LicenseManager.get_user_license_info(user_id)
            return jsonify({
                'message': message,
                'license': license_info
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"License activation error: {str(e)}")
        return jsonify({'error': 'License activation failed'}), 500

@license_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_license():
    """Deactivate the current user's license"""
    try:
        user_id = get_jwt_identity()
        
        # Deactivate the license
        success, message = LicenseManager.deactivate_license(user_id)
        
        if success:
            # Get updated license info
            license_info, _ = LicenseManager.get_user_license_info(user_id)
            return jsonify({
                'message': message,
                'license': license_info
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"License deactivation error: {str(e)}")
        return jsonify({'error': 'License deactivation failed'}), 500

@license_bp.route('/status', methods=['GET'])
@jwt_required()
def get_license_status():
    """Get the current user's license status"""
    try:
        user_id = get_jwt_identity()
        
        # Get license info
        license_info, error = LicenseManager.get_user_license_info(user_id)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({'license': license_info}), 200
        
    except Exception as e:
        current_app.logger.error(f"License status error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve license status'}), 500

@license_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_license_key():
    """Validate a license key without activating it"""
    try:
        data = request.get_json()
        if not data or 'license_key' not in data:
            return jsonify({'error': 'License key is required'}), 400
        
        license_key = data['license_key'].strip()
        if not license_key:
            return jsonify({'error': 'License key cannot be empty'}), 400
        
        # Validate the license key
        license_data, error = LicenseManager.validate_license_key(license_key)
        
        if error:
            return jsonify({
                'valid': False,
                'error': error
            }), 400
        
        return jsonify({
            'valid': True,
            'license_data': {
                'type': license_data['type'],
                'expires': license_data['expires'],
                'features': license_data['features']
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"License validation error: {str(e)}")
        return jsonify({'error': 'License validation failed'}), 500

@license_bp.route('/features', methods=['GET'])
@jwt_required()
def get_available_features():
    """Get all available license features"""
    try:
        return jsonify({
            'license_types': LicenseManager.LICENSE_FEATURES
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Features retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve features'}), 500

@license_bp.route('/check-feature', methods=['POST'])
@jwt_required()
def check_feature_access():
    """Check if the current user has access to a specific feature"""
    try:
        data = request.get_json()
        if not data or 'feature' not in data:
            return jsonify({'error': 'Feature name is required'}), 400
        
        feature = data['feature']
        user_id = get_jwt_identity()
        
        # Check feature access
        has_access = LicenseManager.check_feature_access(user_id, feature)
        
        # Get current license info
        license_info, _ = LicenseManager.get_user_license_info(user_id)
        
        return jsonify({
            'feature': feature,
            'has_access': has_access,
            'current_license': license_info['type'] if license_info else 'free'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Feature check error: {str(e)}")
        return jsonify({'error': 'Feature check failed'}), 500

@license_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_license():
    """Generate a new license key (web-based generator)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Extract parameters
        license_type = data.get('license_type', 'premium')
        duration_days = data.get('duration_days', 365)
        user_email = data.get('user_email', '')
        
        # Validate license type
        if license_type not in LicenseManager.LICENSE_FEATURES:
            return jsonify({'error': 'Invalid license type'}), 400
        
        # Validate duration
        try:
            duration_days = int(duration_days)
            if duration_days < 1 or duration_days > 3650:  # Max 10 years
                return jsonify({'error': 'Duration must be between 1 and 3650 days'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid duration format'}), 400
        
        # Validate email format if provided
        if user_email and '@' not in user_email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Generate license key
        license_key = LicenseManager.generate_license_key(
            license_type=license_type,
            duration_days=duration_days,
            user_email=user_email
        )
        
        if not license_key:
            return jsonify({'error': 'Failed to generate license key'}), 500
        
        # Validate the generated key
        license_data, error = LicenseManager.validate_license_key(license_key)
        
        if error:
            return jsonify({'error': f'Generated license is invalid: {error}'}), 500
        
        # Return the generated license with details
        return jsonify({
            'success': True,
            'license_key': license_key,
            'license_data': {
                'type': license_data['type'],
                'user_email': license_data.get('user_email', ''),
                'created': license_data['created'],
                'expires': license_data['expires'],
                'duration_days': duration_days,
                'features': license_data['features']
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"License generation error: {str(e)}")
        return jsonify({'error': 'License generation failed'}), 500

@license_bp.route('/types', methods=['GET'])
def get_license_types():
    """Get available license types and their features (public endpoint)"""
    try:
        license_types = {}
        
        for license_type, features in LicenseManager.LICENSE_FEATURES.items():
            # Create a user-friendly description
            description = {
                'free': 'Basic features for getting started',
                'premium': 'Advanced features for serious traders',
                'enterprise': 'All features with unlimited access'
            }.get(license_type, 'Custom license type')
            
            # Format features for display
            formatted_features = {}
            for feature, value in features.items():
                if feature == 'max_bots' and value == -1:
                    formatted_features[feature] = 'Unlimited'
                else:
                    formatted_features[feature] = value
            
            license_types[license_type] = {
                'name': license_type.title(),
                'description': description,
                'features': formatted_features
            }
        
        return jsonify({
            'license_types': license_types
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"License types retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve license types'}), 500