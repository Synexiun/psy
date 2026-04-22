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
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
