import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  footer,
  className = '',
  contentClassName = '',
  titleClassName = '',
  bodyClassName = '',
  footerClassName = '',
  closeOnOverlayClick = true,
  variant = 'default',
  ...props
}) => {
  const { isDark } = useTheme();
  // Size classes
  const sizeClasses = {
    sm: 'sm:max-w-sm',
    md: 'sm:max-w-md',
    lg: 'sm:max-w-lg',
    xl: 'sm:max-w-xl',
    '2xl': 'sm:max-w-2xl',
    '3xl': 'sm:max-w-3xl',
    '4xl': 'sm:max-w-4xl',
    '5xl': 'sm:max-w-5xl',
    full: 'sm:max-w-full'
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog 
        as="div" 
        className={`fixed z-50 inset-0 overflow-y-auto ${className}`} 
        onClose={closeOnOverlayClick ? onClose : () => {}}
        {...props}
      >
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className={`fixed inset-0 backdrop-blur-sm transition-all duration-300 ${
              isDark ? 'bg-gray-900/80' : 'bg-gray-500/75'
            }`} />
          </Transition.Child>

          {/* This element is to trick the browser into centering the modal contents. */}
          <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
            &#8203;
          </span>
          
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enterTo="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 translate-y-0 sm:scale-100"
            leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <div className={`inline-block align-bottom rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle ${sizeClasses[size]} w-full ${
              variant === 'glass' 
                ? `backdrop-blur-md bg-white/10 ${isDark ? 'bg-gray-800/20' : ''} border border-white/20` 
                : `bg-white ${isDark ? 'bg-gray-800' : ''} border border-gray-200 ${isDark ? 'border-gray-700' : ''}`
            } ${contentClassName}`}>
              {/* Modal Header */}
              {title && (
                <div className={`px-6 py-5 border-b border-gray-200 ${isDark ? 'border-gray-700' : ''} ${titleClassName}`}>
                  <div className="flex items-center justify-between">
                    <Dialog.Title as="h3" className={`text-xl font-semibold text-gray-900 ${isDark ? 'text-white' : ''}`}>
                      {title}
                    </Dialog.Title>
                    {showCloseButton && (
                      <button
                        type="button"
                        className={`rounded-lg p-2 text-gray-400 hover:text-gray-500 ${isDark ? 'text-gray-500 hover:text-gray-300' : ''} 
                                   hover:bg-gray-100 ${isDark ? 'hover:bg-gray-700' : ''} 
                                   focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 
                                   transition-all duration-200`}
                        onClick={onClose}
                      >
                        <span className="sr-only">Close</span>
                        <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                      </button>
                    )}
                  </div>
                </div>
              )}
              
              {/* Modal Body */}
              <div className={`px-6 py-6 ${bodyClassName}`}>
                {children}
              </div>
              
              {/* Modal Footer */}
              {footer && (
                <div className={`px-6 py-4 bg-gray-50 ${isDark ? 'bg-gray-800/50' : ''} border-t border-gray-200 ${isDark ? 'border-gray-700' : ''} ${footerClassName}`}>
                  {footer}
                </div>
              )}
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};

export default Modal;