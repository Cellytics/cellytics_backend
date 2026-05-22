"use client";

import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorAlert } from '@/components/ErrorAlert';
import { useAuth } from '@/context/AuthContext';
import { zoneService } from '@/lib/zoneService';
import { getErrorMessage } from '@/lib/api';
import type { ZoneExecutiveData } from '@/types/zone';

export default function UsersPage() {
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
        const executiveData = await zoneService.getZoneExecutiveData(zoneId);
        setData(executiveData);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [zoneId]);

  if (isLoading) {
    return (
      <div className="flex h-screen flex-col">
        <Header pageTitle="Users" />
        <div className="flex-1 p-8">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header pageTitle="Pastors and Structure" subtitle={data?.dashboard.zone_name || zoneId} />

      <div className="flex-1 overflow-y-auto bg-slate-50 p-8">
        {error && <ErrorAlert message={error} />}

        {!data || data.fellowships.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-slate-600 shadow-sm">
            No fellowships found for this zone.
          </div>
        ) : (
          <div className="space-y-4">
            {data.fellowships.map((fellowship) => (
              <div key={fellowship.id} className="rounded-lg border border-gray-200 bg-white shadow-sm">
                <div className="grid gap-4 border-b border-gray-100 px-6 py-5 md:grid-cols-[1.2fr_1fr_1fr]">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Fellowship</p>
                    <h3 className="mt-1 font-serif text-xl text-navy">{fellowship.name}</h3>
                    <p className="text-sm text-slate-500">{fellowship.location || 'No location set'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pastor</p>
                    <p className="mt-1 font-semibold text-slate-900">{fellowship.pastor_name || 'Pastor not assigned'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Phone Number</p>
                    <p className="mt-1 font-semibold text-slate-900">{fellowship.pastor_phone || '-'}</p>
                  </div>
                </div>

                <div className="space-y-3 p-6">
                  {fellowship.senior_cells.length === 0 ? (
                    <p className="text-sm text-slate-600">No senior cells have been created under this fellowship.</p>
                  ) : (
                    fellowship.senior_cells.map((seniorCell) => (
                      <details key={seniorCell.id} className="rounded-md border border-gray-200 bg-slate-50 p-4">
                        <summary className="cursor-pointer font-semibold text-navy">
                          {seniorCell.name}
                          <span className="ml-2 text-xs font-normal text-slate-500">
                            {seniorCell.total_cells} cell(s)
                          </span>
                        </summary>
                        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                          {seniorCell.cells.length === 0 ? (
                            <p className="text-sm text-slate-600">No cells under this senior cell yet.</p>
                          ) : (
                            seniorCell.cells.map((cell) => (
                              <details key={cell.id} className="rounded-md border border-gray-200 bg-white p-3">
                                <summary className="cursor-pointer text-sm font-semibold text-slate-800">{cell.name}</summary>
                                <div className="mt-2 text-xs text-slate-600">
                                  <p>Meeting day: {cell.default_meeting_day || 'Not set'}</p>
                                  <p>Meeting time: {cell.meeting_time || 'Not set'}</p>
                                </div>
                              </details>
                            ))
                          )}
                        </div>
                      </details>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
