export const dynamic = 'force-static';

export default function ForbiddenPage(): React.JSX.Element {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center px-6 text-center">
      <h1 className="text-2xl font-semibold">Access denied</h1>
      <p className="mt-3 text-[hsl(215,16%,47%)]">
        Your account does not have the clinician role required to view this portal.
        If you believe this is a mistake, contact your organization administrator.
      </p>
    </main>
  );
}
