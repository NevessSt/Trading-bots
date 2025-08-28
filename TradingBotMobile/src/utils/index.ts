/**
 * Utils Index - Export all utility functions for easy importing
 */

export * from './formatters';
export * from './validation';

// Re-export everything as named exports for convenience
export {
  formatCurrency,
  formatPercentage,
  formatLargeNumber,
  formatDate,
  formatTime,
  formatRelativeTime,
  formatNumber,
  formatCryptoSymbol,
  truncateText,
  formatFileSize,
  formatVolume,
  formatMarketCap,
  getPriceChangeColor,
  formatPrice,
  formatOrderType,
  formatTradeSide,
  formatAccountBalance,
} from './formatters';

export {
  validateEmail,
  validatePassword,
  validatePhoneNumber,
  validateApiKey,
  validateTradingAmount,
  validatePrice,
  validatePercentage,
  validateRequired,
  validateMinLength,
  validateMaxLength,
  validateUrl,
  validateCryptoAddress,
  validateTradingSymbol,
  validateRiskPercentage,
  validateStopLoss,
  validateTakeProfit,
  validateForm,
} from './validation';