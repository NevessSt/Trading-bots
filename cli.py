#!/usr/bin/env python3
"""
TradingBot Pro - Command Line Interface

Provides command-line tools for managing the trading bot:
- Start/stop trading bots
- Run backtests and optimizations
- Monitor portfolio performance
- Manage system health
- Database operations

Usage:
    python cli.py --help
    python cli.py start-bot --strategy rsi --symbol BTCUSDT
    python cli.py backtest --strategy macd --symbol ETHUSDT --days 30
    python cli.py optimize --strategy grid --symbol BTCUSDT

Author: TradingBot Pro Team
Version: 2.0.0
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.bot_engine.trading_engine import TradingEngine, TradingBotConfig
    from backend.bot_engine.backtesting_engine import BacktestingEngine
    from backend.bot_engine.strategy_factory import StrategyFactory
    from backend.bot_engine.portfolio_manager import PortfolioManager
    from backend.bot_engine.market_data_manager import MarketDataManager
    from backend.utils.logger import setup_logger
    from backend.auth.license_manager import verify_license
    from config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)

class TradingBotCLI:
    """
    Command Line Interface for TradingBot Pro.
    """
    
    def __init__(self):
        self.logger = setup_logger('TradingBot-CLI')
        self.trading_engine: Optional[TradingEngine] = None
        self.backtest_engine: Optional[BacktestingEngine] = None
        
    def initialize_engines(self) -> bool:
        """
        Initialize trading and backtesting engines.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load environment variables
            env_file = Path('.env')
            if env_file.exists():
                from dotenv import load_dotenv
                load_dotenv(env_file)
            
            # Verify license
            if not verify_license():
                self.logger.error("Invalid or expired license")
                return False
            
            # Initialize trading engine
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
                    }
                }
            )
            
            self.trading_engine = TradingEngine(config)
            self.backtest_engine = BacktestingEngine()
            
            self.logger.info("Engines initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize engines: {e}")
            return False
    
    def start_bot(self, args) -> None:
        """
        Start a new trading bot.
        
        Args:
            args: Command line arguments
        """
        if not self.trading_engine:
            print("Error: Trading engine not initialized")
            return
        
        try:
            # Parse parameters if provided
            parameters = {}
            if args.parameters:
                parameters = json.loads(args.parameters)
            
            # Parse risk settings
            risk_settings = {}
            if args.stop_loss:
                risk_settings['stop_loss'] = args.stop_loss
            if args.take_profit:
                risk_settings['take_profit'] = args.take_profit
            if args.max_positions:
                risk_settings['max_positions'] = args.max_positions
            
            # Start the bot
            bot_id = self.trading_engine.start_bot(
                strategy=args.strategy,
                symbol=args.symbol,
                timeframe=args.timeframe,
                parameters=parameters,
                risk_settings=risk_settings,
                position_size=args.position_size
            )
            
            print(f"✅ Bot started successfully!")
            print(f"Bot ID: {bot_id}")
            print(f"Strategy: {args.strategy}")
            print(f"Symbol: {args.symbol}")
            print(f"Timeframe: {args.timeframe}")
            print(f"Position Size: {args.position_size}")
            
            if parameters:
                print(f"Parameters: {json.dumps(parameters, indent=2)}")
            
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            self.logger.error(f"Bot start failed: {e}", exc_info=True)
    
    def stop_bot(self, args) -> None:
        """
        Stop a trading bot.
        
        Args:
            args: Command line arguments
        """
        if not self.trading_engine:
            print("Error: Trading engine not initialized")
            return
        
        try:
            success = self.trading_engine.stop_bot(args.bot_id)
            
            if success:
                print(f"✅ Bot {args.bot_id} stopped successfully")
            else:
                print(f"❌ Bot {args.bot_id} not found or already stopped")
                
        except Exception as e:
            print(f"❌ Failed to stop bot: {e}")
            self.logger.error(f"Bot stop failed: {e}", exc_info=True)
    
    def list_bots(self, args) -> None:
        """
        List all active trading bots.
        
        Args:
            args: Command line arguments
        """
        if not self.trading_engine:
            print("Error: Trading engine not initialized")
            return
        
        try:
            bots = self.trading_engine.get_active_bots()
            
            if not bots:
                print("No active bots")
                return
            
            print(f"\n📊 Active Bots ({len(bots)}):")
            print("=" * 80)
            
            for bot in bots:
                print(f"Bot ID: {bot['bot_id']}")
                print(f"Strategy: {bot['strategy']}")
                print(f"Symbol: {bot['symbol']}")
                print(f"Status: {bot['status']}")
                print(f"P&L: ${bot.get('pnl', 0):.2f}")
                print(f"Positions: {bot.get('positions', 0)}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Failed to list bots: {e}")
            self.logger.error(f"Bot listing failed: {e}", exc_info=True)
    
    def run_backtest(self, args) -> None:
        """
        Run a strategy backtest.
        
        Args:
            args: Command line arguments
        """
        if not self.backtest_engine:
            print("Error: Backtest engine not initialized")
            return
        
        try:
            # Parse parameters
            parameters = {}
            if args.parameters:
                parameters = json.loads(args.parameters)
            else:
                # Get default parameters
                parameters = StrategyFactory.get_default_parameters(args.strategy)
            
            # Create strategy
            strategy = StrategyFactory.create_strategy(args.strategy, parameters)
            
            print(f"🔄 Running backtest...")
            print(f"Strategy: {args.strategy}")
            print(f"Symbol: {args.symbol}")
            print(f"Timeframe: {args.timeframe}")
            print(f"Days: {args.days}")
            print(f"Initial Balance: ${args.initial_balance}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            # Run backtest
            results = self.backtest_engine.run_backtest(
                strategy=strategy,
                symbol=args.symbol,
                timeframe=args.timeframe,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_balance=args.initial_balance
            )
            
            # Display results
            print("\n📈 Backtest Results:")
            print("=" * 50)
            print(f"Total Return: {results.total_return:.2%}")
            print(f"Annual Return: {results.annual_return:.2%}")
            print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
            print(f"Sortino Ratio: {results.sortino_ratio:.2f}")
            print(f"Max Drawdown: {results.max_drawdown:.2%}")
            print(f"Win Rate: {results.win_rate:.2%}")
            print(f"Profit Factor: {results.profit_factor:.2f}")
            print(f"Total Trades: {results.total_trades}")
            print(f"Winning Trades: {results.winning_trades}")
            print(f"Losing Trades: {results.losing_trades}")
            print(f"Average Trade: ${results.avg_trade:.2f}")
            print(f"Best Trade: ${results.best_trade:.2f}")
            print(f"Worst Trade: ${results.worst_trade:.2f}")
            
            # Save results if requested
            if args.save_results:
                filename = f"backtest_{args.strategy}_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(results.__dict__, f, indent=2, default=str)
                print(f"\n💾 Results saved to: {filename}")
                
        except Exception as e:
            print(f"❌ Backtest failed: {e}")
            self.logger.error(f"Backtest failed: {e}", exc_info=True)
    
    def optimize_strategy(self, args) -> None:
        """
        Optimize strategy parameters.
        
        Args:
            args: Command line arguments
        """
        if not self.backtest_engine:
            print("Error: Backtest engine not initialized")
            return
        
        try:
            # Parse parameter ranges
            param_ranges = {}
            if args.param_ranges:
                param_ranges = json.loads(args.param_ranges)
            else:
                # Use default ranges based on strategy
                if args.strategy == 'rsi':
                    param_ranges = {
                        'rsi_period': range(10, 21),
                        'oversold_threshold': range(20, 35),
                        'overbought_threshold': range(65, 81)
                    }
                elif args.strategy == 'macd':
                    param_ranges = {
                        'fast_period': range(8, 15),
                        'slow_period': range(20, 30),
                        'signal_period': range(7, 12)
                    }
                elif args.strategy == 'ema_crossover':
                    param_ranges = {
                        'fast_ema': range(5, 15),
                        'slow_ema': range(20, 50)
                    }
                else:
                    print(f"No default parameter ranges for strategy: {args.strategy}")
                    return
            
            print(f"🔄 Optimizing strategy parameters...")
            print(f"Strategy: {args.strategy}")
            print(f"Symbol: {args.symbol}")
            print(f"Parameter ranges: {param_ranges}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            # Run optimization
            optimal_params = self.backtest_engine.optimize_parameters(
                strategy_name=args.strategy,
                symbol=args.symbol,
                timeframe=args.timeframe,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                param_ranges=param_ranges,
                initial_balance=args.initial_balance,
                optimization_target=args.optimization_target
            )
            
            print("\n🎯 Optimization Results:")
            print("=" * 50)
            print(f"Optimal Parameters: {json.dumps(optimal_params['parameters'], indent=2)}")
            print(f"Best {args.optimization_target}: {optimal_params['score']:.4f}")
            
            # Save results if requested
            if args.save_results:
                filename = f"optimization_{args.strategy}_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(optimal_params, f, indent=2, default=str)
                print(f"\n💾 Results saved to: {filename}")
                
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            self.logger.error(f"Optimization failed: {e}", exc_info=True)
    
    def show_portfolio(self, args) -> None:
        """
        Show portfolio summary.
        
        Args:
            args: Command line arguments
        """
        if not self.trading_engine:
            print("Error: Trading engine not initialized")
            return
        
        try:
            portfolio = self.trading_engine.get_portfolio_summary()
            
            print("\n💼 Portfolio Summary:")
            print("=" * 50)
            print(f"Total Value: ${portfolio.get('total_value', 0):.2f}")
            print(f"Available Balance: ${portfolio.get('available_balance', 0):.2f}")
            print(f"Total P&L: ${portfolio.get('total_pnl', 0):.2f}")
            print(f"Daily P&L: ${portfolio.get('daily_pnl', 0):.2f}")
            print(f"Total Return: {portfolio.get('total_return', 0):.2%}")
            print(f"Sharpe Ratio: {portfolio.get('sharpe_ratio', 0):.2f}")
            print(f"Max Drawdown: {portfolio.get('max_drawdown', 0):.2%}")
            print(f"Active Positions: {portfolio.get('active_positions', 0)}")
            
            # Show positions if any
            positions = portfolio.get('positions', [])
            if positions:
                print("\n📊 Active Positions:")
                print("-" * 50)
                for pos in positions:
                    print(f"Symbol: {pos['symbol']}")
                    print(f"Size: {pos['size']}")
                    print(f"Entry Price: ${pos['entry_price']:.4f}")
                    print(f"Current Price: ${pos['current_price']:.4f}")
                    print(f"P&L: ${pos['pnl']:.2f}")
                    print("-" * 30)
                    
        except Exception as e:
            print(f"❌ Failed to get portfolio: {e}")
            self.logger.error(f"Portfolio retrieval failed: {e}", exc_info=True)
    
    def show_market_data(self, args) -> None:
        """
        Show market data for a symbol.
        
        Args:
            args: Command line arguments
        """
        try:
            market_manager = MarketDataManager()
            
            # Get ticker data
            ticker = market_manager.get_ticker(args.symbol)
            
            print(f"\n📊 Market Data for {args.symbol}:")
            print("=" * 50)
            print(f"Price: ${ticker.get('price', 0):.4f}")
            print(f"24h Change: {ticker.get('change_24h', 0):.2%}")
            print(f"24h Volume: {ticker.get('volume_24h', 0):,.0f}")
            print(f"24h High: ${ticker.get('high_24h', 0):.4f}")
            print(f"24h Low: ${ticker.get('low_24h', 0):.4f}")
            print(f"Bid: ${ticker.get('bid', 0):.4f}")
            print(f"Ask: ${ticker.get('ask', 0):.4f}")
            print(f"Spread: {ticker.get('spread', 0):.4f}")
            
        except Exception as e:
            print(f"❌ Failed to get market data: {e}")
            self.logger.error(f"Market data retrieval failed: {e}", exc_info=True)
    
    def show_system_health(self, args) -> None:
        """
        Show system health status.
        
        Args:
            args: Command line arguments
        """
        if not self.trading_engine:
            print("Error: Trading engine not initialized")
            return
        
        try:
            health = self.trading_engine.get_system_health()
            
            print("\n🏥 System Health:")
            print("=" * 50)
            print(f"Overall Status: {'✅ Healthy' if health.get('healthy', False) else '❌ Unhealthy'}")
            print(f"Database: {'✅ Connected' if health.get('database', False) else '❌ Disconnected'}")
            print(f"Redis: {'✅ Connected' if health.get('redis', False) else '❌ Disconnected'}")
            print(f"Exchanges: {health.get('exchanges_connected', 0)}/{health.get('total_exchanges', 0)} Connected")
            print(f"Active Bots: {health.get('active_bots', 0)}")
            print(f"Memory Usage: {health.get('memory_usage', 0):.1f}%")
            print(f"CPU Usage: {health.get('cpu_usage', 0):.1f}%")
            print(f"Uptime: {health.get('uptime', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Failed to get system health: {e}")
            self.logger.error(f"System health check failed: {e}", exc_info=True)

def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description='TradingBot Pro - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py start-bot --strategy rsi --symbol BTCUSDT --timeframe 1h
  python cli.py backtest --strategy macd --symbol ETHUSDT --days 30
  python cli.py optimize --strategy grid --symbol BTCUSDT --days 60
  python cli.py list-bots
  python cli.py portfolio
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start bot command
    start_parser = subparsers.add_parser('start-bot', help='Start a new trading bot')
    start_parser.add_argument('--strategy', required=True, help='Trading strategy name')
    start_parser.add_argument('--symbol', required=True, help='Trading symbol (e.g., BTCUSDT)')
    start_parser.add_argument('--timeframe', default='1h', help='Timeframe for analysis')
    start_parser.add_argument('--position-size', type=float, help='Position size for trading')
    start_parser.add_argument('--parameters', help='Strategy parameters as JSON string')
    start_parser.add_argument('--stop-loss', type=float, help='Stop loss percentage')
    start_parser.add_argument('--take-profit', type=float, help='Take profit percentage')
    start_parser.add_argument('--max-positions', type=int, help='Maximum concurrent positions')
    
    # Stop bot command
    stop_parser = subparsers.add_parser('stop-bot', help='Stop a trading bot')
    stop_parser.add_argument('--bot-id', required=True, help='Bot ID to stop')
    
    # List bots command
    list_parser = subparsers.add_parser('list-bots', help='List all active trading bots')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run strategy backtest')
    backtest_parser.add_argument('--strategy', required=True, help='Trading strategy name')
    backtest_parser.add_argument('--symbol', required=True, help='Trading symbol')
    backtest_parser.add_argument('--timeframe', default='1h', help='Timeframe for analysis')
    backtest_parser.add_argument('--days', type=int, default=30, help='Number of days to backtest')
    backtest_parser.add_argument('--initial-balance', type=float, default=10000, help='Initial balance')
    backtest_parser.add_argument('--parameters', help='Strategy parameters as JSON string')
    backtest_parser.add_argument('--save-results', action='store_true', help='Save results to file')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize strategy parameters')
    optimize_parser.add_argument('--strategy', required=True, help='Trading strategy name')
    optimize_parser.add_argument('--symbol', required=True, help='Trading symbol')
    optimize_parser.add_argument('--timeframe', default='1h', help='Timeframe for analysis')
    optimize_parser.add_argument('--days', type=int, default=60, help='Number of days for optimization')
    optimize_parser.add_argument('--initial-balance', type=float, default=10000, help='Initial balance')
    optimize_parser.add_argument('--param-ranges', help='Parameter ranges as JSON string')
    optimize_parser.add_argument('--optimization-target', default='sharpe_ratio', 
                               choices=['total_return', 'sharpe_ratio', 'sortino_ratio', 'profit_factor'],
                               help='Optimization target metric')
    optimize_parser.add_argument('--save-results', action='store_true', help='Save results to file')
    
    # Portfolio command
    portfolio_parser = subparsers.add_parser('portfolio', help='Show portfolio summary')
    
    # Market data command
    market_parser = subparsers.add_parser('market', help='Show market data')
    market_parser.add_argument('--symbol', required=True, help='Trading symbol')
    
    # System health command
    health_parser = subparsers.add_parser('health', help='Show system health status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = TradingBotCLI()
    
    if not cli.initialize_engines():
        print("❌ Failed to initialize engines")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'start-bot':
            cli.start_bot(args)
        elif args.command == 'stop-bot':
            cli.stop_bot(args)
        elif args.command == 'list-bots':
            cli.list_bots(args)
        elif args.command == 'backtest':
            cli.run_backtest(args)
        elif args.command == 'optimize':
            cli.optimize_strategy(args)
        elif args.command == 'portfolio':
            cli.show_portfolio(args)
        elif args.command == 'market':
            cli.show_market_data(args)
        elif args.command == 'health':
            cli.show_system_health(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Command failed: {e}")
        cli.logger.error(f"CLI command failed: {e}", exc_info=True)

if __name__ == '__main__':
    main()