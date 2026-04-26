import { getLocale } from 'next-intl/server';
import Link from 'next/link';

// Locale-specific 404 page.
// not-found.tsx receives no params from Next.js, so we use next-intl's
// getLocale() to derive the current locale from the request context.
// setRequestLocale() is intentionally omitted here — not-found renders
// outside the normal route tree so the locale is already established by
// the parent [locale]/layout.tsx before this component ever fires.

export default async function LocaleNotFound(): Promise<React.JSX.Element> {
  const locale = await getLocale();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface-secondary px-6 text-center">
      <p className="text-sm font-semibold uppercase tracking-widest text-ink-quaternary">404</p>

      <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink-primary sm:text-4xl">
        Page not found
      </h1>

      <p className="mt-4 max-w-sm text-sm leading-relaxed text-ink-tertiary">
        The page you&apos;re looking for doesn&apos;t exist or may have been moved.
      </p>

      <Link
        href={`/${locale}`}
        className="mt-8 inline-flex h-10 items-center rounded-md bg-accent-bronze px-5 text-sm font-medium text-white transition-colors hover:bg-accent-bronze-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2"
      >
        Go home
      </Link>
    </main>
  );
}
