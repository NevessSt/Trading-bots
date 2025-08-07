# Import routes for easier access
from api.auth_routes import auth_bp
from api.trading_routes import trading_bp

__all__ = ['auth_bp', 'trading_bp']