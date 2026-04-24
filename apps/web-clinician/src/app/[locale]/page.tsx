/**
 * Clinician Dashboard — /[locale]
 *
 * Lists patients who have actively granted the signed-in clinician access
 * via a clinician_link record. Only consented, active links are shown.
 *
 * ALPHA / Phase 2: API wiring is stubbed. The stub data mirrors the real
 * ClinicianLinkItem shape from services/api/src/discipline/enterprise/router.py
 * so the swap-in cost is minimal.
 *
 * Access rules (enforced at multiple layers):
 *   1. Middleware (middleware.ts) — requires `roles.includes('clinician')` on the
 *      Clerk session JWT before the request reaches this page at all.
 *   2. Backend (when wired) — GET /v1/enterprise/clinician-links scopes results to
 *      the authenticated clinician's own links, consented only.
 *   3. This page — never renders real names; always pseudonymous Patient #N display.
 *
 * PHI note: The dashboard itself shows only derived / aggregate state (last check-in
 * date, state indicator, scopes). Individual-level PHI requires navigating to the
 * client detail page which carries an additional step-up re-auth gate.
 */

import Link from 'next/link';
import { setRequestLocale } from 'next-intl/server';
import { ClinicianNav } from '@/components/ClinicianNav';

// ---------------------------------------------------------------------------
// Types — mirror the enterprise API response shape
// ---------------------------------------------------------------------------

type UrgencyState = 'calm' | 'elevated' | 'high';

interface StubPatient {
  /** Pseudonymous display index shown in UI as "Patient #N" */
  displayIndex: number;
  /**
   * Opaque patient ID — a random UUID that maps to the real user_id server-side.
   * NEVER expose real names or PII in this structure.
   */
  patientId: string;
  lastCheckIn: string;       // ISO-8601 date string
  currentState: UrgencyState;
  scopes: string[];
}

// ---------------------------------------------------------------------------
// Stub data — 2 dev patients with obviously fake UUIDs
// (Replace with real API fetch when the portal moves out of alpha)
// ---------------------------------------------------------------------------

const STUB_PATIENTS: StubPatient[] = [
  {
    displayIndex: 1,
    patientId: '00000000-0000-0000-0000-000000000001',
    lastCheckIn: '2026-04-22',
    currentState: 'calm',
    scopes: ['check_ins', 'assessments'],
  },
  {
    displayIndex: 2,
    patientId: '00000000-0000-0000-0000-000000000002',
    lastCheckIn: '2026-04-20',
    currentState: 'elevated',
    scopes: ['check_ins', 'assessments', 'journal'],
  },
];

// ---------------------------------------------------------------------------
// Sub-components (server-renderable — no hooks needed)
// ---------------------------------------------------------------------------

function UrgencyDot({ state }: { state: UrgencyState }): React.JSX.Element {
  const config: Record<UrgencyState, { color: string; label: string }> = {
    calm: { color: 'bg-[hsl(142,71%,45%)]', label: 'Calm' },
    elevated: { color: 'bg-[hsl(38,92%,50%)]', label: 'Elevated' },
    high: { color: 'bg-[hsl(0,84%,60%)]', label: 'High urgency' },
  };
  const { color, label } = config[state];
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`inline-block h-2.5 w-2.5 rounded-full ${color}`}
        aria-hidden="true"
      />
      <span className="text-sm capitalize text-[hsl(222,47%,11%)]">{label}</span>
    </span>
  );
}

const SCOPE_LABELS: Record<string, string> = {
  check_ins: 'Check-ins',
  assessments: 'Assessments',
  journal: 'Journal',
  patterns: 'Patterns',
};

function ScopeBadge({ scope }: { scope: string }): React.JSX.Element {
  const label = SCOPE_LABELS[scope] ?? scope;
  return (
    <span className="inline-flex items-center rounded-full bg-[hsl(220,14%,94%)] px-2 py-0.5 text-xs font-medium text-[hsl(220,14%,30%)]">
      {label}
    </span>
  );
}

function formatCheckInDate(iso: string): string {
  // Render in a locale-neutral format — Latin digits always, no locale-dependent formatting
  // for clinical dates per the Latin-digit rule (CLAUDE.md §9).
  const d = new Date(iso);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default async function ClinicianDashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  setRequestLocale(locale);

  const patients = STUB_PATIENTS; // TODO: replace with real API call to GET /v1/enterprise/clinician-links

  return (
    <>
      <ClinicianNav />

      <main className="mx-auto max-w-5xl px-6 py-8">
        {/* ------------------------------------------------------------------ */}
        {/* Audit / access notice banner                                        */}
        {/* ------------------------------------------------------------------ */}
        <div
          role="note"
          aria-label="Data access notice"
          className="mb-8 flex items-start gap-3 rounded-xl border border-[hsl(217,91%,85%)] bg-[hsl(217,91%,97%)] px-5 py-4 text-sm text-[hsl(217,60%,32%)]"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="mt-0.5 h-5 w-5 shrink-0 text-[hsl(217,91%,52%)]"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
              clipRule="evenodd"
            />
          </svg>
          <p>
            This portal displays data <strong>only from clients who have actively shared with you</strong>.
            All access is logged for audit purposes. Individual client views require re-authentication.
          </p>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* Page header                                                         */}
        {/* ------------------------------------------------------------------ */}
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-[hsl(222,47%,11%)]">Clinician Portal</h1>
          <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
            Shared clients · invite-only alpha
          </p>
        </header>

        {/* ------------------------------------------------------------------ */}
        {/* Clients section                                                     */}
        {/* ------------------------------------------------------------------ */}
        <section aria-labelledby="clients-heading">
          <h2
            id="clients-heading"
            className="mb-4 text-base font-medium text-[hsl(222,47%,11%)]"
          >
            Shared clients
          </h2>

          {patients.length === 0 ? (
            /* Empty state */
            <div className="rounded-xl border border-dashed border-[hsl(220,14%,82%)] bg-white px-6 py-10 text-center">
              <p className="text-sm text-[hsl(215,16%,47%)]">
                No linked clients yet. Clients appear here once they grant you access.
              </p>
            </div>
          ) : (
            /* Clients table */
            <div className="overflow-hidden rounded-xl border border-[hsl(220,14%,90%)] bg-white shadow-sm">
              {/* Desktop table */}
              <table className="hidden w-full text-sm md:table">
                <thead>
                  <tr className="border-b border-[hsl(220,14%,90%)] bg-[hsl(220,14%,98%)]">
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Patient
                    </th>
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Last check-in
                    </th>
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Current state
                    </th>
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Scopes granted
                    </th>
                    <th scope="col" className="px-5 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(220,14%,94%)]">
                  {patients.map((p) => (
                    <tr key={p.patientId} className="hover:bg-[hsl(220,14%,99%)] transition-colors">
                      <td className="px-5 py-4 font-medium text-[hsl(222,47%,11%)]">
                        {/* Pseudonymous display — never show real name */}
                        Patient #{p.displayIndex}
                        <span className="ml-2 text-xs font-mono text-[hsl(215,16%,57%)] select-all">
                          {p.patientId.slice(0, 8)}…
                        </span>
                      </td>
                      {/* Latin digits enforced via tabular-nums + ltr direction per CLAUDE.md §9 */}
                      <td
                        className="px-5 py-4 tabular-nums text-[hsl(215,16%,47%)]"
                        dir="ltr"
                      >
                        {formatCheckInDate(p.lastCheckIn)}
                      </td>
                      <td className="px-5 py-4">
                        <UrgencyDot state={p.currentState} />
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-1">
                          {p.scopes.map((s) => (
                            <ScopeBadge key={s} scope={s} />
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-end">
                        <Link
                          href={`/${locale}/clients/${p.patientId}`}
                          className="inline-flex items-center rounded-md bg-[hsl(217,91%,52%)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[hsl(217,91%,44%)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(217,91%,52%)]/50"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Mobile card list */}
              <ul className="divide-y divide-[hsl(220,14%,94%)] md:hidden">
                {patients.map((p) => (
                  <li key={p.patientId} className="px-5 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-[hsl(222,47%,11%)]">
                          Patient #{p.displayIndex}
                        </p>
                        <p className="mt-0.5 font-mono text-xs text-[hsl(215,16%,57%)]">
                          {p.patientId.slice(0, 8)}…
                        </p>
                        <div className="mt-2">
                          <UrgencyDot state={p.currentState} />
                        </div>
                        <p
                          className="mt-1 text-xs tabular-nums text-[hsl(215,16%,47%)]"
                          dir="ltr"
                        >
                          Last check-in: {formatCheckInDate(p.lastCheckIn)}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {p.scopes.map((s) => (
                            <ScopeBadge key={s} scope={s} />
                          ))}
                        </div>
                      </div>
                      <Link
                        href={`/${locale}/clients/${p.patientId}`}
                        className="shrink-0 inline-flex items-center rounded-md bg-[hsl(217,91%,52%)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[hsl(217,91%,44%)] transition-colors"
                      >
                        View
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Footer note                                                         */}
        {/* ------------------------------------------------------------------ */}
        <p className="mt-8 text-xs text-[hsl(215,16%,57%)]">
          Discipline OS Clinician Portal · invite-only alpha · access is audit-logged ·{' '}
          <span className="tabular-nums" dir="ltr">{patients.length}</span>{' '}
          {patients.length === 1 ? 'client' : 'clients'} linked
        </p>
      </main>
    </>
  );
}
