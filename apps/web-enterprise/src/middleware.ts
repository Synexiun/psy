import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
import { routing } from './i18n/routing';

const intl = createMiddleware(routing);

const isPublic = createRouteMatcher([
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
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
    const intlResponse = intl(req);
    return intlResponse ?? NextResponse.next();
  }

  const { userId, sessionClaims } = await auth();
  if (!userId) {
    await auth.protect();
  }

  const roles = (sessionClaims?.['roles'] as string[] | undefined) ?? [];
  if (!roles.includes('enterprise_admin')) {
    const url = req.nextUrl.clone();
    url.pathname = '/forbidden';
    return NextResponse.rewrite(url);
  }

  const intlResponse = intl(req);
  return intlResponse ?? NextResponse.next();
});

export const config = {
  matcher: ['/((?!api/webhooks|_next|_vercel|.*\\..*).*)', '/'],
};
