/**
 * AUTH CONTEXT
 * 
 * This is the global auth state for the entire app.
 * It handles:
 * - Storing the current user
 * - Login/logout logic
 * - Token persistence
 * - Loading and error states
 * 
 * HOW IT WORKS:
 * 1. Wrap your app with <AuthProvider> in layout.tsx
 * 2. Use const { user, isAuthenticated } = useAuth() anywhere in your app
 * 3. Automatically redirects to login if not authenticated
 */

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, getErrorMessage } from '@/lib/api';
import { AUTH_TOKEN_KEY, USER_KEY } from '@/utils/constants';
import type { User, AuthContextType, LoginRequest, LoginResponse } from '@/types/auth';

// Create the context (this is where the data lives)
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AUTH PROVIDER COMPONENT
 * 
 * Wrap your app with this to provide auth context to all children.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * EFFECT: Run on mount
   * 
   * Check if user is already logged in (token in localStorage)
   * If yes, restore the user session
   */
  useEffect(() => {
    const restoreSession = () => {
      try {
        // Check if we have a saved token and user
        const savedToken = localStorage.getItem(AUTH_TOKEN_KEY);
        const savedUser = localStorage.getItem(USER_KEY);

        if (savedToken && savedUser) {
          // Parse and restore user
          setUser(JSON.parse(savedUser));
        }
      } catch (err) {
        console.error('Error restoring session:', err);
        // Clear corrupted data
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  /**
   * LOGIN FUNCTION
   * 
   * Makes POST request to /auth/login with phone and PIN
   * Saves token and user to localStorage
   * Updates context state
   */
  const login = async (phone: string, pin: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', {
        phone,
        pin,
      } satisfies LoginRequest);

      const { access_token, user: userData } = response.data;

      // Save to localStorage
      localStorage.setItem(AUTH_TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));

      // Update context state
      setUser(userData);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * LOGOUT FUNCTION
   * 
   * Clears user and token from localStorage
   * Updates context state
   */
  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setError(null);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * HOOK: useAuth
 * 
 * Use this hook anywhere in your app to access auth context.
 * Example:
 * 
 *   const { user, isAuthenticated, login } = useAuth();
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
