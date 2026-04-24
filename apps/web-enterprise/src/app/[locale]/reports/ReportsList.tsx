'use client';

import * as React from 'react';

interface ReportType {
  id: string;
  title: string;
  description: string;
  // Stub: in production this would be the API call to kick off PDF generation.
}

const REPORT_TYPES: ReportType[] = [
  {
    id: 'monthly-engagement',
    title: 'Monthly Engagement Report',
    description:
      'Aggregate tool usage, session counts, and engagement rate trends for the past calendar month. All cohorts below 5 are suppressed.',
  },
  {
    id: 'wellbeing-trends',
    title: 'Wellbeing Trends',
    description:
      'WHO-5 Wellbeing Index trajectory across departments over the trailing 90 days. Requires a minimum cohort of 5 respondents per group.',
  },
  {
    id: 'tool-adoption',
    title: 'Tool Adoption Report',
    description:
      'Breakdown of which coping tools were accessed, in what order, and with what frequency. Aggregate counts only — no user-level sequences.',
  },
];

export function ReportsList(): React.JSX.Element {
  const [generating, setGenerating] = React.useState<string | null>(null);

  function handleGenerate(reportId: string, _reportTitle: string): void {
    // Stub — production implementation will POST to /v1/enterprise/reports/{reportId}
    // then poll for the PDF artifact presigned URL.
    // No individual user identifiers are passed in this call.
    setGenerating(reportId);
    setTimeout(() => setGenerating(null), 1500);
  }

  return (
    <section aria-labelledby="report-types-heading" className="mt-8">
      <h2 id="report-types-heading" className="text-base font-semibold text-[hsl(222,47%,11%)]">
        Available report types
      </h2>

      <ul className="mt-4 space-y-4" role="list">
        {REPORT_TYPES.map((report) => {
          const isGenerating = generating === report.id;
          return (
            <li
              key={report.id}
              className="flex flex-col gap-3 rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 shadow-sm sm:flex-row sm:items-start sm:justify-between"
            >
              <div className="flex-1">
                <h3 className="text-sm font-medium text-[hsl(222,47%,11%)]">{report.title}</h3>
                <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">{report.description}</p>
              </div>
              <div className="shrink-0">
                <button
                  type="button"
                  onClick={() => handleGenerate(report.id, report.title)}
                  disabled={isGenerating}
                  aria-label={`Generate PDF for ${report.title}`}
                  className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-[hsl(220,14%,82%)] bg-white px-4 text-sm font-medium text-[hsl(222,47%,11%)] transition-colors hover:bg-[hsl(220,14%,96%)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(217,91%,52%)]/30 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <span
                        className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
                        aria-hidden="true"
                      />
                      Generating…
                    </>
                  ) : (
                    <>
                      {/* PDF icon */}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0-6a.75.75 0 000 1.5h3a.75.75 0 000-1.5h-3z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Generate PDF
                    </>
                  )}
                </button>
              </div>
            </li>
          );
        })}
      </ul>

      {/* Aggregate-only note */}
      <div className="mt-6 rounded-md border border-[hsl(220,14%,90%)] bg-[hsl(220,14%,97%)] p-4 text-sm text-[hsl(215,16%,47%)]">
        <strong className="text-[hsl(222,47%,11%)]">Note:</strong> Reports are aggregate only.
        No individual user data is included in any generated document. All figures are subject to
        the k&nbsp;&ge;&nbsp;5 privacy floor and differential privacy noise. Do not share
        generated reports with parties outside your organization.
      </div>
    </section>
  );
}
