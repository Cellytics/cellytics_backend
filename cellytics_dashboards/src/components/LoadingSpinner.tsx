/**
 * LOADING SPINNER COMPONENT
 * 
 * Shows a spinning loader while data is being fetched.
 * Used for loading states on pages and components.
 * 
 * Usage:
 *   {isLoading && <LoadingSpinner />}
 */

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
        <div className="absolute inset-0 rounded-full border-4 border-navy border-t-gold animate-spin"></div>
      </div>
      <span className="ml-4 text-gray-600">Loading...</span>
    </div>
  );
}
