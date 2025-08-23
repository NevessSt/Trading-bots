import React, { useState, useEffect } from 'react';
import { CalendarIcon } from '@heroicons/react/24/outline';
import { format, isValid, parse, startOfDay, endOfDay, addDays, subDays, subMonths } from 'date-fns';

const DateRangePicker = ({
  startDate,
  endDate,
  onChange,
  label,
  error,
  className = '',
  dateFormat = 'yyyy-MM-dd',
  presets = true,
  ...props
}) => {
  const [localStartDate, setLocalStartDate] = useState('');
  const [localEndDate, setLocalEndDate] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  
  // Initialize local state from props
  useEffect(() => {
    if (startDate && isValid(startDate)) {
      setLocalStartDate(format(startDate, dateFormat));
    }
    if (endDate && isValid(endDate)) {
      setLocalEndDate(format(endDate, dateFormat));
    }
  }, [startDate, endDate, dateFormat]);
  
  // Handle start date change
  const handleStartDateChange = (e) => {
    const value = e.target.value;
    setLocalStartDate(value);
    
    const parsedDate = parse(value, dateFormat, new Date());
    if (isValid(parsedDate)) {
      const newStartDate = startOfDay(parsedDate);
      onChange({
        startDate: newStartDate,
        endDate: endDate || new Date()
      });
    }
  };
  
  // Handle end date change
  const handleEndDateChange = (e) => {
    const value = e.target.value;
    setLocalEndDate(value);
    
    const parsedDate = parse(value, dateFormat, new Date());
    if (isValid(parsedDate)) {
      const newEndDate = endOfDay(parsedDate);
      onChange({
        startDate: startDate || subDays(new Date(), 7),
        endDate: newEndDate
      });
    }
  };
  
  // Apply preset date range
  const applyPreset = (preset) => {
    const today = new Date();
    let newStartDate, newEndDate;
    
    switch (preset) {
      case 'today':
        newStartDate = startOfDay(today);
        newEndDate = endOfDay(today);
        break;
      case 'yesterday':
        newStartDate = startOfDay(subDays(today, 1));
        newEndDate = endOfDay(subDays(today, 1));
        break;
      case 'last7Days':
        newStartDate = startOfDay(subDays(today, 6));
        newEndDate = endOfDay(today);
        break;
      case 'last30Days':
        newStartDate = startOfDay(subDays(today, 29));
        newEndDate = endOfDay(today);
        break;
      case 'thisMonth':
        newStartDate = startOfDay(new Date(today.getFullYear(), today.getMonth(), 1));
        newEndDate = endOfDay(today);
        break;
      case 'lastMonth':
        const lastMonth = subMonths(today, 1);
        newStartDate = startOfDay(new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1));
        newEndDate = endOfDay(new Date(today.getFullYear(), today.getMonth(), 0));
        break;
      default:
        return;
    }
    
    setLocalStartDate(format(newStartDate, dateFormat));
    setLocalEndDate(format(newEndDate, dateFormat));
    
    onChange({
      startDate: newStartDate,
      endDate: newEndDate
    });
    
    setIsOpen(false);
  };
  
  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      
      <div className="flex">
        <div className="relative flex-grow">
          <input
            type="text"
            value={localStartDate}
            onChange={handleStartDateChange}
            placeholder={dateFormat.toLowerCase()}
            className={`block w-full rounded-l-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${error ? 'border-danger-500' : 'border-gray-300'}`}
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <CalendarIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
        
        <div className="flex items-center justify-center px-2 bg-gray-100 border-t border-b border-gray-300">
          <span className="text-gray-500">to</span>
        </div>
        
        <div className="relative flex-grow">
          <input
            type="text"
            value={localEndDate}
            onChange={handleEndDateChange}
            placeholder={dateFormat.toLowerCase()}
            className={`block w-full rounded-r-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${error ? 'border-danger-500' : 'border-gray-300'}`}
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <CalendarIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
      </div>
      
      {presets && (
        <div className="relative">
          <button
            type="button"
            className="mt-1 text-sm text-primary-600 hover:text-primary-800 focus:outline-none"
            onClick={() => setIsOpen(!isOpen)}
          >
            Quick select
          </button>
          
          {isOpen && (
            <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-1 text-sm ring-1 ring-black ring-opacity-5 focus:outline-none">
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('today')}
              >
                Today
              </button>
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('yesterday')}
              >
                Yesterday
              </button>
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('last7Days')}
              >
                Last 7 days
              </button>
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('last30Days')}
              >
                Last 30 days
              </button>
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('thisMonth')}
              >
                This month
              </button>
              <button
                type="button"
                className="block w-full px-4 py-2 text-left hover:bg-gray-100"
                onClick={() => applyPreset('lastMonth')}
              >
                Last month
              </button>
            </div>
          )}
        </div>
      )}
      
      {error && (
        <p className="mt-1 text-sm text-danger-600">{error}</p>
      )}
    </div>
  );
};

export default DateRangePicker;