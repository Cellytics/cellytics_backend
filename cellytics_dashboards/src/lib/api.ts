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

// Export API_BASE_URL for use in components
export { API_BASE_URL };

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

// ═══════════════════════════════════════════════════════════════════════════════
// MANAGEMENT API METHODS
// ═══════════════════════════════════════════════════════════════════════════════

export const managementAPI = {
  /**
   * Assign a cell to a senior cell
   */
  async assignCellToSeniorCell(cellId: string, seniorCellId: string) {
    return apiClient.post(`/admin/cells/${cellId}/assign-senior-cell`, null, {
      params: { senior_cell_id: seniorCellId }
    });
  },

  /**
   * Send in-app notification to poke a cell leader
   */
  async pokeCellLeader(userId: string, message?: string) {
    return apiClient.post(`/admin/users/${userId}/poke`, null, {
      params: { ...(message && { message }) }
    });
  },

  /**
   * Validate a cell report
   */
  async validateCellReport(reportId: string) {
    return apiClient.post(`/admin/cell-reports/${reportId}/validate`);
  },

  /**
   * Confirm finances for a cell report
   */
  async confirmReportFinances(reportId: string) {
    return apiClient.post(`/admin/cell-reports/${reportId}/confirm-finances`);
  },

  /**
   * Create a new senior cell
   */
  async createSeniorCell(fellowshipId: string, data: { name: string; leader_id?: string }) {
    return apiClient.post(`/admin/senior-cells`, data, {
      params: { fellowship_id: fellowshipId }
    });
  },

  /**
   * Update a senior cell
   */
  async updateSeniorCell(seniorCellId: string, data: { name?: string; leader_id?: string }) {
    return apiClient.patch(`/admin/senior-cells/${seniorCellId}`, data);
  },

  /**
   * Delete a senior cell
   */
  async deleteSeniorCell(seniorCellId: string) {
    return apiClient.delete(`/admin/senior-cells/${seniorCellId}`);
  }
};
