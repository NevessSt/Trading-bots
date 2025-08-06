import pandas as pd
import numpy as np

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self):
        """Initialize the base strategy"""
        self.name = 'Base Strategy'
        self.description = 'Base strategy class that all strategies inherit from'
    
    def generate_signals(self, df):
        """Generate trading signals
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement generate_signals()")
    
    def get_parameters(self):
        """Get strategy parameters
        
        Returns:
            dict: Strategy parameters
        """
        # This method should be implemented by subclasses
        return {}
    
    def set_parameters(self, parameters):
        """Set strategy parameters
        
        Args:
            parameters (dict): Strategy parameters
        """
        # This method should be implemented by subclasses
        pass
    
    def get_name(self):
        """Get strategy name
        
        Returns:
            str: Strategy name
        """
        return self.name
    
    def get_description(self):
        """Get strategy description
        
        Returns:
            str: Strategy description
        """
        return self.description
    
    def backtest(self, df, initial_capital=10000.0):
        """Backtest the strategy
        
        Args:
            df (pandas.DataFrame): OHLCV data
            initial_capital (float): Initial capital
            
        Returns:
            dict: Backtest results
        """
        # Generate signals
        signals_df = self.generate_signals(df)
        
        # Initialize portfolio and holdings
        positions = pd.Series(index=signals_df.index).fillna(0.0)
        portfolio = pd.DataFrame(index=signals_df.index)
        portfolio['positions'] = positions
        portfolio['cash'] = initial_capital
        portfolio['holdings'] = 0.0
        portfolio['total'] = 0.0
        
        # Calculate positions and holdings
        for i in range(len(signals_df)):
            # Update positions based on signals
            if i > 0:
                portfolio['positions'].iloc[i] = portfolio['positions'].iloc[i-1]
            
            # Buy signal
            if signals_df['signal'].iloc[i] == 1:
                # Calculate shares to buy
                price = signals_df['close'].iloc[i]
                available_cash = portfolio['cash'].iloc[i-1] if i > 0 else initial_capital
                shares_to_buy = available_cash / price
                
                # Update positions and cash
                portfolio['positions'].iloc[i] = shares_to_buy
                portfolio['cash'].iloc[i] = 0.0
            
            # Sell signal
            elif signals_df['signal'].iloc[i] == -1:
                # Calculate cash from selling
                price = signals_df['close'].iloc[i]
                shares_to_sell = portfolio['positions'].iloc[i]
                cash_from_selling = shares_to_sell * price
                
                # Update positions and cash
                portfolio['positions'].iloc[i] = 0.0
                portfolio['cash'].iloc[i] = cash_from_selling
            
            # No signal
            else:
                if i > 0:
                    portfolio['cash'].iloc[i] = portfolio['cash'].iloc[i-1]
                else:
                    portfolio['cash'].iloc[i] = initial_capital
            
            # Update holdings and total
            portfolio['holdings'].iloc[i] = portfolio['positions'].iloc[i] * signals_df['close'].iloc[i]
            portfolio['total'].iloc[i] = portfolio['cash'].iloc[i] + portfolio['holdings'].iloc[i]
        
        # Calculate returns
        portfolio['returns'] = portfolio['total'].pct_change()
        
        # Calculate metrics
        total_return = (portfolio['total'].iloc[-1] - initial_capital) / initial_capital
        annual_return = total_return / (len(signals_df) / 252)  # Assuming 252 trading days per year
        sharpe_ratio = portfolio['returns'].mean() / portfolio['returns'].std() * np.sqrt(252)
        max_drawdown = (portfolio['total'] / portfolio['total'].cummax() - 1.0).min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'portfolio': portfolio
        }