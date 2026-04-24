import type { Metadata } from 'next';
import React from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'Discipline OS · Crisis support',
  description:
    'If you are in crisis, you are not alone. Hotline numbers and local emergency contacts for your country.',
  robots: { index: true, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // lang and dir are set per-locale on the wrapper <div> in [locale]/layout.tsx.
  // The root layout is a structural shell only; no static lang attr here to avoid
  // overriding the per-locale values that the static export generates.
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
