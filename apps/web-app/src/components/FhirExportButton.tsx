'use client';
import * as React from 'react';
import { useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { ApiError } from '@disciplineos/api-client';

interface FhirExportButtonProps {
  periodId: string;
  locale: string;
  label: string;
  stepUpLabel: string;
  errorLabel: string;
}

export function FhirExportButton({ periodId, locale: _locale, label, stepUpLabel, errorLabel }: FhirExportButtonProps): React.ReactElement {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<'idle' | 'loading' | 'step-up-required' | 'error'>('idle');

  async function handleExport(): Promise<void> {
    setStatus('loading');
    try {
      const token = await getToken();
      if (!token) { setStatus('error'); return; }
      const res = await globalThis.fetch('/api/exports/fhir-r4', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ period_id: periodId }),
      });
      if (res.status === 401) {
        // Clerk step-up required — surface the step-up UI message.
        // When Clerk step-up API is fully wired (Phase 5), this triggers
        // the built-in factor verification modal.
        setStatus('step-up-required');
        return;
      }
      if (!res.ok) {
        let msg = `HTTP ${res.status}`;
        try { const b = await res.json() as { detail?: string }; if (b.detail) msg = b.detail; } catch { /* ignore */ }
        throw new ApiError(res.status, { code: 'server_error', message: msg });
      }
      // Download the blob
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fhir-r4-${periodId}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  const isLoading = status === 'loading';

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => void handleExport()}
        disabled={isLoading}
        data-testid="fhir-export-btn"
        className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium bg-surface-secondary hover:bg-surface-tertiary border border-border-subtle transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 disabled:opacity-50"
      >
        {isLoading ? (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 animate-spin" aria-hidden="true">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
        )}
        {label}
      </button>
      {status === 'step-up-required' && (
        <p className="text-xs text-signal-warning">{stepUpLabel}</p>
      )}
      {status === 'error' && (
        <p className="text-xs text-signal-crisis">{errorLabel}</p>
      )}
    </div>
  );
}
