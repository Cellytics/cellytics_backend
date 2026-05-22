/**
 * CREATE FELLOWSHIP MODAL COMPONENT
 * 
 * Simple modal form to create a new fellowship.
 * Used by zonal admin to add fellowships to their zone.
 * 
 * Usage:
 *   <CreateFellowshipModal
 *     isOpen={showModal}
 *     onClose={() => setShowModal(false)}
 *     onSubmit={handleCreateFellowship}
 *     isLoading={isLoading}
 *   />
 */

import { useState } from 'react';
import { Button } from './Button';
import { ErrorAlert } from './ErrorAlert';

interface CreateFellowshipModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string, location?: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export function CreateFellowshipModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  error,
}: CreateFellowshipModalProps) {
  const [formData, setFormData] = useState({ name: '', location: '' });
  const [localError, setLocalError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!formData.name.trim()) {
      setLocalError('Fellowship name is required');
      return;
    }

    try {
      await onSubmit(formData.name, formData.location || undefined);
      setFormData({ name: '', location: '' });
      onClose();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Failed to create fellowship');
    }
  };

  const handleClose = () => {
    setFormData({ name: '', location: '' });
    setLocalError(null);
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={handleClose}
      ></div>

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-sm w-full">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-xl font-bold text-navy">Create New Fellowship</h2>
            <button
              onClick={handleClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              x
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4">
            {/* Error Alert */}
            {(error || localError) && (
              <ErrorAlert message={(error || localError) ?? ''} onClose={() => setLocalError(null)} />
            )}

            {/* Fellowship Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Fellowship Name *
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Grace Fellowship"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent outline-none"
                disabled={isLoading}
              />
            </div>

            {/* Location */}
            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                Location (Optional)
              </label>
              <input
                id="location"
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g., Bamenda"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent outline-none"
                disabled={isLoading}
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={isLoading}
                disabled={isLoading}
                className="flex-1"
              >
                Create Fellowship
              </Button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
