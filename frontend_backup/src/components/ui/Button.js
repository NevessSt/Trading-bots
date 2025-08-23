import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';

const Button = ({
  children,
  type = 'button',
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  isLoading = false,
  to = null,
  onClick,
  ...props
}) => {
  // Base classes for all buttons
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none transition duration-150 ease-in-out';
  
  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  // Get theme context
  const { isDark } = useTheme();

  // Variant classes with theme support
  const variantClasses = {
    primary: `bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 
             focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed 
             shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200`,
    secondary: `bg-gradient-to-r from-gray-600 to-gray-700 text-white hover:from-gray-700 hover:to-gray-800 
               focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed 
               shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200`,
    success: `bg-gradient-to-r from-green-600 to-green-700 text-white hover:from-green-700 hover:to-green-800 
             focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed 
             shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200`,
    danger: `bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 
            focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed 
            shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200`,
    warning: `bg-gradient-to-r from-yellow-600 to-yellow-700 text-white hover:from-yellow-700 hover:to-yellow-800 
             focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed 
             shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200`,
    'outline-primary': `border-2 border-blue-600 text-blue-600 bg-transparent hover:bg-blue-50 ${isDark ? 'hover:bg-blue-900/20' : ''} 
                       focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed 
                       transition-all duration-200`,
    'outline-secondary': `border-2 border-gray-600 text-gray-600 bg-transparent hover:bg-gray-50 ${isDark ? 'hover:bg-gray-800/20' : ''} 
                         focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed 
                         transition-all duration-200`,
    ghost: `text-gray-700 ${isDark ? 'text-gray-300' : ''} bg-transparent hover:bg-gray-100 ${isDark ? 'hover:bg-gray-800' : ''} 
           focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed 
           transition-all duration-200`,
    glass: `backdrop-blur-md bg-white/10 ${isDark ? 'bg-gray-800/20' : ''} border border-white/20 text-white 
           hover:bg-white/20 focus:ring-2 focus:ring-offset-2 focus:ring-white/50 disabled:opacity-50 
           disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all duration-200`
  };
  
  // Loading state
  const loadingClasses = isLoading ? 'relative !text-transparent' : '';
  
  // Combine all classes
  const buttonClasses = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${loadingClasses} ${className}`;
  
  // Loading spinner
  const LoadingSpinner = () => (
    <div className="absolute inset-0 flex items-center justify-center">
      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  );
  
  // If it's a link
  if (to) {
    return (
      <Link
        to={to}
        className={buttonClasses}
        {...props}
      >
        {children}
        {isLoading && <LoadingSpinner />}
      </Link>
    );
  }
  
  // Regular button
  return (
    <button
      type={type}
      className={buttonClasses}
      disabled={disabled || isLoading}
      onClick={onClick}
      {...props}
    >
      {children}
      {isLoading && <LoadingSpinner />}
    </button>
  );
};

export default Button;