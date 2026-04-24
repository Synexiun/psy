// PHI BOUNDARY: This page reads individual patient data. Backend sets X-Phi-Boundary: 1.
// The middleware (src/middleware.ts) also sets X-Phi-Boundary: 1 on all /:locale/clients/:id routes
// as a belt-and-suspenders measure so the audit-log correlator picks it up at the edge.

/**
 * Individual Patient View — /[locale]/clients/[patientId]
 *
 * SECURITY CONTRACT (must not be weakened):
 *   1. Real patient name is NEVER rendered — display is always "Patient #[index]".
 *   2. Step-up re-auth is required before rendering individual-level data.
 *      Currently rendered as a UI gate; Clerk step-up must be wired before GA.
 *   3. Each data tab is scope-gated: only rendered if the clinician_link.scopes
 *      array contains the required scope key.
 *   4. All clinical score values use Latin digits regardless of locale (tabular-nums,
 *      dir="ltr" on score cells) — CLAUDE.md §9 / Kroenke 2001 requirement.
 *
 * API wiring: stubbed for Phase 2 alpha. Data shapes mirror the enterprise and
 * psychometric API schemas so the real fetch is a drop-in replacement.
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { setRequestLocale } from 'next-intl/server';
import { ClinicianNav } from '@/components/ClinicianNav';
import { PatientTabs } from '@/components/PatientTabs';
import { StepUpGate } from '@/components/StepUpGate';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AssessmentScore {
  date: string;         // ISO-8601
  instrument: string;   // e.g. "PHQ-9", "GAD-7"
  score: number;        // Latin digits only when rendered
  severity: string;     // e.g. "Mild", "Moderate"
}

interface CheckInEntry {
  date: string;
  urgeIntensity: number; // 1–10
  notes: string;
}

interface PatientStub {
  displayIndex: number;
  patientId: string;
  scopes: string[];
  lastCheckIn: string;
  checkIns: CheckInEntry[];
  assessmentScores: AssessmentScore[];
  journalEntryCount: number; // Count only — journal text itself is scope-gated and never shown
}

// ---------------------------------------------------------------------------
// Stub data — obviously fake UUIDs, realistic score ranges
// ---------------------------------------------------------------------------

const STUB_PATIENTS: Record<string, PatientStub> = {
  '00000000-0000-0000-0000-000000000001': {
    displayIndex: 1,
    patientId: '00000000-0000-0000-0000-000000000001',
    scopes: ['check_ins', 'assessments'],
    lastCheckIn: '2026-04-22',
    checkIns: [
      { date: '2026-04-22', urgeIntensity: 3, notes: '' },
      { date: '2026-04-19', urgeIntensity: 6, notes: '' },
      { date: '2026-04-15', urgeIntensity: 4, notes: '' },
    ],
    assessmentScores: [
      { date: '2026-04-01', instrument: 'PHQ-9', score: 11, severity: 'Moderate' },
      { date: '2026-03-01', instrument: 'PHQ-9', score: 14, severity: 'Moderate' },
      { date: '2026-02-01', instrument: 'PHQ-9', score: 17, severity: 'Moderately Severe' },
      { date: '2026-04-01', instrument: 'GAD-7', score: 8, severity: 'Moderate' },
      { date: '2026-03-01', instrument: 'GAD-7', score: 10, severity: 'Moderate' },
    ],
    journalEntryCount: 0, // scope not granted
  },
  '00000000-0000-0000-0000-000000000002': {
    displayIndex: 2,
    patientId: '00000000-0000-0000-0000-000000000002',
    scopes: ['check_ins', 'assessments', 'journal'],
    lastCheckIn: '2026-04-20',
    checkIns: [
      { date: '2026-04-20', urgeIntensity: 7, notes: '' },
      { date: '2026-04-17', urgeIntensity: 5, notes: '' },
      { date: '2026-04-12', urgeIntensity: 8, notes: '' },
    ],
    assessmentScores: [
      { date: '2026-04-05', instrument: 'PHQ-9', score: 7, severity: 'Mild' },
      { date: '2026-03-05', instrument: 'PHQ-9', score: 9, severity: 'Mild' },
      { date: '2026-04-05', instrument: 'GAD-7', score: 5, severity: 'Mild' },
      { date: '2026-03-05', instrument: 'GAD-7', score: 7, severity: 'Mild' },
    ],
    journalEntryCount: 12,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  const d = new Date(iso);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ---------------------------------------------------------------------------
// Page — server component
// ---------------------------------------------------------------------------

export default async function PatientDetailPage({
  params,
}: {
  params: Promise<{ locale: string; patientId: string }>;
}): Promise<React.JSX.Element> {
  const { locale, patientId } = await params;
  setRequestLocale(locale);

  // In production: fetch from GET /v1/enterprise/clinician-links?patient_id={patientId}
  // and validate the link is active + consented before rendering any data.
  const patient = STUB_PATIENTS[patientId];

  if (!patient) {
    notFound();
  }

  return (
    <>
      <ClinicianNav />

      <main className="mx-auto max-w-5xl px-6 py-8">
        {/* ---------------------------------------------------------------- */}
        {/* Back navigation                                                   */}
        {/* ---------------------------------------------------------------- */}
        <Link
          href={`/${locale}`}
          className="inline-flex items-center gap-1.5 text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors mb-6"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            className="h-4 w-4"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M9.78 4.22a.75.75 0 010 1.06L7.06 8l2.72 2.72a.75.75 0 11-1.06 1.06L5.47 8.53a.75.75 0 010-1.06l3.25-3.25a.75.75 0 011.06 0z"
              clipRule="evenodd"
            />
          </svg>
          Back to dashboard
        </Link>

        {/* ---------------------------------------------------------------- */}
        {/* Patient header — pseudonymous, never real name                   */}
        {/* ---------------------------------------------------------------- */}
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[hsl(222,47%,11%)]">
              Patient #{patient.displayIndex}
            </h1>
            <p
              className="mt-1 font-mono text-xs text-[hsl(215,16%,57%)] select-all"
              aria-label={`Patient identifier: ${patient.patientId}`}
            >
              ID: {patient.patientId}
            </p>
          </div>
          <p
            className="text-sm tabular-nums text-[hsl(215,16%,47%)]"
            dir="ltr"
          >
            Last check-in: {formatDate(patient.lastCheckIn)}
          </p>
        </header>

        {/* ---------------------------------------------------------------- */}
        {/* Step-up re-auth gate (layer 2 after middleware role check)        */}
        {/* Per spec (Docs/Technicals/14_Authentication_Logging.md §2.8):    */}
        {/* step-up re-auth is required before any individual-level PHI view. */}
        {/* StepUpGate never renders children until identity is re-verified.  */}
        {/* ---------------------------------------------------------------- */}
        <StepUpGate patientId={patient.patientId}>
          {/* Scoped tab navigation — client component for interactivity */}
          <PatientTabs
            locale={locale}
            scopes={patient.scopes}
            checkIns={patient.checkIns}
            assessmentScores={patient.assessmentScores}
            journalEntryCount={patient.journalEntryCount}
          />
        </StepUpGate>
      </main>
    </>
  );
}
