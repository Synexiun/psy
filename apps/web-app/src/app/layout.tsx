import type { Metadata } from 'next';
import { Providers } from '@/components/Providers';

export const metadata: Metadata = {
  metadataBase: new URL('https://app.disciplineos.com'),
  title: {
    default: 'Discipline OS',
    template: '%s · Discipline OS',
  },
  description:
    'Close the loop on urges. Evidence-based intervention delivered in the critical 60-second window.',
  applicationName: 'Discipline OS',
  keywords: ['behavioral health', 'addiction recovery', 'urge management', 'mental health'],
  authors: [{ name: 'Discipline OS' }],
  robots: { index: false, follow: false }, // app is auth-gated — never index
  manifest: '/manifest.webmanifest',
  icons: {
    icon: '/icons/icon-192.png',
    apple: '/icons/icon-192.png',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Discipline OS',
  },
  formatDetection: { telephone: false },
};

// Root layout intentionally contains no locale-specific chrome — that lives in
// [locale]/layout.tsx.  ClerkProvider (which needs the nonce) is also rendered
// in the locale layout, so nonce reading is collocated there.
export default function RootLayout({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <html suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
