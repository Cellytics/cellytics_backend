"use client";

import { Fragment, useEffect, useMemo, useState } from 'react';
import { Header } from '@/components/Header';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { SuccessAlert } from '@/components/SuccessAlert';
import { Button } from '@/components/Button';
import { useAuth } from '@/context/AuthContext';
import { zoneService } from '@/lib/zoneService';
import { getErrorMessage } from '@/lib/api';
import type { FellowshipSummary, ZoneExecutiveData } from '@/types/zone';

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

type WeekAggregate = {
  week: string;
  fellowships: FellowshipSummary[];
  totals: {
    reports: number;
    attendance: number;
    firstTimers: number;
    filledHolyGhost: number;
    soulsWon: number;
    finances: number;
  };
};

function aggregateWeek(data: ZoneExecutiveData, week: string): WeekAggregate {
  const reports = data.reports.filter((report) => report.week_start_date === week);

  const fellowships = data.fellowships.map((fellowship) => {
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

      return {
        ...seniorCell,
        cells,
        reports_submitted: cells.reduce((sum, cell) => sum + cell.reports_submitted, 0),
        total_attendance: cells.reduce((sum, cell) => sum + cell.total_attendance, 0),
        total_first_timers: cells.reduce((sum, cell) => sum + cell.total_first_timers, 0),
        total_filled_holy_ghost: cells.reduce((sum, cell) => sum + cell.total_filled_holy_ghost, 0),
        total_souls_won: cells.reduce((sum, cell) => sum + cell.total_souls_won, 0),
        total_finances: cells.reduce((sum, cell) => sum + cell.total_finances, 0),
      };
    });

    return {
      ...fellowship,
      senior_cells: seniorCells,
      reports_submitted: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.reports_submitted, 0),
      total_attendance: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_attendance, 0),
      total_first_timers: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_first_timers, 0),
      total_filled_holy_ghost: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_filled_holy_ghost, 0),
      souls_won: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_souls_won, 0),
      total_finances: seniorCells.reduce((sum, seniorCell) => sum + seniorCell.total_finances, 0),
    };
  });

  return {
    week,
    fellowships,
    totals: {
      reports: reports.length,
      attendance: reports.reduce((sum, report) => sum + (report.total_attendance || 0), 0),
      firstTimers: reports.reduce((sum, report) => sum + (report.first_timers || 0), 0),
      filledHolyGhost: reports.reduce((sum, report) => sum + (report.filled_holy_ghost || 0), 0),
      soulsWon: reports.reduce((sum, report) => sum + (report.souls_won || 0), 0),
      finances: reports.reduce((sum, report) => sum + (report.finance_total || 0), 0),
    },
  };
}

export default function ReportsPage() {
  const { user } = useAuth();
  const zoneId = user?.zone_id;
  const [data, setData] = useState<ZoneExecutiveData | null>(null);
  const [selectedWeek, setSelectedWeek] = useState('');
  const [expandedFellowshipId, setExpandedFellowshipId] = useState<string | null>(null);
  const [validatedWeeks, setValidatedWeeks] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!zoneId) {
        setError('Zone ID missing');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const executiveData = await zoneService.getZoneExecutiveData(zoneId);
        const weeks = Array.from(new Set(executiveData.reports.map((report) => report.week_start_date))).sort().reverse();
        setData(executiveData);
        setSelectedWeek(weeks[0] || executiveData.dashboard.week_start);
        setValidatedWeeks(JSON.parse(localStorage.getItem(`zone-validations-${zoneId}`) || '[]'));
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [zoneId]);

  const weeks = useMemo(() => {
    if (!data) return [];
    return Array.from(new Set(data.reports.map((report) => report.week_start_date))).sort().reverse();
  }, [data]);

  const aggregate = useMemo(() => {
    if (!data || !selectedWeek) return null;
    return aggregateWeek(data, selectedWeek);
  }, [data, selectedWeek]);

  const validateWeek = () => {
    if (!zoneId || !selectedWeek || validatedWeeks.includes(selectedWeek)) return;
    const next = [...validatedWeeks, selectedWeek];
    setValidatedWeeks(next);
    localStorage.setItem(`zone-validations-${zoneId}`, JSON.stringify(next));
    setSuccess(`Week of ${new Date(selectedWeek).toLocaleDateString()} validated for zone review.`);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen flex-col">
        <Header pageTitle="Reports" />
        <div className="flex-1 p-8">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header pageTitle="Aggregate Reports" subtitle={data?.dashboard.zone_name || zoneId} />
      <div className="flex-1 overflow-y-auto bg-slate-50 p-8">
        {error && <ErrorAlert message={error} />}
        {success && <SuccessAlert message={success} onClose={() => setSuccess(null)} />}

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Week in Question</p>
            <select
              value={selectedWeek}
              onChange={(event) => setSelectedWeek(event.target.value)}
              className="mt-2 rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              {weeks.map((week) => (
                <option key={week} value={week}>
                  Week of {new Date(week).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={validateWeek} disabled={!selectedWeek || validatedWeeks.includes(selectedWeek)}>
            {validatedWeeks.includes(selectedWeek) ? 'Validated' : 'Validate Week'}
          </Button>
        </div>

        {aggregate ? (
          <>
            <div className="mb-6 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">Reports</p>
                <p className="mt-2 text-2xl font-bold text-navy">{aggregate.totals.reports}</p>
              </div>
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">Attendance</p>
                <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(aggregate.totals.attendance)}</p>
              </div>
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">First Timers</p>
                <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(aggregate.totals.firstTimers)}</p>
              </div>
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">Filled With H/S</p>
                <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(aggregate.totals.filledHolyGhost)}</p>
              </div>
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">Souls Won</p>
                <p className="mt-2 text-2xl font-bold text-navy">{formatNumber(aggregate.totals.soulsWon)}</p>
              </div>
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <p className="text-xs text-slate-500">Finances</p>
                <p className="mt-2 text-2xl font-bold text-navy">{formatMoney(aggregate.totals.finances)}</p>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
              <div className="border-b border-gray-100 px-6 py-5">
                <h3 className="font-serif text-lg text-navy">Fellowship Weekly Aggregates</h3>
                <p className="text-sm text-slate-500">Open a fellowship to inspect senior cells and the cells beneath them.</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Fellowship</th>
                      <th className="px-4 py-3">Reports</th>
                      <th className="px-4 py-3">Attendance</th>
                      <th className="px-4 py-3">First Timers</th>
                      <th className="px-4 py-3">Filled With H/S</th>
                      <th className="px-4 py-3">Finances</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aggregate.fellowships.map((fellowship) => (
                      <Fragment key={fellowship.id}>
                        <tr className="border-b border-gray-100">
                          <td className="px-4 py-4">
                            <button
                              className="font-semibold text-navy hover:text-gold"
                              onClick={() => setExpandedFellowshipId(expandedFellowshipId === fellowship.id ? null : fellowship.id)}
                            >
                              {expandedFellowshipId === fellowship.id ? '- ' : '+ '}
                              {fellowship.name}
                            </button>
                          </td>
                          <td className="px-4 py-4">{fellowship.reports_submitted}</td>
                          <td className="px-4 py-4">{formatNumber(fellowship.total_attendance)}</td>
                          <td className="px-4 py-4">{formatNumber(fellowship.total_first_timers)}</td>
                          <td className="px-4 py-4">{formatNumber(fellowship.total_filled_holy_ghost)}</td>
                          <td className="px-4 py-4">{formatMoney(fellowship.total_finances)}</td>
                        </tr>
                        {expandedFellowshipId === fellowship.id && (
                          <tr className="border-b border-gray-100 bg-slate-50">
                            <td colSpan={6} className="px-4 py-4">
                              <div className="grid gap-4 lg:grid-cols-2">
                                {fellowship.senior_cells.map((seniorCell) => (
                                  <details key={seniorCell.id} className="rounded-md border border-gray-200 bg-white p-4">
                                    <summary className="cursor-pointer font-semibold text-navy">{seniorCell.name}</summary>
                                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-700">
                                      <p>Reports: {seniorCell.reports_submitted}</p>
                                      <p>Attendance: {formatNumber(seniorCell.total_attendance)}</p>
                                      <p>First Timers: {formatNumber(seniorCell.total_first_timers)}</p>
                                      <p>Filled H/S: {formatNumber(seniorCell.total_filled_holy_ghost)}</p>
                                      <p className="col-span-2">Finances: {formatMoney(seniorCell.total_finances)}</p>
                                    </div>
                                    <div className="mt-4 space-y-2 border-t border-gray-100 pt-3">
                                      {seniorCell.cells.map((cell) => (
                                        <div key={cell.id} className="flex items-center justify-between text-xs text-slate-600">
                                          <span className="font-medium text-navy">{cell.name}</span>
                                          <span>{cell.reports_submitted} report(s), {formatNumber(cell.total_attendance)} attendance</span>
                                        </div>
                                      ))}
                                    </div>
                                  </details>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-slate-600 shadow-sm">
            No reports found for this zone yet.
          </div>
        )}
      </div>
    </div>
  );
}
