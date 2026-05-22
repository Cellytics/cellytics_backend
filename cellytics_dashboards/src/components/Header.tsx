/**
 * HEADER COMPONENT
 * 
 * Top header bar shown on all dashboard pages.
 * Shows current page title and user profile menu.
 * 
 * Usage:
 *   <Header pageTitle="Zone Dashboard" />
 */

'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface HeaderProps {
  pageTitle: string;
  subtitle?: string;
}

export function Header({ pageTitle, subtitle }: HeaderProps) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
      {/* Left: Page Title */}
      <div>
        <h2 className="text-2xl font-bold text-navy">{pageTitle}</h2>
        {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
      </div>

      {/* Right: User Profile Menu */}
      <div className="relative">
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold to-orange-accent flex items-center justify-center text-white font-bold">
            {user?.name.charAt(0).toUpperCase()}
          </div>
          <div className="text-sm text-left">
            <p className="font-medium text-gray-800">{user?.name}</p>
            <p className="text-xs text-gray-500">{user?.phone}</p>
          </div>
          <span className="text-gray-400">v</span>
        </button>

        {/* Dropdown Menu */}
        {showUserMenu && (
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2">
            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 text-left text-sm text-gray-800 hover:bg-gray-100 transition-colors"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
