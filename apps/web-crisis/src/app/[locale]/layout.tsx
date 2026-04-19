import { notFound } from 'next/navigation';
import { SUPPORTED_LOCALES, isRtl, isCrisisLocale } from '@/lib/locale';

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

  return (
    <div lang={locale} dir={isRtl(locale) ? 'rtl' : 'ltr'} className="min-h-screen">
      {children}
    </div>
  );
}
