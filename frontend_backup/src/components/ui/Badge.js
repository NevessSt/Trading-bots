import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

const Badge = ({
  children,
  variant = 'primary',
  size = 'md',
  rounded = 'full',
  className = '',
  icon: Icon,
  dot = false,
  ...props
}) => {
  const { isDark } = useTheme();
  // Base classes for all badges
  const baseClasses = 'inline-flex items-center font-medium';
  
  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base'
  };
  
  // Rounded classes
  const roundedClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    full: 'rounded-full'
  };
  
  // Variant classes with theme support
  const variantClasses = {
    primary: `bg-blue-100 text-blue-800 ${isDark ? 'bg-blue-900/30 text-blue-300' : ''}`,
    secondary: `bg-gray-100 text-gray-800 ${isDark ? 'bg-gray-800 text-gray-300' : ''}`,
    success: `bg-green-100 text-green-800 ${isDark ? 'bg-green-900/30 text-green-300' : ''}`,
    danger: `bg-red-100 text-red-800 ${isDark ? 'bg-red-900/30 text-red-300' : ''}`,
    warning: `bg-yellow-100 text-yellow-800 ${isDark ? 'bg-yellow-900/30 text-yellow-300' : ''}`,
    info: `bg-cyan-100 text-cyan-800 ${isDark ? 'bg-cyan-900/30 text-cyan-300' : ''}`,
    purple: `bg-purple-100 text-purple-800 ${isDark ? 'bg-purple-900/30 text-purple-300' : ''}`,
    pink: `bg-pink-100 text-pink-800 ${isDark ? 'bg-pink-900/30 text-pink-300' : ''}`,
    'primary-outline': `bg-transparent text-blue-600 border border-blue-300 ${isDark ? 'text-blue-400 border-blue-600' : ''}`,
    'secondary-outline': `bg-transparent text-gray-600 border border-gray-300 ${isDark ? 'text-gray-400 border-gray-600' : ''}`,
    'success-outline': `bg-transparent text-green-600 border border-green-300 ${isDark ? 'text-green-400 border-green-600' : ''}`,
    'danger-outline': `bg-transparent text-red-600 border border-red-300 ${isDark ? 'text-red-400 border-red-600' : ''}`,
    'warning-outline': `bg-transparent text-yellow-600 border border-yellow-300 ${isDark ? 'text-yellow-400 border-yellow-600' : ''}`,
    gradient: `bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg`,
    glass: `backdrop-blur-md bg-white/10 ${isDark ? 'bg-gray-800/20' : ''} border border-white/20 text-white shadow-lg`
  };
  
  // Combine all classes
  const badgeClasses = `${baseClasses} ${sizeClasses[size]} ${roundedClasses[rounded]} ${variantClasses[variant]} ${className}`;
  
  return (
    <span className={badgeClasses} {...props}>
      {dot && (
        <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${
          variant.includes('primary') ? 'bg-blue-400' :
          variant.includes('success') ? 'bg-green-400' :
          variant.includes('danger') ? 'bg-red-400' :
          variant.includes('warning') ? 'bg-yellow-400' :
          'bg-gray-400'
        }`} />
      )}
      {Icon && (
        <Icon className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} ${
          children ? 'mr-1' : ''
        }`} />
      )}
      {children}
    </span>
  );
};

export default Badge;