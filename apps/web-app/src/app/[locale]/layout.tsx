import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Inter, Fraunces, Vazirmatn } from 'next/font/google';
import { headers } from 'next/headers';
import { ClerkProvider } from '@clerk/nextjs';
import { isRtl, type Locale } from '@disciplineos/i18n-catalog';
import { routing } from '@/i18n/routing';
import { ThemeSync } from '@/components/ThemeSync';
import '../globals.css';

const inter = Inter({
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-inter',
});

const fraunces = Fraunces({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-fraunces',
  axes: ['SOFT', 'WONK', 'opsz'],
});

const vazirmatn = Vazirmatn({
  subsets: ['arabic'],
  display: 'swap',
  variable: '--font-vazirmatn',
});

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    alternates: {
      canonical: `https://app.disciplineos.com/${locale}`,
      languages: {
        en: 'https://app.disciplineos.com/en',
        fr: 'https://app.disciplineos.com/fr',
        ar: 'https://app.disciplineos.com/ar',
        fa: 'https://app.disciplineos.com/fa',
      },
    },
  };
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}): Promise<React.JSX.Element> {
  const { locale } = await params;
  if (!(routing.locales as readonly string[]).includes(locale)) notFound();
  setRequestLocale(locale);

  const dir = isRtl(locale as Locale) ? 'rtl' : 'ltr';

  const messages = await getMessages();
  const clerkKey = process.env['NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY'];

  // Read the per-request nonce injected by middleware.ts so ClerkProvider can
  // stamp it onto any inline scripts it emits, satisfying the nonce-based CSP.
  const headersList = await headers();
  const nonce = headersList.get('x-nonce') ?? '';
  const isFa = locale === 'fa';
  const fontVars = `${inter.variable} ${fraunces.variable}${isFa ? ' ' + vazirmatn.variable : ''}`.trim();
  const shell = (
    <html
      lang={locale}
      dir={dir}
      className={fontVars}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-surface-primary text-ink-primary antialiased">
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );

  if (!clerkKey) {
    return shell;
  }

  return (
    <ClerkProvider publishableKey={clerkKey} nonce={nonce}>
      <html
        lang={locale}
        dir={dir}
        className={fontVars}
        suppressHydrationWarning
      >
        <body className="min-h-screen bg-surface-primary text-ink-primary antialiased">
          <ThemeSync />
          <NextIntlClientProvider messages={messages}>
            {children}
          </NextIntlClientProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
