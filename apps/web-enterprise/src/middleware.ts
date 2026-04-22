import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
import { routing } from './i18n/routing';

const intl = createMiddleware(routing);

const isPublic = createRouteMatcher([
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
  '/:locale/crisis(.*)',
  '/api/health',
]);

/**
 * Enterprise middleware:
 *   1. Clerk auth gate.
 *   2. Require role=enterprise_admin on every non-public route.
 *   3. The server NEVER returns individual-level data to this surface; the k-anonymity
 *      guarantee (k ≥ 5) lives at the SQL view layer in discipline.analytics — middleware
 *      cannot undermine it. We still require admin role client-side to avoid leaking
 *      org-level headers to curious employees.
 */
export default clerkMiddleware(async (auth, req) => {
  if (isPublic(req)) {
    return intl(req);
  }

  auth.protect();

  const roles = ((await auth()).sessionClaims?.['roles'] as string[] | undefined) ?? [];
  if (!roles.includes('enterprise_admin')) {
    const url = req.nextUrl.clone();
    url.pathname = '/forbidden';
    return NextResponse.rewrite(url);
  }

  return intl(req);
});

export const config = {
  matcher: ['/((?!api/webhooks|_next|_vercel|.*\\..*).*)', '/'],
};
