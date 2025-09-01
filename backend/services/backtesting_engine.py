import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    side: str  # 'long' or 'short'
    pnl: float
    pnl_percentage: float
    fees: float = 0.0
    strategy: str = ""
    notes: str = ""

@dataclass
class BacktestResults:
    """Comprehensive backtest results"""
    # Basic metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Trade analysis
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    profit_factor: float = 0.0
    
    # Time analysis
    avg_trade_duration: float = 0.0
    start_date: datetime = None
    end_date: datetime = None
    
    # Portfolio metrics
    initial_capital: float = 0.0
    final_capital: float = 0.0
    peak_capital: float = 0.0
    
    # Additional metrics
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    monthly_returns: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)

class PerformanceAnalyzer:
    """Advanced performance analysis for backtesting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_metrics(self, trades: List[Trade], equity_curve: pd.Series, 
                         initial_capital: float) -> BacktestResults:
        """Calculate comprehensive performance metrics"""
        results = BacktestResults()
        results.trades = trades
        results.equity_curve = equity_curve
        results.initial_capital = initial_capital
        results.final_capital = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital
        
        if len(trades) == 0:
            return results
        
        # Basic trade statistics
        results.total_trades = len(trades)
        results.winning_trades = len([t for t in trades if t.pnl > 0])
        results.losing_trades = len([t for t in trades if t.pnl < 0])
        results.win_rate = results.winning_trades / results.total_trades if results.total_trades > 0 else 0
        
        # Return calculations
        results.total_return = (results.final_capital - results.initial_capital) / results.initial_capital
        
        # Time-based calculations
        if trades:
            results.start_date = min(t.entry_time for t in trades)
            results.end_date = max(t.exit_time for t in trades)
            days = (results.end_date - results.start_date).days
            results.annualized_return = (1 + results.total_return) ** (365.25 / max(days, 1)) - 1 if days > 0 else 0
        
        # Trade analysis
        winning_trades = [t.pnl for t in trades if t.pnl > 0]
        losing_trades = [t.pnl for t in trades if t.pnl < 0]
        
        results.avg_win = np.mean(winning_trades) if winning_trades else 0
        results.avg_loss = np.mean(losing_trades) if losing_trades else 0
        results.largest_win = max(winning_trades) if winning_trades else 0
        results.largest_loss = min(losing_trades) if losing_trades else 0
        
        # Profit factor
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        results.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades]  # in hours
        results.avg_trade_duration = np.mean(durations) if durations else 0
        
        # Risk metrics
        if len(equity_curve) > 1:
            results.peak_capital = equity_curve.max()
            results = self._calculate_risk_metrics(results, equity_curve)
        
        return results
    
    def _calculate_risk_metrics(self, results: BacktestResults, equity_curve: pd.Series) -> BacktestResults:
        """Calculate risk-adjusted performance metrics"""
        # Calculate returns
        returns = equity_curve.pct_change().dropna()
        
        if len(returns) == 0:
            return results
        
        # Volatility (annualized)
        results.volatility = returns.std() * np.sqrt(252)  # Assuming daily data
        
        # Drawdown calculation
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        results.drawdown_series = drawdown
        results.max_drawdown = abs(drawdown.min())
        
        # Drawdown duration
        drawdown_periods = self._calculate_drawdown_periods(drawdown)
        results.max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = results.annualized_return - risk_free_rate
        results.sharpe_ratio = excess_returns / results.volatility if results.volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        results.sortino_ratio = excess_returns / downside_deviation if downside_deviation > 0 else 0
        
        # Calmar ratio
        results.calmar_ratio = results.annualized_return / results.max_drawdown if results.max_drawdown > 0 else 0
        
        # Monthly returns
        if len(equity_curve) > 30:  # At least a month of data
            monthly_equity = equity_curve.resample('M').last()
            results.monthly_returns = monthly_equity.pct_change().dropna()
        
        return results
    
    def _calculate_drawdown_periods(self, drawdown: pd.Series) -> List[int]:
        """Calculate drawdown periods in days"""
        periods = []
        in_drawdown = False
        start_idx = 0
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                start_idx = i
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                periods.append(i - start_idx)
        
        # Handle case where drawdown continues to end
        if in_drawdown:
            periods.append(len(drawdown) - start_idx)
        
        return periods

class BacktestReportGenerator:
    """Generate comprehensive backtest reports"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, results: BacktestResults, strategy_name: str = "Strategy") -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        report = {
            'strategy_name': strategy_name,
            'generated_at': datetime.now().isoformat(),
            'summary': self._generate_summary(results),
            'detailed_metrics': self._generate_detailed_metrics(results),
            'trade_analysis': self._generate_trade_analysis(results),
            'risk_analysis': self._generate_risk_analysis(results),
            'monthly_performance': self._generate_monthly_performance(results)
        }
        
        # Save report
        report_file = self.output_dir / f"{strategy_name}_backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate visualizations
        self._generate_visualizations(results, strategy_name)
        
        return report
    
    def _generate_summary(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            'total_return_pct': round(results.total_return * 100, 2),
            'annualized_return_pct': round(results.annualized_return * 100, 2),
            'max_drawdown_pct': round(results.max_drawdown * 100, 2),
            'sharpe_ratio': round(results.sharpe_ratio, 2),
            'win_rate_pct': round(results.win_rate * 100, 2),
            'total_trades': results.total_trades,
            'profit_factor': round(results.profit_factor, 2),
            'trading_period_days': (results.end_date - results.start_date).days if results.start_date else 0
        }
    
    def _generate_detailed_metrics(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate detailed performance metrics"""
        return {
            'returns': {
                'total_return': results.total_return,
                'annualized_return': results.annualized_return,
                'volatility': results.volatility,
                'initial_capital': results.initial_capital,
                'final_capital': results.final_capital,
                'peak_capital': results.peak_capital
            },
            'risk_metrics': {
                'max_drawdown': results.max_drawdown,
                'max_drawdown_duration_days': results.max_drawdown_duration,
                'sharpe_ratio': results.sharpe_ratio,
                'sortino_ratio': results.sortino_ratio,
                'calmar_ratio': results.calmar_ratio
            },
            'trade_metrics': {
                'total_trades': results.total_trades,
                'winning_trades': results.winning_trades,
                'losing_trades': results.losing_trades,
                'win_rate': results.win_rate,
                'avg_trade_duration_hours': results.avg_trade_duration
            }
        }
    
    def _generate_trade_analysis(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate trade-level analysis"""
        return {
            'profit_loss': {
                'avg_win': results.avg_win,
                'avg_loss': results.avg_loss,
                'largest_win': results.largest_win,
                'largest_loss': results.largest_loss,
                'profit_factor': results.profit_factor
            },
            'trade_distribution': self._analyze_trade_distribution(results.trades),
            'symbol_performance': self._analyze_symbol_performance(results.trades)
        }
    
    def _generate_risk_analysis(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate risk analysis"""
        return {
            'drawdown_analysis': {
                'max_drawdown': results.max_drawdown,
                'max_drawdown_duration': results.max_drawdown_duration,
                'avg_drawdown': results.drawdown_series.mean() if len(results.drawdown_series) > 0 else 0
            },
            'var_analysis': self._calculate_var(results),
            'stress_scenarios': self._generate_stress_scenarios(results)
        }
    
    def _generate_monthly_performance(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate monthly performance analysis"""
        if len(results.monthly_returns) == 0:
            return {'monthly_returns': [], 'best_month': 0, 'worst_month': 0}
        
        return {
            'monthly_returns': results.monthly_returns.to_dict(),
            'best_month': results.monthly_returns.max(),
            'worst_month': results.monthly_returns.min(),
            'positive_months': (results.monthly_returns > 0).sum(),
            'negative_months': (results.monthly_returns < 0).sum()
        }
    
    def _analyze_trade_distribution(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trade distribution"""
        if not trades:
            return {}
        
        pnl_values = [t.pnl_percentage for t in trades]
        
        return {
            'pnl_percentiles': {
                '10th': np.percentile(pnl_values, 10),
                '25th': np.percentile(pnl_values, 25),
                '50th': np.percentile(pnl_values, 50),
                '75th': np.percentile(pnl_values, 75),
                '90th': np.percentile(pnl_values, 90)
            },
            'pnl_std': np.std(pnl_values),
            'pnl_skewness': self._calculate_skewness(pnl_values),
            'pnl_kurtosis': self._calculate_kurtosis(pnl_values)
        }
    
    def _analyze_symbol_performance(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze performance by symbol"""
        if not trades:
            return {}
        
        symbol_stats = {}
        symbols = set(t.symbol for t in trades)
        
        for symbol in symbols:
            symbol_trades = [t for t in trades if t.symbol == symbol]
            total_pnl = sum(t.pnl for t in symbol_trades)
            win_rate = len([t for t in symbol_trades if t.pnl > 0]) / len(symbol_trades)
            
            symbol_stats[symbol] = {
                'total_trades': len(symbol_trades),
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'avg_pnl': total_pnl / len(symbol_trades)
            }
        
        return symbol_stats
    
    def _calculate_var(self, results: BacktestResults, confidence_level: float = 0.05) -> Dict[str, float]:
        """Calculate Value at Risk"""
        if len(results.equity_curve) < 2:
            return {'var_5pct': 0, 'cvar_5pct': 0}
        
        returns = results.equity_curve.pct_change().dropna()
        
        if len(returns) == 0:
            return {'var_5pct': 0, 'cvar_5pct': 0}
        
        var = np.percentile(returns, confidence_level * 100)
        cvar = returns[returns <= var].mean()
        
        return {
            'var_5pct': var,
            'cvar_5pct': cvar
        }
    
    def _generate_stress_scenarios(self, results: BacktestResults) -> Dict[str, Any]:
        """Generate stress test scenarios"""
        return {
            'market_crash_scenario': {
                'description': '20% market drop',
                'estimated_impact': -0.20 * results.final_capital * 0.8  # Assuming 80% correlation
            },
            'volatility_spike_scenario': {
                'description': 'Volatility doubles',
                'estimated_max_drawdown': results.max_drawdown * 1.5
            }
        }
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness of data"""
        if len(data) < 3:
            return 0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0
        
        skewness = np.mean([((x - mean) / std) ** 3 for x in data])
        return skewness
    
    def _calculate_kurtosis(self, data: List[float]) -> float:
        """Calculate kurtosis of data"""
        if len(data) < 4:
            return 0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0
        
        kurtosis = np.mean([((x - mean) / std) ** 4 for x in data]) - 3
        return kurtosis
    
    def _generate_visualizations(self, results: BacktestResults, strategy_name: str):
        """Generate visualization charts"""
        try:
            # Create subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Equity Curve', 'Drawdown',
                    'Monthly Returns', 'Trade PnL Distribution',
                    'Rolling Sharpe Ratio', 'Cumulative Returns vs Benchmark'
                ),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Equity curve
            if len(results.equity_curve) > 0:
                fig.add_trace(
                    go.Scatter(x=results.equity_curve.index, y=results.equity_curve.values,
                              name='Equity', line=dict(color='blue')),
                    row=1, col=1
                )
            
            # Drawdown
            if len(results.drawdown_series) > 0:
                fig.add_trace(
                    go.Scatter(x=results.drawdown_series.index, y=results.drawdown_series.values * 100,
                              name='Drawdown %', fill='tonexty', line=dict(color='red')),
                    row=1, col=2
                )
            
            # Monthly returns
            if len(results.monthly_returns) > 0:
                colors = ['green' if x > 0 else 'red' for x in results.monthly_returns.values]
                fig.add_trace(
                    go.Bar(x=results.monthly_returns.index, y=results.monthly_returns.values * 100,
                          name='Monthly Returns %', marker_color=colors),
                    row=2, col=1
                )
            
            # Trade PnL distribution
            if results.trades:
                pnl_values = [t.pnl_percentage * 100 for t in results.trades]
                fig.add_trace(
                    go.Histogram(x=pnl_values, name='Trade PnL %', nbinsx=20),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_layout(
                height=1200,
                title_text=f"{strategy_name} - Backtest Analysis Dashboard",
                showlegend=True
            )
            
            # Save chart
            chart_file = self.output_dir / f"{strategy_name}_analysis_dashboard.html"
            fig.write_html(str(chart_file))
            
            self.logger.info(f"Visualization saved to {chart_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {e}")

class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.analyzer = PerformanceAnalyzer()
        self.report_generator = BacktestReportGenerator()
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, trades: List[Trade], strategy_name: str = "Strategy") -> Dict[str, Any]:
        """Run complete backtest analysis"""
        self.logger.info(f"Running backtest for {strategy_name} with {len(trades)} trades")
        
        # Generate equity curve from trades
        equity_curve = self._generate_equity_curve(trades)
        
        # Calculate performance metrics
        results = self.analyzer.calculate_metrics(trades, equity_curve, self.initial_capital)
        
        # Generate comprehensive report
        report = self.report_generator.generate_report(results, strategy_name)
        
        self.logger.info(f"Backtest completed. Total return: {results.total_return:.2%}")
        
        return report
    
    def _generate_equity_curve(self, trades: List[Trade]) -> pd.Series:
        """Generate equity curve from trade list"""
        if not trades:
            return pd.Series([self.initial_capital], index=[datetime.now()])
        
        # Sort trades by exit time
        sorted_trades = sorted(trades, key=lambda t: t.exit_time)
        
        # Create equity curve
        equity_data = []
        current_equity = self.initial_capital
        
        for trade in sorted_trades:
            current_equity += trade.pnl
            equity_data.append({
                'timestamp': trade.exit_time,
                'equity': current_equity
            })
        
        df = pd.DataFrame(equity_data)
        df.set_index('timestamp', inplace=True)
        
        return df['equity']

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample trades for testing
    sample_trades = [
        Trade(
            symbol="BTC/USDT",
            entry_time=datetime(2023, 1, 1, 10, 0),
            exit_time=datetime(2023, 1, 1, 14, 0),
            entry_price=20000,
            exit_price=20500,
            quantity=0.1,
            side="long",
            pnl=50,
            pnl_percentage=0.025,
            strategy="MA_Crossover"
        ),
        Trade(
            symbol="ETH/USDT",
            entry_time=datetime(2023, 1, 2, 9, 0),
            exit_time=datetime(2023, 1, 2, 15, 0),
            entry_price=1500,
            exit_price=1450,
            quantity=1.0,
            side="long",
            pnl=-50,
            pnl_percentage=-0.033,
            strategy="MA_Crossover"
        )
    ]
    
    # Run backtest
    engine = BacktestEngine(initial_capital=10000)
    report = engine.run_backtest(sample_trades, "Sample_Strategy")
    
    print("Backtest completed!")
    print(f"Total Return: {report['summary']['total_return_pct']}%")
    print(f"Win Rate: {report['summary']['win_rate_pct']}%")
    print(f"Sharpe Ratio: {report['summary']['sharpe_ratio']}")