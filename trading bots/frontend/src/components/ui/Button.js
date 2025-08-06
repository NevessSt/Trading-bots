import React from 'react';
import { Link } from 'react-router-dom';

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
  
  // Variant classes
  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-primary-300',
    secondary: 'bg-secondary-600 text-white hover:bg-secondary-700 focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:bg-secondary-300',
    success: 'bg-success-600 text-white hover:bg-success-700 focus:ring-2 focus:ring-offset-2 focus:ring-success-500 disabled:bg-success-300',
    danger: 'bg-danger-600 text-white hover:bg-danger-700 focus:ring-2 focus:ring-offset-2 focus:ring-danger-500 disabled:bg-danger-300',
    warning: 'bg-warning-600 text-white hover:bg-warning-700 focus:ring-2 focus:ring-offset-2 focus:ring-warning-500 disabled:bg-warning-300',
    'outline-primary': 'border border-primary-600 text-primary-600 bg-transparent hover:bg-primary-50 focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:text-primary-300 disabled:border-primary-300',
    'outline-secondary': 'border border-secondary-600 text-secondary-600 bg-transparent hover:bg-secondary-50 focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:text-secondary-300 disabled:border-secondary-300',
    'outline-success': 'border border-success-600 text-success-600 bg-transparent hover:bg-success-50 focus:ring-2 focus:ring-offset-2 focus:ring-success-500 disabled:text-success-300 disabled:border-success-300',
    'outline-danger': 'border border-danger-600 text-danger-600 bg-transparent hover:bg-danger-50 focus:ring-2 focus:ring-offset-2 focus:ring-danger-500 disabled:text-danger-300 disabled:border-danger-300',
    'outline-warning': 'border border-warning-600 text-warning-600 bg-transparent hover:bg-warning-50 focus:ring-2 focus:ring-offset-2 focus:ring-warning-500 disabled:text-warning-300 disabled:border-warning-300',
    ghost: 'text-gray-700 bg-transparent hover:bg-gray-100 focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:text-gray-300'
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