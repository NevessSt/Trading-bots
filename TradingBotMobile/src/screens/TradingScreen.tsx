import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Animated,
  Dimensions,
  Modal,
} from 'react-native';
import {LineChart} from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useTradingContext} from '../context/TradingContext';

const {width} = Dimensions.get('window');
const chartWidth = width - 40;

interface OrderType {
  id: string;
  name: string;
  description: string;
}

interface TimeframeOption {
  id: string;
  label: string;
  value: string;
}

const TradingScreen: React.FC = () => {
  const {theme, isDark} = useTheme();
  const {watchlist, executeTrade, refreshData} = useTradingContext();
  
  const [selectedAsset, setSelectedAsset] = useState(watchlist[0] || null);
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState('market');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  const orderTypes: OrderType[] = [
    {
      id: 'market',
      name: 'Market',
      description: 'Execute immediately at current market price',
    },
    {
      id: 'limit',
      name: 'Limit',
      description: 'Execute only at specified price or better',
    },
    {
      id: 'stop',
      name: 'Stop',
      description: 'Execute when price reaches stop level',
    },
    {
      id: 'stop_limit',
      name: 'Stop Limit',
      description: 'Stop order that becomes limit order when triggered',
    },
  ];

  const timeframes: TimeframeOption[] = [
    {id: '1m', label: '1M', value: '1m'},
    {id: '5m', label: '5M', value: '5m'},
    {id: '15m', label: '15M', value: '15m'},
    {id: '1h', label: '1H', value: '1h'},
    {id: '4h', label: '4H', value: '4h'},
    {id: '1d', label: '1D', value: '1d'},
  ];

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

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getChangeColor = (value: number): string => {
    return value >= 0 ? '#4caf50' : '#f44336';
  };

  const generateChartData = () => {
    // Mock price data - in real app, this would come from API
    const mockData = {
      labels: ['', '', '', '', '', ''],
      datasets: [
        {
          data: [
            selectedAsset?.price * 0.98,
            selectedAsset?.price * 0.99,
            selectedAsset?.price * 1.01,
            selectedAsset?.price * 0.97,
            selectedAsset?.price * 1.02,
            selectedAsset?.price || 0,
          ],
          color: (opacity = 1) => {
            const color = selectedAsset?.change >= 0 ? '#4caf50' : '#f44336';
            return `rgba(${color === '#4caf50' ? '76, 175, 80' : '244, 67, 54'}, ${opacity})`;
          },
          strokeWidth: 2,
        },
      ],
    };
    return mockData;
  };

  const calculateTotal = (): number => {
    const qty = parseFloat(quantity) || 0;
    const priceValue = orderType === 'market' ? selectedAsset?.price || 0 : parseFloat(price) || 0;
    return qty * priceValue;
  };

  const handleTrade = async () => {
    if (!selectedAsset) {
      Alert.alert('Error', 'Please select an asset to trade');
      return;
    }

    if (!quantity || parseFloat(quantity) <= 0) {
      Alert.alert('Error', 'Please enter a valid quantity');
      return;
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      Alert.alert('Error', 'Please enter a valid price for limit order');
      return;
    }

    setIsLoading(true);
    try {
      const tradeData = {
        symbol: selectedAsset.symbol,
        type: tradeType,
        orderType,
        quantity: parseFloat(quantity),
        price: orderType === 'market' ? selectedAsset.price : parseFloat(price),
        stopLoss: stopLoss ? parseFloat(stopLoss) : undefined,
        takeProfit: takeProfit ? parseFloat(takeProfit) : undefined,
      };

      const success = await executeTrade(tradeData);
      if (success) {
        Alert.alert(
          'Trade Executed',
          `${tradeType.toUpperCase()} order for ${quantity} ${selectedAsset.symbol} has been placed successfully.`,
          [
            {
              text: 'OK',
              onPress: () => {
                setShowOrderModal(false);
                resetForm();
              },
            },
          ]
        );
      } else {
        Alert.alert('Trade Failed', 'Unable to execute trade. Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'An error occurred while executing the trade');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setQuantity('');
    setPrice('');
    setStopLoss('');
    setTakeProfit('');
    setOrderType('market');
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity style={styles.backButton}>
        <Icon name="arrow-back" size={24} color={theme.colors.onSurface} />
      </TouchableOpacity>
      <Text style={[styles.headerTitle, {color: theme.colors.onSurface}]}>
        Trading
      </Text>
      <TouchableOpacity style={styles.searchButton}>
        <Icon name="search" size={24} color={theme.colors.onSurface} />
      </TouchableOpacity>
    </View>
  );

  const renderAssetSelector = () => (
    <View style={styles.assetSelectorContainer}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {watchlist.map((asset) => (
          <TouchableOpacity
            key={asset.symbol}
            style={[
              styles.assetCard,
              {
                backgroundColor:
                  selectedAsset?.symbol === asset.symbol
                    ? theme.colors.primary
                    : theme.colors.surface,
              },
            ]}
            onPress={() => setSelectedAsset(asset)}
          >
            <Text
              style={[
                styles.assetSymbol,
                {
                  color:
                    selectedAsset?.symbol === asset.symbol
                      ? theme.colors.onPrimary
                      : theme.colors.onSurface,
                },
              ]}
            >
              {asset.symbol}
            </Text>
            <Text
              style={[
                styles.assetPrice,
                {
                  color:
                    selectedAsset?.symbol === asset.symbol
                      ? theme.colors.onPrimary
                      : theme.colors.onSurface,
                },
              ]}
            >
              {formatCurrency(asset.price)}
            </Text>
            <Text
              style={[
                styles.assetChange,
                {
                  color:
                    selectedAsset?.symbol === asset.symbol
                      ? theme.colors.onPrimary
                      : getChangeColor(asset.change),
                },
              ]}
            >
              {formatPercentage(asset.change)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  const renderPriceChart = () => (
    <Animated.View
      style={[
        styles.chartContainer,
        {
          backgroundColor: theme.colors.surface,
          opacity: fadeAnim,
          transform: [{translateY: slideAnim}],
        },
      ]}
    >
      <View style={styles.chartHeader}>
        <View>
          <Text style={[styles.chartTitle, {color: theme.colors.onSurface}]}>
            {selectedAsset?.name || 'Select Asset'}
          </Text>
          <Text style={[styles.chartPrice, {color: theme.colors.onSurface}]}>
            {selectedAsset ? formatCurrency(selectedAsset.price) : '--'}
          </Text>
          {selectedAsset && (
            <Text style={[styles.chartChange, {color: getChangeColor(selectedAsset.change)}]}>
              {formatPercentage(selectedAsset.change)}
            </Text>
          )}
        </View>
        
        <View style={styles.timeframeSelector}>
          {timeframes.map((tf) => (
            <TouchableOpacity
              key={tf.id}
              style={[
                styles.timeframeButton,
                {
                  backgroundColor:
                    selectedTimeframe === tf.value
                      ? theme.colors.primary
                      : 'transparent',
                },
              ]}
              onPress={() => setSelectedTimeframe(tf.value)}
            >
              <Text
                style={[
                  styles.timeframeText,
                  {
                    color:
                      selectedTimeframe === tf.value
                        ? theme.colors.onPrimary
                        : theme.colors.onSurfaceVariant,
                  },
                ]}
              >
                {tf.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      
      {selectedAsset && (
        <LineChart
          data={generateChartData()}
          width={chartWidth}
          height={200}
          chartConfig={{
            backgroundColor: theme.colors.surface,
            backgroundGradientFrom: theme.colors.surface,
            backgroundGradientTo: theme.colors.surface,
            decimalPlaces: 2,
            color: (opacity = 1) => {
              const color = selectedAsset.change >= 0 ? '#4caf50' : '#f44336';
              return `rgba(${color === '#4caf50' ? '76, 175, 80' : '244, 67, 54'}, ${opacity})`;
            },
            labelColor: (opacity = 1) => theme.colors.onSurfaceVariant,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '0',
            },
          }}
          bezier
          withHorizontalLabels={false}
          withVerticalLabels={false}
          style={{
            marginVertical: 8,
            borderRadius: 16,
          }}
        />
      )}
    </Animated.View>
  );

  const renderTradeButtons = () => (
    <View style={styles.tradeButtonsContainer}>
      <TouchableOpacity
        style={[styles.tradeButton, styles.buyButton]}
        onPress={() => {
          setTradeType('buy');
          setShowOrderModal(true);
        }}
        disabled={!selectedAsset}
      >
        <Icon name="trending-up" size={24} color="#ffffff" />
        <Text style={styles.tradeButtonText}>Buy</Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tradeButton, styles.sellButton]}
        onPress={() => {
          setTradeType('sell');
          setShowOrderModal(true);
        }}
        disabled={!selectedAsset}
      >
        <Icon name="trending-down" size={24} color="#ffffff" />
        <Text style={styles.tradeButtonText}>Sell</Text>
      </TouchableOpacity>
    </View>
  );

  const renderOrderModal = () => (
    <Modal
      visible={showOrderModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowOrderModal(false)}
    >
      <View style={[styles.modalContainer, {backgroundColor: theme.colors.background}]}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowOrderModal(false)}>
            <Icon name="close" size={24} color={theme.colors.onSurface} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, {color: theme.colors.onSurface}]}>
            {tradeType.toUpperCase()} {selectedAsset?.symbol}
          </Text>
          <View style={{width: 24}} />
        </View>
        
        <ScrollView style={styles.modalContent}>
          {/* Order Type Selector */}
          <View style={styles.orderTypeContainer}>
            <Text style={[styles.sectionTitle, {color: theme.colors.onSurface}]}>
              Order Type
            </Text>
            <View style={styles.orderTypeGrid}>
              {orderTypes.map((type) => (
                <TouchableOpacity
                  key={type.id}
                  style={[
                    styles.orderTypeButton,
                    {
                      backgroundColor:
                        orderType === type.id ? theme.colors.primary : theme.colors.surface,
                      borderColor: theme.colors.outline,
                    },
                  ]}
                  onPress={() => setOrderType(type.id)}
                >
                  <Text
                    style={[
                      styles.orderTypeName,
                      {
                        color:
                          orderType === type.id
                            ? theme.colors.onPrimary
                            : theme.colors.onSurface,
                      },
                    ]}
                  >
                    {type.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          {/* Quantity Input */}
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Quantity</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="0.00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={quantity}
              onChangeText={setQuantity}
              keyboardType="decimal-pad"
            />
          </View>
          
          {/* Price Input (for limit orders) */}
          {orderType !== 'market' && (
            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Price</Text>
              <TextInput
                style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
                placeholder={selectedAsset ? formatCurrency(selectedAsset.price) : '0.00'}
                placeholderTextColor={theme.colors.onSurfaceVariant}
                value={price}
                onChangeText={setPrice}
                keyboardType="decimal-pad"
              />
            </View>
          )}
          
          {/* Stop Loss */}
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Stop Loss (Optional)</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="0.00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={stopLoss}
              onChangeText={setStopLoss}
              keyboardType="decimal-pad"
            />
          </View>
          
          {/* Take Profit */}
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Take Profit (Optional)</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="0.00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={takeProfit}
              onChangeText={setTakeProfit}
              keyboardType="decimal-pad"
            />
          </View>
          
          {/* Order Summary */}
          <View style={[styles.orderSummary, {backgroundColor: theme.colors.surface}]}>
            <Text style={[styles.summaryTitle, {color: theme.colors.onSurface}]}>Order Summary</Text>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, {color: theme.colors.onSurfaceVariant}]}>Type:</Text>
              <Text style={[styles.summaryValue, {color: theme.colors.onSurface}]}>
                {tradeType.toUpperCase()} {orderType.toUpperCase()}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, {color: theme.colors.onSurfaceVariant}]}>Quantity:</Text>
              <Text style={[styles.summaryValue, {color: theme.colors.onSurface}]}>
                {quantity || '0'} {selectedAsset?.symbol}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, {color: theme.colors.onSurfaceVariant}]}>Price:</Text>
              <Text style={[styles.summaryValue, {color: theme.colors.onSurface}]}>
                {orderType === 'market'
                  ? `~${selectedAsset ? formatCurrency(selectedAsset.price) : '$0.00'}`
                  : formatCurrency(parseFloat(price) || 0)}
              </Text>
            </View>
            <View style={[styles.summaryRow, styles.totalRow]}>
              <Text style={[styles.summaryLabel, styles.totalLabel, {color: theme.colors.onSurface}]}>
                Total:
              </Text>
              <Text style={[styles.summaryValue, styles.totalValue, {color: theme.colors.onSurface}]}>
                {formatCurrency(calculateTotal())}
              </Text>
            </View>
          </View>
        </ScrollView>
        
        {/* Execute Button */}
        <View style={styles.modalFooter}>
          <TouchableOpacity
            style={[
              styles.executeButton,
              {
                backgroundColor: tradeType === 'buy' ? '#4caf50' : '#f44336',
              },
            ]}
            onPress={handleTrade}
            disabled={isLoading || !quantity}
          >
            {isLoading ? (
              <Icon name="hourglass-empty" size={20} color="#ffffff" />
            ) : (
              <Text style={styles.executeButtonText}>
                {tradeType.toUpperCase()} {selectedAsset?.symbol}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={[styles.container, {backgroundColor: theme.colors.background}]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {renderHeader()}
        {renderAssetSelector()}
        {renderPriceChart()}
        {renderTradeButtons()}
      </ScrollView>
      {renderOrderModal()}
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
  searchButton: {
    padding: 4,
  },
  assetSelectorContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  assetCard: {
    padding: 12,
    borderRadius: 12,
    marginRight: 12,
    minWidth: 100,
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
  assetSymbol: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  assetPrice: {
    fontSize: 12,
    marginBottom: 2,
  },
  assetChange: {
    fontSize: 10,
    fontWeight: '500',
  },
  chartContainer: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 16,
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
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  chartPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  chartChange: {
    fontSize: 14,
    fontWeight: '500',
  },
  timeframeSelector: {
    flexDirection: 'row',
  },
  timeframeButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 4,
  },
  timeframeText: {
    fontSize: 10,
    fontWeight: '500',
  },
  tradeButtonsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 12,
  },
  tradeButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  buyButton: {
    backgroundColor: '#4caf50',
  },
  sellButton: {
    backgroundColor: '#f44336',
  },
  tradeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 20,
  },
  orderTypeContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  orderTypeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  orderTypeButton: {
    flex: 1,
    minWidth: '45%',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  orderTypeName: {
    fontSize: 14,
    fontWeight: '500',
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  orderSummary: {
    padding: 16,
    borderRadius: 12,
    marginVertical: 20,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  totalRow: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
    paddingTop: 8,
    marginTop: 8,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '600',
  },
  totalValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalFooter: {
    padding: 20,
    paddingBottom: 40,
  },
  executeButton: {
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  executeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TradingScreen;