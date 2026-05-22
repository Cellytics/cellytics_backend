/**
 * API TYPES
 * 
 * These define the error handling and response structures
 * for API communication.
 */

export interface ApiError {
  status: number;
  detail: string;
  timestamp?: string;
}

export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
}
