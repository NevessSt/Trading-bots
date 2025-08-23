import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { EnvelopeIcon, PhoneIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const Contact = () => {
  const { isDark } = useTheme();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
    priority: 'medium'
  });
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
      const token = localStorage.getItem('token');
      const response = await fetch('/api/support/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        toast.success('Message sent successfully! We\'ll get back to you soon.');
        setFormData({
          name: '',
          email: '',
          subject: '',
          message: '',
          priority: 'medium'
        });
      } else {
        toast.error(data.error || 'Failed to send message');
      }
    } catch (error) {
      console.error('Contact form error:', error);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen ${isDark ? 'bg-slate-900' : 'bg-gradient-to-br from-slate-50 to-blue-50'} py-12 px-4 sm:px-6 lg:px-8`}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg mb-6">
            <ChatBubbleLeftRightIcon className="h-8 w-8 text-white" />
          </div>
          <h1 className={`text-4xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'} mb-4`}>
            Contact Support
          </h1>
          <p className={`text-lg ${isDark ? 'text-slate-400' : 'text-slate-600'} max-w-2xl mx-auto`}>
            Have questions or need help? We're here to assist you with your trading bot experience.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Information */}
          <div className="lg:col-span-1">
            <div className={`${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-white/80 border-slate-200'} backdrop-blur-sm rounded-2xl shadow-xl border p-6`}>
              <h2 className={`text-xl font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'} mb-6`}>
                Get in Touch
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${isDark ? 'bg-blue-900/30' : 'bg-blue-100'}`}>
                    <EnvelopeIcon className={`h-5 w-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                  </div>
                  <div>
                    <p className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Email</p>
                    <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>support@tradingbot.com</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${isDark ? 'bg-green-900/30' : 'bg-green-100'}`}>
                    <PhoneIcon className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                  </div>
                  <div>
                    <p className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Phone</p>
                    <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>+1 (555) 123-4567</p>
                  </div>
                </div>
              </div>
              
              <div className={`mt-6 p-4 rounded-lg ${isDark ? 'bg-blue-900/20' : 'bg-blue-50'}`}>
                <h3 className={`font-medium ${isDark ? 'text-blue-300' : 'text-blue-800'} mb-2`}>Response Times</h3>
                <ul className={`text-sm ${isDark ? 'text-blue-200' : 'text-blue-700'} space-y-1`}>
                  <li>• High Priority: 2-4 hours</li>
                  <li>• Medium Priority: 12-24 hours</li>
                  <li>• Low Priority: 24-48 hours</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <div className={`${isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-white/80 border-slate-200'} backdrop-blur-sm rounded-2xl shadow-xl border p-8`}>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="name" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                      Full Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      required
                      value={formData.name}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                        isDark 
                          ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                          : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                      placeholder="Enter your full name"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="email" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                      Email Address *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      value={formData.email}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                        isDark 
                          ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                          : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                      placeholder="Enter your email address"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="subject" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                      Subject *
                    </label>
                    <input
                      type="text"
                      id="subject"
                      name="subject"
                      required
                      value={formData.subject}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                        isDark 
                          ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                          : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                      placeholder="Brief description of your inquiry"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="priority" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                      Priority
                    </label>
                    <select
                      id="priority"
                      name="priority"
                      value={formData.priority}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 ${
                        isDark 
                          ? 'bg-slate-700/50 border-slate-600 text-slate-100 focus:border-blue-500 focus:bg-slate-700' 
                          : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-blue-500 focus:bg-white'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    >
                      <option value="low">Low - General inquiry</option>
                      <option value="medium">Medium - Account issue</option>
                      <option value="high">High - Trading problem</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="message" className={`block text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'} mb-2`}>
                    Message *
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    required
                    rows={6}
                    value={formData.message}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 rounded-xl border transition-all duration-200 resize-none ${
                      isDark 
                        ? 'bg-slate-700/50 border-slate-600 text-slate-100 placeholder-slate-400 focus:border-blue-500 focus:bg-slate-700' 
                        : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-500 focus:border-blue-500 focus:bg-white'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    placeholder="Please provide detailed information about your inquiry..."
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Sending Message...
                    </>
                  ) : (
                    'Send Message'
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;