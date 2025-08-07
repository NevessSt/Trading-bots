import React from 'react';

const Spinner = ({
  size = 'md',
  color = 'primary',
  className = '',
  ...props
}) => {
  // Size classes
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
    xl: 'h-16 w-16 border-4'
  };
  
  // Color classes
  const colorClasses = {
    primary: 'border-primary-500',
    secondary: 'border-secondary-500',
    success: 'border-success-500',
    danger: 'border-danger-500',
    warning: 'border-warning-500',
    gray: 'border-gray-500',
    white: 'border-white'
  };
  
  return (
    <div
      className={`animate-spin rounded-full ${sizeClasses[size]} border-t-transparent ${colorClasses[color]} ${className}`}
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export default Spinner;