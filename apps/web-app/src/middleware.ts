import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import createMiddleware from 'next-intl/middleware';
import { NextResponse, NextRequest } from 'next/server';

import { routing } from './i18n/routing';

const intl = createMiddleware(routing);

const PUBLIC_ROUTES = [
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
  '/:locale/sign-up(.*)',
  '/:locale/crisis(.*)',
  '/api/health',
];

const isPublic = createRouteMatcher(PUBLIC_ROUTES);

const PHI_ROUTES = [
  '/:locale/check-in(.*)',
  '/:locale/reports(.*)',
  '/:locale/assessments/history(.*)',
  '/:locale/journal(.*)',
  '/:locale/patterns(.*)',
];

const isPhiRoute = createRouteMatcher(PHI_ROUTES);

/**
 * Build a per-request Content-Security-Policy with a cryptographic nonce.
 * The nonce is forwarded to the layout via the `x-nonce` request header so
 * Server Components can inject it into <Script> tags and <ClerkProvider>.
 *
 * `'unsafe-inline'` is intentionally retained in style-src — Tailwind's
 * runtime CSS-in-JS approach requires it and it does not create a script
 * injection vector.
 */
function buildCsp(nonce: string): string {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' https://*.clerk.accounts.dev https://challenges.cloudflare.com`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.clerk.accounts.dev https://api.disciplineos.com",
    "frame-src https://challenges.cloudflare.com",
    "worker-src 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');
}

/**
 * Composition order matters:
 *   1. Nonce is generated first so it can be embedded in the CSP header that
 *      wraps every downstream response — including Clerk's injected scripts.
 *   2. Clerk gates on the auth boundary (redirecting to sign-in if needed).
 *   3. Locale negotiation runs on every request that passes the gate, so the
 *      redirect target is locale-prefixed correctly.
 *   4. The crisis path MUST remain public regardless of auth state — enforced
 *      via PUBLIC_ROUTES above.
 */
export default clerkMiddleware((auth, req) => {
  // Generate a fresh base64-encoded nonce for every request.
  // crypto.randomUUID() is available in the Next.js Edge runtime globally.
  const nonce = btoa(crypto.randomUUID());

  // Forward the nonce to Server Components via a request header.
  const requestHeaders = new Headers(req.headers);
  requestHeaders.set('x-nonce', nonce);

  if (!isPublic(req)) {
    auth.protect();
  }

  // Run next-intl with the augmented request headers.
  const intlResponse = intl(
    new NextRequest(req.url, { headers: requestHeaders, method: req.method }),
  );

  // Attach the CSP header to whatever response next-intl produced (could be a
  // redirect or a rewrite — we always want the nonce-based policy on it).
  const response = intlResponse ?? NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set('Content-Security-Policy', buildCsp(nonce));
  if (isPhiRoute(req)) {
    response.headers.set('X-Phi-Boundary', '1');
  }
  return response;
});

export const config = {
  matcher: ['/((?!api/webhooks|_next|_vercel|.*\\..*).*)', '/'],
};
