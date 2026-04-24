import React from 'react';
import { notFound } from 'next/navigation';
import { SUPPORTED_LOCALES, isRtl, isCrisisLocale, type CrisisLocale } from '@/lib/locale';

export function generateStaticParams() {
  return SUPPORTED_LOCALES.map((locale) => ({ locale }));
}

export default async function CrisisLocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isCrisisLocale(locale)) notFound();

  const rtl = isRtl(locale as CrisisLocale);

  return (
    <div lang={locale} dir={rtl ? 'rtl' : 'ltr'} className="min-h-screen">
      {rtl && (
        // Vazirmatn covers both Arabic and Persian scripts. Only loaded for RTL
        // locales (ar, fa) to avoid a font download on en/fr pages. No runtime
        // package dependency — pure CDN link keeps this surface maximally lean.
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&display=swap"
        />
      )}
      {children}
    </div>
  );
}
