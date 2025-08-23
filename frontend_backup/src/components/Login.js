import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { EyeIcon, EyeSlashIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { isDark } = useTheme();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      if (result.success) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-blue-50'} py-12 px-4 sm:px-6 lg:px-8`}>
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
            <ChartBarIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className={`mt-6 text-center text-3xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
            Welcome back
          </h2>
          <p className={`mt-2 text-center text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Sign in to your trading account
          </p>
          <p className={`mt-1 text-center text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-500 transition-colors duration-200"
            >
              Sign up
            </Link>
          </p>
        </div>
        
        {/* Login Form */}
        <div className={`${isDark ? 'bg-slate-800/50' : 'bg-white/80'} backdrop-blur-sm rounded-2xl shadow-xl border ${isDark ? 'border-slate-700' : 'border-slate-200'} p-8`}>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={`w-full px-4 py-3 rounded-xl border ${isDark ? 'border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-400' : 'border-slate-300 bg-white text-slate-900 placeholder-slate-500'} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>
              <div>
                <label htmlFor="password" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    className={`w-full px-4 py-3 pr-12 rounded-xl border ${isDark ? 'border-slate-600 bg-slate-700/50 text-slate-100 placeholder-slate-400' : 'border-slate-300 bg-white text-slate-900 placeholder-slate-500'} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200`}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleInputChange}
                  />
                  <button
                    type="button"
                    className={`absolute inset-y-0 right-0 pr-4 flex items-center ${isDark ? 'text-slate-400 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'} transition-colors duration-200`}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded transition-colors duration-200"
                />
                <label htmlFor="remember-me" className={`ml-2 block text-sm ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500 transition-colors duration-200">
                  Forgot password?
                </a>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] transition-all duration-200 shadow-lg"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing in...
                </>
              ) : (
                'Sign in to your account'
              )}
            </button>
          </form>
        </div>

        {/* Demo Credentials */}
        <div className={`${isDark ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'} p-6 rounded-2xl border backdrop-blur-sm`}>
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <h3 className={`text-sm font-semibold ${isDark ? 'text-blue-300' : 'text-blue-800'}`}>Demo Account</h3>
          </div>
          <div className={`text-sm ${isDark ? 'text-blue-200' : 'text-blue-700'} space-y-2`}>
            <div className="flex justify-between items-center">
              <span className="font-medium">Email:</span>
              <code className={`px-2 py-1 rounded text-xs ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-white text-slate-700'}`}>demo@example.com</code>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Password:</span>
              <code className={`px-2 py-1 rounded text-xs ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-white text-slate-700'}`}>demo123456</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;