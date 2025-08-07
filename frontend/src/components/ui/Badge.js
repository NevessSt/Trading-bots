import React from 'react';

const Badge = ({
  children,
  variant = 'primary',
  size = 'md',
  rounded = 'full',
  className = '',
  ...props
}) => {
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
  
  // Variant classes
  const variantClasses = {
    primary: 'bg-primary-100 text-primary-800',
    secondary: 'bg-secondary-100 text-secondary-800',
    success: 'bg-success-100 text-success-800',
    danger: 'bg-danger-100 text-danger-800',
    warning: 'bg-warning-100 text-warning-800',
    info: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
    'primary-outline': 'bg-white text-primary-800 border border-primary-300',
    'secondary-outline': 'bg-white text-secondary-800 border border-secondary-300',
    'success-outline': 'bg-white text-success-800 border border-success-300',
    'danger-outline': 'bg-white text-danger-800 border border-danger-300',
    'warning-outline': 'bg-white text-warning-800 border border-warning-300',
    'info-outline': 'bg-white text-blue-800 border border-blue-300',
    'gray-outline': 'bg-white text-gray-800 border border-gray-300'
  };
  
  // Combine all classes
  const badgeClasses = `${baseClasses} ${sizeClasses[size]} ${roundedClasses[rounded]} ${variantClasses[variant]} ${className}`;
  
  return (
    <span className={badgeClasses} {...props}>
      {children}
    </span>
  );
};

export default Badge;