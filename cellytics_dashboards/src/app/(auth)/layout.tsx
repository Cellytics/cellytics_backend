/**
 * AUTH LAYOUT
 * 
 * Layout for authentication pages (login, signup, etc).
 * These pages don't need the sidebar/header.
 * 
 * Routes under (auth):
 *   GET /login
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding/Info */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-navy via-blue-900 to-navy flex-col justify-center px-12 text-white">
        <h1 className="text-5xl font-bold text-gold mb-6">Cellytics</h1>
        <p className="text-xl text-gray-300 mb-8">
          Church cell management made simple and effective.
        </p>
        <ul className="space-y-4 text-gray-300">
          <li className="flex items-start gap-3">
            <span className="text-gold">✓</span>
            <span>Manage cells, senior cells, and fellowships</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-gold">✓</span>
            <span>Track member growth and engagement</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-gold">✓</span>
            <span>View zone-wide analytics</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-gold">✓</span>
            <span>Role-based access control</span>
          </li>
        </ul>
      </div>

      {/* Right side - Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center px-6 py-12">
        {children}
      </div>
    </div>
  );
}
