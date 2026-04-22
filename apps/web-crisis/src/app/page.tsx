import React from 'react';

/**
 * Root path — static export fallback.
 *
 * In production, the CDN (CloudFront/S3) redirects / → /en/ at the edge.
 * This page exists so the static export builds without error and provides
 * a manual fallback link if a user lands here without the redirect.
 */
export default function RootPage() {
  return (
    <main className="mx-auto max-w-2xl px-5 py-8">
      <p>
        <a href="/en/" className="underline">
          Go to crisis support (English)
        </a>
      </p>
    </main>
  );
}
