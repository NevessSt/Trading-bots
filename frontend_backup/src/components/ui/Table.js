import React from 'react';
import { Spinner } from './index';
import { useTheme } from '../../contexts/ThemeContext';

const Table = ({
  columns,
  data,
  isLoading = false,
  emptyMessage = 'No data available',
  className = '',
  headerClassName = '',
  bodyClassName = '',
  rowClassName = '',
  cellClassName = '',
  striped = true,
  hoverable = true,
  bordered = false,
  compact = false,
  variant = 'default', // default, glass, elevated
  ...props
}) => {
  const { isDark } = useTheme();

  // Base classes with theme support
  const baseClasses = `min-w-full divide-y ${isDark ? 'divide-slate-700' : 'divide-slate-200'}`;
  
  // Variant classes
  const variantClasses = {
    default: '',
    glass: 'backdrop-blur-sm bg-white/70 dark:bg-slate-900/70',
    elevated: 'shadow-lg'
  };
  
  // Conditional classes
  const conditionalClasses = [
    bordered ? `border ${isDark ? 'border-slate-700' : 'border-slate-200'}` : '',
    compact ? 'text-xs' : 'text-sm',
    variantClasses[variant]
  ].filter(Boolean).join(' ');
  
  // Row classes with theme support
  const getRowClasses = (index) => {
    const baseRowClasses = 'transition-all duration-200';
    const stripedClasses = striped && index % 2 === 0 
      ? (isDark ? 'bg-slate-900' : 'bg-white')
      : (isDark ? 'bg-slate-800/50' : 'bg-slate-50/50');
    const hoverClasses = hoverable 
      ? (isDark ? 'hover:bg-slate-700/50 hover:shadow-md' : 'hover:bg-slate-100/80 hover:shadow-md')
      : '';
    
    return [
      baseRowClasses,
      stripedClasses,
      hoverClasses,
      rowClassName
    ].filter(Boolean).join(' ');
  };
  
  return (
    <div className={`overflow-x-auto rounded-xl ${bordered ? `border ${isDark ? 'border-slate-700' : 'border-slate-200'}` : 'shadow-sm'} ${className}`} {...props}>
      <table className={`${baseClasses} ${conditionalClasses}`}>
        <thead className={`${isDark ? 'bg-slate-800/50' : 'bg-slate-50/80'} backdrop-blur-sm ${headerClassName}`}>
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                scope="col"
                className={`px-6 py-4 text-left text-xs font-semibold ${isDark ? 'text-slate-300' : 'text-slate-600'} uppercase tracking-wider border-b ${isDark ? 'border-slate-700' : 'border-slate-200'} ${column.headerClassName || ''}`}
                style={column.width ? { width: column.width } : {}}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={`${isDark ? 'bg-slate-900/50' : 'bg-white/50'} divide-y ${isDark ? 'divide-slate-700' : 'divide-slate-200'} ${bodyClassName}`}>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-16 text-center">
                <div className="flex flex-col items-center space-y-3">
                  <Spinner size="lg" color="primary" />
                  <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading data...</p>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-16 text-center">
                <div className="flex flex-col items-center space-y-2">
                  <div className={`w-12 h-12 rounded-full ${isDark ? 'bg-slate-700' : 'bg-slate-100'} flex items-center justify-center mb-2`}>
                    <svg className={`w-6 h-6 ${isDark ? 'text-slate-400' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4m0 0l-4-4m4 4V3" />
                    </svg>
                  </div>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>{emptyMessage}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>No records found to display</p>
                </div>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr key={rowIndex} className={getRowClasses(rowIndex)}>
                {columns.map((column, colIndex) => (
                  <td 
                    key={colIndex} 
                    className={`px-6 py-4 whitespace-nowrap ${isDark ? 'text-slate-200' : 'text-slate-700'} ${cellClassName} ${column.cellClassName || ''}`}
                  >
                    {column.cell ? column.cell(row, rowIndex) : row[column.accessor]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Table;