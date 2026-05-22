/**
 * LANDING PAGE
 * 
 * Users see this before login.
 * Simple page with welcome message and link to login.
 * 
 * Routes:
 *   GET /
 */

import Link from 'next/link';
import { Button } from '@/components/Button';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-navy via-blue-900 to-navy flex items-center justify-center px-4">
      <div className="text-center max-w-2xl">
        {/* Logo/Branding */}
        <h1 className="text-5xl font-bold text-gold mb-4">Cellytics</h1>
        <p className="text-xl text-gray-300 mb-2">Church Cell Management System</p>
        <p className="text-gray-400 mb-8">
          Manage your cells, track growth, and lead effectively with Cellytics dashboards.
        </p>

        {/* CTA */}
        <Link href="/login">
          <Button variant="primary">
            Get Started
          </Button>
        </Link>

        {/* Features preview */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
            <p className="text-2xl mb-2">📊</p>
            <h3 className="font-bold text-white mb-2">Smart Dashboards</h3>
            <p className="text-gray-300 text-sm">
              Role-based dashboards for cells, senior cells, fellowships, and zones.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
            <p className="text-2xl mb-2">🔒</p>
            <h3 className="font-bold text-white mb-2">Secure Access</h3>
            <p className="text-gray-300 text-sm">
              JWT authentication with role-based access control.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
            <p className="text-2xl mb-2">📈</p>
            <h3 className="font-bold text-white mb-2">Track Growth</h3>
            <p className="text-gray-300 text-sm">
              Monitor member growth, attendance, and engagement metrics.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur p-6 rounded-lg">
            <p className="text-2xl mb-2">⚡</p>
            <h3 className="font-bold text-white mb-2">Real-time Data</h3>
            <p className="text-gray-300 text-sm">
              Instant access to aggregated data from your backend.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
