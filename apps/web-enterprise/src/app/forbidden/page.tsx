export const dynamic = 'force-static';

export default function ForbiddenPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center px-6 text-center">
      <h1 className="text-2xl font-semibold">Access denied</h1>
      <p className="mt-3 text-[hsl(215,16%,47%)]">
        Your account does not have the enterprise admin role required to view this portal.
        Contact your organization owner to request access.
      </p>
    </main>
  );
}
