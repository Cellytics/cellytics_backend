'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { DonutChart } from '@/components/DonutChart';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { SuccessAlert } from '@/components/SuccessAlert';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { AUTH_TOKEN_KEY } from '@/utils/constants';
import { useParams } from 'next/navigation';

type Period = 'week' | 'month' | 'year' | 'all';
type TrendPoint = { week: string; attendance: number; first_timers: number; souls_won: number };

interface FellowshipDashboardData {
  fellowship_id: string;
  fellowship_name: string;
  pastor_name: string;
  location: string;
  period: string;
  period_start: string;
  period_end: string;
  stats: {
    total_senior_cells: number;
    total_cells: number;
    cells_reported: number;
    submission_rate_percent: number;
    total_attendance: number;
    total_first_timers: number;
    total_souls_won: number;
    total_new_members: number;
    total_finances: number;
    growth_rate_percent: number;
  };
  cells_needing_attention: any[];
  top_performers: any;
  trends: TrendPoint[];
  conversion_sources: any[];
}

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

const getPeriodLabel = (period: Period) => {
  if (period === 'week') return 'This Week';
  if (period === 'month') return 'This Month';
  if (period === 'year') return 'This Year';
  return 'All Data';
};



function StatTile({ label, value, tone = 'gold' }: { label: string; value: string | number; tone?: 'gold' | 'green' | 'orange' }) {
  const border = tone === 'green' ? 'border-l-forest-green' : tone === 'orange' ? 'border-l-orange-accent' : 'border-l-gold';
  return (
    <div className={`min-h-[78px] rounded-md border border-gray-200 ${border} border-l-4 bg-white px-4 py-3 shadow-sm`}>
      <p className="text-[11px] font-semibold text-slate-500">{label}</p>
      <p className={`mt-2 text-xl font-bold ${tone === 'green' ? 'text-forest-green' : tone === 'orange' ? 'text-orange-accent' : 'text-navy'}`}>
        {value}
      </p>
    </div>
  );
}

function FellowshipTopbar({
  fellowshipName,
  pastorName,
  location,
  period,
  onPeriodChange,
}: {
  fellowshipName: string;
  pastorName: string;
  location: string;
  period: Period;
  onPeriodChange: (period: Period) => void;
}) {
  return (
    <div className="mb-6 rounded-xl border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold text-navy">Welcome, {pastorName}.</h1>
          <p className="mt-1 text-slate-500">{fellowshipName} • {location}</p>
        </div>
        <select
          value={period}
          onChange={(event) => onPeriodChange(event.target.value as Period)}
          className="rounded-full border border-gray-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
        >
          {(['week', 'month', 'year', 'all'] as Period[]).map((option) => (
            <option key={option} value={option}>{getPeriodLabel(option)}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

function TrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
        <p className="text-center text-sm text-slate-500">No trend data available</p>
      </div>
    );
  }

  const maxAttendance = Math.max(...data.map((w) => w.attendance), 1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <h2 className="mb-4 font-serif text-base text-navy">Attendance Trend</h2>
      <div className="flex h-64 items-end gap-2 sm:gap-3">
        {data.map((week, index) => {
          const height = Math.max((week.attendance / maxAttendance) * 100, 10);
          const isCurrent = index === data.length - 1;

          return (
            <div key={week.week} className="flex flex-1 flex-col items-center gap-2">
              <div className="relative h-full w-full rounded-t bg-slate-50">
                <div
                  className={`w-full rounded-t ${isCurrent ? 'bg-gold' : 'bg-slate-200'}`}
                  style={{ height: `${height}%` }}
                  title={`${week.attendance} attendance`}
                />
              </div>
              <p className="text-[10px] text-slate-400">
                {index === 0 ? 'Start' : isCurrent ? 'Current' : ''}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CellsNeedingAttention({ cells }: { cells: any[] }) {
  if (cells.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-center text-sm text-slate-500">✓ All cells are reporting well</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-100 px-6 py-5">
        <h2 className="font-serif text-base text-navy">Cells Needing Attention</h2>
      </div>
      <div className="divide-y divide-gray-100">
        {cells.map((cell) => (
          <div key={cell.cell_id} className="flex items-start justify-between px-6 py-4">
            <div>
              <p className="font-semibold text-slate-900">{cell.cell_name}</p>
              <p className="text-xs text-slate-500">{cell.leader_name}</p>
              <p className="mt-1 text-sm text-red-600">{cell.reason}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${cell.status === 'critical' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
              {cell.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SeniorCellsGrid({ performers }: { performers: any }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-6 py-5">
          <h2 className="font-serif text-base text-navy">Top Senior Cells</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {performers.top_senior_cells.map((sc: any, idx: number) => (
            <div key={sc.id} className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gold text-sm font-bold text-navy">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-semibold text-slate-900">{sc.name}</p>
                  <p className="text-xs text-slate-500">{sc.leader_name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-navy">{formatNumber(sc.total_attendance)}</p>
                <p className="text-xs text-slate-500">attendance</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-6 py-5">
          <h2 className="font-serif text-base text-navy">Top Cells</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {performers.top_cells.map((cell: any, idx: number) => (
            <div key={cell.id} className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-navy text-sm font-bold text-gold">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-semibold text-slate-900">{cell.name}</p>
                  <p className="text-xs text-slate-500">{cell.leader_name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-navy">{formatNumber(cell.total_attendance)}</p>
                <p className="text-xs text-slate-500">attendance</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function FellowshipDashboardPage() {
  const { isLoading: authLoading } = useAuth();
  const params = useParams();
  const fellowshipId = params?.id as string;

  const [data, setData] = useState<FellowshipDashboardData | null>(null);
  const [period, setPeriod] = useState<Period>('week');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadDashboard = async () => {
    if (!fellowshipId) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/dashboards/fellowship/${fellowshipId}?period=${period}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY)}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load dashboard');
      }

      const dashboardData = await response.json();
      setData(dashboardData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fellowshipId, period]);

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-5">
        <ErrorAlert message={error || 'Unable to load fellowship dashboard'} />
      </div>
    );
  }

  const { stats, cells_needing_attention, top_performers, trends, conversion_sources } = data;

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6 lg:px-7">
        {successMessage && <SuccessAlert message={successMessage} onClose={() => setSuccessMessage(null)} />}
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        <FellowshipTopbar
          fellowshipName={data.fellowship_name}
          pastorName={data.pastor_name}
          location={data.location}
          period={period}
          onPeriodChange={setPeriod}
        />

        <div className="mb-5 grid gap-3 md:grid-cols-3 lg:grid-cols-4">
          <StatTile label="Total Cells" value={stats.total_cells} />
          <StatTile 
            label="Reporting" 
            value={`${stats.cells_reported}/${stats.total_cells}`} 
            tone={stats.submission_rate_percent >= 80 ? 'green' : stats.submission_rate_percent >= 60 ? 'orange' : 'gold'} 
          />
          <StatTile label="Total Attendance" value={formatNumber(stats.total_attendance)} />
          <StatTile label="Souls Won" value={formatNumber(stats.total_souls_won)} />
          <StatTile label="Collected" value={formatMoney(stats.total_finances)} />
          <StatTile label="First Timers" value={formatNumber(stats.total_first_timers)} />
          <StatTile label="New Members" value={formatNumber(stats.total_new_members)} />
          <StatTile label="Senior Cells" value={stats.total_senior_cells} />
          <StatTile 
            label="Growth Rate" 
            value={`${stats.growth_rate_percent > 0 ? '+' : ''}${stats.growth_rate_percent}%`}
            tone={stats.growth_rate_percent > 0 ? 'green' : 'orange'}
          />
        </div>

        <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_400px]">
          <TrendChart data={trends} />
          
          <DonutChart
            data={conversion_sources.map((source, index) => {
              const colors = ['#1E3A8A', '#F59E0B', '#10B981', '#EF4444'];
              return {
                label: source.source,
                value: source.count,
                color: colors[index % colors.length],
              };
            })}
            centerLabel="Total"
            centerValue={conversion_sources.reduce((sum, s) => sum + s.count, 0).toLocaleString()}
            title="Conversion Sources"
          />
        </div>

        <div className="mb-6">
          <SeniorCellsGrid performers={top_performers} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <CellsNeedingAttention cells={cells_needing_attention} />
          
          <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
            <h2 className="mb-4 font-serif text-base text-navy">Quick Actions</h2>
            <div className="flex flex-col gap-3">
              <Link href={`/dashboard/fellowship/${fellowshipId}/senior-cells`}>
                <Button className="w-full">View Senior Cells</Button>
              </Link>
              <Link href={`/dashboard/fellowship/${fellowshipId}/cells`}>
                <Button variant="secondary" className="w-full">View All Cells</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
