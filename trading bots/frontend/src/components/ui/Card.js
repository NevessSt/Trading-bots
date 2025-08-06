import React from 'react';

const Card = ({
  children,
  title,
  subtitle,
  icon: Icon,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  footer,
  isLoading = false,
  ...props
}) => {
  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden ${className}`}
      {...props}
    >
      {/* Card Header */}
      {(title || subtitle || Icon) && (
        <div className={`px-4 py-5 sm:px-6 border-b border-gray-200 ${headerClassName}`}>
          <div className="flex items-center">
            {Icon && <Icon className="h-6 w-6 text-primary-500 mr-3" />}
            <div>
              {title && <h3 className="text-lg font-medium leading-6 text-gray-900">{title}</h3>}
              {subtitle && <p className="mt-1 max-w-2xl text-sm text-gray-500">{subtitle}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Card Body */}
      <div className={`px-4 py-5 sm:p-6 ${bodyClassName}`}>
        {isLoading ? (
          <div className="flex justify-center items-center py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : (
          children
        )}
      </div>

      {/* Card Footer */}
      {footer && (
        <div className={`px-4 py-4 sm:px-6 bg-gray-50 border-t border-gray-200 ${footerClassName}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;