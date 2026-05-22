/**
 * ROOT LAYOUT
 * 
 * This wraps the ENTIRE app.
 * Every page you visit goes through this layout.
 * 
 * Here we:
 * 1. Set up global styles (Tailwind)
 * 2. Initialize the AuthProvider
 * 3. Configure fonts and metadata
 */

import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import './globals.css';

export const metadata: Metadata = {
  title: 'Cellytics - Dashboard',
  description: 'Church cell management system dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        {/* AuthProvider wraps everything so all pages have access to auth context */}
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
