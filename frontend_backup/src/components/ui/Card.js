import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

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
  variant = 'default',
  ...props
}) => {
  const { isDark } = useTheme();

  // Variant classes for different card styles
  const variantClasses = {
    default: `bg-white ${isDark ? 'bg-gray-800' : ''} border border-gray-200 ${isDark ? 'border-gray-700' : ''} shadow-sm hover:shadow-md transition-all duration-200`,
    glass: `backdrop-blur-md bg-white/10 ${isDark ? 'bg-gray-800/20' : ''} border border-white/20 shadow-lg hover:shadow-xl transition-all duration-200`,
    elevated: `bg-white ${isDark ? 'bg-gray-800' : ''} border border-gray-200 ${isDark ? 'border-gray-700' : ''} shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200`,
    gradient: `bg-gradient-to-br from-white to-gray-50 ${isDark ? 'from-gray-800 to-gray-900' : ''} border border-gray-200 ${isDark ? 'border-gray-700' : ''} shadow-md hover:shadow-lg transition-all duration-200`
  };

  return (
    <div
      className={`rounded-xl overflow-hidden ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {/* Card Header */}
      {(title || subtitle || Icon) && (
        <div className={`px-6 py-5 border-b border-gray-200 ${isDark ? 'border-gray-700' : ''} ${headerClassName}`}>
          <div className="flex items-center">
            {Icon && (
              <div className="flex-shrink-0 mr-4">
                <div className={`p-2 rounded-lg bg-blue-100 ${isDark ? 'bg-blue-900/30' : ''}`}>
                  <Icon className={`h-6 w-6 text-blue-600 ${isDark ? 'text-blue-400' : ''}`} />
                </div>
              </div>
            )}
            <div className="flex-1">
              {title && (
                <h3 className={`text-lg font-semibold leading-6 text-gray-900 ${isDark ? 'text-white' : ''}`}>
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className={`mt-1 text-sm text-gray-500 ${isDark ? 'text-gray-400' : ''}`}>
                  {subtitle}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Card Body */}
      <div className={`px-6 py-5 ${bodyClassName}`}>
        {isLoading ? (
          <div className="flex justify-center items-center py-8">
            <div className="relative">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
              <div className="absolute inset-0 animate-ping rounded-full h-10 w-10 border border-blue-400 opacity-20"></div>
            </div>
          </div>
        ) : (
          children
        )}
      </div>

      {/* Card Footer */}
      {footer && (
        <div className={`px-6 py-4 bg-gray-50 ${isDark ? 'bg-gray-800/50' : ''} border-t border-gray-200 ${isDark ? 'border-gray-700' : ''} ${footerClassName}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;