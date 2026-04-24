'use client';

/**
 * StepUpGate — Clerk step-up re-authentication gate for PHI-sensitive views.
 *
 * SECURITY CONTRACT (must not be weakened):
 *   - `children` are NEVER rendered until `isVerified` is true.
 *   - The gate is the second layer of PHI defense, after the middleware
 *     role check (layer 1). See Docs/Technicals/14_Authentication_Logging.md §2.8.
 *   - Verification state is ephemeral (component lifetime only). Navigating
 *     away and back re-presents the gate. This is intentional: a clinician
 *     switching between patient records re-verifies each time, limiting the
 *     blast radius of an unlocked device.
 *
 * Implementation note on `__internal_openReverification`:
 *   Clerk v6 exposes `useReverification()` to wrap API fetchers that return a
 *   server-side reverification challenge. That hook is not appropriate here
 *   because we want to gate unconditionally on page load, not in response to a
 *   401 from an API route.  The correct approach is `useClerk()` which gives
 *   access to `clerk.__internal_openReverification(props)` — the same underlying
 *   modal that `useReverification` drives, but triggered imperatively.  The
 *   `__internal_` prefix marks it as non-public API in Clerk's type system;
 *   there is no stable public equivalent in v6 for an unconditional gate. We
 *   pin `@clerk/nextjs` to `^6.0.0` (currently 6.39.2) and will migrate to the
 *   stable API when Clerk promotes it.
 */

import { useClerk } from '@clerk/nextjs';
import { useState } from 'react';

// --------------------------------------------------------------------------
// Types
// --------------------------------------------------------------------------

interface StepUpGateProps {
  /** The patient ID being accessed — used only for labelling; PHI never in this component. */
  patientId: string;
  /** Content to show once step-up is verified. Never rendered before verification. */
  children: React.ReactNode;
}

// --------------------------------------------------------------------------
// Component
// --------------------------------------------------------------------------

export function StepUpGate({ children }: StepUpGateProps): React.JSX.Element {
  const clerk = useClerk();
  const [isVerified, setIsVerified] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [wasCancelled, setWasCancelled] = useState(false);

  const handleVerify = () => {
    setIsVerifying(true);
    setWasCancelled(false);

    // `__internal_openReverification` is the imperative entry point into
    // Clerk's user-verification modal (passkey / TOTP / backup code / password
    // depending on what the clinician has enrolled).  `afterVerification` fires
    // on success; `afterVerificationCancelled` fires when the modal is closed
    // without completing verification.
    clerk.__internal_openReverification({
      afterVerification: () => {
        setIsVerifying(false);
        setIsVerified(true);
      },
      afterVerificationCancelled: () => {
        setIsVerifying(false);
        setWasCancelled(true);
      },
    });
  };

  // Gate passed — render the protected content.
  if (isVerified) {
    return <>{children}</>;
  }

  // Gate not yet passed — render the verification prompt.
  return (
    <div
      role="alert"
      aria-live="polite"
      className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-center"
    >
      {/* Lock icon */}
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-6 w-6 text-amber-600"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      <h2 className="text-base font-semibold text-amber-900">
        Identity verification required
      </h2>

      <p className="mt-2 text-sm text-amber-700">
        Viewing individual client data requires re-authentication. This confirms
        it&apos;s you, not someone who found your unlocked device.
      </p>

      {wasCancelled && (
        <p
          role="status"
          className="mt-3 text-sm font-medium text-amber-800"
        >
          Verification was cancelled. Please verify your identity to continue.
        </p>
      )}

      <button
        type="button"
        onClick={handleVerify}
        disabled={isVerifying}
        className="mt-4 inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-700 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
      >
        {isVerifying ? 'Verifying…' : 'Verify identity'}
      </button>

      <p className="mt-3 text-xs text-amber-600">
        All PHI access is logged for clinical audit compliance.
      </p>
    </div>
  );
}
