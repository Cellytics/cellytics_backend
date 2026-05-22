"use client";

import { useEffect, useMemo, useState } from 'react';
import { Header } from '@/components/Header';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { useAuth } from '@/context/AuthContext';
import { getErrorMessage } from '@/lib/api';
import { zoneService } from '@/lib/zoneService';
import type { ZoneExecutiveData } from '@/types/zone';

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

export default function ZoneAnalyticsPage() {
  const { user } = useAuth();
  const zoneId = user?.zone_id;
  const [data, setData] = useState<ZoneExecutiveData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!zoneId) {
        setError('Zone ID missing');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        setData(await zoneService.getZoneExecutiveData(zoneId));
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [zoneId]);

  const weeklyTrend = useMemo(() => {
    if (!data) return [];
    const byWeek = new Map<string, { attendance: number; firstTimers: number; finances: number }>();

    data.reports.forEach((report) => {
      const current = byWeek.get(report.week_start_date) || { attendance: 0, firstTimers: 0, finances: 0 };
      byWeek.set(report.week_start_date, {
        attendance: current.attendance + (report.total_attendance || 0),
        firstTimers: current.firstTimers + (report.first_timers || 0),
        finances: current.finances + (report.finance_total || 0),
      });
    });

    return Array.from(byWeek.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-8)
      .map(([week, totals]) => ({ week, ...totals }));
  }, [data]);

  const maxAttendance = Math.max(...weeklyTrend.map((week) => week.attendance), 1);

  if (isLoading) {
    return (
      <div className="flex h-screen flex-col">
        <Header pageTitle="Analytics" />
        <div className="flex-1 p-8">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header pageTitle="Analytics" subtitle={data?.dashboard.zone_name || zoneId} />
      <div className="flex-1 overflow-y-auto bg-slate-50 p-8">
        {error && <ErrorAlert message={error} />}

        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-xs text-slate-500">Total Attendance</p>
            <p className="mt-2 text-2xl font-bold text-navy">
              {formatNumber(data?.reports.reduce((sum, report) => sum + (report.total_attendance || 0), 0) || 0)}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-xs text-slate-500">First Timers</p>
            <p className="mt-2 text-2xl font-bold text-navy">
              {formatNumber(data?.reports.reduce((sum, report) => sum + (report.first_timers || 0), 0) || 0)}
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-xs text-slate-500">Total Finances</p>
            <p className="mt-2 text-2xl font-bold text-navy">
              {formatMoney(data?.reports.reduce((sum, report) => sum + (report.finance_total || 0), 0) || 0)}
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-lg text-navy">Weekly Attendance Trend</h2>
          <div className="mt-8 flex h-72 items-end gap-3">
            {weeklyTrend.length === 0 ? (
              <p className="text-sm text-slate-600">No report trend data yet.</p>
            ) : (
              weeklyTrend.map((week) => (
                <div key={week.week} className="flex flex-1 flex-col items-center gap-3">
                  <div className="flex h-full w-full items-end rounded-t bg-slate-50">
                    <div
                      className="w-full rounded-t bg-gold"
                      style={{ height: `${Math.max((week.attendance / maxAttendance) * 100, 8)}%` }}
                      title={`${week.attendance} attendance`}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">{new Date(week.week).toLocaleDateString()}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
