/**
 * AUTH TYPES
 * 
 * These types define the shape of authentication data.
 * They match what your FastAPI backend returns.
 */

export type UserRole = 'cell_leader' | 'senior_cell_leader' | 'fellowship_pastor' | 'zonal_admin' | 'system_admin';

export interface User {
  id: string;
  phone: string;
  name: string;
  role: UserRole;
  zone_id?: string;
  fellowship_id?: string;
  senior_cell_id?: string;
  cell_id?: string;
  is_active: boolean;
}

export interface LoginRequest {
  phone: string;
  pin: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (phone: string, pin: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}
