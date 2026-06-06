'use client';

import { useState, useEffect } from 'react';
import { managementAPI, getErrorMessage, apiClient } from '@/lib/api';

interface ConfirmFinancesModalProps {
  fellowshipId: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

interface FinanceReport {
  id: string;
  cell_name: string;
  week: string;
  total_finances: number;
  submitted_by: string;
  status: string;
}

export default function ConfirmFinancesModal({
  fellowshipId,
  onClose,
  onSuccess,
  onError,
}: ConfirmFinancesModalProps) {
  const [reports, setReports] = useState<FinanceReport[]>([]);
  const [selectedReportId, setSelectedReportId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await apiClient.get(`/dashboards/fellowship/${fellowshipId}?period=week`);
        const financeReports = response.data.cells_needing_attention || [];
        setReports(financeReports);
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
      await managementAPI.confirmReportFinances(selectedReportId);
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
        <h2 className="text-2xl font-bold text-gray-900">Confirm Report Finances</h2>
        <p className="mt-1 text-gray-600">Review and confirm financial collections</p>

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
                  {report.cell_name} - {report.week}
                </option>
              ))}
            </select>
          </div>

          {selectedReportId && (
            <div className="rounded-md bg-yellow-50 p-4">
              {(() => {
                const report = reports.find((r) => r.id === selectedReportId);
                return (
                  <div className="text-sm text-gray-700">
                    <p><strong>Cell:</strong> {report?.cell_name}</p>
                    <p><strong>Submitted by:</strong> {report?.submitted_by}</p>
                    <p><strong>Total Finances:</strong> XAF {(report?.total_finances || 0).toLocaleString()}</p>
                    <p><strong>Week:</strong> {report?.week}</p>
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
              className="flex-1 rounded-md bg-yellow-600 py-2 px-4 text-sm font-medium text-white hover:bg-yellow-700 disabled:bg-gray-400"
            >
              {loading ? 'Confirming...' : 'Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
