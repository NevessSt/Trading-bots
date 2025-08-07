import React from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/solid';

const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  siblingCount = 1,
  className = '',
  ...props
}) => {
  // Generate page numbers to display
  const generatePaginationItems = () => {
    // Always show first and last page
    const firstPage = 1;
    const lastPage = totalPages;
    
    // Calculate range of pages to show around current page
    const leftSiblingIndex = Math.max(currentPage - siblingCount, firstPage);
    const rightSiblingIndex = Math.min(currentPage + siblingCount, lastPage);
    
    // Determine if we need to show ellipsis
    const shouldShowLeftDots = leftSiblingIndex > firstPage + 1;
    const shouldShowRightDots = rightSiblingIndex < lastPage - 1;
    
    // Generate the array of page numbers to display
    const pageNumbers = [];
    
    // Always add first page
    pageNumbers.push(firstPage);
    
    // Add left ellipsis if needed
    if (shouldShowLeftDots) {
      pageNumbers.push('left-ellipsis');
    }
    
    // Add pages around current page
    for (let i = leftSiblingIndex; i <= rightSiblingIndex; i++) {
      if (i !== firstPage && i !== lastPage) {
        pageNumbers.push(i);
      }
    }
    
    // Add right ellipsis if needed
    if (shouldShowRightDots) {
      pageNumbers.push('right-ellipsis');
    }
    
    // Always add last page if it's different from first page
    if (lastPage !== firstPage) {
      pageNumbers.push(lastPage);
    }
    
    return pageNumbers;
  };
  
  // Handle page change
  const handlePageChange = (page) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };
  
  // If there's only one page or less, don't show pagination
  if (totalPages <= 1) {
    return null;
  }
  
  const paginationItems = generatePaginationItems();
  
  return (
    <nav className={`flex items-center justify-between border-t border-gray-200 px-4 sm:px-0 py-3 ${className}`} {...props}>
      <div className="hidden sm:block">
        <p className="text-sm text-gray-700">
          Showing page <span className="font-medium">{currentPage}</span> of{' '}
          <span className="font-medium">{totalPages}</span>
        </p>
      </div>
      <div className="flex-1 flex justify-between sm:justify-end">
        {/* Previous button */}
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'} mr-3`}
        >
          <ChevronLeftIcon className="h-5 w-5 mr-1" />
          Previous
        </button>
        
        {/* Page numbers */}
        <div className="hidden md:flex">
          {paginationItems.map((item, index) => {
            if (item === 'left-ellipsis' || item === 'right-ellipsis') {
              return (
                <span
                  key={`ellipsis-${index}`}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                >
                  ...
                </span>
              );
            }
            
            return (
              <button
                key={item}
                onClick={() => handlePageChange(item)}
                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${item === currentPage ? 'z-10 bg-primary-50 border-primary-500 text-primary-600' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
              >
                {item}
              </button>
            );
          })}
        </div>
        
        {/* Next button */}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
        >
          Next
          <ChevronRightIcon className="h-5 w-5 ml-1" />
        </button>
      </div>
    </nav>
  );
};

export default Pagination;