'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
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

function StatCard({ 
  label, 
  value, 
  subtext = '', 
  tone = 'gold',
  percentage = null 
}: { 
  label: string; 
  value: string | number; 
  subtext?: string;
  tone?: 'gold' | 'green' | 'blue' | 'purple' | 'orange';
  percentage?: number | null;
}) {
  const colorClasses = {
    gold: 'border-l-gold text-yellow-600',
    green: 'border-l-green-500 text-green-600',
    blue: 'border-l-navy text-navy',
    purple: 'border-l-purple-500 text-purple-600',
    orange: 'border-l-orange-500 text-orange-600',
  };

  const colors = colorClasses[tone];

  return (
    <div className={`rounded-lg border border-gray-200 ${colors.split(' ')[0]} border-l-4 bg-white px-4 py-3 shadow-sm`}>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${colors.split(' ').slice(1).join(' ')}`}>
        {value}
      </p>
      {subtext && <p className="mt-1 text-xs text-slate-400">{subtext}</p>}
      {percentage !== null && (
        <p className={`mt-1 text-xs font-semibold ${percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {percentage >= 0 ? '↑' : '↓'} {Math.abs(percentage)}%
        </p>
      )}
    </div>
  );
}

function FellowshipTopbar({
  fellowshipName,
  period,
  onPeriodChange,
  onRefresh,
}: {
  fellowshipName: string;
  period: Period;
  onPeriodChange: (period: Period) => void;
  onRefresh: () => void;
}) {
  return (
    <div className="mb-6 rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-navy text-sm font-bold text-gold">
            {fellowshipName.charAt(0)}
          </div>
          <div>
            <p className="text-lg font-semibold text-navy">Welcome, {fellowshipName.split(' ')[0]}.</p>
            <p className="text-xs text-slate-500">Your fellowship at a glance.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={period}
            onChange={(event) => onPeriodChange(event.target.value as Period)}
            className="rounded-lg border border-gray-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-100"
          >
            {(['week', 'month', 'year', 'all'] as Period[]).map((option) => (
              <option key={option} value={option}>{getPeriodLabel(option)}</option>
            ))}
          </select>
          <button
            onClick={onRefresh}
            className="rounded-lg border border-gray-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-100"
          >
            ↻ Refresh
          </button>
        </div>
      </div>
    </div>
  );
}

function AttendanceTrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
        <p className="text-center text-sm text-slate-500">No trend data available</p>
      </div>
    );
  }

  const maxAttendance = Math.max(...data.map((w) => w.attendance + w.first_timers), 1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="font-semibold text-navy">Fellowship Attendance Trend</h2>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-sm bg-navy"></div>
            <span className="text-slate-600">Attendance</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-sm bg-sky-200"></div>
            <span className="text-slate-600">Variance</span>
          </div>
        </div>
      </div>
      
      <div className="flex h-64 items-end gap-1 sm:gap-2">
        {data.map((week) => {
          const attendanceHeight = (week.attendance / maxAttendance) * 100;
          const totalHeight = ((week.attendance + week.first_timers) / maxAttendance) * 100;
          const varianceHeight = totalHeight - attendanceHeight;

          return (
            <div key={week.week} className="flex flex-1 flex-col items-center gap-2">
              <div className="relative h-full w-full rounded-t bg-slate-50">
                {/* Main attendance bar */}
                <div
                  className="w-full rounded-t bg-navy transition-all"
                  style={{ height: `${attendanceHeight}%` }}
                  title={`${week.attendance} attendance`}
                />
                {/* Variance bar */}
                {varianceHeight > 0 && (
                  <div
                    className="w-full bg-sky-200 transition-all"
                    style={{ height: `${varianceHeight}%` }}
                    title={`${week.first_timers} first timers`}
                  />
                )}
              </div>
              <p className="text-[10px] text-slate-400">
                Week {week.week.split(' ')[1] || week.week}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ConversionSourcesChart({ data }: { data: any[] }) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
        <p className="text-center text-sm text-slate-500">No conversion data available</p>
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.count, 0);
  const colors = ['bg-navy', 'bg-gold', 'bg-sky-500', 'bg-emerald-500', 'bg-purple-500'];

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <h2 className="mb-6 font-semibold text-navy">Conversion Sources</h2>
      
      {/* Simple pie chart representation */}
      <div className="flex flex-col gap-4">
        {data.map((source, idx) => {
          const percentage = ((source.count / total) * 100).toFixed(1);
          
          return (
            <div key={source.source}>
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`h-3 w-3 rounded-full ${colors[idx % colors.length]}`}></div>
                  <span className="text-sm font-semibold text-slate-700">{source.source}</span>
                </div>
                <span className="text-sm font-bold text-navy">{percentage}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full ${colors[idx % colors.length]}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-center">
        <p className="text-xs text-slate-500">
          Total: <span className="font-bold text-navy">{formatNumber(total)}</span> souls
        </p>
      </div>
    </div>
  );
}

function SeniorCellPerformanceTable({ performers }: { performers: any }) {
  if (!performers || !performers.top_senior_cells || performers.top_senior_cells.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
        <p className="text-center text-sm text-slate-500">No senior cell data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-100 px-6 py-4">
        <h2 className="font-semibold text-navy">Senior Cell Performance</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-slate-50">
              <th className="px-6 py-3 text-left font-semibold text-slate-600">Division</th>
              <th className="px-6 py-3 text-left font-semibold text-slate-600">Leader</th>
              <th className="px-6 py-3 text-right font-semibold text-slate-600">Reporting</th>
              <th className="px-6 py-3 text-right font-semibold text-slate-600">Growth</th>
              <th className="px-6 py-3 text-right font-semibold text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {performers.top_senior_cells.map((sc: any) => (
              <tr key={sc.id} className="border-b border-gray-100 hover:bg-slate-50">
                <td className="px-6 py-4">
                  <span className="font-semibold text-slate-900">{sc.name}</span>
                </td>
                <td className="px-6 py-4 text-slate-600">{sc.leader_name || 'N/A'}</td>
                <td className="px-6 py-4 text-right">
                  <span className="font-semibold text-navy">{sc.reporting_rate || '0'}%</span>
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="font-semibold text-emerald-600">
                    {sc.growth_rate && sc.growth_rate > 0 ? '+' : ''}{sc.growth_rate || '0'}%
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <span className={`inline-block rounded-full px-3 py-1 text-xs font-bold uppercase ${
                    (sc.growth_rate || 0) > 10 ? 'bg-emerald-100 text-emerald-700' :
                    (sc.growth_rate || 0) > 0 ? 'bg-blue-100 text-blue-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>
                    {(sc.growth_rate || 0) > 10 ? 'Excellent' : (sc.growth_rate || 0) > 0 ? 'Healthy' : 'Average'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function GrowthMetricsSection({ stats }: { stats: any }) {
  const metrics = [
    {
      label: 'First Timers',
      value: stats.total_first_timers,
      icon: '✨',
      color: 'text-emerald-600',
    },
    {
      label: 'Foundation School Enroll.',
      value: stats.total_new_members,
      icon: '📚',
      color: 'text-blue-600',
    },
    {
      label: 'Water Baptisms',
      value: stats.total_souls_won,
      icon: '💧',
      color: 'text-sky-600',
    },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <h2 className="mb-6 font-semibold text-navy">Growth Metrics (MoM)</h2>
      <div className="space-y-4">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-700">{metric.label}</span>
              <span className={`text-lg font-bold ${metric.color}`}>+18%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-200">
              <div className="h-full rounded-full bg-emerald-500" style={{ width: '75%' }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CellsNeedingSupportAlerts({ cells }: { cells: any[] }) {
  if (cells.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-center text-sm font-semibold text-slate-500">✓ All cells are reporting well</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-100 px-6 py-4">
        <h2 className="font-semibold text-navy">⚠️ Cells Needing Support</h2>
      </div>
      <div className="space-y-3 p-6">
        {cells.slice(0, 2).map((cell) => (
          <div
            key={cell.cell_id}
            className={`rounded-lg border-l-4 p-4 ${
              cell.status === 'critical'
                ? 'border-l-red-500 border border-red-200 bg-red-50'
                : 'border-l-yellow-500 border border-yellow-200 bg-yellow-50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className={`font-semibold ${cell.status === 'critical' ? 'text-red-900' : 'text-yellow-900'}`}>
                  {cell.cell_name}
                </p>
                <p className="mt-1 text-xs text-slate-600">{cell.reason}</p>
              </div>
              <span
                className={`ml-3 whitespace-nowrap rounded-full px-2 py-1 text-xs font-bold uppercase ${
                  cell.status === 'critical'
                    ? 'bg-red-200 text-red-700'
                    : 'bg-yellow-200 text-yellow-700'
                }`}
              >
                {cell.status}
              </span>
            </div>
          </div>
        ))}
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
      <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        {successMessage && <SuccessAlert message={successMessage} onClose={() => setSuccessMessage(null)} />}
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        {/* Topbar */}
        <FellowshipTopbar
          fellowshipName={data.fellowship_name}
          period={period}
          onPeriodChange={setPeriod}
          onRefresh={loadDashboard}
        />

        {/* Key Stats Grid */}
        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <StatCard
            label="Total Cells"
            value={stats.total_cells}
            subtext="All Cells"
            tone="blue"
          />
          <StatCard
            label="Reporting"
            value={`${Math.round(stats.submission_rate_percent)}%`}
            subtext="Submission Rate"
            tone="green"
          />
          <StatCard
            label="Total Attendance"
            value={formatNumber(stats.total_attendance)}
            subtext="Weekly Average"
            tone="purple"
          />
          <StatCard
            label="Souls Won"
            value={formatNumber(stats.total_souls_won)}
            subtext="New Members"
            tone="orange"
          />
          <StatCard
            label="Collected"
            value={formatMoney(stats.total_finances)}
            subtext="Total Finances"
            tone="gold"
          />
          <StatCard
            label="Growth Rate"
            value={`${stats.growth_rate_percent > 0 ? '+' : ''}${stats.growth_rate_percent}%`}
            subtext="Month on Month"
            percentage={stats.growth_rate_percent}
            tone={stats.growth_rate_percent > 0 ? 'green' : 'orange'}
          />
        </div>

        {/* Charts Section */}
        <div className="mb-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <AttendanceTrendChart data={trends} />
          </div>
          <ConversionSourcesChart data={conversion_sources} />
        </div>

        {/* Senior Cells Performance */}
        <div className="mb-6">
          <SeniorCellPerformanceTable performers={top_performers} />
        </div>

        {/* Growth Metrics and Cells Needing Support */}
        <div className="mb-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <CellsNeedingSupportAlerts cells={cells_needing_attention} />
          </div>
          <GrowthMetricsSection stats={stats} />
        </div>

        {/* Quick Actions */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-navy px-6 py-5 shadow-sm">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-white">Quick Actions</h2>
              <p className="mt-1 text-xs text-slate-300">Manage your fellowship efficiently</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Link href={`/dashboard/fellowship/${fellowshipId}/senior-cells`}>
                <Button className="w-full bg-gold text-navy hover:bg-yellow-400 sm:w-auto">
                  View Senior Cells
                </Button>
              </Link>
              <Link href={`/dashboard/fellowship/${fellowshipId}/cells`}>
                <Button variant="secondary" className="w-full border border-white text-white hover:bg-slate-700 sm:w-auto">
                  View All Cells
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:justify-between">
          <div className="flex gap-2">
            <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50">
              🔍 Filter
            </button>
            <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50">
              📥 Export
            </button>
          </div>
          <button
            onClick={loadDashboard}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            ↻ Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
}
