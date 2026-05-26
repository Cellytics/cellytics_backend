'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/Button';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';

interface CellStatus {
  cell_id: string;
  cell_name: string;
  senior_cell_name: string;
  leader_name: string;
  status: string;
  attendance: number;
  souls_won: number;
  finance: number;
}

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

function getStatusColor(status: string) {
  if (status === 'SUBMITTED') return 'bg-green-100 text-green-700';
  if (status === 'LATE') return 'bg-yellow-100 text-yellow-700';
  if (status === 'NO_REPORT') return 'bg-red-100 text-red-700';
  return 'bg-gray-100 text-gray-700';
}

export default function CellsPage() {
  const { isLoading: authLoading } = useAuth();
  const params = useParams();
  const fellowshipId = params?.id as string;

  const [cells, setCells] = useState<CellStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  useEffect(() => {
    if (!fellowshipId) return;

    const loadCells = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // This would normally call a dedicated endpoint
        // For now, we'll fetch from the dashboard endpoint
        const response = await fetch(
          `${API_BASE_URL}/dashboards/fellowship/${fellowshipId}?period=week`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load cells');
        }

        await response.json();
        // Parse cells from the dashboard data
        // This is a simplified implementation
        setCells([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load cells');
      } finally {
        setIsLoading(false);
      }
    };

    loadCells();
  }, [fellowshipId]);

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6 lg:px-7">
        <div className="mb-5">
          <Link href={`/dashboard/fellowship/${fellowshipId}`}>
            <Button variant="secondary" className="mb-4">← Back to Dashboard</Button>
          </Link>
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h1 className="font-serif text-2xl font-bold text-navy">All Cells</h1>
            <p className="mt-1 text-slate-500">View and manage all cells in this fellowship</p>
          </div>
        </div>

        <div className="mb-5 flex gap-2">
          <button
            onClick={() => setFilterStatus('')}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              filterStatus === '' 
                ? 'bg-navy text-white' 
                : 'border border-gray-200 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            All Cells
          </button>
          <button
            onClick={() => setFilterStatus('SUBMITTED')}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              filterStatus === 'SUBMITTED' 
                ? 'bg-green-600 text-white' 
                : 'border border-gray-200 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            Submitted
          </button>
          <button
            onClick={() => setFilterStatus('NO_REPORT')}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              filterStatus === 'NO_REPORT' 
                ? 'bg-red-600 text-white' 
                : 'border border-gray-200 bg-white text-slate-700 hover:bg-slate-50'
            }`}
          >
            No Report
          </button>
        </div>

        {error && <ErrorAlert message={error} />}

        {cells.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <p className="text-slate-500">No cells found</p>
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-600">
                  <tr>
                    <th className="px-6 py-3">Cell</th>
                    <th className="px-6 py-3">Senior Cell</th>
                    <th className="px-6 py-3">Leader</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Attendance</th>
                    <th className="px-6 py-3">Souls Won</th>
                    <th className="px-6 py-3">Collections</th>
                    <th className="px-6 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {cells.map((cell) => (
                    <tr key={cell.cell_id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-semibold text-slate-900">{cell.cell_name}</td>
                      <td className="px-6 py-4 text-slate-700">{cell.senior_cell_name}</td>
                      <td className="px-6 py-4 text-slate-700">{cell.leader_name}</td>
                      <td className="px-6 py-4">
                        <span className={`rounded-full px-3 py-1 text-xs font-bold ${getStatusColor(cell.status)}`}>
                          {cell.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-700">{formatNumber(cell.attendance)}</td>
                      <td className="px-6 py-4 text-slate-700">{formatNumber(cell.souls_won)}</td>
                      <td className="px-6 py-4 text-slate-700">{formatMoney(cell.finance)}</td>
                      <td className="px-6 py-4">
                        <Link href={`/dashboard/fellowship/${fellowshipId}/cells/${cell.cell_id}`} className="text-sm font-semibold text-navy hover:text-gold">
                          View Report
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
