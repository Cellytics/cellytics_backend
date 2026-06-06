'use client';

import { useState, useEffect } from 'react';
import { managementAPI, getErrorMessage, apiClient } from '@/lib/api';

interface PokeCellLeaderModalProps {
  fellowshipId: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

interface CellLeader {
  id: string;
  name: string;
  phone: string;
  cell_name: string;
}

export default function PokeCellLeaderModal({
  fellowshipId,
  onClose,
  onSuccess,
  onError,
}: PokeCellLeaderModalProps) {
  const [leaders, setLeaders] = useState<CellLeader[]>([]);
  const [selectedLeaderId, setSelectedLeaderId] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const fetchLeaders = async () => {
      try {
        // Fetch cells from the fellowship to get cell leaders
        const response = await apiClient.get(`/dashboards/fellowship/${fellowshipId}`);
        const cellsData = response.data.cells_needing_attention || [];
        const leadersList = cellsData.map((cell: any) => ({
          id: cell.submitted_by_id,
          name: cell.leader_name,
          phone: cell.leader_phone,
          cell_name: cell.cell_name,
        }));
        setLeaders(leadersList);
      } catch (error) {
        onError(getErrorMessage(error));
      } finally {
        setLoadingData(false);
      }
    };
    fetchLeaders();
  }, [fellowshipId, onError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeaderId) {
      onError('Please select a cell leader');
      return;
    }

    setLoading(true);
    try {
      await managementAPI.pokeCellLeader(selectedLeaderId, message || undefined);
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
          <p className="text-center text-gray-600">Loading leaders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-2xl font-bold text-gray-900">Send Reminder</h2>
        <p className="mt-1 text-gray-600">Poke a cell leader for unsubmitted reports</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Select Cell Leader</label>
            <select
              value={selectedLeaderId}
              onChange={(e) => setSelectedLeaderId(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option value="">-- Select a leader --</option>
              {leaders.map((leader) => (
                <option key={leader.id} value={leader.id}>
                  {leader.name} - {leader.cell_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Custom Message (Optional)</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Leave empty for default message"
              rows={3}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="rounded-md bg-blue-50 p-3 text-xs text-gray-700">
            <strong>Default Message:</strong> Please submit your cell report for this week. We're waiting for your update!
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
              className="flex-1 rounded-md bg-red-600 py-2 px-4 text-sm font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
            >
              {loading ? 'Sending...' : 'Send Reminder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
