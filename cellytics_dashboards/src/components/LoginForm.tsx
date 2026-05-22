'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from './Button';
import { ErrorAlert } from './ErrorAlert';
import { useAuth } from '@/context/AuthContext';

export function LoginForm() {
  const [phone, setPhone] = useState('');
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!phone.trim()) {
      setError('Phone number is required');
      return;
    }

    if (!/^\d{6}$/.test(pin)) {
      setError('PIN must be exactly 6 digits');
      return;
    }

    setIsLoading(true);
    try {
      await login(phone, pin);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mx-auto w-full max-w-sm space-y-4">
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <div>
        <label htmlFor="phone" className="mb-1 block text-sm font-medium text-gray-700">
          Phone Number
        </label>
        <input
          id="phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="+237690000000"
          required
          disabled={isLoading}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none focus:border-transparent focus:ring-2 focus:ring-gold disabled:bg-gray-100"
        />
        <p className="mt-1 text-xs text-gray-500">Include country code, e.g. +237.</p>
      </div>

      <div>
        <label htmlFor="pin" className="mb-1 block text-sm font-medium text-gray-700">
          PIN
        </label>
        <input
          id="pin"
          type="password"
          value={pin}
          onChange={(event) => setPin(event.target.value.replace(/\D/g, '').slice(0, 6))}
          placeholder="000000"
          required
          disabled={isLoading}
          maxLength={6}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none focus:border-transparent focus:ring-2 focus:ring-gold disabled:bg-gray-100"
        />
        <p className="mt-1 text-xs text-gray-500">Your 6-digit PIN.</p>
      </div>

      <Button type="submit" fullWidth loading={isLoading} disabled={isLoading}>
        Sign In
      </Button>

      <p className="text-center text-sm text-gray-600">
        Contact your administrator if you don&apos;t have login credentials.
      </p>
    </form>
  );
}
