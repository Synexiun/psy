'use client';

/**
 * PatientTabs — scope-gated tab view for an individual patient.
 *
 * SCOPE CONTRACT:
 *   Each tab is only rendered if the clinician_link.scopes array contains
 *   the corresponding scope key. If the scope is absent, the tab shows an
 *   "Access not granted" message rather than being hidden entirely — this
 *   is intentional: it makes the scope boundary visible to the clinician
 *   rather than silently omitting data categories.
 *
 * LATIN DIGITS:
 *   All clinical score values (PHQ-9, GAD-7 totals) are rendered with
 *   `tabular-nums` CSS and `dir="ltr"` to enforce Latin digits regardless
 *   of the page locale. CLAUDE.md §9 / Kroenke 2001.
 *
 * PHI note: Journal tab shows only an entry count, never the text content,
 *   even when the journal scope is granted. Full text access would require
 *   a separate PHI-gated fetch — out of scope for Phase 2 alpha.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Types (mirrored from the page — kept local to avoid a shared types file for now)
// ---------------------------------------------------------------------------

interface AssessmentScore {
  date: string;
  instrument: string;
  score: number;
  severity: string;
}

interface CheckInEntry {
  date: string;
  urgeIntensity: number;
  notes: string;
}

interface PatientTabsProps {
  locale: string;
  scopes: string[];
  checkIns: CheckInEntry[];
  assessmentScores: AssessmentScore[];
  journalEntryCount: number;
}

type TabId = 'check_ins' | 'assessments' | 'journal';

const TABS: { id: TabId; label: string }[] = [
  { id: 'check_ins', label: 'Check-ins' },
  { id: 'assessments', label: 'Assessments' },
  { id: 'journal', label: 'Journal' },
];

// ---------------------------------------------------------------------------
// Sub-views (one per tab)
// ---------------------------------------------------------------------------

function AccessNotGranted({ scopeLabel }: { scopeLabel: string }): React.JSX.Element {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-dashed border-[hsl(220,14%,82%)] bg-[hsl(220,14%,98%)] px-5 py-6 text-sm text-[hsl(215,16%,47%)]">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        className="h-5 w-5 shrink-0 text-[hsl(215,16%,57%)]"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
          clipRule="evenodd"
        />
      </svg>
      <span>
        <strong>Access not granted</strong> — this client has not shared{' '}
        <strong>{scopeLabel}</strong> data with you.
      </span>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
}

function CheckInsView({ checkIns }: { checkIns: CheckInEntry[] }): React.JSX.Element {
  if (checkIns.length === 0) {
    return (
      <p className="text-sm text-[hsl(215,16%,47%)]">No check-ins recorded yet.</p>
    );
  }
  return (
    <div className="overflow-hidden rounded-xl border border-[hsl(220,14%,90%)] bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[hsl(220,14%,90%)] bg-[hsl(220,14%,98%)]">
            <th
              scope="col"
              className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
            >
              Date
            </th>
            <th
              scope="col"
              className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
            >
              Urge intensity (1–10)
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[hsl(220,14%,94%)]">
          {checkIns.map((c, i) => (
            <tr key={i} className="hover:bg-[hsl(220,14%,99%)] transition-colors">
              {/* Latin digits: tabular-nums + ltr */}
              <td className="px-5 py-3 tabular-nums text-[hsl(215,16%,47%)]" dir="ltr">
                {formatDate(c.date)}
              </td>
              <td className="px-5 py-3">
                <div className="flex items-center gap-3">
                  {/* Latin digits enforced per CLAUDE.md §9 */}
                  <span
                    className="tabular-nums font-semibold text-[hsl(222,47%,11%)]"
                    dir="ltr"
                  >
                    {c.urgeIntensity}
                  </span>
                  {/* Visual intensity bar */}
                  <div
                    className="h-2 w-24 overflow-hidden rounded-full bg-[hsl(220,14%,90%)]"
                    aria-hidden="true"
                  >
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(c.urgeIntensity / 10) * 100}%`,
                        backgroundColor:
                          c.urgeIntensity <= 3
                            ? 'hsl(142,71%,45%)'
                            : c.urgeIntensity <= 6
                            ? 'hsl(38,92%,50%)'
                            : 'hsl(0,84%,60%)',
                      }}
                    />
                  </div>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AssessmentsView({
  scores,
}: {
  scores: AssessmentScore[];
}): React.JSX.Element {
  if (scores.length === 0) {
    return (
      <p className="text-sm text-[hsl(215,16%,47%)]">No assessment scores recorded yet.</p>
    );
  }

  // Group by instrument
  const instruments = [...new Set(scores.map((s) => s.instrument))];

  return (
    <div className="flex flex-col gap-8">
      {instruments.map((inst) => {
        const instScores = scores
          .filter((s) => s.instrument === inst)
          .sort((a, b) => a.date.localeCompare(b.date));

        return (
          <section key={inst} aria-labelledby={`inst-${inst}`}>
            <h3
              id={`inst-${inst}`}
              className="mb-3 text-sm font-semibold text-[hsl(222,47%,11%)]"
            >
              {inst}
            </h3>
            <div className="overflow-hidden rounded-xl border border-[hsl(220,14%,90%)] bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[hsl(220,14%,90%)] bg-[hsl(220,14%,98%)]">
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Date
                    </th>
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Score
                    </th>
                    <th
                      scope="col"
                      className="px-5 py-3 text-start text-xs font-semibold uppercase tracking-wide text-[hsl(215,16%,47%)]"
                    >
                      Severity
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(220,14%,94%)]">
                  {instScores.map((s, i) => (
                    <tr key={i} className="hover:bg-[hsl(220,14%,99%)] transition-colors">
                      {/* Latin digits: tabular-nums + dir="ltr" per CLAUDE.md §9 */}
                      <td
                        className="px-5 py-3 tabular-nums text-[hsl(215,16%,47%)]"
                        dir="ltr"
                      >
                        {formatDate(s.date)}
                      </td>
                      <td
                        className="px-5 py-3 font-semibold tabular-nums text-[hsl(222,47%,11%)]"
                        dir="ltr"
                      >
                        {s.score}
                      </td>
                      <td className="px-5 py-3 text-[hsl(215,16%,47%)]">
                        {s.severity}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-[hsl(215,16%,57%)]">
              {inst === 'PHQ-9'
                ? 'Scores per Kroenke et al. (2001): 0–4 None, 5–9 Mild, 10–14 Moderate, 15–19 Moderately Severe, 20–27 Severe.'
                : inst === 'GAD-7'
                ? 'Scores per Spitzer et al. (2006): 0–4 Minimal, 5–9 Mild, 10–14 Moderate, 15–21 Severe.'
                : null}
            </p>
          </section>
        );
      })}
    </div>
  );
}

function JournalView({
  journalEntryCount,
}: {
  journalEntryCount: number;
}): React.JSX.Element {
  return (
    <div className="rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 text-sm text-[hsl(215,16%,47%)]">
      <p>
        This client has{' '}
        {/* Latin digits per CLAUDE.md §9 */}
        <strong
          className="tabular-nums text-[hsl(222,47%,11%)]"
          dir="ltr"
        >
          {journalEntryCount}
        </strong>{' '}
        {journalEntryCount === 1 ? 'journal entry' : 'journal entries'}.
      </p>
      <p className="mt-2 text-xs text-[hsl(215,16%,57%)]">
        Journal text content is private. Only entry counts are available in the
        clinician portal in this phase.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main tab component
// ---------------------------------------------------------------------------

export function PatientTabs({
  scopes,
  checkIns,
  assessmentScores,
  journalEntryCount,
}: PatientTabsProps): React.JSX.Element {
  const [activeTab, setActiveTab] = React.useState<TabId>('check_ins');

  return (
    <div>
      {/* Tab bar */}
      <div
        role="tablist"
        aria-label="Patient data sections"
        className="mb-6 flex gap-1 border-b border-[hsl(220,14%,90%)]"
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          const hasScope = scopes.includes(tab.id);
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              id={`tab-${tab.id}`}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={[
                'relative px-4 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(217,91%,52%)]/50 rounded-t-md',
                isActive
                  ? 'text-[hsl(217,91%,44%)] after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-[2px] after:rounded-t-full after:bg-[hsl(217,91%,52%)]'
                  : 'text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)]',
                !hasScope ? 'opacity-60' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              {tab.label}
              {!hasScope && (
                <span
                  className="ml-1.5 inline-block h-2 w-2 rounded-full bg-[hsl(220,14%,75%)]"
                  aria-label="Access not granted"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab panels */}
      {TABS.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={activeTab !== tab.id}
        >
          {activeTab === tab.id && (
            <>
              {!scopes.includes(tab.id) ? (
                <AccessNotGranted scopeLabel={tab.label} />
              ) : tab.id === 'check_ins' ? (
                <CheckInsView checkIns={checkIns} />
              ) : tab.id === 'assessments' ? (
                <AssessmentsView scores={assessmentScores} />
              ) : (
                <JournalView journalEntryCount={journalEntryCount} />
              )}
            </>
          )}
        </div>
      ))}
    </div>
  );
}
