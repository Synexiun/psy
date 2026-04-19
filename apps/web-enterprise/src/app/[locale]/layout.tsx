import type { Metadata } from 'next';
import { NextIntlClientProvider, hasLocale } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Inter, IBM_Plex_Sans_Arabic, Vazirmatn } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import { isRtl, type Locale } from '@disciplineos/i18n-catalog';
import { routing } from '@/i18n/routing';
import '../globals.css';

const inter = Inter({
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-inter',
});

const plexArabic = IBM_Plex_Sans_Arabic({
  subsets: ['arabic'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-plex-arabic',
});

const vazirmatn = Vazirmatn({
  subsets: ['arabic'],
  display: 'swap',
  variable: '--font-vazirmatn',
});

export const metadata: Metadata = {
  title: {
    default: 'Discipline OS — Enterprise',
    template: '%s · Enterprise',
  },
  description: 'Aggregate organization-level dashboards for Discipline OS administrators.',
  robots: { index: false, follow: false },
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);

  const dir = isRtl(locale as Locale) ? 'rtl' : 'ltr';

  return (
    <ClerkProvider>
      <html
        lang={locale}
        dir={dir}
        className={`${inter.variable} ${plexArabic.variable} ${vazirmatn.variable}`}
      >
        <body className="min-h-screen bg-white text-[hsl(222,47%,11%)] antialiased">
          <NextIntlClientProvider>{children}</NextIntlClientProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
