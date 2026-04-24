import createNextIntlPlugin from 'next-intl/plugin';
import bundleAnalyzer from '@next/bundle-analyzer';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');
const withBundleAnalyzer = bundleAnalyzer({ enabled: process.env.ANALYZE === 'true' });

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  transpilePackages: [
    '@disciplineos/design-system',
    '@disciplineos/i18n-catalog',
    '@disciplineos/api-client',
    '@disciplineos/safety-directory',
  ],
  typedRoutes: true,
  async headers() {
    // Content-Security-Policy is intentionally absent here.
    // It is set dynamically per-request by middleware.ts using a cryptographic
    // nonce, which makes 'unsafe-inline' in script-src unnecessary.
    // A static CSP here would lack the nonce and would be overridden by the
    // middleware header anyway — keeping it would only create confusion.
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(self), geolocation=()' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
        ],
      },
    ];
  },
};

export default withBundleAnalyzer(withNextIntl(nextConfig));
