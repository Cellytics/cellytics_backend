'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ReactNode } from 'react';
import { useAuth } from '@/context/AuthContext';

interface SidebarProps {
  children: ReactNode;
}

interface SidebarItemProps {
  href: string;
  children: ReactNode;
  icon?: ReactNode;
}

function SidebarRoot({ children }: SidebarProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <aside className="flex h-screen w-64 flex-col bg-navy text-white shadow-xl">
      <div className="border-b border-white/10 px-5 py-5">
        <h1 className="font-serif text-xl font-bold text-white">Christ Embassy Portal</h1>
        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-gold">Cellytics</p>
      </div>

      {user && (
        <div className="mx-4 mt-4 rounded-lg bg-white/10 p-4">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-gold font-bold text-navy">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <p className="text-sm font-semibold">{user.name}</p>
          <p className="text-xs text-slate-300">{user.phone}</p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-gold">
            {user.role.split('_').join(' ')}
          </p>
        </div>
      )}

      <nav className="mt-4 flex-1 space-y-1 px-2">{children}</nav>

      <div className="space-y-3 border-t border-white/10 px-4 py-5">
        <button className="w-full rounded-full bg-gold px-4 py-3 text-sm font-semibold text-navy shadow">
          Generate Report
        </button>
        <button className="block text-sm text-slate-200 hover:text-white">Support</button>
        <button onClick={handleLogout} className="block text-sm font-semibold text-red-300 hover:text-red-200">
          Sign Out
        </button>
      </div>
    </aside>
  );
}

function SidebarItem({ href, children, icon }: SidebarItemProps) {
  const pathname = usePathname();
  const isActive = href === '/dashboard/zone' ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-md px-4 py-3 text-sm font-semibold transition-colors ${
        isActive
          ? 'bg-white/15 text-gold border-l-4 border-gold'
          : 'text-slate-200 hover:bg-white/10 hover:text-white border-l-4 border-transparent'
      }`}
    >
      {icon && <span className="w-6 text-center text-xs font-bold">{icon}</span>}
      <span>{children}</span>
    </Link>
  );
}

export const Sidebar = Object.assign(SidebarRoot, {
  Item: SidebarItem,
});
