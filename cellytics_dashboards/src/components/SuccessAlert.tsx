/**
 * SUCCESS ALERT COMPONENT
 * 
 * Displays success messages in a user-friendly way.
 * Used for successful operations, confirmations, etc.
 * 
 * Usage:
 *   {success && <SuccessAlert message={success} />}
 */

interface SuccessAlertProps {
  message: string;
  onClose?: () => void;
}

export function SuccessAlert({ message, onClose }: SuccessAlertProps) {
  return (
    <div className="bg-forest-green/10 border border-forest-green text-forest-green px-4 py-3 rounded-lg flex items-start justify-between">
      <div className="flex items-start gap-3">
        <div className="text-xl mt-0.5">✓</div>
        <p>{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-forest-green hover:text-forest-green/80 font-bold ml-4"
        >
          ✕
        </button>
      )}
    </div>
  );
}
