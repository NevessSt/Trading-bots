from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import requests
from functools import wraps

# Import license validation
try:
    from backend.license_check import verify_license, check_feature, get_license_status
except ImportError:
    print("Warning: License validation not available. Running in development mode.")
    def verify_license():
        return True, "Development mode"
    def check_feature(feature):
        return True
    def get_license_status():
        return {'valid': True, 'message': 'Development mode', 'license_type': 'development'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# License validation decorator
def license_required(feature=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_valid, message = verify_license()
            if not is_valid:
                if request.is_json:
                    return jsonify({'error': 'License validation failed', 'message': message}), 403
                flash(f'License Error: {message}', 'error')
                return redirect(url_for('license_status'))
            
            if feature and not check_feature(feature):
                if request.is_json:
                    return jsonify({'error': 'Feature not available', 'feature': feature}), 403
                flash(f'Feature "{feature}" not available in your license', 'warning')
                return redirect(url_for('license_status'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy=True)
    strategies = db.relationship('TradingStrategy', backref='user', lazy=True)
    trades = db.relationship('Trade', backref='user', lazy=True)
    risk_settings = db.relationship('RiskSetting', backref='user', lazy=True)

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)
    key_name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(200), nullable=False)
    api_secret = db.Column(db.String(200), nullable=False)  # Should be encrypted in production
    is_testnet = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TradingStrategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    strategy_type = db.Column(db.String(50), nullable=False)  # 'grid', 'dca', 'scalping', etc.
    parameters = db.Column(db.Text)  # JSON string of strategy parameters
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('trading_strategy.id'), nullable=True)
    exchange = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    profit_loss = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='completed')
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

class RiskSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_daily_loss = db.Column(db.Float, default=100.0)
    max_position_size = db.Column(db.Float, default=1000.0)
    stop_loss_percentage = db.Column(db.Float, default=5.0)
    take_profit_percentage = db.Column(db.Float, default=10.0)
    max_open_positions = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create default risk settings
        risk_settings = RiskSetting(user_id=user.id)
        db.session.add(risk_settings)
        db.session.commit()
        
        return jsonify({'message': 'Registration successful'}), 201
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
@license_required('basic_trading')
def dashboard():
    # Get user statistics
    total_trades = Trade.query.filter_by(user_id=current_user.id).count()
    total_profit = db.session.query(db.func.sum(Trade.profit_loss)).filter_by(user_id=current_user.id).scalar() or 0
    active_strategies = TradingStrategy.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    # Get recent trades
    recent_trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.executed_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         total_trades=total_trades,
                         total_profit=total_profit,
                         active_strategies=active_strategies,
                         recent_trades=recent_trades)

@app.route('/api-keys')
@login_required
@license_required('basic_trading')
def api_keys():
    keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return render_template('api_keys.html', api_keys=keys)

@app.route('/api/api-keys', methods=['POST'])
@login_required
@license_required('basic_trading')
def add_api_key():
    data = request.get_json()
    
    api_key = APIKey(
        user_id=current_user.id,
        exchange=data.get('exchange'),
        key_name=data.get('key_name'),
        api_key=data.get('api_key'),
        api_secret=data.get('api_secret'),
        is_testnet=data.get('is_testnet', True)
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    return jsonify({'message': 'API key added successfully'}), 201

@app.route('/strategies')
@login_required
def strategies():
    user_strategies = TradingStrategy.query.filter_by(user_id=current_user.id).all()
    return render_template('strategies.html', strategies=user_strategies)

@app.route('/api/strategies', methods=['POST'])
@login_required
@license_required('advanced_trading')
def create_strategy():
    data = request.get_json()
    
    strategy = TradingStrategy(
        user_id=current_user.id,
        name=data.get('name'),
        description=data.get('description'),
        strategy_type=data.get('strategy_type'),
        parameters=json.dumps(data.get('parameters', {}))
    )
    
    db.session.add(strategy)
    db.session.commit()
    
    return jsonify({'message': 'Strategy created successfully'}), 201

@app.route('/performance')
@login_required
@license_required('portfolio_management')
def performance():
    # Calculate performance metrics
    trades = Trade.query.filter_by(user_id=current_user.id).all()
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.profit_loss > 0])
    losing_trades = len([t for t in trades if t.profit_loss < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = sum(t.profit_loss for t in trades)
    
    # Daily performance data for charts
    daily_performance = {}
    for trade in trades:
        date_key = trade.executed_at.strftime('%Y-%m-%d')
        if date_key not in daily_performance:
            daily_performance[date_key] = 0
        daily_performance[date_key] += trade.profit_loss
    
    return render_template('performance.html',
                         total_trades=total_trades,
                         win_rate=win_rate,
                         total_profit=total_profit,
                         daily_performance=daily_performance)

@app.route('/market-data')
@login_required
@license_required('market_data')
def market_data():
    return render_template('market.html')

@app.route('/api/market-data/<symbol>')
@login_required
@license_required('market_data')
def get_market_data(symbol):
    # Mock market data - in production, integrate with real exchange APIs
    import random
    
    price = round(random.uniform(30000, 70000), 2)
    change_24h = round(random.uniform(-5, 5), 2)
    volume_24h = round(random.uniform(1000000, 10000000), 2)
    
    return jsonify({
        'symbol': symbol,
        'price': price,
        'change_24h': change_24h,
        'volume_24h': volume_24h,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/risk-settings')
@login_required
@license_required('risk_management')
def risk_settings():
    settings = RiskSetting.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = RiskSetting(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    return render_template('risk_management.html', settings=settings)

@app.route('/api/risk-settings', methods=['POST'])
@login_required
@license_required('risk_management')
def update_risk_settings():
    data = request.get_json()
    
    settings = RiskSetting.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = RiskSetting(user_id=current_user.id)
    
    settings.max_daily_loss = data.get('max_daily_loss', settings.max_daily_loss)
    settings.max_position_size = data.get('max_position_size', settings.max_position_size)
    settings.stop_loss_percentage = data.get('stop_loss_percentage', settings.stop_loss_percentage)
    settings.take_profit_percentage = data.get('take_profit_percentage', settings.take_profit_percentage)
    settings.max_open_positions = data.get('max_open_positions', settings.max_open_positions)
    settings.updated_at = datetime.utcnow()
    
    db.session.add(settings)
    db.session.commit()
    
    return jsonify({'message': 'Risk settings updated successfully'})

@app.route('/license-status')
def license_status():
    """Display license status information."""
    license_info = get_license_status()
    return render_template('license_status.html', license_info=license_info)

@app.route('/api/license-status')
def api_license_status():
    """API endpoint for license status."""
    license_info = get_license_status()
    return jsonify(license_info)

@app.route('/activate-license', methods=['GET', 'POST'])
@login_required
def activate_license():
    """License activation page"""
    if request.method == 'POST':
        license_code = request.form.get('license_code', '').strip()
        
        if not license_code:
            flash('Please enter a license code', 'error')
            return render_template('activate_license.html')
        
        try:
            from backend.license_activation import LicenseActivator
            activator = LicenseActivator()
            success, message = activator.activate_license(license_code)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('license_status'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            flash(f'Activation failed: {str(e)}', 'error')
    
    return render_template('activate_license.html')

@app.route('/api/activate-license', methods=['POST'])
@login_required
def api_activate_license():
    """API endpoint for license activation"""
    data = request.get_json()
    license_code = data.get('license_code', '').strip()
    
    if not license_code:
        return jsonify({
            'success': False,
            'message': 'License code is required'
        }), 400
    
    try:
        from backend.license_activation import LicenseActivator
        activator = LicenseActivator()
        success, message = activator.activate_license(license_code)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Activation failed: {str(e)}'
        }), 500

@app.route('/api/machine-id')
@login_required
def api_machine_id():
    """API endpoint to get machine ID"""
    try:
        from tools.machine_id import generate_machine_id
        machine_id = generate_machine_id()
        return jsonify({
            'machine_id': machine_id
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get machine ID: {str(e)}'
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create demo data if no users exist
        if not User.query.first():
            demo_user = User(
                username='demo',
                email='demo@example.com',
                password_hash=generate_password_hash('demo123')
            )
            db.session.add(demo_user)
            db.session.commit()
            
            # Add demo trades
            import random
            for i in range(20):
                trade = Trade(
                    user_id=demo_user.id,
                    exchange='binance',
                    symbol='BTCUSDT',
                    side='buy' if i % 2 == 0 else 'sell',
                    quantity=round(random.uniform(0.001, 0.1), 6),
                    price=round(random.uniform(30000, 70000), 2),
                    total_value=round(random.uniform(100, 1000), 2),
                    profit_loss=round(random.uniform(-50, 100), 2),
                    executed_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                trade.total_value = trade.quantity * trade.price
                db.session.add(trade)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)