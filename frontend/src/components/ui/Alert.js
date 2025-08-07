import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/solid';

const Alert = ({
  children,
  variant = 'info',
  title,
  icon: CustomIcon,
  dismissible = false,
  onDismiss,
  className = '',
  ...props
}) => {
  // Base classes for all alerts
  const baseClasses = 'rounded-md p-4';
  
  // Variant classes and icons
  const variants = {
    success: {
      classes: 'bg-success-50 border border-success-200',
      textColor: 'text-success-800',
      iconColor: 'text-success-400',
      icon: CheckCircleIcon
    },
    danger: {
      classes: 'bg-danger-50 border border-danger-200',
      textColor: 'text-danger-800',
      iconColor: 'text-danger-400',
      icon: ExclamationCircleIcon
    },
    warning: {
      classes: 'bg-warning-50 border border-warning-200',
      textColor: 'text-warning-800',
      iconColor: 'text-warning-400',
      icon: ExclamationTriangleIcon
    },
    info: {
      classes: 'bg-blue-50 border border-blue-200',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-400',
      icon: InformationCircleIcon
    }
  };
  
  const { classes, textColor, iconColor, icon: Icon } = variants[variant];
  const FinalIcon = CustomIcon || Icon;
  
  return (
    <div className={`${baseClasses} ${classes} ${className}`} {...props}>
      <div className="flex">
        <div className="flex-shrink-0">
          <FinalIcon className={`h-5 w-5 ${iconColor}`} aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <div className={`${textColor}`}>
            {title && <h3 className="text-sm font-medium">{title}</h3>}
            <div className={`${title ? 'mt-2' : ''} text-sm`}>
              {children}
            </div>
          </div>
        </div>
        {dismissible && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onDismiss}
                className={`inline-flex rounded-md p-1.5 ${iconColor} hover:bg-${variant}-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${variant}-500`}
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alert;