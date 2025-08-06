import React from 'react';
import { Spinner } from './index';

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
  ...props
}) => {
  // Base classes
  const baseClasses = 'min-w-full divide-y divide-gray-200';
  
  // Conditional classes
  const conditionalClasses = [
    bordered ? 'border border-gray-200' : '',
    compact ? 'text-xs' : 'text-sm'
  ].filter(Boolean).join(' ');
  
  // Row classes
  const getRowClasses = (index) => {
    return [
      'transition-colors',
      striped && index % 2 === 0 ? 'bg-white' : 'bg-gray-50',
      hoverable ? 'hover:bg-gray-100' : '',
      rowClassName
    ].filter(Boolean).join(' ');
  };
  
  return (
    <div className={`overflow-x-auto rounded-lg ${bordered ? 'border border-gray-200' : 'shadow-sm'} ${className}`} {...props}>
      <table className={`${baseClasses} ${conditionalClasses}`}>
        <thead className={`bg-gray-50 ${headerClassName}`}>
          <tr>
            {columns.map((column, index) => (
              <th
                key={index}
                scope="col"
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.headerClassName || ''}`}
                style={column.width ? { width: column.width } : {}}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={`bg-white divide-y divide-gray-200 ${bodyClassName}`}>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center">
                <div className="flex justify-center">
                  <Spinner size="lg" color="primary" />
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr key={rowIndex} className={getRowClasses(rowIndex)}>
                {columns.map((column, colIndex) => (
                  <td 
                    key={colIndex} 
                    className={`px-6 py-4 whitespace-nowrap ${cellClassName} ${column.cellClassName || ''}`}
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