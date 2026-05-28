'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/Button';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { AUTH_TOKEN_KEY } from '@/utils/constants';

interface CellData {
  id: string;
  name: string;
  leader_name: string;
  reports_count: number;
  total_attendance: number;
  total_souls_won: number;
  total_finances: number;
}

interface SeniorCellDetailsResponse {
  senior_cell_id: string;
  senior_cell_name: string;
  leader_name: string;
  period: string;
  period_start: string;
  period_end: string;
  total_cells: number;
  cells: CellData[];
  stats: {
    total_attendance: number;
    total_souls_won: number;
    total_finances: number;
  };
}

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

export default function SeniorCellDetailsPage() {
  const { isLoading: authLoading } = useAuth();
  const params = useParams();
  const fellowshipId = params?.id as string;
  const seniorCellId = params?.sId as string;

  const [data, setData] = useState<SeniorCellDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!seniorCellId) return;

    const loadDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/dashboards/senior-cell/${seniorCellId}/details`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY)}`,
            },
          }
        );
        if (!response.ok) {
          throw new Error('Failed to load senior cell details');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load senior cell details');
      } finally {
        setIsLoading(false);
      }
    };

    loadDetails();
  }, [seniorCellId]);

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5">
        <ErrorAlert message={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-5">
        <ErrorAlert message="Unable to load senior cell details" />
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6 lg:px-7">
        <div className="mb-5">
          <Link href={`/dashboard/fellowship/${fellowshipId}/senior-cells`}>
            <Button variant="secondary" className="mb-4">← Back to Senior Cells</Button>
          </Link>
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h1 className="font-serif text-2xl font-bold text-navy">{data.senior_cell_name}</h1>
            <p className="mt-1 text-slate-500">{data.leader_name} • {data.total_cells} cells</p>
          </div>
        </div>

        <div className="mb-6 grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-slate-500">Total Attendance</p>
            <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(data.stats.total_attendance)}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-slate-500">Souls Won</p>
            <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(data.stats.total_souls_won)}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-slate-500">Collections</p>
            <p className="mt-2 text-2xl font-bold text-navy">{formatMoney(data.stats.total_finances)}</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-slate-500">Cells Count</p>
            <p className="mt-2 text-2xl font-bold text-navy">{data.total_cells}</p>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-6 py-5">
            <h2 className="font-serif text-base text-navy">Cells in {data.senior_cell_name}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-600">
                <tr>
                  <th className="px-6 py-3">Cell Name</th>
                  <th className="px-6 py-3">Leader</th>
                  <th className="px-6 py-3">Reports</th>
                  <th className="px-6 py-3">Attendance</th>
                  <th className="px-6 py-3">Souls Won</th>
                  <th className="px-6 py-3">Collections</th>
                  <th className="px-6 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.cells.map((cell) => (
                  <tr key={cell.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-semibold text-slate-900">{cell.name}</td>
                    <td className="px-6 py-4 text-slate-700">{cell.leader_name}</td>
                    <td className="px-6 py-4 text-slate-700">{cell.reports_count}</td>
                    <td className="px-6 py-4 text-slate-700">{formatNumber(cell.total_attendance)}</td>
                    <td className="px-6 py-4 text-slate-700">{formatNumber(cell.total_souls_won)}</td>
                    <td className="px-6 py-4 text-slate-700">{formatMoney(cell.total_finances)}</td>
                    <td className="px-6 py-4">
                      <Link href={`/dashboard/fellowship/${fellowshipId}/cells/${cell.id}`} className="text-sm font-semibold text-navy hover:text-gold">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
