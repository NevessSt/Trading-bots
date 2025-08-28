/**
 * Utility functions for data validation in the mobile app
 */

/**
 * Email validation
 */
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
};

/**
 * Password validation
 */
export const validatePassword = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Phone number validation (basic)
 */
export const validatePhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^[+]?[1-9]\d{1,14}$/;
  return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
};

/**
 * API key validation
 */
export const validateApiKey = (apiKey: string): boolean => {
  // Basic validation - should be non-empty and alphanumeric
  const apiKeyRegex = /^[a-zA-Z0-9]{16,}$/;
  return apiKeyRegex.test(apiKey.trim());
};

/**
 * Trading amount validation
 */
export const validateTradingAmount = (
  amount: string,
  minAmount: number = 0,
  maxAmount?: number
): {
  isValid: boolean;
  error?: string;
} => {
  const numAmount = parseFloat(amount);
  
  if (isNaN(numAmount)) {
    return {
      isValid: false,
      error: 'Please enter a valid number',
    };
  }
  
  if (numAmount <= minAmount) {
    return {
      isValid: false,
      error: `Amount must be greater than ${minAmount}`,
    };
  }
  
  if (maxAmount && numAmount > maxAmount) {
    return {
      isValid: false,
      error: `Amount must be less than or equal to ${maxAmount}`,
    };
  }
  
  return { isValid: true };
};

/**
 * Price validation
 */
export const validatePrice = (
  price: string,
  minPrice: number = 0
): {
  isValid: boolean;
  error?: string;
} => {
  const numPrice = parseFloat(price);
  
  if (isNaN(numPrice)) {
    return {
      isValid: false,
      error: 'Please enter a valid price',
    };
  }
  
  if (numPrice <= minPrice) {
    return {
      isValid: false,
      error: `Price must be greater than ${minPrice}`,
    };
  }
  
  return { isValid: true };
};

/**
 * Percentage validation
 */
export const validatePercentage = (
  percentage: string,
  min: number = 0,
  max: number = 100
): {
  isValid: boolean;
  error?: string;
} => {
  const numPercentage = parseFloat(percentage);
  
  if (isNaN(numPercentage)) {
    return {
      isValid: false,
      error: 'Please enter a valid percentage',
    };
  }
  
  if (numPercentage < min || numPercentage > max) {
    return {
      isValid: false,
      error: `Percentage must be between ${min}% and ${max}%`,
    };
  }
  
  return { isValid: true };
};

/**
 * Required field validation
 */
export const validateRequired = (
  value: string,
  fieldName: string = 'Field'
): {
  isValid: boolean;
  error?: string;
} => {
  if (!value || value.trim().length === 0) {
    return {
      isValid: false,
      error: `${fieldName} is required`,
    };
  }
  
  return { isValid: true };
};

/**
 * Minimum length validation
 */
export const validateMinLength = (
  value: string,
  minLength: number,
  fieldName: string = 'Field'
): {
  isValid: boolean;
  error?: string;
} => {
  if (value.length < minLength) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${minLength} characters long`,
    };
  }
  
  return { isValid: true };
};

/**
 * Maximum length validation
 */
export const validateMaxLength = (
  value: string,
  maxLength: number,
  fieldName: string = 'Field'
): {
  isValid: boolean;
  error?: string;
} => {
  if (value.length > maxLength) {
    return {
      isValid: false,
      error: `${fieldName} must be no more than ${maxLength} characters long`,
    };
  }
  
  return { isValid: true };
};

/**
 * URL validation
 */
export const validateUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Crypto address validation (basic)
 */
export const validateCryptoAddress = (
  address: string,
  currency?: string
): boolean => {
  if (!address || address.trim().length === 0) {
    return false;
  }
  
  // Basic validation - alphanumeric with some special characters
  const addressRegex = /^[a-zA-Z0-9]{25,}$/;
  return addressRegex.test(address.trim());
};

/**
 * Trading symbol validation
 */
export const validateTradingSymbol = (symbol: string): boolean => {
  if (!symbol || symbol.trim().length === 0) {
    return false;
  }
  
  // Should be uppercase letters, possibly with numbers
  const symbolRegex = /^[A-Z0-9]{2,}$/;
  return symbolRegex.test(symbol.trim().toUpperCase());
};

/**
 * Risk percentage validation
 */
export const validateRiskPercentage = (
  risk: string
): {
  isValid: boolean;
  error?: string;
} => {
  const numRisk = parseFloat(risk);
  
  if (isNaN(numRisk)) {
    return {
      isValid: false,
      error: 'Please enter a valid risk percentage',
    };
  }
  
  if (numRisk <= 0) {
    return {
      isValid: false,
      error: 'Risk percentage must be greater than 0',
    };
  }
  
  if (numRisk > 50) {
    return {
      isValid: false,
      error: 'Risk percentage should not exceed 50% for safety',
    };
  }
  
  return { isValid: true };
};

/**
 * Stop loss validation
 */
export const validateStopLoss = (
  stopLoss: string,
  currentPrice: number,
  orderType: 'buy' | 'sell'
): {
  isValid: boolean;
  error?: string;
} => {
  const numStopLoss = parseFloat(stopLoss);
  
  if (isNaN(numStopLoss)) {
    return {
      isValid: false,
      error: 'Please enter a valid stop loss price',
    };
  }
  
  if (numStopLoss <= 0) {
    return {
      isValid: false,
      error: 'Stop loss price must be greater than 0',
    };
  }
  
  if (orderType === 'buy' && numStopLoss >= currentPrice) {
    return {
      isValid: false,
      error: 'Stop loss for buy order must be below current price',
    };
  }
  
  if (orderType === 'sell' && numStopLoss <= currentPrice) {
    return {
      isValid: false,
      error: 'Stop loss for sell order must be above current price',
    };
  }
  
  return { isValid: true };
};

/**
 * Take profit validation
 */
export const validateTakeProfit = (
  takeProfit: string,
  currentPrice: number,
  orderType: 'buy' | 'sell'
): {
  isValid: boolean;
  error?: string;
} => {
  const numTakeProfit = parseFloat(takeProfit);
  
  if (isNaN(numTakeProfit)) {
    return {
      isValid: false,
      error: 'Please enter a valid take profit price',
    };
  }
  
  if (numTakeProfit <= 0) {
    return {
      isValid: false,
      error: 'Take profit price must be greater than 0',
    };
  }
  
  if (orderType === 'buy' && numTakeProfit <= currentPrice) {
    return {
      isValid: false,
      error: 'Take profit for buy order must be above current price',
    };
  }
  
  if (orderType === 'sell' && numTakeProfit >= currentPrice) {
    return {
      isValid: false,
      error: 'Take profit for sell order must be below current price',
    };
  }
  
  return { isValid: true };
};

/**
 * Form validation helper
 */
export const validateForm = (
  fields: Record<string, any>,
  rules: Record<string, ((value: any) => { isValid: boolean; error?: string })[]>
): {
  isValid: boolean;
  errors: Record<string, string>;
} => {
  const errors: Record<string, string> = {};
  
  for (const [fieldName, validators] of Object.entries(rules)) {
    const fieldValue = fields[fieldName];
    
    for (const validator of validators) {
      const result = validator(fieldValue);
      if (!result.isValid) {
        errors[fieldName] = result.error || 'Invalid value';
        break; // Stop at first error for this field
      }
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};