import { setRequestLocale } from 'next-intl/server';

export default async function EnterpriseDashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  setRequestLocale(locale);
  return <EnterpriseDashboard />;
}

// ---------------------------------------------------------------------------
// K-anonymity helper — enforce k ≥ 5 at the render boundary.
// The DB view already suppresses sub-k cells (returns null), but we also
// gate here as defence-in-depth. Never show 0 or a small number; show the
// explicit string "Insufficient data" so the admin understands why.
// ---------------------------------------------------------------------------

function safeDisplay(n: number | null): string {
  if (n === null || n < 5) return 'Insufficient data';
  return n.toLocaleString('en'); // always Latin digits
}

// ---------------------------------------------------------------------------
// Stub data — replace with API calls once the backend endpoints are wired.
// All values go through safeDisplay() before rendering.
// ---------------------------------------------------------------------------

const STUB_METRICS = {
  activeMembers7d: 847,
  toolsUsed7d: 2341,
  avgUrgeHandledPct: 73,
  wellbeingIndex: 6.8,
};

const WEEKLY_ENGAGEMENT: { label: string; pct: number }[] = [
  { label: 'W1', pct: 65 },
  { label: 'W2', pct: 71 },
  { label: 'W3', pct: 68 },
  { label: 'W4', pct: 74 },
  { label: 'W5', pct: 78 },
  { label: 'W6', pct: 73 },
];

const TOP_TOOLS: { rank: number; name: string; pct: number }[] = [
  { rank: 1, name: 'Box Breathing', pct: 34 },
  { rank: 2, name: '5-4-3-2-1 Grounding', pct: 28 },
  { rank: 3, name: 'Urge Surfing', pct: 19 },
  { rank: 4, name: 'STOP Technique', pct: 12 },
  { rank: 5, name: 'Other', pct: 7 },
];

interface DeptRow {
  name: string;
  members: number;
  active7d: number | null; // null = sub-k suppressed
  wellbeingIndex: number | null;
}

const DEPARTMENTS: DeptRow[] = [
  { name: 'Engineering', members: 234, active7d: 189, wellbeingIndex: 6.9 },
  { name: 'Operations', members: 156, active7d: 121, wellbeingIndex: 6.6 },
  { name: 'Sales', members: 98, active7d: 74, wellbeingIndex: 7.1 },
  { name: 'HR', members: 45, active7d: 38, wellbeingIndex: 7.4 },
  // Below k ≥ 5 threshold — active and wellbeing cells are suppressed
  { name: 'Legal', members: 3, active7d: null, wellbeingIndex: null },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Enforce LTR + tabular numerics for every displayed number. */
function Metric({ value }: { value: string }): React.JSX.Element {
  if (value === 'Insufficient data') {
    return (
      <span className="text-sm font-normal text-[hsl(215,16%,47%)] italic">
        Insufficient data
      </span>
    );
  }
  return (
    <span className="tabular-nums" style={{ direction: 'ltr' }}>
      {value}
    </span>
  );
}

function MetricCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit?: string;
}): React.JSX.Element {
  return (
    <article className="rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 shadow-sm">
      <h2 className="text-sm font-medium text-[hsl(215,16%,47%)]">{label}</h2>
      <p className="mt-2 text-3xl font-semibold text-[hsl(222,47%,11%)]">
        <Metric value={value} />
        {unit && value !== 'Insufficient data' && (
          <span className="ml-1 text-lg font-normal text-[hsl(215,16%,47%)]">{unit}</span>
        )}
      </p>
    </article>
  );
}

function DPFootnote(): React.JSX.Element {
  return (
    <p className="mt-2 text-xs text-[hsl(215,16%,57%)]">
      * Figures use differential privacy and may vary slightly from exact counts.
    </p>
  );
}

function WeeklyEngagementChart(): React.JSX.Element {
  return (
    <section aria-labelledby="engagement-chart-heading" className="rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 shadow-sm">
      <h2 id="engagement-chart-heading" className="text-base font-semibold text-[hsl(222,47%,11%)]">
        Weekly engagement rate
      </h2>
      {/* CSS bar chart — no JS charting library */}
      <div
        className="mt-4 flex items-end gap-3"
        style={{ height: '120px' }}
        role="img"
        aria-label="Bar chart showing weekly engagement rates"
      >
        {WEEKLY_ENGAGEMENT.map(({ label, pct }) => (
          <div
            key={label}
            className="flex flex-1 flex-col items-center gap-1"
            style={{ height: '100%' }}
          >
            <span
              className="text-xs font-medium tabular-nums text-[hsl(215,16%,47%)]"
              style={{ direction: 'ltr' }}
            >
              {pct}%
            </span>
            <div
              className="w-full rounded-t-sm bg-[hsl(217,91%,60%)] transition-all"
              style={{ height: `${pct}%` }}
              aria-hidden="true"
            />
            <span className="text-xs text-[hsl(215,16%,57%)]">{label}</span>
          </div>
        ))}
      </div>
      <DPFootnote />
    </section>
  );
}

function TopToolsList(): React.JSX.Element {
  return (
    <section aria-labelledby="top-tools-heading" className="rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 shadow-sm">
      <h2 id="top-tools-heading" className="text-base font-semibold text-[hsl(222,47%,11%)]">
        Top coping tools used (7d)
      </h2>
      <ul className="mt-4 space-y-3" role="list">
        {TOP_TOOLS.map(({ rank, name, pct }) => (
          <li key={rank} className="flex items-center gap-3">
            <span
              className="w-4 shrink-0 text-xs font-medium tabular-nums text-[hsl(215,16%,47%)]"
              style={{ direction: 'ltr' }}
            >
              {rank}.
            </span>
            <span className="w-36 shrink-0 truncate text-sm text-[hsl(222,47%,11%)]">{name}</span>
            <div className="relative flex-1">
              <div className="h-2 w-full overflow-hidden rounded-full bg-[hsl(220,14%,93%)]">
                <div
                  className="h-full rounded-full bg-[hsl(217,91%,60%)]"
                  style={{ width: `${pct}%` }}
                  role="presentation"
                />
              </div>
            </div>
            <span
              className="w-9 shrink-0 text-right text-xs tabular-nums text-[hsl(215,16%,47%)]"
              style={{ direction: 'ltr' }}
            >
              {pct}%
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function DepartmentTable(): React.JSX.Element {
  return (
    <section aria-labelledby="dept-heading" className="rounded-xl border border-[hsl(220,14%,90%)] bg-white p-5 shadow-sm">
      <h2 id="dept-heading" className="text-base font-semibold text-[hsl(222,47%,11%)]">
        Department breakdown
      </h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[hsl(220,14%,93%)] text-left text-xs font-medium text-[hsl(215,16%,47%)]">
              <th scope="col" className="pb-2 pr-4">
                Department
              </th>
              <th scope="col" className="pb-2 pr-4 tabular-nums">
                Members
              </th>
              {/* Column header explains k-anonymity suppression */}
              <th scope="col" className="pb-2 pr-4" title="Groups smaller than 5 are suppressed">
                <span className="flex items-center gap-1">
                  Active (7d)
                  <span
                    className="inline-flex h-4 w-4 cursor-default items-center justify-center rounded-full bg-[hsl(220,14%,90%)] text-[10px] leading-none text-[hsl(215,16%,47%)]"
                    aria-label="Groups smaller than 5 are suppressed"
                  >
                    ?
                  </span>
                </span>
              </th>
              <th scope="col" className="pb-2" title="Groups smaller than 5 are suppressed">
                <span className="flex items-center gap-1">
                  Wellbeing Index
                  <span
                    className="inline-flex h-4 w-4 cursor-default items-center justify-center rounded-full bg-[hsl(220,14%,90%)] text-[10px] leading-none text-[hsl(215,16%,47%)]"
                    aria-label="Groups smaller than 5 are suppressed"
                  >
                    ?
                  </span>
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[hsl(220,14%,96%)]">
            {DEPARTMENTS.map((dept) => {
              const membersDisplay = safeDisplay(dept.members);
              const activeDisplay =
                dept.active7d === null
                  ? 'Insufficient data'
                  : safeDisplay(dept.active7d);
              const wellbeingDisplay =
                dept.wellbeingIndex === null
                  ? 'Insufficient data'
                  : dept.members < 5
                  ? 'Insufficient data'
                  : dept.wellbeingIndex.toLocaleString('en', {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    }) + '/10';

              return (
                <tr key={dept.name} className="text-[hsl(222,47%,11%)]">
                  <td className="py-2.5 pr-4 font-medium">{dept.name}</td>
                  <td className="py-2.5 pr-4">
                    {membersDisplay === 'Insufficient data' ? (
                      <span className="text-xs italic text-[hsl(215,16%,47%)]">
                        Insufficient data
                      </span>
                    ) : (
                      <span className="tabular-nums" style={{ direction: 'ltr' }}>
                        {membersDisplay}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pr-4">
                    {activeDisplay === 'Insufficient data' ? (
                      <span className="text-xs italic text-[hsl(215,16%,47%)]">
                        Insufficient data
                      </span>
                    ) : (
                      <span className="tabular-nums" style={{ direction: 'ltr' }}>
                        {activeDisplay}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5">
                    {wellbeingDisplay === 'Insufficient data' ? (
                      <span className="text-xs italic text-[hsl(215,16%,47%)]">
                        Insufficient data
                      </span>
                    ) : (
                      <span className="tabular-nums" style={{ direction: 'ltr' }}>
                        {wellbeingDisplay}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-[hsl(215,16%,57%)]">
        Groups smaller than 5 members are suppressed to protect individual privacy.
      </p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function EnterpriseDashboard(): React.JSX.Element {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      {/* Header */}
      <header className="border-b border-[hsl(220,14%,90%)] pb-6">
        <h1 className="text-2xl font-semibold text-[hsl(222,47%,11%)]">
          Discipline OS · Enterprise
        </h1>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          Organization-level aggregate view. Individual user data is never visible in this portal.
        </p>
      </header>

      {/* Privacy floor notice */}
      <div
        role="note"
        className="mt-6 rounded-md border border-[hsl(38,92%,50%)]/30 bg-[hsl(38,92%,97%)] p-4 text-sm text-[hsl(38,30%,30%)]"
      >
        <strong>Privacy floor:</strong> any cohort smaller than 5 people is suppressed —
        cells show &ldquo;Insufficient data&rdquo; rather than exact counts. Enforced in the
        database and again at this render boundary.{' '}
        <span className="tabular-nums" style={{ direction: 'ltr' }} aria-hidden="true" />
      </div>

      {/* Key metrics row */}
      <section aria-labelledby="key-metrics-heading" className="mt-8">
        <h2 id="key-metrics-heading" className="sr-only">
          Key metrics
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Active members (7d)"
            value={safeDisplay(STUB_METRICS.activeMembers7d)}
          />
          <MetricCard
            label="Tools used (7d)"
            value={safeDisplay(STUB_METRICS.toolsUsed7d)}
          />
          <MetricCard
            label="Avg urge handled"
            value={
              STUB_METRICS.avgUrgeHandledPct < 5
                ? 'Insufficient data'
                : STUB_METRICS.avgUrgeHandledPct.toLocaleString('en') + '%'
            }
          />
          <MetricCard
            label="Org wellbeing index"
            value={
              STUB_METRICS.wellbeingIndex < 5
                ? 'Insufficient data'
                : STUB_METRICS.wellbeingIndex.toLocaleString('en', {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                  })
            }
            unit="/10"
          />
        </div>
        <DPFootnote />
      </section>

      {/* Weekly engagement bar chart */}
      <div className="mt-8">
        <WeeklyEngagementChart />
      </div>

      {/* Bottom two-column section */}
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <TopToolsList />
        <DepartmentTable />
      </div>

      {/* Aggregate-only reminder footer */}
      <footer className="mt-10 border-t border-[hsl(220,14%,90%)] pt-4 text-xs text-[hsl(215,16%,57%)]">
        All data shown is aggregate only. No individual user data is accessible through this portal.
        Figures use differential privacy and may vary slightly from exact counts.
      </footer>
    </main>
  );
}
