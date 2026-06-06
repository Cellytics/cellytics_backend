'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { SuccessAlert } from '@/components/SuccessAlert';
import { managementAPI, getErrorMessage } from '@/lib/api';
import CreateSeniorCellModal from '@/components/modals/CreateSeniorCellModal';
import AssignCellModal from '@/components/modals/AssignCellModal';
import ValidateReportModal from '@/components/modals/ValidateReportModal';
import ConfirmFinancesModal from '@/components/modals/ConfirmFinancesModal';
import PokeCellLeaderModal from '@/components/modals/PokeCellLeaderModal';

interface ManagementItem {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  modal: string;
}

const managementItems: ManagementItem[] = [
  {
    id: 'create-senior-cell',
    title: 'Create Senior Cell',
    description: 'Add a new senior cell to your fellowship',
    icon: '➕',
    color: 'bg-blue-500',
    modal: 'createSeniorCell',
  },
  {
    id: 'assign-cell',
    title: 'Assign Cell to Senior Cell',
    description: 'Assign existing cells to a senior cell',
    icon: '🔗',
    color: 'bg-green-500',
    modal: 'assignCell',
  },
  {
    id: 'validate-report',
    title: 'Validate Cell Report',
    description: 'Review and validate cell submission reports',
    icon: '✅',
    color: 'bg-purple-500',
    modal: 'validateReport',
  },
  {
    id: 'confirm-finances',
    title: 'Confirm Finances',
    description: 'Confirm and verify financial collections',
    icon: '💰',
    color: 'bg-yellow-500',
    modal: 'confirmFinances',
  },
  {
    id: 'poke-leader',
    title: 'Poke Cell Leader',
    description: 'Send a reminder to leaders who haven\'t submitted',
    icon: '📢',
    color: 'bg-red-500',
    modal: 'pokeLeader',
  },
];

export default function ManagementPage() {
  const params = useParams();
  const fellowshipId = params.id as string;
  
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleModalClose = () => {
    setActiveModal(null);
    setSuccess(null);
    setError(null);
  };

  const handleSuccess = (message: string) => {
    setSuccess(message);
    setActiveModal(null);
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleError = (message: string) => {
    setError(message);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <Link href={`/dashboard/fellowship/${fellowshipId}`} className="text-blue-600 hover:text-blue-800 text-sm font-semibold">
            ← Back to Dashboard
          </Link>
          <h1 className="mt-3 text-4xl font-bold text-gray-900">Fellowship Management</h1>
          <p className="mt-2 text-gray-600">Manage your cells, validate reports, and send notifications</p>
        </div>

        {/* Alerts */}
        {success && <SuccessAlert message={success} />}
        {error && <ErrorAlert message={error} />}

        {/* Management Items Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {managementItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveModal(item.modal)}
              className="group rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-lg hover:border-blue-300"
            >
              <div className={`${item.color} inline-flex h-12 w-12 items-center justify-center rounded-lg text-2xl`}>
                {item.icon}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900 text-left">{item.title}</h3>
              <p className="mt-2 text-sm text-gray-600 text-left">{item.description}</p>
              <div className="mt-4 flex items-center text-blue-600 group-hover:translate-x-1 transition-transform">
                <span className="text-sm font-semibold">Get Started</span>
                <span className="ml-2">→</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Modals */}
      {activeModal === 'createSeniorCell' && (
        <CreateSeniorCellModal
          fellowshipId={fellowshipId}
          onClose={handleModalClose}
          onSuccess={() => handleSuccess('Senior cell created successfully!')}
          onError={(msg) => handleError(msg)}
        />
      )}
      {activeModal === 'assignCell' && (
        <AssignCellModal
          fellowshipId={fellowshipId}
          onClose={handleModalClose}
          onSuccess={() => handleSuccess('Cell assigned successfully!')}
          onError={(msg) => handleError(msg)}
        />
      )}
      {activeModal === 'validateReport' && (
        <ValidateReportModal
          fellowshipId={fellowshipId}
          onClose={handleModalClose}
          onSuccess={() => handleSuccess('Report validated successfully!')}
          onError={(msg) => handleError(msg)}
        />
      )}
      {activeModal === 'confirmFinances' && (
        <ConfirmFinancesModal
          fellowshipId={fellowshipId}
          onClose={handleModalClose}
          onSuccess={() => handleSuccess('Finances confirmed successfully!')}
          onError={(msg) => handleError(msg)}
        />
      )}
      {activeModal === 'pokeLeader' && (
        <PokeCellLeaderModal
          fellowshipId={fellowshipId}
          onClose={handleModalClose}
          onSuccess={() => handleSuccess('Notification sent successfully!')}
          onError={(msg) => handleError(msg)}
        />
      )}
    </div>
  );
}
