import type { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://www.disciplineos.com'),
  title: {
    default: 'Discipline OS — Close the loop on urges',
    template: '%s · Discipline OS',
  },
  description:
    'Evidence-based behavioral intervention platform. Detects rising urges and delivers coping tools in the critical 60-second window.',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://www.disciplineos.com',
    siteName: 'Discipline OS',
    title: 'Discipline OS — Close the loop on urges',
    description:
      'Evidence-based behavioral intervention for addiction recovery and urge management.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Discipline OS',
    description: 'Evidence-based behavioral intervention. Close the loop on urges.',
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }): React.JSX.Element {
  return <>{children}</>;
}
