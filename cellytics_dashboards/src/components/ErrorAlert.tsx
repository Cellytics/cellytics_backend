/**
 * ERROR ALERT COMPONENT
 * 
 * Displays error messages in a user-friendly way.
 * Used for API errors, validation errors, etc.
 * 
 * Usage:
 *   {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
 */

interface ErrorAlertProps {
  message: string;
  onClose?: () => void;
}

export function ErrorAlert({ message, onClose }: ErrorAlertProps) {
  return (
    <div className="bg-red-alert/10 border border-red-alert text-red-alert px-4 py-3 rounded-lg flex items-start justify-between">
      <div className="flex items-start gap-3">
        <div className="text-xl mt-0.5">⚠️</div>
        <p>{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-red-alert hover:text-red-alert/80 font-bold ml-4"
        >
          ✕
        </button>
      )}
    </div>
  );
}
