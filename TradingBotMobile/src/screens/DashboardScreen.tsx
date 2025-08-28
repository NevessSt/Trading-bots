import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Animated,
  Dimensions,
  Alert,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useTradingContext} from '../context/TradingContext';
import {useAuth} from '../context/AuthContext';

const {width} = Dimensions.get('window');

interface QuickAction {
  id: string;
  title: string;
  icon: string;
  color: string;
  onPress: () => void;
}

const DashboardScreen: React.FC = () => {
  const {theme, isDark} = useTheme();
  const {portfolio, watchlist, refreshData, isLoading} = useTradingContext();
  const {user} = useAuth();
  
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    // Animate screen entrance
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshData();
    } catch (error) {
      Alert.alert('Error', 'Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  const quickActions: QuickAction[] = [
    {
      id: 'buy',
      title: 'Buy',
      icon: 'trending-up',
      color: theme.colors.primary,
      onPress: () => Alert.alert('Buy', 'Navigate to buy screen'),
    },
    {
      id: 'sell',
      title: 'Sell',
      icon: 'trending-down',
      color: '#f44336',
      onPress: () => Alert.alert('Sell', 'Navigate to sell screen'),
    },
    {
      id: 'portfolio',
      title: 'Portfolio',
      icon: 'pie-chart',
      color: '#ff9800',
      onPress: () => Alert.alert('Portfolio', 'Navigate to portfolio screen'),
    },
    {
      id: 'alerts',
      title: 'Alerts',
      icon: 'notifications',
      color: '#9c27b0',
      onPress: () => Alert.alert('Alerts', 'Navigate to alerts screen'),
    },
  ];

  const timeframes = ['1h', '24h', '7d', '30d'];

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getChangeColor = (value: number): string => {
    return value >= 0 ? '#4caf50' : '#f44336';
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View>
        <Text style={[styles.greeting, {color: theme.colors.onSurface}]}>
          Good {getTimeOfDay()}, {user?.name || 'Trader'}!
        </Text>
        <Text style={[styles.subtitle, {color: theme.colors.onSurfaceVariant}]}>
          Here's your trading overview
        </Text>
      </View>
      <TouchableOpacity style={styles.profileButton}>
        <Icon name="account-circle" size={32} color={theme.colors.primary} />
      </TouchableOpacity>
    </View>
  );

  const renderPortfolioSummary = () => (
    <Animated.View
      style={[
        styles.portfolioCard,
        {
          backgroundColor: theme.colors.surface,
          opacity: fadeAnim,
          transform: [{translateY: slideAnim}],
        },
      ]}
    >
      <LinearGradient
        colors={isDark ? ['#1e3a8a', '#3b82f6'] : ['#3b82f6', '#1e40af']}
        style={styles.portfolioGradient}
        start={{x: 0, y: 0}}
        end={{x: 1, y: 1}}
      >
        <View style={styles.portfolioHeader}>
          <Text style={styles.portfolioTitle}>Total Portfolio Value</Text>
          <Icon name="visibility" size={20} color="#ffffff" />
        </View>
        
        <Text style={styles.portfolioValue}>
          {formatCurrency(portfolio.totalValue)}
        </Text>
        
        <View style={styles.portfolioChange}>
          <Icon
            name={portfolio.totalChange >= 0 ? 'trending-up' : 'trending-down'}
            size={16}
            color="#ffffff"
          />
          <Text style={styles.portfolioChangeText}>
            {formatPercentage(portfolio.totalChange)} ({selectedTimeframe})
          </Text>
        </View>
        
        <View style={styles.portfolioStats}>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>Available</Text>
            <Text style={styles.statValue}>{formatCurrency(portfolio.availableBalance)}</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statLabel}>P&L Today</Text>
            <Text style={[styles.statValue, {color: getChangeColor(portfolio.dailyPnL)}]}>
              {formatCurrency(portfolio.dailyPnL)}
            </Text>
          </View>
        </View>
      </LinearGradient>
    </Animated.View>
  );

  const renderTimeframeSelector = () => (
    <View style={styles.timeframeContainer}>
      {timeframes.map((timeframe) => (
        <TouchableOpacity
          key={timeframe}
          style={[
            styles.timeframeButton,
            {
              backgroundColor:
                selectedTimeframe === timeframe
                  ? theme.colors.primary
                  : theme.colors.surface,
              borderColor: theme.colors.outline,
            },
          ]}
          onPress={() => setSelectedTimeframe(timeframe)}
        >
          <Text
            style={[
              styles.timeframeText,
              {
                color:
                  selectedTimeframe === timeframe
                    ? theme.colors.onPrimary
                    : theme.colors.onSurface,
              },
            ]}
          >
            {timeframe}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderQuickActions = () => (
    <View style={styles.quickActionsContainer}>
      <Text style={[styles.sectionTitle, {color: theme.colors.onSurface}]}>
        Quick Actions
      </Text>
      <View style={styles.quickActionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[styles.quickActionButton, {backgroundColor: theme.colors.surface}]}
            onPress={action.onPress}
          >
            <View style={[styles.quickActionIcon, {backgroundColor: action.color}]}>
              <Icon name={action.icon} size={24} color="#ffffff" />
            </View>
            <Text style={[styles.quickActionText, {color: theme.colors.onSurface}]}>
              {action.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderWatchlist = () => (
    <View style={styles.watchlistContainer}>
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, {color: theme.colors.onSurface}]}>
          Watchlist
        </Text>
        <TouchableOpacity>
          <Text style={[styles.seeAllText, {color: theme.colors.primary}]}>
            See All
          </Text>
        </TouchableOpacity>
      </View>
      
      {watchlist.slice(0, 5).map((asset) => (
        <TouchableOpacity
          key={asset.symbol}
          style={[styles.watchlistItem, {backgroundColor: theme.colors.surface}]}
        >
          <View style={styles.assetInfo}>
            <View style={[styles.assetIcon, {backgroundColor: theme.colors.primary}]}>
              <Text style={[styles.assetSymbol, {color: theme.colors.onPrimary}]}>
                {asset.symbol.substring(0, 2)}
              </Text>
            </View>
            <View style={styles.assetDetails}>
              <Text style={[styles.assetName, {color: theme.colors.onSurface}]}>
                {asset.name}
              </Text>
              <Text style={[styles.assetSymbolText, {color: theme.colors.onSurfaceVariant}]}>
                {asset.symbol}
              </Text>
            </View>
          </View>
          
          <View style={styles.assetPrice}>
            <Text style={[styles.priceText, {color: theme.colors.onSurface}]}>
              {formatCurrency(asset.price)}
            </Text>
            <Text style={[styles.changeText, {color: getChangeColor(asset.change)}]}>
              {formatPercentage(asset.change)}
            </Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderActivePositions = () => (
    <View style={styles.positionsContainer}>
      <View style={styles.sectionHeader}>
        <Text style={[styles.sectionTitle, {color: theme.colors.onSurface}]}>
          Active Positions
        </Text>
        <TouchableOpacity>
          <Text style={[styles.seeAllText, {color: theme.colors.primary}]}>
            Manage
          </Text>
        </TouchableOpacity>
      </View>
      
      {portfolio.positions.slice(0, 3).map((position) => (
        <TouchableOpacity
          key={position.symbol}
          style={[styles.positionItem, {backgroundColor: theme.colors.surface}]}
        >
          <View style={styles.positionInfo}>
            <Text style={[styles.positionSymbol, {color: theme.colors.onSurface}]}>
              {position.symbol}
            </Text>
            <Text style={[styles.positionType, {color: theme.colors.onSurfaceVariant}]}>
              {position.type} • {position.quantity} units
            </Text>
          </View>
          
          <View style={styles.positionValue}>
            <Text style={[styles.positionAmount, {color: theme.colors.onSurface}]}>
              {formatCurrency(position.currentValue)}
            </Text>
            <Text style={[styles.positionPnL, {color: getChangeColor(position.unrealizedPnL)}]}>
              {formatCurrency(position.unrealizedPnL)}
            </Text>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const getTimeOfDay = (): string => {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 18) return 'afternoon';
    return 'evening';
  };

  return (
    <View style={[styles.container, {backgroundColor: theme.colors.background}]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[theme.colors.primary]}
            tintColor={theme.colors.primary}
          />
        }
      >
        {renderHeader()}
        {renderPortfolioSummary()}
        {renderTimeframeSelector()}
        {renderQuickActions()}
        {renderWatchlist()}
        {renderActivePositions()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  profileButton: {
    padding: 4,
  },
  portfolioCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  portfolioGradient: {
    padding: 20,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  portfolioTitle: {
    color: '#ffffff',
    fontSize: 14,
    opacity: 0.9,
  },
  portfolioValue: {
    color: '#ffffff',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  portfolioChange: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  portfolioChangeText: {
    color: '#ffffff',
    fontSize: 14,
    marginLeft: 4,
  },
  portfolioStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    color: '#ffffff',
    fontSize: 12,
    opacity: 0.8,
    marginBottom: 4,
  },
  statValue: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  timeframeContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  timeframeButton: {
    flex: 1,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 4,
  },
  timeframeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  quickActionsContainer: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quickActionButton: {
    width: (width - 60) / 4,
    aspectRatio: 1,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  quickActionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
  },
  watchlistContainer: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '500',
  },
  watchlistItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  assetInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  assetIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  assetSymbol: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  assetDetails: {
    flex: 1,
  },
  assetName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  assetSymbolText: {
    fontSize: 12,
  },
  assetPrice: {
    alignItems: 'flex-end',
  },
  priceText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  changeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  positionsContainer: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  positionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  positionInfo: {
    flex: 1,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  positionType: {
    fontSize: 12,
  },
  positionValue: {
    alignItems: 'flex-end',
  },
  positionAmount: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  positionPnL: {
    fontSize: 12,
    fontWeight: '500',
  },
});

export default DashboardScreen;