import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const AuthLayout = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-secondary-700 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link to="/">
          <img
            className="mx-auto h-12 w-auto"
            src="/logo192.png"
            alt="CryptoTrader AI"
          />
        </Link>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
          CryptoTrader AI
        </h2>
        <p className="mt-2 text-center text-sm text-gray-200">
          The AI-powered crypto trading bot for emerging markets
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <Outlet />
        </div>
      </div>
      
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-200">
          &copy; {new Date().getFullYear()} CryptoTrader AI. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default AuthLayout;