import { create } from 'zustand';
import axios from 'axios';
import { toast } from 'react-hot-toast';

export const useAuthStore = create((set, get) => ({
  // State
  user: null,
  isAuthenticated: null,
  isLoading: false,
  error: null,
  
  // Actions
  register: async (userData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post('/api/auth/register', userData);
      set({ 
        user: response.data.user,
        isAuthenticated: true,
        isLoading: false 
      });
      
      // Store tokens
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      
      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      toast.success('Registration successful!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed';
      set({ error: errorMessage, isLoading: false, isAuthenticated: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post('/api/auth/login', credentials);
      set({ 
        user: response.data.user,
        isAuthenticated: true,
        isLoading: false 
      });
      
      // Store tokens
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      
      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      toast.success('Login successful!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      set({ error: errorMessage, isLoading: false, isAuthenticated: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  logout: () => {
    // Remove tokens
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    // Remove Authorization header
    delete axios.defaults.headers.common['Authorization'];
    
    set({ user: null, isAuthenticated: false });
    toast.success('Logged out successfully');
  },
  
  checkAuth: async () => {
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (!accessToken || !refreshToken) {
      set({ isAuthenticated: false });
      return false;
    }
    
    try {
      // Set Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      
      // Get user profile
      const response = await axios.get('/api/auth/profile');
      set({ user: response.data, isAuthenticated: true });
      return true;
    } catch (error) {
      // Try to refresh token if unauthorized
      if (error.response?.status === 401) {
        return get().refreshToken();
      }
      
      set({ isAuthenticated: false });
      return false;
    }
  },
  
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (!refreshToken) {
      set({ isAuthenticated: false });
      return false;
    }
    
    try {
      const response = await axios.post('/api/auth/refresh', { refresh_token: refreshToken });
      
      // Store new tokens
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      
      // Set default Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // Get user profile
      const profileResponse = await axios.get('/api/auth/profile');
      set({ user: profileResponse.data, isAuthenticated: true });
      
      return true;
    } catch (error) {
      // If refresh token is invalid, logout
      get().logout();
      return false;
    }
  },
  
  updateProfile: async (userData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.put('/api/auth/profile', userData);
      set({ 
        user: response.data,
        isLoading: false 
      });
      
      toast.success('Profile updated successfully!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to update profile';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  updatePassword: async (passwordData) => {
    set({ isLoading: true, error: null });
    try {
      await axios.put('/api/auth/password', passwordData);
      set({ isLoading: false });
      
      toast.success('Password updated successfully!');
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to update password';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
}));

// Setup axios interceptor for token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried to refresh token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshed = await useAuthStore.getState().refreshToken();
      
      if (refreshed) {
        // Retry the original request with new token
        const accessToken = localStorage.getItem('accessToken');
        originalRequest.headers['Authorization'] = `Bearer ${accessToken}`;
        return axios(originalRequest);
      }
    }
    
    return Promise.reject(error);
  }
);

// Initialize axios with token if available
const accessToken = localStorage.getItem('accessToken');
if (accessToken) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
}