import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from .base_strategy import BaseStrategy
import asyncio
import logging

class ArbitrageStrategy(BaseStrategy):
    """Arbitrage Strategy for cross-exchange price differences
    
    This strategy identifies and exploits price differences between:
    - Different exchanges for the same trading pair
    - Different trading pairs on the same exchange (triangular arbitrage)
    - Spot vs futures price differences
    
    Features:
    - Real-time price monitoring across multiple exchanges
    - Automatic opportunity detection
    - Risk management with slippage protection
    - Transaction cost optimization
    - Latency-aware execution
    """
    
    def __init__(self, **params):
        super().__init__()
        
        # Strategy parameters
        self.min_profit_threshold = params.get('min_profit_threshold', 0.005)  # 0.5% minimum profit
        self.max_position_size = params.get('max_position_size', 1000)  # Max USD per trade
        self.slippage_tolerance = params.get('slippage_tolerance', 0.002)  # 0.2% slippage tolerance
        self.transaction_cost = params.get('transaction_cost', 0.001)  # 0.1% transaction cost
        self.max_execution_time = params.get('max_execution_time', 30)  # 30 seconds max execution
        self.price_update_interval = params.get('price_update_interval', 1)  # 1 second price updates
        
        # Arbitrage types
        self.enable_cross_exchange = params.get('enable_cross_exchange', True)
        self.enable_triangular = params.get('enable_triangular', True)
        self.enable_spot_futures = params.get('enable_spot_futures', False)
        
        # Risk management
        self.max_daily_trades = params.get('max_daily_trades', 50)
        self.max_concurrent_trades = params.get('max_concurrent_trades', 3)
        self.cooldown_period = params.get('cooldown_period', 60)  # 60 seconds between trades
        
        # Internal state
        self.active_opportunities = {}
        self.trade_history = []
        self.last_trade_time = 0
        self.daily_trade_count = 0
        
        self.logger = logging.getLogger(__name__)
        
    def get_name(self) -> str:
        return "Arbitrage Strategy"
    
    def get_description(self) -> str:
        return "Exploits price differences between exchanges and trading pairs for risk-free profits"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'min_profit_threshold': {
                'type': 'float',
                'default': 0.005,
                'min': 0.001,
                'max': 0.02,
                'description': 'Minimum profit threshold (as decimal, e.g., 0.005 = 0.5%)'
            },
            'max_position_size': {
                'type': 'float',
                'default': 1000,
                'min': 100,
                'max': 10000,
                'description': 'Maximum position size in USD'
            },
            'slippage_tolerance': {
                'type': 'float',
                'default': 0.002,
                'min': 0.001,
                'max': 0.01,
                'description': 'Maximum acceptable slippage (as decimal)'
            },
            'transaction_cost': {
                'type': 'float',
                'default': 0.001,
                'min': 0.0005,
                'max': 0.005,
                'description': 'Estimated transaction cost per trade (as decimal)'
            },
            'max_execution_time': {
                'type': 'integer',
                'default': 30,
                'min': 10,
                'max': 120,
                'description': 'Maximum execution time in seconds'
            },
            'enable_cross_exchange': {
                'type': 'boolean',
                'default': True,
                'description': 'Enable cross-exchange arbitrage'
            },
            'enable_triangular': {
                'type': 'boolean',
                'default': True,
                'description': 'Enable triangular arbitrage'
            },
            'enable_spot_futures': {
                'type': 'boolean',
                'default': False,
                'description': 'Enable spot-futures arbitrage'
            },
            'max_daily_trades': {
                'type': 'integer',
                'default': 50,
                'min': 10,
                'max': 200,
                'description': 'Maximum trades per day'
            },
            'max_concurrent_trades': {
                'type': 'integer',
                'default': 3,
                'min': 1,
                'max': 10,
                'description': 'Maximum concurrent arbitrage trades'
            }
        }
    
    def should_buy(self, data: Dict[str, Any]) -> bool:
        """Check if arbitrage opportunity exists for buying"""
        try:
            # Check if we can execute more trades
            if not self._can_trade():
                return False
            
            # Get current prices from multiple sources
            opportunities = self._find_arbitrage_opportunities(data)
            
            if not opportunities:
                return False
            
            # Select best opportunity
            best_opportunity = max(opportunities, key=lambda x: x['profit_potential'])
            
            # Validate opportunity
            if self._validate_opportunity(best_opportunity):
                self.active_opportunities[best_opportunity['id']] = best_opportunity
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in should_buy: {e}")
            return False
    
    def should_sell(self, data: Dict[str, Any]) -> bool:
        """Check if we should close arbitrage positions"""
        try:
            # Check active opportunities for completion
            for opp_id, opportunity in list(self.active_opportunities.items()):
                if self._should_close_opportunity(opportunity, data):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in should_sell: {e}")
            return False
    
    def get_position_size(self, data: Dict[str, Any]) -> float:
        """Calculate optimal position size for arbitrage"""
        try:
            # Get the best active opportunity
            if not self.active_opportunities:
                return 0
            
            best_opp = max(self.active_opportunities.values(), 
                          key=lambda x: x['profit_potential'])
            
            # Calculate position size based on:
            # 1. Available capital
            # 2. Risk limits
            # 3. Market liquidity
            # 4. Profit potential
            
            available_capital = data.get('available_balance', 1000)
            
            # Use smaller of max position size or available capital
            base_size = min(self.max_position_size, available_capital * 0.1)
            
            # Adjust for profit potential
            profit_multiplier = min(2.0, best_opp['profit_potential'] / self.min_profit_threshold)
            
            # Adjust for market liquidity
            liquidity_factor = min(1.0, best_opp.get('liquidity_score', 0.5))
            
            position_size = base_size * profit_multiplier * liquidity_factor
            
            return max(10, min(position_size, self.max_position_size))
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 100  # Default safe size
    
    def _can_trade(self) -> bool:
        """Check if we can execute a new trade"""
        import time
        
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_trade_time < self.cooldown_period:
            return False
        
        # Check daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return False
        
        # Check concurrent trade limit
        if len(self.active_opportunities) >= self.max_concurrent_trades:
            return False
        
        return True
    
    def _find_arbitrage_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find available arbitrage opportunities"""
        opportunities = []
        
        try:
            # Cross-exchange arbitrage
            if self.enable_cross_exchange:
                cross_exchange_opps = self._find_cross_exchange_opportunities(data)
                opportunities.extend(cross_exchange_opps)
            
            # Triangular arbitrage
            if self.enable_triangular:
                triangular_opps = self._find_triangular_opportunities(data)
                opportunities.extend(triangular_opps)
            
            # Spot-futures arbitrage
            if self.enable_spot_futures:
                spot_futures_opps = self._find_spot_futures_opportunities(data)
                opportunities.extend(spot_futures_opps)
            
        except Exception as e:
            self.logger.error(f"Error finding opportunities: {e}")
        
        return opportunities
    
    def _find_cross_exchange_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find cross-exchange arbitrage opportunities"""
        opportunities = []
        
        # Mock implementation - in real scenario, you'd connect to multiple exchanges
        symbol = data.get('symbol', 'BTC/USDT')
        current_price = data.get('close', 0)
        
        if current_price <= 0:
            return opportunities
        
        # Simulate price differences between exchanges
        exchanges = {
            'binance': current_price * (1 + np.random.normal(0, 0.001)),
            'coinbase': current_price * (1 + np.random.normal(0, 0.001)),
            'kraken': current_price * (1 + np.random.normal(0, 0.001))
        }
        
        # Find profitable pairs
        exchange_pairs = [(ex1, ex2) for ex1 in exchanges for ex2 in exchanges if ex1 != ex2]
        
        for buy_exchange, sell_exchange in exchange_pairs:
            buy_price = exchanges[buy_exchange]
            sell_price = exchanges[sell_exchange]
            
            # Calculate profit potential
            profit_potential = (sell_price - buy_price) / buy_price - (2 * self.transaction_cost)
            
            if profit_potential > self.min_profit_threshold:
                opportunities.append({
                    'id': f"cross_{buy_exchange}_{sell_exchange}_{int(time.time())}",
                    'type': 'cross_exchange',
                    'buy_exchange': buy_exchange,
                    'sell_exchange': sell_exchange,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'profit_potential': profit_potential,
                    'symbol': symbol,
                    'liquidity_score': 0.8,  # Mock liquidity score
                    'timestamp': time.time()
                })
        
        return opportunities
    
    def _find_triangular_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find triangular arbitrage opportunities"""
        opportunities = []
        
        # Mock implementation for triangular arbitrage
        # In real scenario, you'd analyze BTC/USDT, ETH/USDT, BTC/ETH rates
        
        base_price = data.get('close', 0)
        if base_price <= 0:
            return opportunities
        
        # Simulate triangular opportunity
        # Example: USDT -> BTC -> ETH -> USDT
        btc_usdt = base_price
        eth_usdt = base_price * 0.065  # Mock ETH price
        btc_eth = btc_usdt / eth_usdt
        
        # Calculate if triangular trade is profitable
        # Start with 1000 USDT
        start_amount = 1000
        btc_amount = start_amount / btc_usdt
        eth_amount = btc_amount * btc_eth
        final_usdt = eth_amount * eth_usdt
        
        profit_potential = (final_usdt - start_amount) / start_amount - (3 * self.transaction_cost)
        
        if profit_potential > self.min_profit_threshold:
            opportunities.append({
                'id': f"triangular_{int(time.time())}",
                'type': 'triangular',
                'path': ['USDT', 'BTC', 'ETH', 'USDT'],
                'rates': [btc_usdt, btc_eth, eth_usdt],
                'profit_potential': profit_potential,
                'liquidity_score': 0.7,
                'timestamp': time.time()
            })
        
        return opportunities
    
    def _find_spot_futures_opportunities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find spot-futures arbitrage opportunities"""
        opportunities = []
        
        # Mock implementation for spot-futures arbitrage
        spot_price = data.get('close', 0)
        if spot_price <= 0:
            return opportunities
        
        # Simulate futures price with contango/backwardation
        futures_price = spot_price * (1 + np.random.normal(0.001, 0.002))
        
        profit_potential = abs(futures_price - spot_price) / spot_price - (2 * self.transaction_cost)
        
        if profit_potential > self.min_profit_threshold:
            opportunities.append({
                'id': f"spot_futures_{int(time.time())}",
                'type': 'spot_futures',
                'spot_price': spot_price,
                'futures_price': futures_price,
                'profit_potential': profit_potential,
                'liquidity_score': 0.9,
                'timestamp': time.time()
            })
        
        return opportunities
    
    def _validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Validate if opportunity is still profitable and executable"""
        try:
            # Check if profit is above threshold
            if opportunity['profit_potential'] < self.min_profit_threshold:
                return False
            
            # Check if opportunity is not too old
            import time
            if time.time() - opportunity['timestamp'] > self.max_execution_time:
                return False
            
            # Check liquidity
            if opportunity.get('liquidity_score', 0) < 0.5:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating opportunity: {e}")
            return False
    
    def _should_close_opportunity(self, opportunity: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Check if we should close an active arbitrage opportunity"""
        try:
            import time
            
            # Close if opportunity is too old
            if time.time() - opportunity['timestamp'] > self.max_execution_time:
                return True
            
            # Close if profit potential has decreased significantly
            current_profit = self._calculate_current_profit(opportunity, data)
            if current_profit < self.min_profit_threshold * 0.5:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking close condition: {e}")
            return True  # Close on error to be safe
    
    def _calculate_current_profit(self, opportunity: Dict[str, Any], data: Dict[str, Any]) -> float:
        """Calculate current profit potential for an opportunity"""
        try:
            # This would recalculate profit based on current market prices
            # For now, return the original profit potential with some decay
            import time
            age = time.time() - opportunity['timestamp']
            decay_factor = max(0.5, 1 - (age / self.max_execution_time))
            
            return opportunity['profit_potential'] * decay_factor
            
        except Exception as e:
            self.logger.error(f"Error calculating current profit: {e}")
            return 0
    
    def on_trade_executed(self, trade_data: Dict[str, Any]):
        """Called when a trade is executed"""
        import time
        
        self.last_trade_time = time.time()
        self.daily_trade_count += 1
        
        # Remove completed opportunity
        if 'opportunity_id' in trade_data:
            self.active_opportunities.pop(trade_data['opportunity_id'], None)
        
        # Log trade
        self.trade_history.append({
            'timestamp': time.time(),
            'trade_data': trade_data,
            'profit': trade_data.get('profit', 0)
        })
        
        self.logger.info(f"Arbitrage trade executed: {trade_data}")
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        try:
            if not self.trade_history:
                return {
                    'total_trades': 0,
                    'total_profit': 0,
                    'win_rate': 0,
                    'avg_profit_per_trade': 0,
                    'active_opportunities': len(self.active_opportunities)
                }
            
            profits = [trade['profit'] for trade in self.trade_history if 'profit' in trade]
            winning_trades = [p for p in profits if p > 0]
            
            return {
                'total_trades': len(self.trade_history),
                'total_profit': sum(profits),
                'win_rate': len(winning_trades) / len(profits) if profits else 0,
                'avg_profit_per_trade': np.mean(profits) if profits else 0,
                'active_opportunities': len(self.active_opportunities),
                'daily_trades_remaining': self.max_daily_trades - self.daily_trade_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting strategy stats: {e}")
            return {'error': str(e)}