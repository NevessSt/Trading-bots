#!/usr/bin/env python3
"""
TradingBot Pro - Main Application Entry Point

A professional-grade cryptocurrency trading bot with advanced features:
- Multi-exchange support (Binance, Coinbase, Kraken)
- Advanced trading strategies with backtesting
- Real-time portfolio management and risk controls
- Web dashboard and REST API
- Enterprise-grade security and monitoring

Author: TradingBot Pro Team
Version: 2.0.0
License: Commercial
"""

import os
import sys
import signal
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from flask import Flask
    from flask_cors import CORS
    from flask_socketio import SocketIO
    import redis
    from backend.bot_engine.trading_engine import TradingEngine, TradingBotConfig
    from backend.utils.logger import setup_logger
    from backend.auth.license_manager import LicenseManager
    from config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Global variables
app: Optional[Flask] = None
socketio: Optional[SocketIO] = None
trading_engine: Optional[TradingEngine] = None
logger: Optional[logging.Logger] = None

def create_app(config_name: str = 'development') -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application
    """
    global app, socketio
    
    app = Flask(__name__,
                template_folder='templates',
                static_folder='frontend/build/static')
    
    # Load configuration
    config_class = getattr(Config, config_name.title() + 'Config', Config.DevelopmentConfig)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    socketio = SocketIO(app, 
                       cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'),
                       ping_interval=app.config.get('WEBSOCKET_PING_INTERVAL', 20),
                       ping_timeout=app.config.get('WEBSOCKET_PING_TIMEOUT', 10))
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize WebSocket events
    register_socketio_events(socketio)
    
    return app

def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints for API routes.
    
    Args:
        app: Flask application instance
    """
    try:
        from backend.api.auth_routes import auth_bp
        from backend.api.trading_routes import trading_bp
        from backend.api.backtest_routes import backtest_bp
        from backend.api.user_routes import user_bp
        from backend.api.admin_routes import admin_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
        app.register_blueprint(trading_bp, url_prefix='/api/v1/trading')
        app.register_blueprint(backtest_bp, url_prefix='/api/v1/backtest')
        app.register_blueprint(user_bp, url_prefix='/api/v1/user')
        app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
        
        logger.info("API blueprints registered successfully")
    except ImportError as e:
        logger.error(f"Failed to register blueprints: {e}")

def register_socketio_events(socketio: SocketIO) -> None:
    """
    Register WebSocket event handlers.
    
    Args:
        socketio: SocketIO instance
    """
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected to WebSocket")
        socketio.emit('status', {'message': 'Connected to TradingBot Pro'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected from WebSocket")
    
    @socketio.on('subscribe_market_data')
    def handle_market_subscription(data):
        symbol = data.get('symbol')
        if symbol and trading_engine:
            # Subscribe to real-time market data
            trading_engine.market_data_manager.subscribe_to_symbol(symbol)
            logger.info(f"Subscribed to market data for {symbol}")
    
    @socketio.on('get_bot_status')
    def handle_bot_status_request():
        if trading_engine:
            active_bots = trading_engine.get_active_bots()
            socketio.emit('bot_status_update', active_bots)

def initialize_trading_engine() -> TradingEngine:
    """
    Initialize the trading engine with configuration.
    
    Returns:
        Configured TradingEngine instance
    """
    config = TradingBotConfig(
        max_concurrent_bots=int(os.getenv('MAX_CONCURRENT_BOTS', 10)),
        default_position_size=float(os.getenv('DEFAULT_POSITION_SIZE', 100.0)),
        max_daily_loss=float(os.getenv('MAX_DAILY_LOSS', 1000.0)),
        risk_free_rate=float(os.getenv('PORTFOLIO_RISK_FREE_RATE', 0.02)),
        database_url=os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db'),
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        exchanges={
            'binance': {
                'api_key': os.getenv('BINANCE_API_KEY'),
                'secret_key': os.getenv('BINANCE_SECRET_KEY'),
                'testnet': os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
            },
            'coinbase': {
                'api_key': os.getenv('COINBASE_API_KEY'),
                'secret_key': os.getenv('COINBASE_SECRET_KEY'),
                'passphrase': os.getenv('COINBASE_PASSPHRASE'),
                'sandbox': os.getenv('COINBASE_SANDBOX', 'True').lower() == 'true'
            },
            'kraken': {
                'api_key': os.getenv('KRAKEN_API_KEY'),
                'secret_key': os.getenv('KRAKEN_SECRET_KEY')
            }
        }
    )
    
    return TradingEngine(config)

def setup_signal_handlers() -> None:
    """
    Setup signal handlers for graceful shutdown.
    """
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        cleanup_and_exit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, signal_handler)

def cleanup_and_exit() -> None:
    """
    Perform cleanup operations before exit.
    """
    global trading_engine
    
    logger.info("Starting cleanup process...")
    
    if trading_engine:
        try:
            # Stop all active bots
            trading_engine.emergency_stop_all()
            
            # Cleanup resources
            trading_engine.cleanup()
            
            logger.info("Trading engine cleanup completed")
        except Exception as e:
            logger.error(f"Error during trading engine cleanup: {e}")
    
    logger.info("Cleanup completed. Exiting...")
    sys.exit(0)

def check_prerequisites() -> bool:
    """
    Check if all prerequisites are met before starting.
    
    Returns:
        True if all prerequisites are met, False otherwise
    """
    # Check license
    try:
        if not verify_license():
            logger.error("Invalid or expired license. Please contact support.")
            return False
    except Exception as e:
        logger.warning(f"License verification failed: {e}")
        if os.getenv('ENVIRONMENT') == 'production':
            return False
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False
    
    # Check required environment variables
    required_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    # Check if at least one exchange is configured
    exchanges_configured = any([
        os.getenv('BINANCE_API_KEY'),
        os.getenv('COINBASE_API_KEY'),
        os.getenv('KRAKEN_API_KEY')
    ])
    
    if not exchanges_configured:
        logger.warning("No exchange API keys configured. Trading will be disabled.")
    
    return True

def run_web_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
    """
    Run the web server.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
        debug: Enable debug mode
    """
    global app, socketio
    
    logger.info(f"Starting TradingBot Pro web server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    if socketio:
        socketio.run(app, host=host, port=port, debug=debug, use_reloader=False)
    else:
        app.run(host=host, port=port, debug=debug, use_reloader=False)

def run_cli_mode(args) -> None:
    """
    Run in CLI mode for command-line operations.
    
    Args:
        args: Parsed command line arguments
    """
    global trading_engine
    
    if args.command == 'start-bot':
        bot_id = trading_engine.start_bot(
            strategy=args.strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            parameters=args.parameters or {},
            position_size=args.position_size
        )
        print(f"Started bot with ID: {bot_id}")
    
    elif args.command == 'stop-bot':
        success = trading_engine.stop_bot(args.bot_id)
        print(f"Bot {args.bot_id} {'stopped' if success else 'not found or already stopped'}")
    
    elif args.command == 'list-bots':
        bots = trading_engine.get_active_bots()
        if bots:
            print("\nActive Bots:")
            for bot in bots:
                print(f"  ID: {bot['bot_id']}, Strategy: {bot['strategy']}, Symbol: {bot['symbol']}")
        else:
            print("No active bots")
    
    elif args.command == 'backtest':
        from backend.bot_engine.backtesting_engine import BacktestingEngine
        from backend.bot_engine.strategy_factory import StrategyFactory
        
        backtest_engine = BacktestingEngine()
        strategy = StrategyFactory.create_strategy(args.strategy, args.parameters or {})
        
        results = backtest_engine.run_backtest(
            strategy=strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            days=args.days
        )
        
        print(f"\nBacktest Results for {args.strategy} on {args.symbol}:")
        print(f"Total Return: {results.total_return:.2%}")
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {results.max_drawdown:.2%}")
        print(f"Win Rate: {results.win_rate:.2%}")
        print(f"Total Trades: {results.total_trades}")

def main() -> None:
    """
    Main application entry point.
    """
    global logger, trading_engine
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TradingBot Pro - Professional Cryptocurrency Trading Bot')
    parser.add_argument('--config', default='development', choices=['development', 'testing', 'production'],
                       help='Configuration environment')
    parser.add_argument('--host', default='0.0.0.0', help='Host address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port number to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    
    # CLI-specific arguments
    parser.add_argument('command', nargs='?', choices=['start-bot', 'stop-bot', 'list-bots', 'backtest'],
                       help='CLI command to execute')
    parser.add_argument('--strategy', help='Trading strategy name')
    parser.add_argument('--symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--timeframe', default='1h', help='Timeframe for analysis')
    parser.add_argument('--bot-id', help='Bot ID for stop-bot command')
    parser.add_argument('--position-size', type=float, help='Position size for trading')
    parser.add_argument('--parameters', type=dict, help='Strategy parameters as JSON')
    parser.add_argument('--days', type=int, default=30, help='Number of days for backtesting')
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logger('TradingBot', level=getattr(logging, log_level.upper()))
    
    # Setup signal handlers
    setup_signal_handlers()
    
    logger.info("="*60)
    logger.info("TradingBot Pro v2.0.0 - Professional Trading Bot")
    logger.info("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Exiting...")
        sys.exit(1)
    
    try:
        # Initialize trading engine
        logger.info("Initializing trading engine...")
        trading_engine = initialize_trading_engine()
        logger.info("Trading engine initialized successfully")
        
        if args.cli:
            # Run in CLI mode
            if not args.command:
                parser.error("CLI mode requires a command")
            run_cli_mode(args)
        else:
            # Create and run web application
            app = create_app(args.config)
            
            # Set debug mode based on environment
            debug_mode = args.debug or (os.getenv('DEBUG', 'False').lower() == 'true')
            
            # Run web server
            run_web_server(args.host, args.port, debug_mode)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        cleanup_and_exit()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        cleanup_and_exit()

if __name__ == '__main__':
    main()