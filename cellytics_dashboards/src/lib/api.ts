/**
 * API CLIENT
 * 
 * This file sets up Axios with:
 * 1. Base URL pointing to your FastAPI backend
 * 2. Request interceptor to attach JWT token
 * 3. Response interceptor for error handling
 * 
 * Think of this as a "smart HTTP wrapper" that knows about auth.
 * Every API call made through this client automatically includes the token.
 */

import axios, { AxiosError } from 'axios';
import { API_BASE_URL, AUTH_TOKEN_KEY } from '@/utils/constants';
import type { ApiError } from '@/types/api';

// Create axios instance with base URL
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * REQUEST INTERCEPTOR
 * 
 * Runs BEFORE every request.
 * Attaches the JWT token to the Authorization header.
 */
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    
    // If token exists, add it to headers
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * RESPONSE INTERCEPTOR
 * 
 * Runs AFTER every response.
 * Handles errors like 401 (token expired).
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // If we get a 401, token is expired/invalid
    if (error.response?.status === 401) {
      // Clear stored auth data
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem('user');
      
      // Redirect to login (you'll implement this in AuthContext)
      // For now, just reject the error
    }
    
    return Promise.reject(error);
  }
);

/**
 * HELPER: Check if error is an API error
 */
export const isApiError = (error: unknown): error is AxiosError<ApiError> => {
  return axios.isAxiosError(error);
};

/**
 * HELPER: Get error message from API error
 */
export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    // Try to get detail from FastAPI error response
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    // Fallback to status text
    return error.message || 'An error occurred';
  }
  return 'An unexpected error occurred';
};
