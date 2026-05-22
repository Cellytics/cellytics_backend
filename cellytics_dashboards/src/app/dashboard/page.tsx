/**
 * DASHBOARD INDEX PAGE
 * 
 * Acts as a router/discovery page.
 * Redirects users to their role-specific dashboard.
 * 
 * Routes:
 *   GET /dashboard
 */

'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { DASHBOARD_ROUTES } from '@/utils/constants';

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      // Route based on user role
      const route = DASHBOARD_ROUTES[user.role];
      if (route) {
        router.push(route);
      }
    }
  }, [user, isLoading, router]);

  return <LoadingSpinner />;
}
