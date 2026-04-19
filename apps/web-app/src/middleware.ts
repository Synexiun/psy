import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
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

/**
 * Composition order matters:
 *   1. Clerk gates on the auth boundary (redirecting to sign-in if needed).
 *   2. Locale negotiation runs on every request that passes the gate, so the
 *      redirect target is locale-prefixed correctly.
 *   3. The crisis path MUST remain public regardless of auth state — enforced
 *      via PUBLIC_ROUTES above.
 */
export default clerkMiddleware(async (auth, req) => {
  if (!isPublic(req)) {
    await auth.protect();
  }
  const intlResponse = intl(req);
  return intlResponse ?? NextResponse.next();
});

export const config = {
  matcher: ['/((?!api/webhooks|_next|_vercel|.*\\..*).*)', '/'],
};
