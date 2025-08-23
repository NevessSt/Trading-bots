import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { isDark } = useTheme();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Password validation
    if (name === 'password') {
      setPasswordValidation({
        length: value.length >= 8,
        uppercase: /[A-Z]/.test(value),
        lowercase: /[a-z]/.test(value),
        number: /\d/.test(value),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(value)
      });
    }
  };

  const isPasswordValid = Object.values(passwordValidation).every(Boolean);
  const doPasswordsMatch = formData.password === formData.confirmPassword;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isPasswordValid) {
      toast.error('Please ensure your password meets all requirements');
      return;
    }

    if (!doPasswordsMatch) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const userData = {
        username: formData.username,
        email: formData.email,
        password: formData.password
      };
      
      const result = await register(userData);
      if (result.success) {
        toast.success('Registration successful! Please check your email to verify your account.');
        navigate('/login');
      }
    } catch (error) {
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const ValidationIcon = ({ isValid }) => (
    isValid ? (
      <CheckIcon className="h-4 w-4 text-green-500" />
    ) : (
      <XMarkIcon className="h-4 w-4 text-red-500" />
    )
  );

  return (
    <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-blue-50'} py-12 px-4 sm:px-6 lg:px-8`}>
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
            <ChartBarIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className={`mt-6 text-center text-3xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
            Join TradingBot Pro
          </h2>
          <p className={`mt-2 text-center text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Create your trading account
          </p>
          <p className={`mt-1 text-center text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-semibold text-blue-600 hover:text-blue-500 transition-colors duration-200"
            >
              Sign in
            </Link>
          </p>
        </div>
        
        {/* Form */}
        <div className={`${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-white/80 border-slate-200'} backdrop-blur-sm rounded-2xl shadow-xl border p-8`}>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-5">
              {/* Username Field */}
              <div>
                <label htmlFor="username" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                    isDark 
                      ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                  placeholder="Enter your username"
                  value={formData.username}
                  onChange={handleInputChange}
                />
              </div>

              {/* Email Field */}
              <div>
                <label htmlFor="email" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                    isDark 
                      ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>

              {/* Password Field */}
              <div>
                <label htmlFor="password" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    className={`w-full px-4 py-3 pr-12 rounded-xl border transition-all duration-200 ${
                      isDark 
                        ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleInputChange}
                  />
                  <button
                    type="button"
                    className={`absolute inset-y-0 right-0 pr-4 flex items-center transition-colors duration-200 ${
                      isDark ? 'text-slate-400 hover:text-slate-300' : 'text-slate-500 hover:text-slate-700'
                    }`}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              
                {/* Password Requirements */}
                {formData.password && (
                  <div className={`mt-3 p-4 rounded-xl ${isDark ? 'bg-slate-700/30 border border-slate-600/50' : 'bg-slate-50 border border-slate-200'}`}>
                    <p className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-3`}>Password Requirements:</p>
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div className="flex items-center space-x-3">
                        <ValidationIcon isValid={passwordValidation.length} />
                        <span className={passwordValidation.length ? 'text-green-500 font-medium' : (isDark ? 'text-slate-400' : 'text-slate-500')}>
                          At least 8 characters
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <ValidationIcon isValid={passwordValidation.uppercase} />
                        <span className={passwordValidation.uppercase ? 'text-green-500 font-medium' : (isDark ? 'text-slate-400' : 'text-slate-500')}>
                          One uppercase letter
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <ValidationIcon isValid={passwordValidation.lowercase} />
                        <span className={passwordValidation.lowercase ? 'text-green-500 font-medium' : (isDark ? 'text-slate-400' : 'text-slate-500')}>
                          One lowercase letter
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <ValidationIcon isValid={passwordValidation.number} />
                        <span className={passwordValidation.number ? 'text-green-500 font-medium' : (isDark ? 'text-slate-400' : 'text-slate-500')}>
                          One number
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <ValidationIcon isValid={passwordValidation.special} />
                        <span className={passwordValidation.special ? 'text-green-500 font-medium' : (isDark ? 'text-slate-400' : 'text-slate-500')}>
                          One special character
                        </span>
                      </div>
                    </div>
                  </div>
                )}
            </div>

              {/* Confirm Password Field */}
              <div>
                <label htmlFor="confirmPassword" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    className={`w-full px-4 py-3 pr-12 rounded-xl border transition-all duration-200 ${
                      formData.confirmPassword && !doPasswordsMatch
                        ? (isDark ? 'border-red-500 bg-red-500/10' : 'border-red-300 bg-red-50')
                        : (isDark 
                          ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                          : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white')
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                  />
                  <button
                    type="button"
                    className={`absolute inset-y-0 right-0 pr-4 flex items-center transition-colors duration-200 ${
                      isDark ? 'text-slate-400 hover:text-slate-300' : 'text-slate-500 hover:text-slate-700'
                    }`}
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {formData.confirmPassword && !doPasswordsMatch && (
                  <p className="mt-2 text-sm text-red-500 font-medium">Passwords do not match</p>
                )}
              </div>
          </div>

            {/* Terms and Conditions */}
            <div className="flex items-start space-x-3">
              <input
                id="terms"
                name="terms"
                type="checkbox"
                required
                className={`mt-1 h-4 w-4 rounded border-2 transition-colors duration-200 ${
                  isDark 
                    ? 'bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500/20' 
                    : 'bg-white border-slate-300 text-blue-600 focus:ring-blue-500/20'
                } focus:ring-2`}
              />
              <label htmlFor="terms" className={`block text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                I agree to the{' '}
                <a href="#" className="font-semibold text-blue-600 hover:text-blue-500 transition-colors duration-200">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="font-semibold text-blue-600 hover:text-blue-500 transition-colors duration-200">
                  Privacy Policy
                </a>
              </label>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading || !isPasswordValid || !doPasswordsMatch}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-blue-600 disabled:hover:to-purple-600 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                    Creating your account...
                  </div>
                ) : (
                  'Create Account'
                )}
              </button>
            </div>

            {/* Sign In Link */}
            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className={`w-full border-t ${isDark ? 'border-slate-600' : 'border-slate-300'}`} />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className={`px-4 ${isDark ? 'bg-slate-800/50 text-slate-400' : 'bg-white/80 text-slate-500'}`}>
                    Already have an account?
                  </span>
                </div>
              </div>

              <div className="mt-6">
                <Link
                  to="/login"
                  className={`w-full flex justify-center py-3 px-4 border rounded-xl shadow-sm text-sm font-semibold transition-all duration-200 ${
                    isDark 
                      ? 'border-slate-600 text-slate-300 bg-slate-700/50 hover:bg-slate-700 hover:border-slate-500' 
                      : 'border-slate-300 text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-400'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 hover:shadow-md`}
                >
                  Sign in to your account
                </Link>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;