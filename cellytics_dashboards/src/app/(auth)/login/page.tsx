/**
 * LOGIN PAGE
 * 
 * The login page.
 * Uses LoginForm component for the actual form.
 * 
 * Routes:
 *   GET /login
 *   POST /login (handled in AuthContext)
 */

'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { LoginForm } from '@/components/LoginForm';

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="w-full max-w-sm">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-navy mb-2">Sign In</h2>
        <p className="text-gray-600">
          Access your Cellytics dashboard with your credentials.
        </p>
      </div>

      <LoginForm />
    </div>
  );
}
