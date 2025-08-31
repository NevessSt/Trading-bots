from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import hashlib
import tempfile
import ast
import inspect
from datetime import datetime
from typing import Dict, Any, List
import logging
from werkzeug.utils import secure_filename

# Import models
from models.user import User
from models.subscription import Subscription
from bot_engine.strategies.base_strategy import BaseStrategy
from bot_engine.dynamic_strategy_manager import DynamicStrategyManager

strategy_marketplace_bp = Blueprint('strategy_marketplace', __name__, url_prefix='/api/marketplace')
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'py'}
MAX_FILE_SIZE = 1024 * 1024  # 1MB
STRATEGY_UPLOAD_DIR = os.path.join(os.getcwd(), 'user_strategies')

# Ensure upload directory exists
os.makedirs(STRATEGY_UPLOAD_DIR, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_strategy_code(code: str) -> Dict[str, Any]:
    """Validate uploaded strategy code for security and compliance"""
    try:
        # Parse the code to check syntax
        tree = ast.parse(code)
        
        # Security checks
        forbidden_imports = [
            'os', 'sys', 'subprocess', 'eval', 'exec', 'open', 'file',
            'input', 'raw_input', '__import__', 'reload', 'compile',
            'globals', 'locals', 'vars', 'dir', 'getattr', 'setattr',
            'delattr', 'hasattr'
        ]
        
        forbidden_functions = [
            'eval', 'exec', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'reload'
        ]
        
        # Check for forbidden imports and function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_imports:
                        return {
                            'valid': False,
                            'error': f'Forbidden import: {alias.name}'
                        }
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in forbidden_imports:
                    return {
                        'valid': False,
                        'error': f'Forbidden import: {node.module}'
                    }
            
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_functions:
                    return {
                        'valid': False,
                        'error': f'Forbidden function call: {node.func.id}'
                    }
        
        # Check for BaseStrategy inheritance
        has_strategy_class = False
        strategy_class_name = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from BaseStrategy
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'BaseStrategy':
                        has_strategy_class = True
                        strategy_class_name = node.name
                        break
        
        if not has_strategy_class:
            return {
                'valid': False,
                'error': 'Strategy must inherit from BaseStrategy'
            }
        
        return {
            'valid': True,
            'strategy_class': strategy_class_name
        }
        
    except SyntaxError as e:
        return {
            'valid': False,
            'error': f'Syntax error: {str(e)}'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }

def extract_strategy_metadata(code: str) -> Dict[str, Any]:
    """Extract metadata from strategy code"""
    try:
        # Create a temporary module to inspect the strategy
        temp_module = {}
        exec(code, temp_module)
        
        # Find the strategy class
        strategy_class = None
        for name, obj in temp_module.items():
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseStrategy) and 
                obj != BaseStrategy):
                strategy_class = obj
                break
        
        if not strategy_class:
            return {}
        
        # Create instance to get metadata
        instance = strategy_class()
        
        metadata = {
            'name': instance.get_name() if hasattr(instance, 'get_name') else 'Unknown Strategy',
            'description': instance.get_description() if hasattr(instance, 'get_description') else 'No description',
            'parameters': instance.get_parameters() if hasattr(instance, 'get_parameters') else {},
            'class_name': strategy_class.__name__
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}

@strategy_marketplace_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_strategy():
    """Upload a custom trading strategy"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if user has permission to upload strategies
        subscription = user.get_current_subscription()
        if not subscription or not subscription.has_feature('custom_strategies'):
            return jsonify({
                'success': False,
                'error': 'Custom strategy upload requires premium subscription'
            }), 403
        
        # Check if file is present
        if 'strategy_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No strategy file provided'
            }), 400
        
        file = request.files['strategy_file']
        strategy_name = request.form.get('strategy_name', '').strip()
        strategy_description = request.form.get('strategy_description', '').strip()
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Only Python (.py) files are allowed'
            }), 400
        
        if not strategy_name:
            return jsonify({
                'success': False,
                'error': 'Strategy name is required'
            }), 400
        
        # Read and validate file content
        file_content = file.read().decode('utf-8')
        
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE} bytes'
            }), 400
        
        # Validate strategy code
        validation_result = validate_strategy_code(file_content)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': f'Strategy validation failed: {validation_result["error"]}'
            }), 400
        
        # Extract metadata
        metadata = extract_strategy_metadata(file_content)
        
        # Generate unique filename
        file_hash = hashlib.md5(file_content.encode()).hexdigest()[:8]
        filename = secure_filename(f"{user_id}_{strategy_name}_{file_hash}.py")
        filepath = os.path.join(STRATEGY_UPLOAD_DIR, filename)
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Save strategy metadata to database (you would need to create a Strategy model)
        strategy_data = {
            'id': f"custom_{user_id}_{file_hash}",
            'name': strategy_name,
            'description': strategy_description or metadata.get('description', 'No description'),
            'filename': filename,
            'filepath': filepath,
            'user_id': user_id,
            'is_public': is_public,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': metadata,
            'file_hash': file_hash,
            'status': 'active'
        }
        
        # Store in a JSON file for now (in production, use a proper database)
        strategies_db_file = os.path.join(STRATEGY_UPLOAD_DIR, 'strategies.json')
        strategies_db = []
        
        if os.path.exists(strategies_db_file):
            with open(strategies_db_file, 'r') as f:
                strategies_db = json.load(f)
        
        strategies_db.append(strategy_data)
        
        with open(strategies_db_file, 'w') as f:
            json.dump(strategies_db, f, indent=2)
        
        # Try to load the strategy dynamically
        try:
            dynamic_manager = DynamicStrategyManager()
            strategy_id = dynamic_manager.add_strategy_from_file(filepath)
            
            if strategy_id:
                logger.info(f"Successfully loaded custom strategy: {strategy_id}")
            else:
                logger.warning(f"Failed to load custom strategy from {filepath}")
        
        except Exception as e:
            logger.error(f"Error loading custom strategy: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Strategy uploaded successfully',
            'strategy': {
                'id': strategy_data['id'],
                'name': strategy_name,
                'description': strategy_data['description'],
                'metadata': metadata
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading strategy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload strategy',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/browse', methods=['GET'])
@jwt_required()
def browse_strategies():
    """Browse available marketplace strategies"""
    try:
        user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        category = request.args.get('category', 'all')
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'created_at')
        
        # Load strategies from JSON file
        strategies_db_file = os.path.join(STRATEGY_UPLOAD_DIR, 'strategies.json')
        strategies = []
        
        if os.path.exists(strategies_db_file):
            with open(strategies_db_file, 'r') as f:
                all_strategies = json.load(f)
            
            # Filter strategies (show public strategies and user's own strategies)
            for strategy in all_strategies:
                if (strategy.get('is_public', False) or 
                    strategy.get('user_id') == user_id):
                    strategies.append(strategy)
        
        # Apply search filter
        if search_query:
            strategies = [
                s for s in strategies 
                if (search_query.lower() in s.get('name', '').lower() or 
                    search_query.lower() in s.get('description', '').lower())
            ]
        
        # Apply category filter
        if category != 'all':
            strategies = [
                s for s in strategies 
                if category in s.get('metadata', {}).get('tags', [])
            ]
        
        # Sort strategies
        if sort_by == 'name':
            strategies.sort(key=lambda x: x.get('name', '').lower())
        elif sort_by == 'created_at':
            strategies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Paginate
        total = len(strategies)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_strategies = strategies[start:end]
        
        # Remove sensitive information
        for strategy in paginated_strategies:
            strategy.pop('filepath', None)
            strategy.pop('file_hash', None)
            if strategy.get('user_id') != user_id:
                strategy.pop('user_id', None)
        
        return jsonify({
            'success': True,
            'strategies': paginated_strategies,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error browsing strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to browse strategies',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/my-strategies', methods=['GET'])
@jwt_required()
def get_my_strategies():
    """Get user's uploaded strategies"""
    try:
        user_id = get_jwt_identity()
        
        # Load strategies from JSON file
        strategies_db_file = os.path.join(STRATEGY_UPLOAD_DIR, 'strategies.json')
        user_strategies = []
        
        if os.path.exists(strategies_db_file):
            with open(strategies_db_file, 'r') as f:
                all_strategies = json.load(f)
            
            # Filter user's strategies
            user_strategies = [
                s for s in all_strategies 
                if s.get('user_id') == user_id
            ]
        
        return jsonify({
            'success': True,
            'strategies': user_strategies,
            'count': len(user_strategies)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user strategies',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/strategy/<strategy_id>', methods=['GET'])
@jwt_required()
def get_strategy_details(strategy_id):
    """Get detailed information about a specific strategy"""
    try:
        user_id = get_jwt_identity()
        
        # Load strategies from JSON file
        strategies_db_file = os.path.join(STRATEGY_UPLOAD_DIR, 'strategies.json')
        
        if not os.path.exists(strategies_db_file):
            return jsonify({
                'success': False,
                'error': 'Strategy not found'
            }), 404
        
        with open(strategies_db_file, 'r') as f:
            all_strategies = json.load(f)
        
        # Find the strategy
        strategy = None
        for s in all_strategies:
            if s.get('id') == strategy_id:
                # Check if user can access this strategy
                if (s.get('is_public', False) or 
                    s.get('user_id') == user_id):
                    strategy = s
                break
        
        if not strategy:
            return jsonify({
                'success': False,
                'error': 'Strategy not found or access denied'
            }), 404
        
        # Remove sensitive information if not owner
        if strategy.get('user_id') != user_id:
            strategy.pop('filepath', None)
            strategy.pop('file_hash', None)
            strategy.pop('user_id', None)
        
        return jsonify({
            'success': True,
            'strategy': strategy
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting strategy details: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get strategy details',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/strategy/<strategy_id>', methods=['DELETE'])
@jwt_required()
def delete_strategy(strategy_id):
    """Delete a user's strategy"""
    try:
        user_id = get_jwt_identity()
        
        # Load strategies from JSON file
        strategies_db_file = os.path.join(STRATEGY_UPLOAD_DIR, 'strategies.json')
        
        if not os.path.exists(strategies_db_file):
            return jsonify({
                'success': False,
                'error': 'Strategy not found'
            }), 404
        
        with open(strategies_db_file, 'r') as f:
            all_strategies = json.load(f)
        
        # Find and remove the strategy
        strategy_to_delete = None
        updated_strategies = []
        
        for strategy in all_strategies:
            if (strategy.get('id') == strategy_id and 
                strategy.get('user_id') == user_id):
                strategy_to_delete = strategy
            else:
                updated_strategies.append(strategy)
        
        if not strategy_to_delete:
            return jsonify({
                'success': False,
                'error': 'Strategy not found or access denied'
            }), 404
        
        # Delete the file
        filepath = strategy_to_delete.get('filepath')
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        # Update the database
        with open(strategies_db_file, 'w') as f:
            json.dump(updated_strategies, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Strategy deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete strategy',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get available strategy categories"""
    try:
        categories = [
            {'id': 'all', 'name': 'All Strategies', 'description': 'All available strategies'},
            {'id': 'technical_analysis', 'name': 'Technical Analysis', 'description': 'Strategies based on technical indicators'},
            {'id': 'arbitrage', 'name': 'Arbitrage', 'description': 'Risk-free profit strategies'},
            {'id': 'scalping', 'name': 'Scalping', 'description': 'High-frequency trading strategies'},
            {'id': 'swing_trading', 'name': 'Swing Trading', 'description': 'Medium-term trading strategies'},
            {'id': 'trend_following', 'name': 'Trend Following', 'description': 'Strategies that follow market trends'},
            {'id': 'mean_reversion', 'name': 'Mean Reversion', 'description': 'Strategies based on price mean reversion'},
            {'id': 'momentum', 'name': 'Momentum', 'description': 'Momentum-based trading strategies'},
            {'id': 'custom', 'name': 'Custom', 'description': 'User-created custom strategies'}
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get categories',
            'details': str(e)
        }), 500

@strategy_marketplace_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_strategy():
    """Validate strategy code before upload"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if user has permission
        subscription = user.get_current_subscription()
        if not subscription or not subscription.has_feature('custom_strategies'):
            return jsonify({
                'success': False,
                'error': 'Custom strategy validation requires premium subscription'
            }), 403
        
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'Strategy code is required'
            }), 400
        
        code = data['code']
        
        # Validate the code
        validation_result = validate_strategy_code(code)
        
        if validation_result['valid']:
            # Extract metadata if valid
            metadata = extract_strategy_metadata(code)
            validation_result['metadata'] = metadata
        
        return jsonify({
            'success': True,
            'validation': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating strategy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate strategy',
            'details': str(e)
        }), 500