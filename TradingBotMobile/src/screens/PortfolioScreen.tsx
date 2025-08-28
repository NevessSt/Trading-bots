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
import {PieChart, LineChart} from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useTradingContext} from '../context/TradingContext';

const {width} = Dimensions.get('window');
const chartWidth = width - 40;

interface TabItem {
  id: string;
  title: string;
  icon: string;
}

const PortfolioScreen: React.FC = () => {
  const {theme, isDark} = useTheme();
  const {portfolio, refreshData, isLoading} = useTradingContext();
  
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  const tabs: TabItem[] = [
    {id: 'overview', title: 'Overview', icon: 'dashboard'},
    {id: 'positions', title: 'Positions', icon: 'account-balance-wallet'},
    {id: 'history', title: 'History', icon: 'history'},
    {id: 'analytics', title: 'Analytics', icon: 'analytics'},
  ];

  const timeframes = ['1d', '7d', '30d', '90d', '1y'];

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
      Alert.alert('Error', 'Failed to refresh portfolio data');
    } finally {
      setRefreshing(false);
    }
  };

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

  const generatePieChartData = () => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    return portfolio.positions.map((position, index) => ({
      name: position.symbol,
      population: position.percentage,
      color: colors[index % colors.length],
      legendFontColor: theme.colors.onSurface,
      legendFontSize: 12,
    }));
  };

  const generateLineChartData = () => {
    // Mock historical data - in real app, this would come from API
    const mockData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        {
          data: [10000, 10500, 9800, 11200, 10800, portfolio.totalValue],
          color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
          strokeWidth: 2,
        },
      ],
    };
    return mockData;
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity style={styles.backButton}>
        <Icon name="arrow-back" size={24} color={theme.colors.onSurface} />
      </TouchableOpacity>
      <Text style={[styles.headerTitle, {color: theme.colors.onSurface}]}>
        Portfolio
      </Text>
      <TouchableOpacity style={styles.moreButton}>
        <Icon name="more-vert" size={24} color={theme.colors.onSurface} />
      </TouchableOpacity>
    </View>
  );

  const renderPortfolioSummary = () => (
    <Animated.View
      style={[
        styles.summaryCard,
        {
          backgroundColor: theme.colors.surface,
          opacity: fadeAnim,
          transform: [{translateY: slideAnim}],
        },
      ]}
    >
      <View style={styles.summaryHeader}>
        <Text style={[styles.summaryTitle, {color: theme.colors.onSurface}]}>
          Total Portfolio Value
        </Text>
        <TouchableOpacity>
          <Icon name="visibility" size={20} color={theme.colors.onSurfaceVariant} />
        </TouchableOpacity>
      </View>
      
      <Text style={[styles.summaryValue, {color: theme.colors.onSurface}]}>
        {formatCurrency(portfolio.totalValue)}
      </Text>
      
      <View style={styles.summaryChange}>
        <Icon
          name={portfolio.totalChange >= 0 ? 'trending-up' : 'trending-down'}
          size={16}
          color={getChangeColor(portfolio.totalChange)}
        />
        <Text style={[styles.summaryChangeText, {color: getChangeColor(portfolio.totalChange)}]}>
          {formatPercentage(portfolio.totalChange)} ({selectedTimeframe})
        </Text>
      </View>
      
      <View style={styles.summaryStats}>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, {color: theme.colors.onSurfaceVariant}]}>Available</Text>
          <Text style={[styles.statValue, {color: theme.colors.onSurface}]}>
            {formatCurrency(portfolio.availableBalance)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, {color: theme.colors.onSurfaceVariant}]}>Invested</Text>
          <Text style={[styles.statValue, {color: theme.colors.onSurface}]}>
            {formatCurrency(portfolio.totalValue - portfolio.availableBalance)}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statLabel, {color: theme.colors.onSurfaceVariant}]}>P&L Today</Text>
          <Text style={[styles.statValue, {color: getChangeColor(portfolio.dailyPnL)}]}>
            {formatCurrency(portfolio.dailyPnL)}
          </Text>
        </View>
      </View>
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

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      {tabs.map((tab) => (
        <TouchableOpacity
          key={tab.id}
          style={[
            styles.tabButton,
            {
              borderBottomColor:
                activeTab === tab.id ? theme.colors.primary : 'transparent',
            },
          ]}
          onPress={() => setActiveTab(tab.id)}
        >
          <Icon
            name={tab.icon}
            size={20}
            color={activeTab === tab.id ? theme.colors.primary : theme.colors.onSurfaceVariant}
          />
          <Text
            style={[
              styles.tabText,
              {
                color:
                  activeTab === tab.id ? theme.colors.primary : theme.colors.onSurfaceVariant,
              },
            ]}
          >
            {tab.title}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderOverviewTab = () => (
    <View style={styles.tabContent}>
      {/* Asset Allocation Chart */}
      <View style={[styles.chartCard, {backgroundColor: theme.colors.surface}]}>
        <Text style={[styles.chartTitle, {color: theme.colors.onSurface}]}>
          Asset Allocation
        </Text>
        {portfolio.positions.length > 0 && (
          <PieChart
            data={generatePieChartData()}
            width={chartWidth}
            height={200}
            chartConfig={{
              color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            }}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            absolute
          />
        )}
      </View>
      
      {/* Performance Chart */}
      <View style={[styles.chartCard, {backgroundColor: theme.colors.surface}]}>
        <Text style={[styles.chartTitle, {color: theme.colors.onSurface}]}>
          Portfolio Performance
        </Text>
        <LineChart
          data={generateLineChartData()}
          width={chartWidth}
          height={200}
          chartConfig={{
            backgroundColor: theme.colors.surface,
            backgroundGradientFrom: theme.colors.surface,
            backgroundGradientTo: theme.colors.surface,
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
            labelColor: (opacity = 1) => theme.colors.onSurfaceVariant,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
              stroke: '#3b82f6',
            },
          }}
          bezier
          style={{
            marginVertical: 8,
            borderRadius: 16,
          }}
        />
      </View>
    </View>
  );

  const renderPositionsTab = () => (
    <View style={styles.tabContent}>
      {portfolio.positions.map((position) => (
        <TouchableOpacity
          key={position.symbol}
          style={[styles.positionCard, {backgroundColor: theme.colors.surface}]}
        >
          <View style={styles.positionHeader}>
            <View style={styles.positionInfo}>
              <View style={[styles.positionIcon, {backgroundColor: theme.colors.primary}]}>
                <Text style={[styles.positionSymbol, {color: theme.colors.onPrimary}]}>
                  {position.symbol.substring(0, 2)}
                </Text>
              </View>
              <View style={styles.positionDetails}>
                <Text style={[styles.positionName, {color: theme.colors.onSurface}]}>
                  {position.symbol}
                </Text>
                <Text style={[styles.positionType, {color: theme.colors.onSurfaceVariant}]}>
                  {position.type} • {position.quantity} units
                </Text>
              </View>
            </View>
            
            <View style={styles.positionValue}>
              <Text style={[styles.positionAmount, {color: theme.colors.onSurface}]}>
                {formatCurrency(position.currentValue)}
              </Text>
              <Text style={[styles.positionPnL, {color: getChangeColor(position.unrealizedPnL)}]}>
                {formatCurrency(position.unrealizedPnL)}
              </Text>
            </View>
          </View>
          
          <View style={styles.positionMetrics}>
            <View style={styles.metricItem}>
              <Text style={[styles.metricLabel, {color: theme.colors.onSurfaceVariant}]}>Avg Price</Text>
              <Text style={[styles.metricValue, {color: theme.colors.onSurface}]}>
                {formatCurrency(position.averagePrice)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={[styles.metricLabel, {color: theme.colors.onSurfaceVariant}]}>Current Price</Text>
              <Text style={[styles.metricValue, {color: theme.colors.onSurface}]}>
                {formatCurrency(position.currentPrice)}
              </Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={[styles.metricLabel, {color: theme.colors.onSurfaceVariant}]}>Allocation</Text>
              <Text style={[styles.metricValue, {color: theme.colors.onSurface}]}>
                {position.percentage.toFixed(1)}%
              </Text>
            </View>
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderHistoryTab = () => (
    <View style={styles.tabContent}>
      <Text style={[styles.comingSoonText, {color: theme.colors.onSurfaceVariant}]}>
        Transaction history coming soon...
      </Text>
    </View>
  );

  const renderAnalyticsTab = () => (
    <View style={styles.tabContent}>
      <Text style={[styles.comingSoonText, {color: theme.colors.onSurfaceVariant}]}>
        Advanced analytics coming soon...
      </Text>
    </View>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'positions':
        return renderPositionsTab();
      case 'history':
        return renderHistoryTab();
      case 'analytics':
        return renderAnalyticsTab();
      default:
        return renderOverviewTab();
    }
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
        {renderTabs()}
        {renderTabContent()}
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
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  moreButton: {
    padding: 4,
  },
  summaryCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '500',
  },
  summaryValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  summaryChange: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  summaryChangeText: {
    fontSize: 14,
    marginLeft: 4,
    fontWeight: '500',
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
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
    marginHorizontal: 2,
  },
  timeframeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 2,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  tabContent: {
    paddingHorizontal: 20,
  },
  chartCard: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  positionCard: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  positionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  positionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  positionSymbol: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  positionDetails: {
    flex: 1,
  },
  positionName: {
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
  positionMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  metricItem: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  metricValue: {
    fontSize: 12,
    fontWeight: '500',
  },
  comingSoonText: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 40,
    fontStyle: 'italic',
  },
});

export default PortfolioScreen;