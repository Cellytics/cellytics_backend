'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/Button';
import { CreateFellowshipModal } from '@/components/CreateFellowshipModal';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { SuccessAlert } from '@/components/SuccessAlert';
import { useAuth } from '@/context/AuthContext';
import { getErrorMessage } from '@/lib/api';
import { zoneService } from '@/lib/zoneService';
import type { FellowshipSummary, ZoneExecutiveData } from '@/types/zone';

const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

function FellowshipEditor({
  fellowship,
  onCancel,
  onSave,
  isSaving,
}: {
  fellowship: FellowshipSummary;
  onCancel: () => void;
  onSave: (name: string, location?: string) => Promise<void>;
  isSaving: boolean;
}) {
  const [name, setName] = useState(fellowship.name);
  const [location, setLocation] = useState(fellowship.location || '');

  return (
    <div className="rounded-lg border border-gold bg-gold/10 p-4">
      <h3 className="font-semibold text-navy">Edit Fellowship</h3>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="text-sm text-slate-700">
          Fellowship name
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="mt-1 w-full"
          />
        </label>
        <label className="text-sm text-slate-700">
          Location
          <input
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            className="mt-1 w-full"
          />
        </label>
      </div>
      <div className="mt-4 flex gap-3">
        <Button onClick={() => onSave(name, location || undefined)} loading={isSaving}>
          Save Changes
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={isSaving}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function FellowshipDetails({ fellowship }: { fellowship: FellowshipSummary }) {
  return (
    <div className="mt-5 rounded-lg border border-gray-200 bg-slate-50 p-5">
      <div className="grid gap-4 md:grid-cols-5">
        <div>
          <p className="text-xs text-slate-500">Senior Cells</p>
          <p className="text-xl font-bold text-navy">{fellowship.senior_cells_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Cells</p>
          <p className="text-xl font-bold text-navy">{fellowship.cells_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Reports</p>
          <p className="text-xl font-bold text-navy">{fellowship.reports_submitted}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Attendance</p>
          <p className="text-xl font-bold text-navy">{fellowship.total_attendance.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Finance</p>
          <p className="text-xl font-bold text-navy">{formatMoney(fellowship.total_finances)}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {fellowship.senior_cells.map((seniorCell) => (
          <div key={seniorCell.id} className="rounded-md border border-gray-200 bg-white p-4">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-navy">{seniorCell.name}</h4>
                <p className="text-xs text-slate-500">{seniorCell.leader_name || 'Leader not assigned'}</p>
              </div>
              <span className="rounded-full bg-navy px-2 py-1 text-xs font-semibold text-white">
                {seniorCell.submission_rate}%
              </span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-slate-700">
              <p>Cells: {seniorCell.total_cells}</p>
              <p>Reports: {seniorCell.reports_submitted}</p>
              <p>Attendance: {seniorCell.total_attendance.toLocaleString()}</p>
              <p>Souls: {seniorCell.total_souls_won}</p>
            </div>
            <div className="mt-3 border-t border-gray-100 pt-3">
              {seniorCell.cells.map((cell) => (
                <div key={cell.id} className="flex justify-between py-1 text-xs text-slate-600">
                  <span>{cell.name}</span>
                  <span>{cell.reports_submitted} report(s)</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function FellowshipsPage() {
  const { user } = useAuth();
  const zoneId = user?.zone_id;
  const [data, setData] = useState<ZoneExecutiveData | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = async () => {
    if (!zoneId) {
      setError('Zone ID missing');
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
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoneId]);

  const createFellowship = async (name: string, location?: string) => {
    if (!zoneId) return;
    setIsSaving(true);
    try {
      await zoneService.createFellowship({ name, location, zone_id: zoneId });
      setSuccess(`Fellowship "${name}" created successfully.`);
      await load();
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const updateFellowship = async (fellowship: FellowshipSummary, name: string, location?: string) => {
    setIsSaving(true);
    setError(null);

    try {
      await zoneService.updateFellowship(fellowship.id, { name, location });
      setSuccess(`Fellowship "${name}" updated.`);
      setEditingId(null);
      await load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  const deleteFellowship = async (fellowship: FellowshipSummary) => {
    const confirmed = window.confirm(`Delete ${fellowship.name}? This will only work if the backend allows deletion.`);
    if (!confirmed) return;

    setIsSaving(true);
    setError(null);

    try {
      await zoneService.deleteFellowship(fellowship.id);
      setSuccess(`Fellowship "${fellowship.name}" deleted.`);
      await load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto max-w-7xl px-8 py-8">
        {success && <SuccessAlert message={success} onClose={() => setSuccess(null)} />}
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="font-serif text-sm text-navy">{data?.dashboard.zone_name || 'Zone'} Administration</p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-900">Fellowship Management</h1>
            <p className="mt-1 text-sm text-slate-600">
              Create, update, monitor, and inspect every fellowship under the zonal secretary scope.
            </p>
          </div>
          <Button onClick={() => setShowCreate(true)}>Create Fellowship</Button>
        </div>

        <div className="space-y-5">
          {(data?.fellowships || []).map((fellowship) => (
            <div key={fellowship.id} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              {editingId === fellowship.id ? (
                <FellowshipEditor
                  fellowship={fellowship}
                  isSaving={isSaving}
                  onCancel={() => setEditingId(null)}
                  onSave={(name, location) => updateFellowship(fellowship, name, location)}
                />
              ) : (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-semibold text-navy">{fellowship.name}</h2>
                      <p className="text-sm text-slate-500">{fellowship.location || 'No location set'}</p>
                      <p className="mt-2 text-sm text-slate-700">
                        Pastor: {fellowship.pastor_name || 'Not assigned'}
                        {fellowship.pastor_phone ? ` (${fellowship.pastor_phone})` : ''}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={() => setExpandedId(expandedId === fellowship.id ? null : fellowship.id)}>
                        {expandedId === fellowship.id ? 'Hide Details' : 'View Details'}
                      </Button>
                      <Button variant="secondary" onClick={() => setEditingId(fellowship.id)}>
                        Edit
                      </Button>
                      <Button variant="danger" onClick={() => deleteFellowship(fellowship)} disabled={isSaving}>
                        Delete
                      </Button>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-4 md:grid-cols-6">
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Senior Cells</p>
                      <p className="text-lg font-bold text-navy">{fellowship.senior_cells_count}</p>
                    </div>
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Cells</p>
                      <p className="text-lg font-bold text-navy">{fellowship.cells_count}</p>
                    </div>
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Reports</p>
                      <p className="text-lg font-bold text-navy">{fellowship.reports_submitted}</p>
                    </div>
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Submission</p>
                      <p className="text-lg font-bold text-navy">{fellowship.submission_rate}%</p>
                    </div>
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Souls</p>
                      <p className="text-lg font-bold text-navy">{fellowship.souls_won}</p>
                    </div>
                    <div className="rounded-md bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Finance</p>
                      <p className="text-lg font-bold text-navy">{formatMoney(fellowship.total_finances)}</p>
                    </div>
                  </div>

                  {expandedId === fellowship.id && <FellowshipDetails fellowship={fellowship} />}
                </>
              )}
            </div>
          ))}
        </div>

        {(data?.fellowships || []).length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
            <p className="text-slate-600">No fellowships found for this zone.</p>
            <Button className="mt-4" onClick={() => setShowCreate(true)}>Create Fellowship</Button>
          </div>
        )}
      </div>

      <CreateFellowshipModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={createFellowship}
        isLoading={isSaving}
        error={error}
      />
    </div>
  );
}
