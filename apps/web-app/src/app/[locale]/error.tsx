'use client';

// error.tsx MUST be a Client Component — Next.js requirement.
// Do NOT use useTranslations() here: i18n context may be unavailable
// when an error boundary triggers (e.g. layout-level throw, i18n load
// failure itself). All copy is hardcoded English.
// If full i18n error strings are needed in future, surface them via a
// separate server-rendered fallback layout, not this boundary.

import { useEffect } from 'react';

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function LocaleError({ error, reset }: ErrorPageProps): React.JSX.Element {
  useEffect(() => {
    // Log the error so it appears in the app log stream.
    // In production the full error is not shown to the user, but we
    // still want it captured for observability.
    console.error('[LocaleError boundary]', error);
  }, [error]);

  // Derive the visible message based on environment.
  // In development, surface the real message to aid debugging.
  // In production, show a safe generic string.
  const userMessage =
    process.env.NODE_ENV === 'development'
      ? error.message
      : 'An unexpected error occurred. Please try again or return home.';

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white px-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-crisis-100">
        {/* Warning icon — inline SVG avoids external dep */}
        <svg
          className="h-6 w-6 text-crisis-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
          />
        </svg>
      </div>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">
        Something went wrong
      </h1>

      <p className="mt-3 max-w-sm text-sm leading-relaxed text-ink-500">{userMessage}</p>

      {/* Digest is safe to surface — it's an opaque server-generated hash */}
      {error.digest && (
        <p className="mt-2 font-mono text-xs text-ink-300">Error ID: {error.digest}</p>
      )}

      <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
        <button
          onClick={reset}
          className="inline-flex h-10 items-center rounded-md bg-brand-500 px-5 text-sm font-medium text-white transition-colors hover:bg-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2"
        >
          Try again
        </button>

        <a
          href="/"
          className="inline-flex h-10 items-center rounded-md border border-surface-200 bg-surface-0 px-5 text-sm font-medium text-ink-700 transition-colors hover:bg-surface-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2"
        >
          Go home
        </a>
      </div>
    </main>
  );
}
