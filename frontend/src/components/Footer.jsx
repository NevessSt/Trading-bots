import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const Footer = () => {
  const { isDark } = useTheme();

  return (
    <footer className={`mt-auto py-6 px-4 border-t ${
      isDark 
        ? 'bg-slate-800 border-slate-700 text-slate-300' 
        : 'bg-white border-slate-200 text-slate-600'
    }`}>
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          {/* Left side - Company info */}
          <div className="text-center md:text-left">
            <p className="text-sm font-medium">
              © 2024 TradingBot Pro. All rights reserved.
            </p>
            <p className="text-xs mt-1">
              Professional cryptocurrency trading platform
            </p>
          </div>

          {/* Center - Legal links */}
          <div className="flex flex-wrap justify-center items-center space-x-6 text-sm">
            <a 
              href="/disclaimer" 
              className={`hover:underline transition-colors ${
                isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'
              }`}
              onClick={(e) => {
                e.preventDefault();
                window.open('/DISCLAIMER.md', '_blank');
              }}
            >
              Risk Disclaimer
            </a>
            <a 
              href="/eula" 
              className={`hover:underline transition-colors ${
                isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'
              }`}
              onClick={(e) => {
                e.preventDefault();
                window.open('/EULA.md', '_blank');
              }}
            >
              Terms of Use (EULA)
            </a>
            <a 
              href="/license" 
              className={`hover:underline transition-colors ${
                isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'
              }`}
            >
              License
            </a>
            <a 
              href="mailto:danielmanji38@gmail.com" 
              className={`hover:underline transition-colors ${
                isDark ? 'hover:text-blue-400' : 'hover:text-blue-600'
              }`}
            >
              Support
            </a>
          </div>

          {/* Right side - Risk warning */}
          <div className="text-center md:text-right max-w-xs">
            <p className="text-xs text-red-500 font-medium">
              ⚠️ High Risk Investment
            </p>
            <p className="text-xs mt-1">
              Trading involves substantial risk of loss
            </p>
          </div>
        </div>

        {/* Bottom disclaimer */}
        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
          <p className="text-xs text-center text-slate-500 dark:text-slate-400">
            This software is for educational purposes only. Cryptocurrency trading involves substantial risk. 
            Never invest more than you can afford to lose. Past performance does not guarantee future results.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;