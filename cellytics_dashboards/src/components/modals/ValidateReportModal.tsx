'use client';

import { useState, useEffect } from 'react';
import { managementAPI, getErrorMessage, apiClient } from '@/lib/api';

interface ValidateReportModalProps {
  fellowshipId: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

interface CellReport {
  id: string;
  cell_name: string;
  submitted_by: string;
  week: string;
  attendance: number;
  souls_won: number;
  status: string;
}

export default function ValidateReportModal({
  fellowshipId,
  onClose,
  onSuccess,
  onError,
}: ValidateReportModalProps) {
  const [reports, setReports] = useState<CellReport[]>([]);
  const [selectedReportId, setSelectedReportId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await apiClient.get(`/dashboards/fellowship/${fellowshipId}?period=week`);
        const cellReports = response.data.cells_needing_attention || [];
        setReports(cellReports);
      } catch (error) {
        onError(getErrorMessage(error));
      } finally {
        setLoadingData(false);
      }
    };
    fetchReports();
  }, [fellowshipId, onError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReportId) {
      onError('Please select a report');
      return;
    }

    setLoading(true);
    try {
      await managementAPI.validateCellReport(selectedReportId);
      onSuccess();
    } catch (error) {
      onError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
          <p className="text-center text-gray-600">Loading reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-2xl font-bold text-gray-900">Validate Cell Report</h2>
        <p className="mt-1 text-gray-600">Review and validate submitted cell reports</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Select Report</label>
            <select
              value={selectedReportId}
              onChange={(e) => setSelectedReportId(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option value="">-- Select a report --</option>
              {reports.map((report) => (
                <option key={report.id} value={report.id}>
                  {report.cell_name} - Week of {report.week}
                </option>
              ))}
            </select>
          </div>

          {selectedReportId && (
            <div className="rounded-md bg-blue-50 p-4">
              {(() => {
                const report = reports.find((r) => r.id === selectedReportId);
                return (
                  <div className="text-sm text-gray-700">
                    <p><strong>Cell:</strong> {report?.cell_name}</p>
                    <p><strong>Submitted by:</strong> {report?.submitted_by}</p>
                    <p><strong>Attendance:</strong> {report?.attendance}</p>
                    <p><strong>Souls Won:</strong> {report?.souls_won}</p>
                  </div>
                );
              })()}
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md border border-gray-300 py-2 px-4 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-md bg-green-600 py-2 px-4 text-sm font-medium text-white hover:bg-green-700 disabled:bg-gray-400"
            >
              {loading ? 'Validating...' : 'Validate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
