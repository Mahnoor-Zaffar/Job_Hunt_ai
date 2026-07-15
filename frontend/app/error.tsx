"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <h2 className="text-lg font-semibold text-red-700 mb-2">Something went wrong</h2>
      <p className="text-sm text-red-600 mb-4">{error.message || "An unexpected error occurred"}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
      >
        Try again
      </button>
    </div>
  );
}
