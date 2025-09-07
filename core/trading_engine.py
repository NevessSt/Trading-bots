"""Core Trading Engine

This module provides the main trading engine that coordinates all trading activities.
It integrates with risk management, portfolio management, and strategy execution.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

# Import from existing backend modules
try:
    from backend.bot_engine.trading_engine import TradingEngine as BackendTradingEngine
    from backend.bot_engine.risk_manager import RiskManager as BackendRiskManager
    from backend.bot_engine.portfolio_manager import PortfolioManager as BackendPortfolioManager
    from backend.services.trading_service import TradingService
except ImportError:
    # Fallback for standalone usage
    BackendTradingEngine = None
    BackendRiskManager = None
    BackendPortfolioManager = None
    TradingService = None

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Represents a trading signal with all necessary information"""
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_name: str = "unknown"
    confidence: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class TradingEngine:
    """Main Trading Engine for executing trades and managing positions
    
    This class serves as the central coordinator for all trading activities,
    integrating risk management, portfolio management, and strategy execution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the trading engine with configuration
        
        Args:
            config: Dictionary containing trading configuration including:
                   - exchange settings
                   - risk parameters
                   - portfolio settings
                   - strategy parameters
        """
        self.config = config
        self.is_running = False
        self.active_positions = {}
        self.pending_orders = {}
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Trading Engine initialized successfully")
    
    def _initialize_components(self):
        """Initialize all trading engine components"""
        try:
            # Use existing backend components if available
            if BackendTradingEngine:
                self.backend_engine = BackendTradingEngine(self.config)
            
            # Initialize risk manager
            self.risk_manager = self._create_risk_manager()
            
            # Initialize portfolio manager
            self.portfolio_manager = self._create_portfolio_manager()
            
            logger.info("All trading components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading components: {e}")
            raise
    
    def _create_risk_manager(self):
        """Create and configure risk manager"""
        from .risk_manager import RiskManager
        return RiskManager(self.config.get('risk', {}))
    
    def _create_portfolio_manager(self):
        """Create and configure portfolio manager"""
        from .portfolio_manager import PortfolioManager
        return PortfolioManager(self.config.get('portfolio', {}))
    
    async def start(self):
        """Start the trading engine"""
        if self.is_running:
            logger.warning("Trading engine is already running")
            return
        
        try:
            logger.info("Starting trading engine...")
            self.is_running = True
            
            # Start all components
            await self._start_components()
            
            logger.info("Trading engine started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the trading engine"""
        if not self.is_running:
            logger.warning("Trading engine is not running")
            return
        
        try:
            logger.info("Stopping trading engine...")
            self.is_running = False
            
            # Stop all components
            await self._stop_components()
            
            logger.info("Trading engine stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
            raise
    
    async def _start_components(self):
        """Start all engine components"""
        # Start risk manager
        if hasattr(self.risk_manager, 'start'):
            await self.risk_manager.start()
        
        # Start portfolio manager
        if hasattr(self.portfolio_manager, 'start'):
            await self.portfolio_manager.start()
    
    async def _stop_components(self):
        """Stop all engine components"""
        # Stop portfolio manager
        if hasattr(self.portfolio_manager, 'stop'):
            await self.portfolio_manager.stop()
        
        # Stop risk manager
        if hasattr(self.risk_manager, 'stop'):
            await self.risk_manager.stop()
    
    async def execute_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Execute a trading signal with comprehensive risk checks and portfolio updates
        
        This is the main entry point for executing trades. It performs multiple
        validation and safety checks before executing the actual trade.
        
        Args:
            signal: TradeSignal object containing trade information including:
                   - symbol: Trading pair (e.g., 'BTCUSDT')
                   - action: 'BUY' or 'SELL'
                   - quantity: Amount to trade
                   - price: Target price (optional)
                   - stop_loss: Stop loss price (optional)
                   - take_profit: Take profit price (optional)
            
        Returns:
            Dictionary containing execution results with keys:
            - success: Boolean indicating if trade was successful
            - error: Error message if trade failed
            - order_id: Unique identifier for the executed order
            - execution_details: Additional trade execution information
        """
        try:
            logger.info(f"Processing trade signal: {signal.action} {signal.quantity} {signal.symbol} "
                       f"at {signal.price or 'market price'} (confidence: {signal.confidence:.2f})")
            
            # Step 1: Validate signal format and basic requirements
            if not self._validate_signal(signal):
                logger.error(f"Signal validation failed for {signal.symbol}")
                return {'success': False, 'error': 'Invalid signal format or parameters'}
            
            # Step 2: Check risk management constraints
            # This includes position size limits, daily loss limits, and other risk controls
            risk_check = await self.risk_manager.check_trade_risk(signal)
            if not risk_check['approved']:
                logger.warning(f"Trade rejected by risk manager for {signal.symbol}: {risk_check['reason']}")
                return {
                    'success': False, 
                    'error': f"Risk management rejection: {risk_check['reason']}",
                    'risk_details': risk_check
                }
            
            # Step 3: Execute the actual trade on the exchange
            logger.info(f"Risk checks passed, executing trade for {signal.symbol}")
            result = await self._execute_trade(signal)
            
            # Step 4: Update portfolio and position tracking if trade was successful
            if result['success']:
                logger.info(f"Trade executed successfully: {result.get('order_id', 'N/A')}")
                await self.portfolio_manager.update_position(signal, result)
                
                # Store the position in active positions for tracking
                self.active_positions[result.get('order_id', signal.symbol)] = {
                    'signal': signal,
                    'execution_result': result,
                    'timestamp': datetime.utcnow()
                }
            else:
                logger.error(f"Trade execution failed for {signal.symbol}: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error executing signal for {signal.symbol}: {e}")
            return {'success': False, 'error': f'Execution error: {str(e)}'}
    
    def _validate_signal(self, signal: TradeSignal) -> bool:
        """
        Validate a trading signal for correctness and completeness
        
        Performs comprehensive validation of the trading signal to ensure
        all required fields are present and values are within acceptable ranges.
        
        Args:
            signal: TradeSignal to validate containing trade parameters
            
        Returns:
            True if signal passes all validation checks, False otherwise
        """
        try:
            # Check for required fields
            if not signal.symbol:
                logger.error("Signal validation failed: Missing symbol")
                return False
            
            if not signal.action:
                logger.error("Signal validation failed: Missing action")
                return False
            
            # Validate action type
            if signal.action not in ['BUY', 'SELL']:
                logger.error(f"Signal validation failed: Invalid action '{signal.action}'. Must be 'BUY' or 'SELL'")
                return False
            
            # Validate quantity
            if signal.quantity <= 0:
                logger.error(f"Signal validation failed: Invalid quantity {signal.quantity}. Must be positive")
                return False
            
            # Validate price if provided
            if signal.price is not None and signal.price <= 0:
                logger.error(f"Signal validation failed: Invalid price {signal.price}. Must be positive")
                return False
            
            # Validate stop loss if provided
            if signal.stop_loss is not None:
                if signal.stop_loss <= 0:
                    logger.error(f"Signal validation failed: Invalid stop loss {signal.stop_loss}. Must be positive")
                    return False
                
                # For BUY orders, stop loss should be below entry price
                if signal.price and signal.action == 'BUY' and signal.stop_loss >= signal.price:
                    logger.error(f"Signal validation failed: Stop loss {signal.stop_loss} should be below entry price {signal.price} for BUY order")
                    return False
                
                # For SELL orders, stop loss should be above entry price
                if signal.price and signal.action == 'SELL' and signal.stop_loss <= signal.price:
                    logger.error(f"Signal validation failed: Stop loss {signal.stop_loss} should be above entry price {signal.price} for SELL order")
                    return False
            
            # Validate take profit if provided
            if signal.take_profit is not None:
                if signal.take_profit <= 0:
                    logger.error(f"Signal validation failed: Invalid take profit {signal.take_profit}. Must be positive")
                    return False
                
                # For BUY orders, take profit should be above entry price
                if signal.price and signal.action == 'BUY' and signal.take_profit <= signal.price:
                    logger.error(f"Signal validation failed: Take profit {signal.take_profit} should be above entry price {signal.price} for BUY order")
                    return False
                
                # For SELL orders, take profit should be below entry price
                if signal.price and signal.action == 'SELL' and signal.take_profit >= signal.price:
                    logger.error(f"Signal validation failed: Take profit {signal.take_profit} should be below entry price {signal.price} for SELL order")
                    return False
            
            # Validate confidence score
            if signal.confidence < 0 or signal.confidence > 1:
                logger.warning(f"Signal confidence {signal.confidence} is outside normal range [0, 1]")
            
            # Validate symbol format (basic check for common patterns)
            if len(signal.symbol) < 3 or not signal.symbol.replace('/', '').replace('-', '').isalnum():
                logger.error(f"Signal validation failed: Invalid symbol format '{signal.symbol}'")
                return False
            
            logger.debug(f"Signal validation passed for {signal.symbol} {signal.action}")
            return True
            
        except Exception as e:
            logger.error(f"Error during signal validation: {e}")
            return False
    
    async def _execute_trade(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Execute a trade based on the validated signal
        
        This method handles the actual trade execution process, including
        order placement, confirmation, and result tracking. In a production
        environment, this would interface with the exchange API.
        
        Args:
            signal: TradeSignal to execute containing all trade parameters
            
        Returns:
            Dictionary containing comprehensive trade execution results including
            status, trade_id, execution price, fees, and timestamps
        """
        execution_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting trade execution for {signal.symbol} {signal.action} {signal.quantity}")
            
            # Pre-execution checks - In production, check exchange connectivity
            logger.debug("Performing pre-execution validation checks")
            
            # Get current market price for realistic simulation
            # In production, this would query the exchange API
            market_price = signal.price or 50000.0  # Mock market price
            execution_price = signal.price or market_price
            
            # Validate execution price against market conditions
            if signal.price and abs(signal.price - market_price) / market_price > 0.05:  # 5% slippage limit
                logger.warning(f"Large price deviation detected: requested {signal.price}, market {market_price}")
            
            # Simulate order placement and execution
            logger.info(f"Executing {signal.action} order for {signal.quantity} {signal.symbol} at {execution_price}")
            
            # Calculate fees (0.1% trading fee simulation)
            trading_fee = 0.001 * signal.quantity * execution_price
            
            # Generate unique order ID
            order_id = f"order_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Calculate execution metrics
            execution_end_time = datetime.utcnow()
            execution_time_ms = int((execution_end_time - execution_start_time).total_seconds() * 1000)
            
            # Prepare comprehensive execution result
            execution_result = {
                'success': True,
                'order_id': order_id,
                'symbol': signal.symbol,
                'action': signal.action,
                'quantity': signal.quantity,
                'requested_price': signal.price,
                'execution_price': execution_price,
                'market_price': market_price,
                'timestamp': execution_start_time,
                'execution_time_ms': execution_time_ms,
                'fees': trading_fee,
                'status': 'filled',
                'confidence': signal.confidence,
                'strategy_name': signal.strategy_name,
                'slippage': abs(execution_price - market_price) / market_price if market_price > 0 else 0
            }
            
            # Log successful execution with detailed information
            logger.info(f"Trade executed successfully: {signal.symbol} {signal.action} {signal.quantity} @ {execution_price} "
                       f"(fees: {trading_fee:.6f}, execution_time: {execution_time_ms}ms)")
            
            return execution_result
            
        except Exception as e:
            execution_end_time = datetime.utcnow()
            execution_time_ms = int((execution_end_time - execution_start_time).total_seconds() * 1000)
            
            error_msg = f"Trade execution failed for {signal.symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'symbol': signal.symbol,
                'action': signal.action,
                'quantity': signal.quantity,
                'timestamp': execution_start_time,
                'execution_time_ms': execution_time_ms,
                'confidence': signal.confidence
            }
    
    def get_active_positions(self) -> Dict[str, Any]:
        """
        Retrieve all currently active trading positions
        
        This method queries the portfolio manager or exchange API to get
        real-time information about open positions, including unrealized
        profit/loss, position size, and entry prices.
        
        Returns:
            Dictionary containing active positions with the following structure:
            {
                'symbol': {
                    'quantity': float,      # Position size (positive for long, negative for short)
                    'entry_price': float,   # Average entry price
                    'current_price': float, # Current market price
                    'unrealized_pnl': float,# Unrealized profit/loss
                    'percentage_change': float, # Percentage change from entry
                    'timestamp': datetime,  # Position open time
                    'side': str            # 'long' or 'short'
                }
            }
        """
        try:
            # In production, this would query the portfolio manager or exchange API
            if hasattr(self, 'portfolio_manager') and self.portfolio_manager:
                positions = self.portfolio_manager.get_positions() if hasattr(self.portfolio_manager, 'get_positions') else {}
                logger.debug(f"Retrieved {len(positions)} active positions")
                return positions
            else:
                logger.debug("Using internal active positions tracking")
                return self.active_positions.copy()
                
        except Exception as e:
            logger.error(f"Failed to retrieve active positions: {e}")
            return self.active_positions.copy()
    
    def get_pending_orders(self) -> Dict[str, Any]:
        """
        Retrieve all currently pending orders from the exchange
        
        This method queries the exchange API to get information about
        orders that have been placed but not yet filled, including
        limit orders, stop orders, and conditional orders.
        
        Returns:
            Dictionary containing pending orders with the following structure:
            {
                'order_id': {
                    'symbol': str,          # Trading pair symbol
                    'side': str,           # 'buy' or 'sell'
                    'type': str,           # 'limit', 'stop', 'stop_limit', etc.
                    'quantity': float,      # Order quantity
                    'price': float,        # Order price (for limit orders)
                    'stop_price': float,   # Stop price (for stop orders)
                    'filled_quantity': float, # Partially filled amount
                    'remaining_quantity': float, # Remaining unfilled amount
                    'status': str,         # 'pending', 'partial', 'cancelled'
                    'timestamp': datetime, # Order creation time
                    'time_in_force': str   # 'GTC', 'IOC', 'FOK', etc.
                }
            }
        """
        try:
            # In production, this would query the exchange API for open orders
            if hasattr(self, 'backend_engine') and self.backend_engine:
                orders = self.backend_engine.get_open_orders() if hasattr(self.backend_engine, 'get_open_orders') else {}
                logger.debug(f"Retrieved {len(orders)} pending orders")
                return orders
            else:
                logger.debug("Using internal pending orders tracking")
                return self.pending_orders.copy()
                
        except Exception as e:
            logger.error(f"Failed to retrieve pending orders: {e}")
            return self.pending_orders.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information about the trading engine
        
        This method provides detailed information about the engine's current
        state, component health, performance metrics, and operational statistics.
        
        Returns:
            Dictionary containing comprehensive status information:
            {
                'is_running': bool,        # Whether engine is currently running
                'uptime_seconds': float,   # Total uptime in seconds
                'components': dict,        # Status of all components
                'performance': dict,       # Performance metrics
                'health': dict            # Health indicators
            }
        """
        try:
            current_time = datetime.utcnow()
            start_time = getattr(self, 'start_time', current_time)
            uptime_seconds = (current_time - start_time).total_seconds() if hasattr(self, 'start_time') else 0
            
            # Component status check
            components_status = {
                'risk_manager': {
                    'available': hasattr(self, 'risk_manager') and self.risk_manager is not None,
                    'status': getattr(self.risk_manager, 'status', 'unknown') if hasattr(self, 'risk_manager') else 'inactive'
                },
                'portfolio_manager': {
                    'available': hasattr(self, 'portfolio_manager') and self.portfolio_manager is not None,
                    'status': getattr(self.portfolio_manager, 'status', 'unknown') if hasattr(self, 'portfolio_manager') else 'inactive'
                },
                'backend_engine': {
                    'available': hasattr(self, 'backend_engine') and self.backend_engine is not None,
                    'status': 'active' if hasattr(self, 'backend_engine') and self.backend_engine else 'inactive'
                }
            }
            
            # Calculate health score based on component availability
            available_components = sum(1 for comp in components_status.values() if comp['available'])
            total_components = len(components_status)
            health_score = (available_components / total_components) * 100 if total_components > 0 else 0
            
            # Performance metrics
            performance_metrics = {
                'uptime_hours': uptime_seconds / 3600,
                'active_positions_count': len(self.active_positions),
                'pending_orders_count': len(self.pending_orders),
                'trades_executed': getattr(self, '_trades_executed', 0),
                'signals_processed': getattr(self, '_signals_processed', 0),
                'errors_encountered': getattr(self, '_errors_count', 0)
            }
            
            # Health indicators
            health_indicators = {
                'overall_health': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical',
                'health_score_percentage': health_score,
                'last_heartbeat': current_time
            }
            
            status_info = {
                'is_running': self.is_running,
                'start_time': start_time,
                'current_time': current_time,
                'uptime_seconds': uptime_seconds,
                'components': components_status,
                'performance': performance_metrics,
                'health': health_indicators,
                'version': getattr(self, 'version', '1.0.0'),
                'mode': 'production' if hasattr(self, 'backend_engine') and self.backend_engine else 'simulation'
            }
            
            logger.debug(f"Engine status retrieved: {health_indicators['overall_health']} health, {uptime_seconds:.1f}s uptime")
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to retrieve engine status: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e),
                'timestamp': datetime.utcnow()
            }

# Example usage and configuration
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """
        Example usage of the TradingEngine class
        
        This example demonstrates how to:
        1. Initialize the trading engine
        2. Start the engine and its components
        3. Create and execute trading signals
        4. Monitor engine status
        5. Properly shut down the engine
        """
        try:
            print("=== Trading Engine Example ===")
            
            # Step 1: Create trading engine instance with configuration
            print("\n1. Initializing Trading Engine...")
            
            # Example configuration for the trading engine
            config = {
                'exchange': {
                    'name': 'binance',
                    'api_key': 'your_api_key',
                    'secret_key': 'your_secret_key',
                    'testnet': True
                },
                'risk': {
                    'max_position_size': 0.1,  # 10% of portfolio
                    'max_daily_loss': 0.05,    # 5% daily loss limit
                    'stop_loss_percentage': 0.02  # 2% stop loss
                },
                'portfolio': {
                    'initial_balance': 10000,
                    'base_currency': 'USDT'
                }
            }
            
            engine = TradingEngine(config)
            
            # Step 2: Start the engine and initialize all components
            print("\n2. Starting Trading Engine...")
            await engine.start()
            
            # Step 3: Check engine status after startup
            print("\n3. Checking Engine Status...")
            status = engine.get_status()
            print(f"Engine Status: {status['health']['overall_health']}")
            print(f"Components Available: {sum(1 for comp in status['components'].values() if comp['available'])}/3")
            print(f"Mode: {status['mode']}")
            
            # Step 4: Create sample trading signals for demonstration
            print("\n4. Creating Sample Trading Signals...")
            
            # Example 1: Basic BUY signal with stop loss and take profit
            buy_signal = TradeSignal(
                symbol='BTCUSDT',
                action='BUY',
                quantity=0.001,
                price=50000.0,
                confidence=0.8,
                strategy_name='momentum_strategy',
                stop_loss=49000.0,  # 2% stop loss
                take_profit=52000.0  # 4% take profit
            )
            
            # Example 2: Market SELL signal
            sell_signal = TradeSignal(
                symbol='ETHUSDT',
                action='SELL',
                quantity=0.01,
                price=None,  # Market order
                confidence=0.75,
                strategy_name='mean_reversion_strategy',
                stop_loss=3200.0,
                take_profit=2800.0
            )
            
            # Step 5: Execute trading signals
            print("\n5. Executing Trading Signals...")
            
            # Execute BUY signal
            print(f"\nExecuting BUY signal for {buy_signal.symbol}...")
            buy_result = await engine.execute_signal(buy_signal)
            if buy_result.get('success', False):
                print(f"✓ BUY executed: {buy_signal.quantity} {buy_signal.symbol} @ {buy_result.get('execution_price', 'N/A')}")
                print(f"  Order ID: {buy_result.get('order_id', 'N/A')}")
                print(f"  Fees: {buy_result.get('fees', 0):.6f}")
                print(f"  Execution Time: {buy_result.get('execution_time_ms', 0)}ms")
            else:
                print(f"✗ BUY failed: {buy_result.get('error', 'Unknown error')}")
            
            # Execute SELL signal
            print(f"\nExecuting SELL signal for {sell_signal.symbol}...")
            sell_result = await engine.execute_signal(sell_signal)
            if sell_result.get('success', False):
                print(f"✓ SELL executed: {sell_signal.quantity} {sell_signal.symbol} @ {sell_result.get('execution_price', 'N/A')}")
                print(f"  Order ID: {sell_result.get('order_id', 'N/A')}")
                print(f"  Fees: {sell_result.get('fees', 0):.6f}")
                print(f"  Execution Time: {sell_result.get('execution_time_ms', 0)}ms")
            else:
                print(f"✗ SELL failed: {sell_result.get('error', 'Unknown error')}")
            
            # Step 6: Check positions and orders after execution
            print("\n6. Checking Positions and Orders...")
            active_positions = engine.get_active_positions()
            pending_orders = engine.get_pending_orders()
            
            print(f"Active Positions: {len(active_positions)}")
            for symbol, position in active_positions.items():
                print(f"  {symbol}: {position.get('quantity', 0)} @ {position.get('entry_price', 0)}")
            
            print(f"Pending Orders: {len(pending_orders)}")
            for order_id, order in pending_orders.items():
                print(f"  {order_id}: {order.get('side', 'N/A')} {order.get('quantity', 0)} {order.get('symbol', 'N/A')}")
            
            # Step 7: Display final engine statistics
            print("\n7. Final Engine Statistics...")
            final_status = engine.get_status()
            performance = final_status.get('performance', {})
            print(f"Trades Executed: {performance.get('trades_executed', 0)}")
            print(f"Signals Processed: {performance.get('signals_processed', 0)}")
            print(f"Errors Encountered: {performance.get('errors_encountered', 0)}")
            print(f"Uptime: {performance.get('uptime_hours', 0):.2f} hours")
            
            # Step 8: Properly shut down the engine
            print("\n8. Shutting Down Trading Engine...")
            await engine.stop()
            print("✓ Engine stopped successfully")
            
        except Exception as e:
            print(f"\n✗ Example execution failed: {e}")
            logger.error(f"Example execution error: {e}", exc_info=True)
            
            # Ensure engine is stopped even if an error occurred
            try:
                await engine.stop()
            except:
                pass
        
        print("\n=== Example Complete ===")
    
    # Run the comprehensive example
    print("Starting Trading Engine Example...")
    asyncio.run(main())