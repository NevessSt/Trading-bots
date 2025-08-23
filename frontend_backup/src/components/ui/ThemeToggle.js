import React from 'react';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

const ThemeToggle = ({ className = '' }) => {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative inline-flex h-10 w-10 items-center justify-center rounded-lg
        bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700
        border border-slate-200 dark:border-slate-700
        transition-all duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        group
        ${className}
      `}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {/* Sun Icon for Light Mode */}
      <SunIcon 
        className={`
          h-5 w-5 text-amber-500 transition-all duration-300 ease-in-out
          ${isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'}
          absolute
        `}
      />
      
      {/* Moon Icon for Dark Mode */}
      <MoonIcon 
        className={`
          h-5 w-5 text-slate-700 dark:text-slate-300 transition-all duration-300 ease-in-out
          ${isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'}
          absolute
        `}
      />
      
      {/* Hover effect */}
      <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/10 group-hover:to-purple-500/10 transition-all duration-200" />
    </button>
  );
};

// Alternative compact version for mobile/small spaces
export const CompactThemeToggle = ({ className = '' }) => {
  const { toggleTheme, isDark } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative inline-flex h-8 w-8 items-center justify-center rounded-md
        bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
        ${className}
      `}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? (
        <SunIcon className="h-4 w-4 text-amber-500" />
      ) : (
        <MoonIcon className="h-4 w-4 text-slate-600" />
      )}
    </button>
  );
};

// Toggle switch style theme toggle
export const SwitchThemeToggle = ({ className = '' }) => {
  const { toggleTheme, isDark } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full
        transition-colors duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        ${isDark ? 'bg-blue-600' : 'bg-slate-200'}
        ${className}
      `}
      role="switch"
      aria-checked={isDark}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <span className="sr-only">Toggle theme</span>
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white shadow-sm
          transition-transform duration-200 ease-in-out
          ${isDark ? 'translate-x-6' : 'translate-x-1'}
        `}
      >
        {isDark ? (
          <MoonIcon className="h-3 w-3 text-blue-600 m-0.5" />
        ) : (
          <SunIcon className="h-3 w-3 text-amber-500 m-0.5" />
        )}
      </span>
    </button>
  );
};

export default ThemeToggle;