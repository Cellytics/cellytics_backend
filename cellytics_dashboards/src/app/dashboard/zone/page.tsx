'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { CreateFellowshipModal } from '@/components/CreateFellowshipModal';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { SuccessAlert } from '@/components/SuccessAlert';
import { useAuth } from '@/context/AuthContext';
import { getErrorMessage } from '@/lib/api';
import { zoneService } from '@/lib/zoneService';
import type { FellowshipSummary, ZoneExecutiveData } from '@/types/zone';

type Period = 'week' | 'month' | 'year' | 'all';
type TrendPoint = { week: string; attendance: number; firstTimers: number };

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

const getPeriodLabel = (period: Period) => {
  if (period === 'week') return 'This Week';
  if (period === 'month') return 'This Month';
  if (period === 'year') return 'This Year';
  return 'All Data';
};

const isInPeriod = (dateValue: string, period: Period) => {
  if (period === 'all') return true;
  const date = new Date(dateValue);
  const now = new Date();
  if (Number.isNaN(date.getTime())) return false;

  if (period === 'week') {
    const start = new Date(now);
    start.setDate(now.getDate() - now.getDay() + 1);
    start.setHours(0, 0, 0, 0);
    return date >= start;
  }

  if (period === 'month') {
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
  }

  return date.getFullYear() === now.getFullYear();
};

const statusFor = (rate: number) => {
  if (rate >= 90) return { label: 'Excellent', className: 'bg-green-100 text-green-700' };
  if (rate >= 80) return { label: 'Stable', className: 'bg-green-50 text-green-700' };
  if (rate >= 65) return { label: 'Warning', className: 'bg-yellow-100 text-yellow-700' };
  return { label: 'Critical', className: 'bg-red-100 text-red-700' };
};

function buildPeriodView(data: ZoneExecutiveData, period: Period) {
  const reports = data.reports.filter((report) => isInPeriod(report.week_start_date, period));
  const reportedCellIds = new Set(reports.map((report) => report.cell_id));

  const fellowships = data.fellowships.map((fellowship) => {
    const fellowshipCellIds = new Set(
      fellowship.senior_cells.flatMap((seniorCell) => seniorCell.cells.map((cell) => cell.id))
    );
    const fellowshipReportedCellIds = new Set(
      reports.filter((report) => fellowshipCellIds.has(report.cell_id)).map((report) => report.cell_id)
    );

    const seniorCells = fellowship.senior_cells.map((seniorCell) => {
      const cells = seniorCell.cells.map((cell) => {
        const cellReports = reports.filter((report) => report.cell_id === cell.id);
        return {
          ...cell,
          reports_submitted: cellReports.length,
          total_attendance: cellReports.reduce((sum, report) => sum + (report.total_attendance || 0), 0),
          total_first_timers: cellReports.reduce((sum, report) => sum + (report.first_timers || 0), 0),
          total_filled_holy_ghost: cellReports.reduce((sum, report) => sum + (report.filled_holy_ghost || 0), 0),
          total_souls_won: cellReports.reduce((sum, report) => sum + (report.souls_won || 0), 0),
          total_finances: cellReports.reduce((sum, report) => sum + (report.finance_total || 0), 0),
        };
      });

      const reportsSubmitted = cells.reduce((sum, cell) => sum + cell.reports_submitted, 0);
      return {
        ...seniorCell,
        cells,
        reports_submitted: reportsSubmitted,
        total_attendance: cells.reduce((sum, cell) => sum + cell.total_attendance, 0),
        total_first_timers: cells.reduce((sum, cell) => sum + cell.total_first_timers, 0),
        total_filled_holy_ghost: cells.reduce((sum, cell) => sum + cell.total_filled_holy_ghost, 0),
        total_souls_won: cells.reduce((sum, cell) => sum + cell.total_souls_won, 0),
        total_finances: cells.reduce((sum, cell) => sum + cell.total_finances, 0),
        submission_rate: seniorCell.total_cells > 0 ? Math.round((reportsSubmitted / seniorCell.total_cells) * 100) : 0,
      };
    });

    const cellsCount = fellowship.cells_count;
    return {
      ...fellowship,
      senior_cells: seniorCells,
      reports_submitted: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.reports_submitted, 0),
      cells_reported: fellowshipReportedCellIds.size,
      total_attendance: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_attendance, 0),
      total_first_timers: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_first_timers, 0),
      total_filled_holy_ghost: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_filled_holy_ghost, 0),
      souls_won: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_souls_won, 0),
      total_finances: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_finances, 0),
      submission_rate: cellsCount > 0 ? Math.round((fellowshipReportedCellIds.size / cellsCount) * 100) : 0,
    };
  });

  const totalCells = fellowships.reduce((sum, fellowship) => sum + fellowship.cells_count, 0);
  return {
    reports,
    fellowships,
    stats: {
      total_fellowships: fellowships.length,
      total_cells: totalCells,
      total_attendance: reports.reduce((sum, report) => sum + (report.total_attendance || 0), 0),
      total_first_timers: reports.reduce((sum, report) => sum + (report.first_timers || 0), 0),
      total_filled_holy_ghost: reports.reduce((sum, report) => sum + (report.filled_holy_ghost || 0), 0),
      total_souls_won: reports.reduce((sum, report) => sum + (report.souls_won || 0), 0),
      total_finances: reports.reduce((sum, report) => sum + (report.finance_total || 0), 0),
      cells_reported: reportedCellIds.size,
      submission_rate_percent: totalCells > 0 ? Math.round((reportedCellIds.size / totalCells) * 100) : 0,
    },
  };
}

function getWeekLabel(date: Date) {
  return date.toISOString().slice(0, 10);
}

function getWeeklyTrend(data: ZoneExecutiveData): TrendPoint[] {
  const byWeek = new Map<string, { attendance: number; firstTimers: number }>();

  data.dashboard.attendance_trend.forEach((point) => {
    byWeek.set(point.week, {
      attendance: point.active_members || 0,
      firstTimers: point.first_timers || 0,
    });
  });

  data.reports.forEach((report) => {
    const current = byWeek.get(report.week_start_date) || { attendance: 0, firstTimers: 0 };
    byWeek.set(report.week_start_date, {
      attendance: current.attendance + (report.total_attendance || 0),
      firstTimers: current.firstTimers + (report.first_timers || 0),
    });
  });

  const weeks = Array.from(byWeek.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-13)
    .map(([week, totals]) => ({ week, ...totals }));

  if (weeks.length >= 13) return weeks;

  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay() + 1);
  monday.setHours(0, 0, 0, 0);

  const existing = new Map(weeks.map((week) => [week.week, week]));
  return Array.from({ length: 13 }, (_, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() - (12 - index) * 7);
    const key = getWeekLabel(date);
    return existing.get(key) || { week: key, attendance: 0, firstTimers: 0 };
  });
}

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

function ZoneTopbar({
  zoneName,
  userName,
  period,
  onPeriodChange,
  onCreateFellowship,
  onGenerateReport,
}: {
  zoneName: string;
  userName: string;
  period: Period;
  onPeriodChange: (period: Period) => void;
  onCreateFellowship: () => void;
  onGenerateReport: () => void;
}) {
  return (
    <div className="mb-5 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-navy text-sm font-bold text-gold">
            Z
          </div>
          <div className="min-w-0">
            <p className="truncate font-serif text-base text-navy">{zoneName} Executive Dashboard</p>
            <p className="text-xs text-slate-500">Welcome back, {userName}. Your zone command center is live.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="hidden rounded-full border border-green-200 bg-green-50 px-3 py-2 text-xs font-semibold text-green-700 lg:block">
            Verified weekly finance stream
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
          <Button variant="secondary" onClick={onCreateFellowship}>Add Fellowship</Button>
          <Button onClick={onGenerateReport}>Generate Report</Button>
        </div>
      </div>
    </div>
  );
}

function TrendChart({ data }: { data: TrendPoint[] }) {
  const maxAttendance = Math.max(...data.map((week) => week.attendance), 1);
  const maxFirstTimers = Math.max(...data.map((week) => week.firstTimers), 1);

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-base text-navy">Zone Attendance Trend</h2>
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-gold" />Active Members</span>
          <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-navy" />First Timers</span>
        </div>
      </div>

      <div className="mt-8 flex h-64 items-end gap-2 sm:gap-3">
        {data.map((week, index) => {
            const attendanceHeight = Math.max((week.attendance / maxAttendance) * 100, 10);
            const firstTimerHeight = Math.max((week.firstTimers / maxFirstTimers) * 65, week.firstTimers > 0 ? 8 : 0);
            const isCurrent = index === data.length - 1;

            return (
              <div key={week.week} className="flex flex-1 flex-col items-center gap-3">
                <div className="relative flex h-full w-full items-end justify-center rounded-t bg-slate-50">
                  <div
                    className={`w-full max-w-12 rounded-t ${isCurrent ? 'bg-gold' : 'bg-slate-200'}`}
                    style={{ height: `${attendanceHeight}%` }}
                    title={`${formatNumber(week.attendance)} attendance`}
                  />
                  {week.firstTimers > 0 && (
                    <div
                      className="absolute bottom-0 w-2 max-w-2 rounded-t bg-navy"
                      style={{ height: `${firstTimerHeight}%` }}
                      title={`${formatNumber(week.firstTimers)} first timers`}
                    />
                  )}
                </div>
                <p className="text-[10px] text-slate-400">
                  {index === 0 ? 'Week 1' : isCurrent ? `Week ${index + 1} (Current)` : index % 4 === 3 ? `Week ${index + 1}` : ''}
                </p>
              </div>
            );
          })}
      </div>
    </div>
  );
}

function FellowshipTable({ fellowships }: { fellowships: FellowshipSummary[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-5">
        <h2 className="font-serif text-base text-navy">Fellowship Leaders Performance</h2>
        <Link href="/dashboard/zone/fellowships" className="rounded-full border border-gold px-4 py-2 text-xs font-semibold text-navy hover:bg-gold/10">
          View All Fellowships
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-5 py-3">Fellowship</th>
              <th className="px-5 py-3">Pastor</th>
              <th className="px-5 py-3">Attendance</th>
              <th className="px-5 py-3">Reports</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {fellowships.map((fellowship) => {
              const status = statusFor(fellowship.submission_rate);
              return (
                <tr key={fellowship.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-5 py-4 font-semibold text-slate-900">{fellowship.name}</td>
                  <td className="px-5 py-4 text-sm text-slate-700">
                    <p>{fellowship.pastor_name || 'Unassigned'}</p>
                    {fellowship.pastor_phone && <p className="text-xs text-slate-400">{fellowship.pastor_phone}</p>}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-700">{formatNumber(fellowship.total_attendance)}</td>
                  <td className="px-5 py-4 text-sm text-slate-700">{fellowship.cells_reported}/{fellowship.cells_count}</td>
                  <td className="px-5 py-4">
                    <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase ${status.className}`}>
                      {status.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function ZoneDashboard() {
  const { user } = useAuth();
  const zoneId = user?.zone_id;
  const [data, setData] = useState<ZoneExecutiveData | null>(null);
  const [period, setPeriod] = useState<Period>('week');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadDashboard = async () => {
    if (!zoneId) {
      setError('Zone ID not found. Please log in again.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      setData(await zoneService.getZoneExecutiveData(zoneId));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoneId]);

  const periodView = useMemo(() => (data ? buildPeriodView(data, period) : null), [data, period]);
  const trend = useMemo(() => (data ? getWeeklyTrend(data) : []), [data]);
  const topFellowship = useMemo(
    () => periodView?.fellowships.slice().sort((a, b) => b.total_attendance - a.total_attendance)[0],
    [periodView]
  );
  const needingSupport = useMemo(
    () => periodView?.fellowships.filter((fellowship) => fellowship.submission_rate < 75) || [],
    [periodView]
  );

  const handleCreateFellowship = async (name: string, location?: string) => {
    if (!zoneId) return;
    setIsCreating(true);
    setError(null);

    try {
      await zoneService.createFellowship({ name, location, zone_id: zoneId });
      setSuccessMessage(`Fellowship "${name}" created successfully.`);
      await loadDashboard();
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleGenerateZoneReport = () => {
    if (!data || !periodView) return;
    const lines = [
      ['Period', getPeriodLabel(period)],
      ['Zone', data.dashboard.zone_name],
      ['Generated At', new Date().toLocaleString()],
      [],
      ['Fellowship', 'Cells', 'Reports', 'Attendance', 'First Timers', 'Filled With Holy Spirit', 'Souls Won', 'Finances'],
      ...periodView.fellowships.map((fellowship) => [
        fellowship.name,
        fellowship.cells_count,
        fellowship.cells_reported,
        fellowship.total_attendance,
        fellowship.total_first_timers,
        fellowship.total_filled_holy_ghost,
        fellowship.souls_won,
        fellowship.total_finances,
      ]),
    ];
    const csv = lines.map((line) => line.map((value) => `"${String(value ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `zone-report-${period}-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setSuccessMessage(`${getPeriodLabel(period)} zone report generated.`);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data || !periodView) {
    return (
      <div className="p-5">
        <ErrorAlert message={error || 'Unable to load zone dashboard'} />
      </div>
    );
  }

  const { dashboard } = data;
  const { fellowships, stats } = periodView;
  const topSouls = fellowships.slice().sort((a, b) => b.souls_won - a.souls_won).slice(0, 3);
  const topFinance = fellowships.slice().sort((a, b) => b.total_finances - a.total_finances).slice(0, 3);

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6 lg:px-7">
        {successMessage && <SuccessAlert message={successMessage} onClose={() => setSuccessMessage(null)} />}
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        <ZoneTopbar
          zoneName={dashboard.zone_name}
          userName={user?.name || 'Zonal Administrator'}
          period={period}
          onPeriodChange={setPeriod}
          onCreateFellowship={() => setShowCreateModal(true)}
          onGenerateReport={handleGenerateZoneReport}
        />

        {topFellowship && (
          <div className="mb-5 rounded-xl bg-navy px-6 py-5 text-white shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-full border-4 border-gold bg-white text-lg font-bold text-navy">
                  {(topFellowship.pastor_name || topFellowship.name).charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-gold">Top Fellowship of the Period</p>
                  <h2 className="mt-1 font-semibold">{topFellowship.name}</h2>
                  <p className="text-sm text-slate-200">
                    {topFellowship.pastor_name || 'Pastor unassigned'} | {topFellowship.submission_rate}% submission | {formatNumber(topFellowship.total_attendance)} attendance
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button onClick={handleGenerateZoneReport}>Generate Report</Button>
                <Link href="/dashboard/zone/analytics" className="rounded-lg bg-white/10 px-4 py-2 text-sm font-semibold text-white hover:bg-white/20">
                  View Analytics
                </Link>
              </div>
            </div>
          </div>
        )}

        <div className="mb-5 grid gap-3 md:grid-cols-4 xl:grid-cols-7">
          <StatTile label="Fellowships" value={stats.total_fellowships} />
          <StatTile label="Cells" value={stats.total_cells} />
          <StatTile label="Attendance" value={formatNumber(stats.total_attendance)} />
          <StatTile label="First Timers" value={formatNumber(stats.total_first_timers)} />
          <StatTile label="Souls Won" value={formatNumber(stats.total_souls_won)} />
          <StatTile label="Collections" value={formatMoney(stats.total_finances)} />
          <StatTile label="Submission" value={`${Math.round(stats.submission_rate_percent)}%`} tone="orange" />
        </div>

        <div className="mb-6">
          <TrendChart data={trend} />
        </div>

        <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4 xl:sticky xl:top-5 xl:max-h-[calc(100vh-2.5rem)] xl:overflow-y-auto xl:pr-1">
            <FellowshipTable fellowships={fellowships} />

            {needingSupport.length > 0 && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
                <h2 className="font-semibold">Fellowships Needing Support</h2>
                <p className="mt-2 max-w-2xl text-sm">
                  {needingSupport.length} fellowship(s) currently have submission rates below 75%. Recommend immediate leadership intervention and pastoral care visits.
                </p>
                <Button className="mt-4" variant="danger">Schedule Intervention</Button>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="font-serif text-base text-navy">Conversion by Fellowship</h2>
              <div className="mx-auto my-6 flex h-36 w-36 items-center justify-center rounded-full border-[18px] border-slate-100 border-b-gold border-l-gold text-center">
                <div>
                  <p className="text-2xl font-bold text-navy">{formatNumber(stats.total_souls_won)}</p>
                  <p className="text-xs text-slate-500">Total Souls</p>
                </div>
              </div>
              <div className="space-y-3">
                {topSouls.map((fellowship) => (
                  <div key={fellowship.id} className="flex justify-between text-sm">
                    <span className="text-slate-600">{fellowship.name}</span>
                    <strong className="text-navy">{fellowship.souls_won}</strong>
                  </div>
                ))}
                <div className="flex justify-between border-t border-gray-100 pt-3 text-sm">
                  <span className="text-slate-600">Filled with H/S</span>
                  <strong className="text-navy">{formatNumber(stats.total_filled_holy_ghost)}</strong>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="font-serif text-base text-navy">Offerings and Tithes</h2>
              <div className="mt-5 space-y-4">
                {topFinance.map((fellowship) => (
                  <div key={fellowship.id}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span>{fellowship.name}</span>
                      <strong>{formatMoney(fellowship.total_finances)}</strong>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full bg-gold"
                        style={{ width: `${Math.min((fellowship.total_finances / Math.max(stats.total_finances, 1)) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg bg-navy p-6 text-white shadow-sm">
              <p className="font-serif text-base">MoM Growth Comparison</p>
              <p className="mt-4 text-sm text-slate-200">
                Your zone is tracking {formatNumber(stats.total_first_timers)} first timers and {formatNumber(stats.total_filled_holy_ghost)} filled with H/S for this period.
              </p>
              <p className="mt-5 text-3xl font-bold text-gold">+{Math.round(stats.submission_rate_percent)}%</p>
              <p className="text-xs text-slate-300">current submission coverage</p>
            </div>
          </div>
        </div>

        <div className="mt-6 border-t border-gray-200 pt-5">
          <h2 className="mb-4 font-serif text-base text-navy">Administrative Power Actions</h2>
          <div className="grid gap-3 md:grid-cols-4">
            <Button onClick={handleGenerateZoneReport}>Generate Zone Report</Button>
            <Button variant="secondary">Broadcast Message</Button>
            <Button variant="secondary">Import Data</Button>
            <Button variant="secondary" onClick={() => setShowCreateModal(true)}>Create Fellowship</Button>
          </div>
        </div>

        <div className="mt-5 rounded-lg border border-gray-200 bg-white px-5 py-4 text-xs text-slate-500">
          System status: live sync. Last loaded {new Date().toLocaleTimeString()}.
        </div>
      </div>

      <CreateFellowshipModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateFellowship}
        isLoading={isCreating}
        error={error}
      />
    </div>
  );
}
