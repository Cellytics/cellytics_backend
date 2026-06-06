'use client';

import { useState } from 'react';
import { managementAPI, getErrorMessage } from '@/lib/api';

interface CreateSeniorCellModalProps {
  fellowshipId: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

export default function CreateSeniorCellModal({
  fellowshipId,
  onClose,
  onSuccess,
  onError,
}: CreateSeniorCellModalProps) {
  const [name, setName] = useState('');
  const [leaderId, setLeaderId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      onError('Senior cell name is required');
      return;
    }

    setLoading(true);
    try {
      await managementAPI.createSeniorCell(fellowshipId, {
        name,
        ...(leaderId && { leader_id: leaderId }),
      });
      onSuccess();
    } catch (error) {
      onError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-2xl font-bold text-gray-900">Create Senior Cell</h2>
        <p className="mt-1 text-gray-600">Add a new senior cell to your fellowship</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Senior Cell Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., North Campus Cell"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Leader ID (Optional)</label>
            <input
              type="text"
              value={leaderId}
              onChange={(e) => setLeaderId(e.target.value)}
              placeholder="Leave empty to assign later"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
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
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
