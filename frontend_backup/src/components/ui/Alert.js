import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/solid';
import { useTheme } from '../../contexts/ThemeContext';

const Alert = ({
  children,
  variant = 'info',
  title,
  icon: CustomIcon,
  dismissible = false,
  onDismiss,
  className = '',
  size = 'md',
  ...props
}) => {
  const { isDark } = useTheme();
  // Size classes
  const sizeClasses = {
    sm: 'p-3 text-sm',
    md: 'p-4',
    lg: 'p-5 text-lg'
  };

  // Base classes for all alerts
  const baseClasses = `rounded-xl border shadow-sm transition-all duration-200 ${sizeClasses[size]}`;
  
  // Variant classes and icons with theme support
  const variants = {
    success: {
      classes: `bg-green-50 border-green-200 ${isDark ? 'bg-green-900/20 border-green-800' : ''}`,
      textColor: `text-green-800 ${isDark ? 'text-green-200' : ''}`,
      iconColor: `text-green-500 ${isDark ? 'text-green-400' : ''}`,
      dismissColor: `text-green-500 hover:bg-green-100 ${isDark ? 'text-green-400 hover:bg-green-800/30' : ''}`,
      icon: CheckCircleIcon
    },
    danger: {
      classes: `bg-red-50 border-red-200 ${isDark ? 'bg-red-900/20 border-red-800' : ''}`,
      textColor: `text-red-800 ${isDark ? 'text-red-200' : ''}`,
      iconColor: `text-red-500 ${isDark ? 'text-red-400' : ''}`,
      dismissColor: `text-red-500 hover:bg-red-100 ${isDark ? 'text-red-400 hover:bg-red-800/30' : ''}`,
      icon: ExclamationCircleIcon
    },
    warning: {
      classes: `bg-yellow-50 border-yellow-200 ${isDark ? 'bg-yellow-900/20 border-yellow-800' : ''}`,
      textColor: `text-yellow-800 ${isDark ? 'text-yellow-200' : ''}`,
      iconColor: `text-yellow-500 ${isDark ? 'text-yellow-400' : ''}`,
      dismissColor: `text-yellow-500 hover:bg-yellow-100 ${isDark ? 'text-yellow-400 hover:bg-yellow-800/30' : ''}`,
      icon: ExclamationTriangleIcon
    },
    info: {
      classes: `bg-blue-50 border-blue-200 ${isDark ? 'bg-blue-900/20 border-blue-800' : ''}`,
      textColor: `text-blue-800 ${isDark ? 'text-blue-200' : ''}`,
      iconColor: `text-blue-500 ${isDark ? 'text-blue-400' : ''}`,
      dismissColor: `text-blue-500 hover:bg-blue-100 ${isDark ? 'text-blue-400 hover:bg-blue-800/30' : ''}`,
      icon: InformationCircleIcon
    }
  };
  
  const { classes, textColor, iconColor, dismissColor, icon: Icon } = variants[variant];
  const FinalIcon = CustomIcon || Icon;
  
  const iconSize = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-6 w-6' : 'h-5 w-5';
  
  return (
    <div className={`${baseClasses} ${classes} ${className}`} {...props}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <div className={`rounded-lg p-1 ${iconColor.includes('green') ? 'bg-green-100' : iconColor.includes('red') ? 'bg-red-100' : iconColor.includes('yellow') ? 'bg-yellow-100' : 'bg-blue-100'} ${isDark ? 'bg-opacity-20' : ''}`}>
            <FinalIcon className={`${iconSize} ${iconColor}`} aria-hidden="true" />
          </div>
        </div>
        <div className="ml-4 flex-1">
          <div className={`${textColor}`}>
            {title && (
              <h3 className={`font-semibold ${size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-lg' : 'text-base'}`}>
                {title}
              </h3>
            )}
            <div className={`${title ? 'mt-1' : ''} ${size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'} opacity-90`}>
              {children}
            </div>
          </div>
        </div>
        {dismissible && (
          <div className="ml-4">
            <button
              type="button"
              onClick={onDismiss}
              className={`inline-flex rounded-lg p-1.5 ${dismissColor} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200`}
            >
              <span className="sr-only">Dismiss</span>
              <XMarkIcon className={`${size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'}`} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alert;