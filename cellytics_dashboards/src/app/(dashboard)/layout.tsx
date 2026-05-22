'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar>
        {user?.role === 'cell_leader' && (
          <Sidebar.Item href="/dashboard/cell-leader" icon="CL">
            My Cell
          </Sidebar.Item>
        )}

        {user?.role === 'senior_cell_leader' && (
          <Sidebar.Item href="/dashboard/senior-cell" icon="SC">
            Senior Cell
          </Sidebar.Item>
        )}

        {user?.role === 'fellowship_pastor' && (
          <Sidebar.Item href="/dashboard/fellowship" icon="FP">
            Fellowship
          </Sidebar.Item>
        )}

        {user?.role === 'zonal_admin' && (
          <>
            <Sidebar.Item href="/dashboard/zone" icon="Z">
              Zone Overview
            </Sidebar.Item>
            <Sidebar.Item href="/dashboard/zone/fellowships" icon="F">
              Fellowships
            </Sidebar.Item>
            <Sidebar.Item href="/dashboard/zone/reports" icon="R">
              Reports
            </Sidebar.Item>
            <Sidebar.Item href="/dashboard/zone/analytics" icon="A">
              Analytics
            </Sidebar.Item>
            <Sidebar.Item href="/dashboard/zone/users" icon="U">
              Users
            </Sidebar.Item>
          </>
        )}

        <div className="my-4 border-t border-navy/30" />
      </Sidebar>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</div>
    </div>
  );
}
