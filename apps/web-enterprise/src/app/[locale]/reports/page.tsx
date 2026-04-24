import { setRequestLocale } from 'next-intl/server';
import { ReportsList } from './ReportsList';

export default async function ReportsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  setRequestLocale(locale);
  return <ReportsPage_ />;
}

function ReportsPage_(): React.JSX.Element {
  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      {/* Header */}
      <header className="border-b border-[hsl(220,14%,90%)] pb-6">
        <h1 className="text-2xl font-semibold text-[hsl(222,47%,11%)]">Reports</h1>
        <p className="mt-1 text-sm text-[hsl(215,16%,47%)]">
          Generate aggregate reports for your organization. No individual user data is included.
        </p>
      </header>

      {/* Privacy reminder banner */}
      <div
        role="note"
        aria-label="Privacy reminder"
        className="mt-6 flex items-start gap-3 rounded-md border border-[hsl(142,71%,60%)]/30 bg-[hsl(142,71%,97%)] p-4 text-sm text-[hsl(142,40%,25%)]"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="mt-0.5 h-5 w-5 shrink-0"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
            clipRule="evenodd"
          />
        </svg>
        <div>
          <strong>Privacy reminder:</strong> Reports are aggregate only. No individual user data
          is included. All figures use differential privacy (k&nbsp;&ge;&nbsp;5 floor) and may
          vary slightly from exact counts.
        </div>
      </div>

      {/* Report list */}
      <ReportsList />
    </main>
  );
}
