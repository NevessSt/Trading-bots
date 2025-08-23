import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      // Actions
      login: async (email, password) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await axios.post(`${API_URL}/auth/login`, { email, password });
          const { access_token, user } = response.data;
          
          // Set auth header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
          
          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Login failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };  // Returns object, doesn't throw
        }
      },
      
      register: async (username, email, password) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await axios.post(`${API_URL}/auth/register`, {
            username,
            email,
            password
          });
          
          const { access_token, user } = response.data;
          
          // Set auth header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
          
          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Registration failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },
      
      logout: () => {
        // Remove auth header
        delete axios.defaults.headers.common['Authorization'];
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null
        });
      },
      
      updateProfile: async (userData) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await axios.put(`${API_URL}/user/profile`, userData, {
            headers: { Authorization: `Bearer ${get().token}` }
          });
          
          set({
            user: { ...get().user, ...response.data.user },
            isLoading: false
          });
          
          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Profile update failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },
      
      changePassword: async (currentPassword, newPassword) => {
        set({ isLoading: true, error: null });
        
        try {
          await axios.put(`${API_URL}/user/password`, {
            current_password: currentPassword,
            new_password: newPassword
          }, {
            headers: { Authorization: `Bearer ${get().token}` }
          });
          
          set({ isLoading: false });
          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Password change failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },
      
      // Check if token is still valid
      checkAuth: async () => {
        const token = get().token;
        
        if (!token) {
          set({ isAuthenticated: false });
          return false;
        }
        
        try {
          await axios.get(`${API_URL}/auth/verify`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          return true;
        } catch (error) {
          // Token is invalid or expired
          get().logout();
          return false;
        }
      },
      
      clearError: () => set({ error: null })
    }),
    {
      name: 'auth-storage', // name of the item in localStorage
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);

export default useAuthStore;