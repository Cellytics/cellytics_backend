'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/Button';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';

interface SeniorCellData {
  id: string;
  name: string;
  leader_name: string;
  total_cells: number;
  cells_reported: number;
  submission_rate: number;
  total_attendance: number;
  total_souls_won: number;
  total_finances: number;
}

interface SeniorCellsResponse {
  fellowship_id: string;
  fellowship_name: string;
  senior_cells: SeniorCellData[];
}

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

function SeniorCellCard({ cell, fellowshipId }: { cell: SeniorCellData; fellowshipId: string }) {
  const status = cell.submission_rate >= 80 ? 'success' : cell.submission_rate >= 60 ? 'warning' : 'critical';
  const statusColors = {
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    critical: 'bg-red-100 text-red-700',
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-navy">{cell.name}</h3>
          <p className="text-xs text-slate-500">{cell.leader_name}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusColors[status]}`}>
          {Math.round(cell.submission_rate)}%
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <p className="text-[11px] text-slate-500">Cells</p>
          <p className="font-bold text-navy">{cell.cells_reported}/{cell.total_cells}</p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500">Attendance</p>
          <p className="font-bold text-navy">{formatNumber(cell.total_attendance)}</p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500">Souls Won</p>
          <p className="font-bold text-navy">{formatNumber(cell.total_souls_won)}</p>
        </div>
        <div>
          <p className="text-[11px] text-slate-500">Collections</p>
          <p className="font-bold text-navy">{formatMoney(cell.total_finances)}</p>
        </div>
      </div>

      <Link href={`/dashboard/fellowship/${fellowshipId}/senior-cells/${cell.id}`}>
        <Button variant="secondary" className="mt-4 w-full text-sm">
          View Details
        </Button>
      </Link>
    </div>
  );
}

export default function SeniorCellsPage() {
  const { isLoading: authLoading } = useAuth();
  const params = useParams();
  const fellowshipId = params?.id as string;

  const [data, setData] = useState<SeniorCellsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fellowshipId) return;

    const loadSeniorCells = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `${API_BASE_URL}/dashboards/fellowship/${fellowshipId}/senior-cells`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load senior cells');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load senior cells');
      } finally {
        setIsLoading(false);
      }
    };

    loadSeniorCells();
  }, [fellowshipId]);

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

  if (!data || data.senior_cells.length === 0) {
    return (
      <div className="p-5">
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
          <p className="text-slate-500">No senior cells found in this fellowship</p>
        </div>
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
            <h1 className="font-serif text-2xl font-bold text-navy">{data.fellowship_name} - Senior Cells</h1>
            <p className="mt-1 text-slate-500">Manage and monitor all senior cells in this fellowship</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.senior_cells.map((cell) => (
            <SeniorCellCard key={cell.id} cell={cell} fellowshipId={fellowshipId} />
          ))}
        </div>
      </div>
    </div>
  );
}
