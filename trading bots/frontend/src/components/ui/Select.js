import React from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/24/solid';

const Select = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  label,
  error,
  disabled = false,
  className = '',
  labelClassName = '',
  buttonClassName = '',
  optionsClassName = '',
  optionClassName = '',
  displayValue,
  ...props
}) => {
  // Function to get display value
  const getDisplayValue = () => {
    if (!value) return placeholder;
    
    if (displayValue) {
      return displayValue(value);
    }
    
    if (typeof value === 'object' && value.label) {
      return value.label;
    }
    
    const selectedOption = options.find(option => {
      if (typeof option === 'object' && option.value !== undefined) {
        return option.value === value;
      }
      return option === value;
    });
    
    if (selectedOption) {
      return typeof selectedOption === 'object' ? selectedOption.label : selectedOption;
    }
    
    return placeholder;
  };
  
  // Function to check if an option is selected
  const isSelected = (option) => {
    if (!value) return false;
    
    if (typeof option === 'object' && option.value !== undefined) {
      if (typeof value === 'object' && value.value !== undefined) {
        return option.value === value.value;
      }
      return option.value === value;
    }
    
    return option === value;
  };
  
  return (
    <div className={className}>
      {label && (
        <label className={`block text-sm font-medium text-gray-700 mb-1 ${labelClassName}`}>
          {label}
        </label>
      )}
      
      <Listbox value={value} onChange={onChange} disabled={disabled}>
        {({ open }) => (
          <div className="relative">
            <Listbox.Button 
              className={`relative w-full bg-white border ${error ? 'border-danger-500' : 'border-gray-300'} rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm ${disabled ? 'bg-gray-100 text-gray-500' : ''} ${buttonClassName}`}
              {...props}
            >
              <span className={`block truncate ${!value ? 'text-gray-500' : ''}`}>
                {getDisplayValue()}
              </span>
              <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </span>
            </Listbox.Button>
            
            <Transition
              show={open}
              as={React.Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options 
                className={`absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm ${optionsClassName}`}
              >
                {options.map((option, index) => {
                  const optionValue = typeof option === 'object' ? option.value : option;
                  const optionLabel = typeof option === 'object' ? option.label : option;
                  
                  return (
                    <Listbox.Option
                      key={index}
                      className={({ active }) =>
                        `${active ? 'text-white bg-primary-600' : 'text-gray-900'} cursor-default select-none relative py-2 pl-3 pr-9 ${optionClassName}`
                      }
                      value={option}
                      disabled={option.disabled}
                    >
                      {({ active, selected }) => (
                        <>
                          <span className={`${isSelected(option) ? 'font-semibold' : 'font-normal'} block truncate`}>
                            {optionLabel}
                          </span>
                          
                          {isSelected(option) && (
                            <span
                              className={`${active ? 'text-white' : 'text-primary-600'} absolute inset-y-0 right-0 flex items-center pr-4`}
                            >
                              <CheckIcon className="h-5 w-5" aria-hidden="true" />
                            </span>
                          )}
                        </>
                      )}
                    </Listbox.Option>
                  );
                })}
              </Listbox.Options>
            </Transition>
          </div>
        )}
      </Listbox>
      
      {error && (
        <p className="mt-1 text-sm text-danger-600">{error}</p>
      )}
    </div>
  );
};

export default Select;