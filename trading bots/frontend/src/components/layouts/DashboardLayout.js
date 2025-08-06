import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import {
  HomeIcon,
  CubeIcon,
  ClockIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Trading Bots', href: '/bots', icon: CubeIcon },
  { name: 'Trade History', href: '/history', icon: ClockIcon },
  { name: 'Performance', href: '/performance', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`} role="dialog" aria-modal="true">
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" aria-hidden="true" onClick={() => setSidebarOpen(false)}></div>
        
        <div className="fixed inset-y-0 left-0 flex flex-col max-w-xs w-full bg-dark-900 transform transition-transform duration-300 ease-in-out">
          <div className="flex items-center justify-between h-16 px-4 bg-dark-800">
            <div className="flex items-center">
              <img className="h-8 w-auto" src="/logo192.png" alt="CryptoTrader AI" />
              <span className="ml-2 text-xl font-bold text-white">CryptoTrader AI</span>
            </div>
            <button
              type="button"
              className="text-gray-400 hover:text-white focus:outline-none"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
          
          <div className="flex-1 flex flex-col overflow-y-auto pt-5 pb-4">
            <nav className="mt-5 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex items-center px-2 py-2 text-base font-medium rounded-md ${isActive ? 'bg-dark-800 text-white' : 'text-gray-300 hover:bg-dark-800 hover:text-white'}`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="mr-4 h-6 w-6 flex-shrink-0" aria-hidden="true" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          
          <div className="p-4 border-t border-dark-700">
            <button
              onClick={handleLogout}
              className="group flex items-center px-2 py-2 text-base font-medium rounded-md text-gray-300 hover:bg-dark-800 hover:text-white w-full"
            >
              <ArrowRightOnRectangleIcon className="mr-4 h-6 w-6 flex-shrink-0" aria-hidden="true" />
              Logout
            </button>
          </div>
        </div>
      </div>
      
      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:border-r lg:border-gray-200 lg:bg-dark-900">
        <div className="flex items-center h-16 px-4 bg-dark-800">
          <img className="h-8 w-auto" src="/logo192.png" alt="CryptoTrader AI" />
          <span className="ml-2 text-xl font-bold text-white">CryptoTrader AI</span>
        </div>
        
        <div className="flex-1 flex flex-col overflow-y-auto pt-5 pb-4">
          <nav className="mt-5 px-2 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${isActive ? 'bg-dark-800 text-white' : 'text-gray-300 hover:bg-dark-800 hover:text-white'}`}
                >
                  <item.icon className="mr-3 h-5 w-5 flex-shrink-0" aria-hidden="true" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
        
        <div className="p-4 border-t border-dark-700">
          <button
            onClick={handleLogout}
            className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-300 hover:bg-dark-800 hover:text-white w-full"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5 flex-shrink-0" aria-hidden="true" />
            Logout
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="lg:pl-64 flex flex-col flex-1">
        {/* Top header */}
        <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white shadow">
          <button
            type="button"
            className="px-4 border-r border-gray-200 text-gray-500 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>
          
          <div className="flex-1 px-4 flex justify-between">
            <div className="flex-1 flex items-center">
              {/* Search bar could go here */}
            </div>
            <div className="ml-4 flex items-center md:ml-6">
              {/* Notification dropdown */}
              <button
                type="button"
                className="p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <BellIcon className="h-6 w-6" aria-hidden="true" />
              </button>
              
              {/* Profile dropdown */}
              <div className="ml-3 relative">
                <div className="flex items-center">
                  <span className="hidden md:block mr-2 text-sm font-medium text-gray-700">
                    {user?.name || 'User'}
                  </span>
                  <UserCircleIcon className="h-8 w-8 text-gray-400" aria-hidden="true" />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Main content area */}
        <main className="flex-1 pb-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;