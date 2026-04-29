import type { Metadata } from 'next';
import { SignIn } from '@clerk/nextjs';
import { setRequestLocale } from 'next-intl/server';
import Link from 'next/link';

export const metadata: Metadata = { title: 'Sign In' };

export default async function SignInPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <div
      lang={locale}
      className="flex min-h-screen flex-col items-center justify-center bg-surface-secondary px-4 py-12"
    >
      <SignIn
        afterSignInUrl={`/${locale}`}
        appearance={{
          variables: {
            colorPrimary: 'hsl(217, 91%, 52%)',
            borderRadius: '0.75rem',
          },
        }}
      />
      <Link
        href="/"
        className="mt-6 text-sm text-[hsl(217,91%,52%)] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(217,91%,52%)] focus-visible:ring-offset-2 rounded-sm"
      >
        ← Back
      </Link>
    </div>
  );
}
