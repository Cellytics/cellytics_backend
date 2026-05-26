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

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      // Route based on user role with proper IDs
      if (user.role === 'cell_leader' && user.cell_id) {
        router.push(`/dashboard/cell/${user.cell_id}`);
      } else if (user.role === 'senior_cell_leader' && user.senior_cell_id) {
        router.push(`/dashboard/senior-cell/${user.senior_cell_id}`);
      } else if (user.role === 'fellowship_pastor' && user.fellowship_id) {
        router.push(`/dashboard/fellowship/${user.fellowship_id}`);
      } else if (user.role === 'zonal_admin' && user.zone_id) {
        router.push(`/dashboard/zone/${user.zone_id}`);
      } else {
        // Fallback - show error
        router.push('/login');
      }
    }
  }, [user, isLoading, router]);

  return <LoadingSpinner />;
}
