'use client';

import { useState, useEffect } from 'react';
import { managementAPI, getErrorMessage, apiClient } from '@/lib/api';

interface AssignCellModalProps {
  fellowshipId: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

interface Cell {
  id: string;
  name: string;
  leader_name: string;
}

interface SeniorCell {
  id: string;
  name: string;
}

export default function AssignCellModal({
  fellowshipId,
  onClose,
  onSuccess,
  onError,
}: AssignCellModalProps) {
  const [cells, setCells] = useState<Cell[]>([]);
  const [seniorCells, setSeniorCells] = useState<SeniorCell[]>([]);
  const [selectedCellId, setSelectedCellId] = useState('');
  const [selectedSeniorCellId, setSelectedSeniorCellId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [cellsRes, seniorCellsRes] = await Promise.all([
          apiClient.get(`/dashboards/fellowship/${fellowshipId}/cells`),
          apiClient.get(`/dashboards/fellowship/${fellowshipId}/senior-cells`),
        ]);
        setCells(cellsRes.data.cells || []);
        setSeniorCells(seniorCellsRes.data.senior_cells || []);
      } catch (error) {
        onError(getErrorMessage(error));
      } finally {
        setLoadingData(false);
      }
    };
    fetchData();
  }, [fellowshipId, onError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCellId || !selectedSeniorCellId) {
      onError('Please select both a cell and a senior cell');
      return;
    }

    setLoading(true);
    try {
      await managementAPI.assignCellToSeniorCell(selectedCellId, selectedSeniorCellId);
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
          <p className="text-center text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-2xl font-bold text-gray-900">Assign Cell to Senior Cell</h2>
        <p className="mt-1 text-gray-600">Link a cell to an existing senior cell</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Select Cell</label>
            <select
              value={selectedCellId}
              onChange={(e) => setSelectedCellId(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option value="">-- Select a cell --</option>
              {cells.map((cell) => (
                <option key={cell.id} value={cell.id}>
                  {cell.name} ({cell.leader_name})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Select Senior Cell</label>
            <select
              value={selectedSeniorCellId}
              onChange={(e) => setSelectedSeniorCellId(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option value="">-- Select a senior cell --</option>
              {seniorCells.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name}
                </option>
              ))}
            </select>
          </div>

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
              className="flex-1 rounded-md bg-blue-600 py-2 px-4 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Assigning...' : 'Assign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
