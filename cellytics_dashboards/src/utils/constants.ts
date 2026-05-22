/**
 * CONSTANTS
 * 
 * Centralize all magic strings and configuration values here.
 * Makes it easy to change things later.
 */

// Backend API base URL - will come from environment variable
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Auth storage key
export const AUTH_TOKEN_KEY = 'auth_token';
export const USER_KEY = 'user';

// Dashboard routes based on role
export const DASHBOARD_ROUTES: Record<string, string> = {
  cell_leader: '/dashboard/cell-leader',
  senior_cell_leader: '/dashboard/senior-cell',
  fellowship_pastor: '/dashboard/fellowship',
  zonal_admin: '/dashboard/zone',
};

// Colors from Tailwind config
export const COLORS = {
  gold: '#C9A646',
  navy: '#10295B',
  green: '#10B981',
  orange: '#F97316',
  red: '#EF4444',
};

// Public routes (routes that don't require authentication)
export const PUBLIC_ROUTES = ['/', '/login'];

// Auth endpoints
export const AUTH_ENDPOINTS = {
  login: '/api/auth/login',
  logout: '/api/auth/logout',
};

// Dashboard endpoints - these match your FastAPI routes
export const DASHBOARD_ENDPOINTS = {
  cell: '/api/dashboards/cell',
  seniorCell: '/api/dashboards/senior-cell',
  fellowship: '/api/dashboards/fellowship',
  zone: '/api/dashboards/zone',
};
