import React, { useState, useEffect, useRef } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon, 
  XCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  QuestionMarkCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  ClipboardDocumentIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

// Enhanced Alert Component
export const EnhancedAlert = ({ type = 'info', title, message, onClose, actions = [] }) => {
  const alertStyles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      icon: CheckCircleIcon,
      iconColor: 'text-green-400',
      titleColor: 'text-green-800',
      messageColor: 'text-green-700'
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: XCircleIcon,
      iconColor: 'text-red-400',
      titleColor: 'text-red-800',
      messageColor: 'text-red-700'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      icon: ExclamationTriangleIcon,
      iconColor: 'text-yellow-400',
      titleColor: 'text-yellow-800',
      messageColor: 'text-yellow-700'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: InformationCircleIcon,
      iconColor: 'text-blue-400',
      titleColor: 'text-blue-800',
      messageColor: 'text-blue-700'
    }
  };

  const style = alertStyles[type];
  const IconComponent = style.icon;

  return (
    <div className={`rounded-md ${style.bg} ${style.border} border p-4 mb-4`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <IconComponent className={`h-5 w-5 ${style.iconColor}`} aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={`text-sm font-medium ${style.titleColor}`}>
              {title}
            </h3>
          )}
          {message && (
            <div className={`${title ? 'mt-2' : ''} text-sm ${style.messageColor}`}>
              <p>{message}</p>
            </div>
          )}
          {actions.length > 0 && (
            <div className="mt-4">
              <div className="flex space-x-2">
                {actions.map((action, index) => (
                  <button
                    key={index}
                    type="button"
                    className={`text-sm font-medium ${style.titleColor} hover:${style.titleColor} underline`}
                    onClick={action.onClick}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                className={`inline-flex rounded-md ${style.bg} p-1.5 ${style.iconColor} hover:${style.bg} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-${type}-50 focus:ring-${type}-600`}
                onClick={onClose}
              >
                <span className="sr-only">Dismiss</span>
                <XCircleIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Tooltip Component
export const EnhancedTooltip = ({ children, content, position = 'top', delay = 500 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showTimeout, setShowTimeout] = useState(null);
  const [hideTimeout, setHideTimeout] = useState(null);

  const showTooltip = () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      setHideTimeout(null);
    }
    const timeout = setTimeout(() => setIsVisible(true), delay);
    setShowTimeout(timeout);
  };

  const hideTooltip = () => {
    if (showTimeout) {
      clearTimeout(showTimeout);
      setShowTimeout(null);
    }
    const timeout = setTimeout(() => setIsVisible(false), 100);
    setHideTimeout(timeout);
  };

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  };

  return (
    <div className="relative inline-block" onMouseEnter={showTooltip} onMouseLeave={hideTooltip}>
      {children}
      {isVisible && (
        <div className={`absolute z-50 ${positionClasses[position]} pointer-events-none`}>
          <div className="bg-gray-900 text-white text-sm rounded-md px-3 py-2 max-w-xs shadow-lg">
            {content}
            <div className={`absolute w-2 h-2 bg-gray-900 transform rotate-45 ${
              position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -mt-1' :
              position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1' :
              position === 'left' ? 'left-full top-1/2 -translate-y-1/2 -ml-1' :
              'right-full top-1/2 -translate-y-1/2 -mr-1'
            }`}></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced Input Component with Validation
export const EnhancedInput = ({ 
  label, 
  type = 'text', 
  value, 
  onChange, 
  error, 
  helpText, 
  required = false,
  placeholder,
  disabled = false,
  icon,
  validation,
  showPasswordToggle = false,
  ...props 
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [validationError, setValidationError] = useState('');

  const inputType = type === 'password' && showPassword ? 'text' : type;

  const handleChange = (e) => {
    const newValue = e.target.value;
    onChange(e);

    // Run validation if provided
    if (validation) {
      const validationResult = validation(newValue);
      setValidationError(validationResult || '');
    }
  };

  const hasError = error || validationError;

  return (
    <div className="mb-4">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <icon className="h-5 w-5 text-gray-400" />
          </div>
        )}
        <input
          type={inputType}
          value={value}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            block w-full rounded-md shadow-sm transition-colors duration-200
            ${icon ? 'pl-10' : 'pl-3'}
            ${showPasswordToggle ? 'pr-10' : 'pr-3'}
            py-2
            ${hasError 
              ? 'border-red-300 text-red-900 placeholder-red-300 focus:outline-none focus:ring-red-500 focus:border-red-500' 
              : isFocused
                ? 'border-blue-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                : 'border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }
            ${disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : 'bg-white'}
          `}
          {...props}
        />
        {showPasswordToggle && type === 'password' && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              type="button"
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        )}
      </div>
      {hasError && (
        <p className="mt-2 text-sm text-red-600">{error || validationError}</p>
      )}
      {helpText && !hasError && (
        <p className="mt-2 text-sm text-gray-500">{helpText}</p>
      )}
    </div>
  );
};

// Enhanced Select Component
export const EnhancedSelect = ({ 
  label, 
  value, 
  onChange, 
  options = [], 
  error, 
  helpText, 
  required = false,
  placeholder = 'Select an option...',
  disabled = false,
  searchable = false,
  multiple = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const selectRef = useRef(null);

  const filteredOptions = searchable 
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  const selectedOption = options.find(option => option.value === value);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (optionValue) => {
    onChange({ target: { value: optionValue } });
    if (!multiple) {
      setIsOpen(false);
    }
  };

  return (
    <div className="mb-4" ref={selectRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          className={`
            relative w-full bg-white border rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm
            ${error ? 'border-red-300' : 'border-gray-300'}
            ${disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''}
          `}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
        >
          <span className="block truncate">
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            {isOpen ? (
              <ChevronUpIcon className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDownIcon className="h-5 w-5 text-gray-400" />
            )}
          </span>
        </button>

        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            {searchable && (
              <div className="px-3 py-2 border-b border-gray-200">
                <input
                  type="text"
                  className="w-full px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Search options..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            )}
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-gray-500">No options found</div>
            ) : (
              filteredOptions.map((option) => (
                <div
                  key={option.value}
                  className={`
                    cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50
                    ${option.value === value ? 'bg-blue-100 text-blue-900' : 'text-gray-900'}
                  `}
                  onClick={() => handleSelect(option.value)}
                >
                  <span className={`block truncate ${option.value === value ? 'font-semibold' : 'font-normal'}`}>
                    {option.label}
                  </span>
                  {option.value === value && (
                    <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600">
                      <CheckIcon className="h-5 w-5" />
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
      {helpText && !error && (
        <p className="mt-2 text-sm text-gray-500">{helpText}</p>
      )}
    </div>
  );
};

// Enhanced Button Component
export const EnhancedButton = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  loading = false, 
  disabled = false, 
  icon, 
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  ...props 
}) => {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white',
    secondary: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500 text-white',
    success: 'bg-green-600 hover:bg-green-700 focus:ring-green-500 text-white',
    danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white',
    warning: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500 text-white',
    outline: 'border border-gray-300 bg-white hover:bg-gray-50 focus:ring-blue-500 text-gray-700',
    ghost: 'bg-transparent hover:bg-gray-100 focus:ring-gray-500 text-gray-700'
  };

  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-4 py-2 text-base',
    xl: 'px-6 py-3 text-base'
  };

  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-md 
    focus:outline-none focus:ring-2 focus:ring-offset-2 
    transition-colors duration-200 
    ${disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
    ${fullWidth ? 'w-full' : ''}
  `;

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]}`}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {icon && iconPosition === 'left' && !loading && (
        <icon className="h-4 w-4 mr-2" />
      )}
      {children}
      {icon && iconPosition === 'right' && !loading && (
        <icon className="h-4 w-4 ml-2" />
      )}
    </button>
  );
};

// Enhanced Modal Component
export const EnhancedModal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  actions
}) => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={closeOnOverlayClick ? onClose : undefined}
        ></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className={`inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:p-6 ${sizes[size]} w-full`}>
          <div className="flex items-center justify-between mb-4">
            {title && (
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                {title}
              </h3>
            )}
            {showCloseButton && (
              <button
                type="button"
                className="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={onClose}
              >
                <span className="sr-only">Close</span>
                <XCircleIcon className="h-6 w-6" />
              </button>
            )}
          </div>

          <div className="mb-6">
            {children}
          </div>

          {actions && (
            <div className="flex justify-end space-x-3">
              {actions.map((action, index) => (
                <EnhancedButton
                  key={index}
                  variant={action.variant || 'primary'}
                  onClick={action.onClick}
                  disabled={action.disabled}
                  loading={action.loading}
                >
                  {action.label}
                </EnhancedButton>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Enhanced Progress Bar
export const EnhancedProgressBar = ({ 
  value, 
  max = 100, 
  label, 
  showPercentage = true, 
  color = 'blue',
  size = 'md',
  animated = false
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colors = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
    purple: 'bg-purple-600'
  };

  const sizes = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  return (
    <div className="w-full">
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
          {showPercentage && <span className="text-sm text-gray-500">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full ${sizes[size]}`}>
        <div 
          className={`${colors[color]} ${sizes[size]} rounded-full transition-all duration-300 ${animated ? 'animate-pulse' : ''}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

// Enhanced Copy to Clipboard Component
export const CopyToClipboard = ({ text, children, onCopy }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Copied to clipboard!');
      if (onCopy) onCopy();
      
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center text-sm text-gray-600 hover:text-gray-800 focus:outline-none"
    >
      {children || (
        <>
          {copied ? (
            <CheckIcon className="h-4 w-4 mr-1" />
          ) : (
            <ClipboardDocumentIcon className="h-4 w-4 mr-1" />
          )}
          {copied ? 'Copied!' : 'Copy'}
        </>
      )}
    </button>
  );
};

// Enhanced Help Icon with Tooltip
export const HelpIcon = ({ content, position = 'top' }) => {
  return (
    <EnhancedTooltip content={content} position={position}>
      <QuestionMarkCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help" />
    </EnhancedTooltip>
  );
};

// Enhanced Card Component
export const EnhancedCard = ({ 
  title, 
  subtitle, 
  children, 
  actions, 
  className = '',
  padding = 'md',
  shadow = 'md'
}) => {
  const paddings = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const shadows = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl'
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${shadows[shadow]} ${className}`}>
      {(title || subtitle || actions) && (
        <div className={`border-b border-gray-200 ${paddings[padding]} pb-4`}>
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
            {actions && (
              <div className="flex space-x-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}
      <div className={paddings[padding]}>
        {children}
      </div>
    </div>
  );
};

export default {
  EnhancedAlert,
  EnhancedTooltip,
  EnhancedInput,
  EnhancedSelect,
  EnhancedButton,
  EnhancedModal,
  EnhancedProgressBar,
  CopyToClipboard,
  HelpIcon,
  EnhancedCard
};