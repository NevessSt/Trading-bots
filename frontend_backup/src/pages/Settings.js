import React, { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useForm } from 'react-hook-form';
import { BellIcon, KeyIcon, UserIcon, CreditCardIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

const Settings = () => {
  const { user, updateProfile, updatePassword, loading, error } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [successMessage, setSuccessMessage] = useState('');
  
  const { 
    register: registerProfile, 
    handleSubmit: handleSubmitProfile, 
    formState: { errors: profileErrors } 
  } = useForm({
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
      telegram: user?.telegram || ''
    }
  });
  
  const { 
    register: registerPassword, 
    handleSubmit: handleSubmitPassword, 
    formState: { errors: passwordErrors },
    reset: resetPassword,
    watch
  } = useForm();
  
  const newPassword = watch('newPassword');
  
  const onProfileSubmit = async (data) => {
    try {
      await updateProfile(data);
      setSuccessMessage('Profile updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Error updating profile:', err);
    }
  };
  
  const onPasswordSubmit = async (data) => {
    try {
      await updatePassword(data.currentPassword, data.newPassword);
      setSuccessMessage('Password updated successfully');
      resetPassword();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Error updating password:', err);
    }
  };
  
  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Settings</h1>
      
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            className={`${activeTab === 'profile' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('profile')}
          >
            <UserIcon className="h-5 w-5 mr-2" />
            Profile
          </button>
          <button
            className={`${activeTab === 'security' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('security')}
          >
            <KeyIcon className="h-5 w-5 mr-2" />
            Security
          </button>
          <button
            className={`${activeTab === 'notifications' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('notifications')}
          >
            <BellIcon className="h-5 w-5 mr-2" />
            Notifications
          </button>
          <button
            className={`${activeTab === 'billing' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('billing')}
          >
            <CreditCardIcon className="h-5 w-5 mr-2" />
            Billing
          </button>
          <button
            className={`${activeTab === 'api' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} flex items-center py-4 px-6 border-b-2 font-medium text-sm`}
            onClick={() => setActiveTab('api')}
          >
            <ShieldCheckIcon className="h-5 w-5 mr-2" />
            API Keys
          </button>
        </div>
        
        <div className="p-6">
          {successMessage && (
            <div className="mb-4 bg-success-50 border border-success-200 text-success-800 px-4 py-3 rounded relative" role="alert">
              <span className="block sm:inline">{successMessage}</span>
            </div>
          )}
          
          {error && (
            <div className="mb-4 bg-danger-50 border border-danger-200 text-danger-800 px-4 py-3 rounded relative" role="alert">
              <strong className="font-bold">Error!</strong>
              <span className="block sm:inline"> {error}</span>
            </div>
          )}
          
          {activeTab === 'profile' && (
            <form onSubmit={handleSubmitProfile(onProfileSubmit)}>
              <div className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Full Name</label>
                  <input
                    id="name"
                    type="text"
                    {...registerProfile('name', { required: 'Name is required' })}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${profileErrors.name ? 'border-danger-500' : 'border-gray-300'}`}
                  />
                  {profileErrors.name && <p className="mt-1 text-sm text-danger-600">{profileErrors.name.message}</p>}
                </div>
                
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email Address</label>
                  <input
                    id="email"
                    type="email"
                    {...registerProfile('email', { 
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${profileErrors.email ? 'border-danger-500' : 'border-gray-300'}`}
                  />
                  {profileErrors.email && <p className="mt-1 text-sm text-danger-600">{profileErrors.email.message}</p>}
                </div>
                
                <div>
                  <label htmlFor="telegram" className="block text-sm font-medium text-gray-700">Telegram Username</label>
                  <div className="mt-1 flex rounded-md shadow-sm">
                    <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500">@</span>
                    <input
                      id="telegram"
                      type="text"
                      {...registerProfile('telegram')}
                      className="flex-1 block w-full rounded-none rounded-r-md border-gray-300 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="username"
                    />
                  </div>
                  <p className="mt-1 text-sm text-gray-500">For receiving trading notifications (optional)</p>
                </div>
                
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary"
                  >
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          )}
          
          {activeTab === 'security' && (
            <form onSubmit={handleSubmitPassword(onPasswordSubmit)}>
              <div className="space-y-6">
                <div>
                  <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">Current Password</label>
                  <input
                    id="currentPassword"
                    type="password"
                    {...registerPassword('currentPassword', { required: 'Current password is required' })}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${passwordErrors.currentPassword ? 'border-danger-500' : 'border-gray-300'}`}
                  />
                  {passwordErrors.currentPassword && <p className="mt-1 text-sm text-danger-600">{passwordErrors.currentPassword.message}</p>}
                </div>
                
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">New Password</label>
                  <input
                    id="newPassword"
                    type="password"
                    {...registerPassword('newPassword', { 
                      required: 'New password is required',
                      minLength: {
                        value: 8,
                        message: 'Password must be at least 8 characters'
                      }
                    })}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${passwordErrors.newPassword ? 'border-danger-500' : 'border-gray-300'}`}
                  />
                  {passwordErrors.newPassword && <p className="mt-1 text-sm text-danger-600">{passwordErrors.newPassword.message}</p>}
                </div>
                
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    {...registerPassword('confirmPassword', { 
                      required: 'Please confirm your password',
                      validate: value => value === newPassword || 'Passwords do not match'
                    })}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${passwordErrors.confirmPassword ? 'border-danger-500' : 'border-gray-300'}`}
                  />
                  {passwordErrors.confirmPassword && <p className="mt-1 text-sm text-danger-600">{passwordErrors.confirmPassword.message}</p>}
                </div>
                
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary"
                  >
                    {loading ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </div>
            </form>
          )}
          
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="trade_notifications"
                        name="trade_notifications"
                        type="checkbox"
                        defaultChecked={user?.notification_preferences?.trade_notifications}
                        className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="trade_notifications" className="font-medium text-gray-700">Trade Notifications</label>
                      <p className="text-gray-500">Receive notifications when your bots execute trades</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="performance_notifications"
                        name="performance_notifications"
                        type="checkbox"
                        defaultChecked={user?.notification_preferences?.performance_notifications}
                        className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="performance_notifications" className="font-medium text-gray-700">Performance Reports</label>
                      <p className="text-gray-500">Receive daily and weekly performance summaries</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="error_notifications"
                        name="error_notifications"
                        type="checkbox"
                        defaultChecked={user?.notification_preferences?.error_notifications}
                        className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="error_notifications" className="font-medium text-gray-700">Error Alerts</label>
                      <p className="text-gray-500">Receive notifications about system errors or bot issues</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Channels</h3>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="email_notifications"
                        name="email_notifications"
                        type="checkbox"
                        defaultChecked={user?.notification_channels?.email}
                        className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="email_notifications" className="font-medium text-gray-700">Email</label>
                      <p className="text-gray-500">Send notifications to {user?.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="telegram_notifications"
                        name="telegram_notifications"
                        type="checkbox"
                        defaultChecked={user?.notification_channels?.telegram}
                        className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="telegram_notifications" className="font-medium text-gray-700">Telegram</label>
                      <p className="text-gray-500">
                        {user?.telegram ? `Send notifications to @${user.telegram}` : 'Add your Telegram username in Profile settings'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <button
                  type="button"
                  className="btn btn-primary"
                >
                  Save Preferences
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'billing' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Current Plan</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="text-xl font-semibold text-gray-900">{user?.subscription?.plan || 'Free Plan'}</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        {user?.subscription?.status === 'active' ? 'Active' : 'Inactive'}
                        {user?.subscription?.next_billing_date && ` • Renews on ${new Date(user.subscription.next_billing_date).toLocaleDateString()}`}
                      </p>
                    </div>
                    <button className="btn btn-outline-primary">
                      {user?.subscription?.plan === 'Free Plan' ? 'Upgrade' : 'Manage'}
                    </button>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Methods</h3>
                {user?.payment_methods && user.payment_methods.length > 0 ? (
                  <div className="space-y-3">
                    {user.payment_methods.map((method, index) => (
                      <div key={index} className="flex justify-between items-center p-3 border border-gray-200 rounded-lg">
                        <div className="flex items-center">
                          <div className="bg-gray-100 p-2 rounded mr-3">
                            <CreditCardIcon className="h-6 w-6 text-gray-600" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{method.brand} •••• {method.last4}</p>
                            <p className="text-sm text-gray-500">Expires {method.exp_month}/{method.exp_year}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          {method.is_default && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                              Default
                            </span>
                          )}
                          <button className="text-gray-400 hover:text-gray-500">
                            <span className="sr-only">Edit</span>
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                              <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 bg-gray-50 rounded-lg">
                    <CreditCardIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No payment methods</h3>
                    <p className="mt-1 text-sm text-gray-500">Add a payment method to upgrade your plan.</p>
                    <div className="mt-6">
                      <button type="button" className="btn btn-primary">
                        Add Payment Method
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Billing History</h3>
                {user?.billing_history && user.billing_history.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th scope="col" className="relative px-6 py-3">
                            <span className="sr-only">Invoice</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {user.billing_history.map((item, index) => (
                          <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(item.date).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {item.description}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              ${item.amount.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${item.status === 'paid' ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'}`}>
                                {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <a href="#" className="text-primary-600 hover:text-primary-900">Invoice</a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-6 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">No billing history available.</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'api' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Binance API Keys</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Connect your Binance account to enable automated trading. We recommend creating API keys with trading permissions only (no withdrawal access).
                </p>
                
                {user?.api_keys?.binance ? (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-medium text-gray-900">Binance API Key</h4>
                        <p className="text-sm text-gray-500 mt-1">
                          API Key: •••••••••••••••••{user.api_keys.binance.key.slice(-4)}
                        </p>
                        <p className="text-sm text-gray-500">
                          Added on {new Date(user.api_keys.binance.added_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button className="btn btn-outline-secondary btn-sm">Update</button>
                        <button className="btn btn-outline-danger btn-sm">Remove</button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No API Keys</h3>
                    <p className="mt-1 text-sm text-gray-500">Add your Binance API keys to start trading.</p>
                    <div className="mt-6">
                      <button type="button" className="btn btn-primary">
                        Add Binance API Keys
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">API Key Security</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                      Your API keys are encrypted and stored securely.
                    </li>
                    <li className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                      We recommend using API keys with trading permissions only, no withdrawal access.
                    </li>
                    <li className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                      Set IP restrictions on your API keys for additional security.
                    </li>
                    <li className="flex items-start">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                      Regularly rotate your API keys to maintain security.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;