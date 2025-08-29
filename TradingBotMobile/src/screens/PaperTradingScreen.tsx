import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useDemoTrading } from '../contexts/DemoTradingContext';
import Card from '../components/Card';
import Button from '../components/Button';
import DemoModeToggle from '../components/DemoModeToggle';

const PaperTradingScreen: React.FC = () => {
  const { theme } = useTheme();
  const {
    isDemoMode,
    portfolio,
    isLoading,
    error,
    refreshPortfolio,
    resetPortfolio,
    getTradeHistory,
    getPositions,
    getPerformanceMetrics,
  } = useDemoTrading();

  const [refreshing, setRefreshing] = useState(false);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [positions, setPositions] = useState([]);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    loadData();
  }, [portfolio]);

  const loadData = () => {
    if (isDemoMode) {
      setTradeHistory(getTradeHistory());
      setPositions(getPositions());
      setMetrics(getPerformanceMetrics());
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshPortfolio();
    loadData();
    setRefreshing(false);
  };

  const handleResetPortfolio = () => {
    Alert.alert(
      'Reset Portfolio',
      'Are you sure you want to reset your demo portfolio? This will clear all positions and trades, and reset your balance to $100,000.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: resetPortfolio,
        },
      ]
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    scrollContent: {
      padding: theme.spacing.md,
    },
    header: {
      marginBottom: theme.spacing.lg,
    },
    title: {
      fontSize: 24,
      fontWeight: '700',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    modeToggleContainer: {
      marginBottom: theme.spacing.lg,
    },
    portfolioSummary: {
      marginBottom: theme.spacing.lg,
    },
    summaryRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: theme.spacing.sm,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    summaryLabel: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      fontWeight: '500',
    },
    summaryValue: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
    },
    profitValue: {
      color: theme.colors.profit,
    },
    lossValue: {
      color: theme.colors.loss,
    },
    metricsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: theme.spacing.md,
      marginBottom: theme.spacing.lg,
    },
    metricCard: {
      flex: 1,
      minWidth: '45%',
      padding: theme.spacing.md,
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius.lg,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    metricLabel: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing.xs,
      textTransform: 'uppercase',
    },
    metricValue: {
      fontSize: 18,
      fontWeight: '700',
      color: theme.colors.text,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    positionItem: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: theme.spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    positionLeft: {
      flex: 1,
    },
    positionSymbol: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
    },
    positionQuantity: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
    positionRight: {
      alignItems: 'flex-end',
    },
    positionPrice: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
    },
    tradeItem: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: theme.spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    tradeLeft: {
      flex: 1,
    },
    tradeType: {
      fontSize: 14,
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    buyType: {
      color: theme.colors.profit,
    },
    sellType: {
      color: theme.colors.loss,
    },
    tradeDetails: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
    tradeRight: {
      alignItems: 'flex-end',
    },
    tradeDate: {
      fontSize: 12,
      color: theme.colors.textSecondary,
    },
    resetButton: {
      marginTop: theme.spacing.lg,
    },
    emptyState: {
      alignItems: 'center',
      paddingVertical: theme.spacing.xxl,
    },
    emptyText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
    errorText: {
      color: theme.colors.error,
      textAlign: 'center',
      marginBottom: theme.spacing.md,
    },
  });

  if (!isDemoMode) {
    return (
      <View style={styles.container}>
        <ScrollView
          style={styles.container}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <View style={styles.header}>
            <Text style={styles.title}>Paper Trading</Text>
            <DemoModeToggle />
          </View>
          
          <Card>
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>
                Switch to Demo Mode to access paper trading features
              </Text>
            </View>
          </Card>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Paper Trading</Text>
          <View style={styles.modeToggleContainer}>
            <DemoModeToggle />
          </View>
        </View>

        {error && <Text style={styles.errorText}>{error}</Text>}

        {/* Portfolio Summary */}
        {portfolio && (
          <Card style={styles.portfolioSummary}>
            <Text style={styles.sectionTitle}>Portfolio Summary</Text>
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Equity</Text>
              <Text style={styles.summaryValue}>
                {formatCurrency(portfolio.equity)}
              </Text>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Cash Balance</Text>
              <Text style={styles.summaryValue}>
                {formatCurrency(portfolio.balance)}
              </Text>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total P&L</Text>
              <Text style={[
                styles.summaryValue,
                portfolio.totalPnL >= 0 ? styles.profitValue : styles.lossValue
              ]}>
                {formatCurrency(portfolio.totalPnL)}
              </Text>
            </View>
          </Card>
        )}

        {/* Performance Metrics */}
        {metrics && (
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Total Return</Text>
              <Text style={[
                styles.metricValue,
                metrics.totalReturn >= 0 ? styles.profitValue : styles.lossValue
              ]}>
                {formatPercentage(metrics.totalReturn)}
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={styles.metricValue}>
                {formatPercentage(metrics.winRate)}
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Total Trades</Text>
              <Text style={styles.metricValue}>
                {metrics.totalTrades}
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <Text style={styles.metricLabel}>Winning Trades</Text>
              <Text style={styles.metricValue}>
                {metrics.winningTrades}
              </Text>
            </View>
          </View>
        )}

        {/* Current Positions */}
        <Card>
          <Text style={styles.sectionTitle}>Current Positions</Text>
          {positions.length > 0 ? (
            positions.map((position, index) => (
              <View key={index} style={styles.positionItem}>
                <View style={styles.positionLeft}>
                  <Text style={styles.positionSymbol}>{position.symbol}</Text>
                  <Text style={styles.positionQuantity}>
                    {position.quantity} shares @ {formatCurrency(position.averagePrice)}
                  </Text>
                </View>
                <View style={styles.positionRight}>
                  <Text style={styles.positionPrice}>
                    {formatCurrency(position.currentPrice)}
                  </Text>
                  <Text style={[
                    styles.summaryValue,
                    position.unrealizedPnL >= 0 ? styles.profitValue : styles.lossValue
                  ]}>
                    {formatCurrency(position.unrealizedPnL)}
                  </Text>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No positions yet</Text>
            </View>
          )}
        </Card>

        {/* Trade History */}
        <Card>
          <Text style={styles.sectionTitle}>Recent Trades</Text>
          {tradeHistory.length > 0 ? (
            tradeHistory.slice(0, 10).map((trade, index) => (
              <View key={index} style={styles.tradeItem}>
                <View style={styles.tradeLeft}>
                  <Text style={[
                    styles.tradeType,
                    trade.type === 'buy' ? styles.buyType : styles.sellType
                  ]}>
                    {trade.type}
                  </Text>
                  <Text style={styles.tradeDetails}>
                    {trade.symbol} - {trade.quantity} @ {formatCurrency(trade.price)}
                  </Text>
                </View>
                <View style={styles.tradeRight}>
                  <Text style={styles.tradeDate}>
                    {formatDate(trade.timestamp)}
                  </Text>
                  <Text style={styles.summaryValue}>
                    {formatCurrency(trade.quantity * trade.price)}
                  </Text>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No trades yet</Text>
            </View>
          )}
        </Card>

        {/* Reset Portfolio Button */}
        <Button
          title="Reset Portfolio"
          onPress={handleResetPortfolio}
          variant="outline"
          style={styles.resetButton}
        />
      </ScrollView>
    </View>
  );
};

export default PaperTradingScreen;