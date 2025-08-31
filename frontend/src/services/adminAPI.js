import axios from 'axios';
import { getAuthToken } from '../utils/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance for admin API
const adminAPI = axios.create({
  baseURL: `${API_BASE_URL}/admin`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
adminAPI.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
adminAPI.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Insufficient permissions
      console.error('Access denied: Insufficient permissions');
    }
    return Promise.reject(error);
  }
);

// Admin API methods
export const adminService = {
  // User management
  getUsers: async (params = {}) => {
    const response = await adminAPI.get('/users', { params });
    return response.data;
  },

  getUserById: async (userId) => {
    const response = await adminAPI.get(`/users/${userId}`);
    return response.data;
  },

  createUser: async (userData) => {
    const response = await adminAPI.post('/users', userData);
    return response.data;
  },

  updateUser: async (userId, userData) => {
    const response = await adminAPI.put(`/users/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await adminAPI.delete(`/users/${userId}`);
    return response.data;
  },

  activateUser: async (userId) => {
    const response = await adminAPI.post(`/users/${userId}/activate`);
    return response.data;
  },

  deactivateUser: async (userId) => {
    const response = await adminAPI.post(`/users/${userId}/deactivate`);
    return response.data;
  },

  upgradeUserLicense: async (userId, licenseData) => {
    const response = await adminAPI.post(`/users/${userId}/upgrade`, licenseData);
    return response.data;
  },

  extendUserLicense: async (userId, extensionData) => {
    const response = await adminAPI.post(`/users/${userId}/extend`, extensionData);
    return response.data;
  },

  resetUserPassword: async (userId) => {
    const response = await adminAPI.post(`/users/${userId}/reset-password`);
    return response.data;
  },

  // License management
  getLicenses: async (params = {}) => {
    const response = await adminAPI.get('/licenses', { params });
    return response.data;
  },

  getLicenseById: async (licenseId) => {
    const response = await adminAPI.get(`/licenses/${licenseId}`);
    return response.data;
  },

  createLicense: async (licenseData) => {
    const response = await adminAPI.post('/licenses', licenseData);
    return response.data;
  },

  updateLicense: async (licenseId, licenseData) => {
    const response = await adminAPI.put(`/licenses/${licenseId}`, licenseData);
    return response.data;
  },

  deleteLicense: async (licenseId) => {
    const response = await adminAPI.delete(`/licenses/${licenseId}`);
    return response.data;
  },

  activateLicense: async (licenseId) => {
    const response = await adminAPI.post(`/licenses/${licenseId}/activate`);
    return response.data;
  },

  deactivateLicense: async (licenseId) => {
    const response = await adminAPI.post(`/licenses/${licenseId}/deactivate`);
    return response.data;
  },

  extendLicense: async (licenseId, extensionData) => {
    const response = await adminAPI.post(`/licenses/${licenseId}/extend`, extensionData);
    return response.data;
  },

  // Statistics and analytics
  getStats: async () => {
    const response = await adminAPI.get('/stats');
    return response.data;
  },

  getUserStats: async (timeframe = '30d') => {
    const response = await adminAPI.get('/stats/users', {
      params: { timeframe }
    });
    return response.data;
  },

  getLicenseStats: async (timeframe = '30d') => {
    const response = await adminAPI.get('/stats/licenses', {
      params: { timeframe }
    });
    return response.data;
  },

  getRevenueStats: async (timeframe = '30d') => {
    const response = await adminAPI.get('/stats/revenue', {
      params: { timeframe }
    });
    return response.data;
  },

  getDemoUserStats: async () => {
    const response = await adminAPI.get('/stats/demo-users');
    return response.data;
  },

  // Export functionality
  exportUsers: async (format = 'csv', filters = {}) => {
    const response = await adminAPI.get('/export/users', {
      params: { format, ...filters },
      responseType: 'blob'
    });
    return response;
  },

  exportLicenses: async (format = 'csv', filters = {}) => {
    const response = await adminAPI.get('/export/licenses', {
      params: { format, ...filters },
      responseType: 'blob'
    });
    return response;
  },

  exportStats: async (format = 'csv', timeframe = '30d') => {
    const response = await adminAPI.get('/export/stats', {
      params: { format, timeframe },
      responseType: 'blob'
    });
    return response;
  },

  // Bulk operations
  bulkUserAction: async (userIds, action, data = {}) => {
    const response = await adminAPI.post('/users/bulk', {
      user_ids: userIds,
      action,
      data
    });
    return response.data;
  },

  bulkLicenseAction: async (licenseIds, action, data = {}) => {
    const response = await adminAPI.post('/licenses/bulk', {
      license_ids: licenseIds,
      action,
      data
    });
    return response.data;
  },

  // System management
  getSystemHealth: async () => {
    const response = await adminAPI.get('/system/health');
    return response.data;
  },

  getSystemLogs: async (level = 'info', limit = 100) => {
    const response = await adminAPI.get('/system/logs', {
      params: { level, limit }
    });
    return response.data;
  },

  clearSystemLogs: async () => {
    const response = await adminAPI.delete('/system/logs');
    return response.data;
  },

  // Demo user management
  getDemoUsers: async () => {
    const response = await adminAPI.get('/demo-users');
    return response.data;
  },

  extendDemoUser: async (userId, days) => {
    const response = await adminAPI.post(`/demo-users/${userId}/extend`, {
      days
    });
    return response.data;
  },

  convertDemoUser: async (userId, licenseType) => {
    const response = await adminAPI.post(`/demo-users/${userId}/convert`, {
      license_type: licenseType
    });
    return response.data;
  },

  cleanupExpiredDemoUsers: async () => {
    const response = await adminAPI.post('/demo-users/cleanup');
    return response.data;
  },

  // OAuth management
  getOAuthProviders: async () => {
    const response = await adminAPI.get('/oauth/providers');
    return response.data;
  },

  updateOAuthProvider: async (provider, config) => {
    const response = await adminAPI.put(`/oauth/providers/${provider}`, config);
    return response.data;
  },

  getOAuthStats: async () => {
    const response = await adminAPI.get('/oauth/stats');
    return response.data;
  },

  // Notification management
  sendNotification: async (notificationData) => {
    const response = await adminAPI.post('/notifications/send', notificationData);
    return response.data;
  },

  getNotificationTemplates: async () => {
    const response = await adminAPI.get('/notifications/templates');
    return response.data;
  },

  updateNotificationTemplate: async (templateId, templateData) => {
    const response = await adminAPI.put(`/notifications/templates/${templateId}`, templateData);
    return response.data;
  },

  // Audit logs
  getAuditLogs: async (params = {}) => {
    const response = await adminAPI.get('/audit-logs', { params });
    return response.data;
  },

  // Settings management
  getSettings: async () => {
    const response = await adminAPI.get('/settings');
    return response.data;
  },

  updateSettings: async (settings) => {
    const response = await adminAPI.put('/settings', settings);
    return response.data;
  }
};

export { adminAPI };
export default adminService;