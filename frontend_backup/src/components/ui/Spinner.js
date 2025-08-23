import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

const Spinner = ({
  size = 'md',
  color = 'primary',
  variant = 'spin',
  className = '',
  ...props
}) => {
  const { isDark } = useTheme();
  // Size classes
  const sizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };
  
  // Color classes with theme support
  const getColorClasses = (colorName) => {
    const colors = {
      primary: isDark ? 'border-blue-400' : 'border-blue-600',
      secondary: isDark ? 'border-gray-400' : 'border-gray-600',
      success: isDark ? 'border-green-400' : 'border-green-600',
      danger: isDark ? 'border-red-400' : 'border-red-600',
      warning: isDark ? 'border-yellow-400' : 'border-yellow-600',
      white: 'border-white',
      current: 'border-current'
    };
    return colors[colorName] || colors.primary;
  };

  // Spinner variants
  const renderSpinner = () => {
    switch (variant) {
      case 'dots':
        return (
          <div className={`flex space-x-1 ${className}`} {...props}>
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`${sizeClasses[size]} rounded-full ${getColorClasses(color).replace('border-', 'bg-')} animate-bounce`}
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
            <span className="sr-only">Loading...</span>
          </div>
        );
      
      case 'pulse':
        return (
          <div className={`relative ${sizeClasses[size]} ${className}`} {...props}>
            <div className={`absolute inset-0 rounded-full ${getColorClasses(color).replace('border-', 'bg-')} animate-ping opacity-20`} />
            <div className={`relative rounded-full ${sizeClasses[size]} ${getColorClasses(color).replace('border-', 'bg-')} animate-pulse`} />
            <span className="sr-only">Loading...</span>
          </div>
        );
      
      case 'bars':
        return (
          <div className={`flex items-end space-x-1 ${className}`} {...props}>
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`w-1 ${getColorClasses(color).replace('border-', 'bg-')} animate-pulse`}
                style={{ 
                  height: size === 'sm' ? '12px' : size === 'md' ? '20px' : '28px',
                  animationDelay: `${i * 0.15}s`,
                  animationDuration: '1s'
                }}
              />
            ))}
            <span className="sr-only">Loading...</span>
          </div>
        );
      
      case 'ring':
        return (
          <div className={`relative ${sizeClasses[size]} ${className}`} {...props}>
            <div className={`absolute inset-0 rounded-full border-2 ${getColorClasses(color)} opacity-20`} />
            <div className={`absolute inset-0 rounded-full border-2 border-transparent ${getColorClasses(color)} border-t-current animate-spin`} />
            <span className="sr-only">Loading...</span>
          </div>
        );
      
      default: // 'spin'
        return (
          <div
            className={`animate-spin rounded-full border-2 ${sizeClasses[size]} border-t-transparent ${getColorClasses(color)} ${className}`}
            {...props}
          >
            <span className="sr-only">Loading...</span>
          </div>
        );
    }
  };
  
  return renderSpinner();
};

export default Spinner;