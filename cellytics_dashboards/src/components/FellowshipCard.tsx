import type { FellowshipCard as FellowshipCardType } from '@/types/zone';

interface FellowshipCardProps {
  fellowship: FellowshipCardType;
  onViewDetails?: () => void;
}

export function FellowshipCard({ fellowship, onViewDetails }: FellowshipCardProps) {
  const submissionRate = fellowship.submission_rate || 0;
  const cellsCount = fellowship.cells_count || 0;
  const cellsReported = fellowship.cells_reported || 0;
  const submissionColor =
    submissionRate >= 90
      ? 'text-forest-green'
      : submissionRate >= 70
      ? 'text-orange-accent'
      : 'text-red-alert';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="mb-4">
        <h3 className="font-bold text-lg text-navy">{fellowship.name || 'Unnamed Fellowship'}</h3>
        {fellowship.location && (
          <p className="text-sm text-gray-600">{fellowship.location}</p>
        )}
        {fellowship.pastor_name && (
          <p className="text-xs text-gray-500 mt-1">Pastor: {fellowship.pastor_name}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4 py-4 border-y border-gray-100">
        <div>
          <p className="text-xs text-gray-600">Cells</p>
          <p className="text-xl font-bold text-navy">{cellsCount}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Senior Cells</p>
          <p className="text-xl font-bold text-navy">{fellowship.senior_cells_count || 0}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Reported This Week</p>
          <p className="text-lg font-bold text-navy">
            {cellsReported}/{cellsCount}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Attendance</p>
          <p className="text-lg font-bold text-navy">
            {(fellowship.total_attendance || 0).toLocaleString()}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs text-gray-600 mb-1">Submission Rate</p>
          <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                submissionRate >= 90
                  ? 'bg-forest-green'
                  : submissionRate >= 70
                  ? 'bg-orange-accent'
                  : 'bg-red-alert'
              }`}
              style={{ width: `${Math.min(submissionRate, 100)}%` }}
            />
          </div>
          <p className={`text-sm font-bold mt-1 ${submissionColor}`}>
            {submissionRate.toFixed(1)}%
          </p>
        </div>

        <div className="text-center">
          <p className="text-xs text-gray-600">Souls Won</p>
          <p className="text-2xl font-bold text-gold">{fellowship.souls_won || 0}</p>
        </div>
      </div>

      {onViewDetails && (
        <button
          onClick={onViewDetails}
          className="w-full px-4 py-2 bg-navy text-white rounded-lg hover:bg-navy/90 transition-colors text-sm font-medium"
        >
          View Details
        </button>
      )}
    </div>
  );
}
