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

const isPhiBoundary = createRouteMatcher([
  '/:locale/clients/:id(.*)',
  '/:locale/sessions(.*)',
]);

/**
 * Clinician middleware:
 *   1. Gate at auth (Clerk).
 *   2. Enforce role=clinician claim on any protected route.
 *   3. Mark PHI-boundary responses with a header the audit-logging service picks up;
 *      actual PHI enforcement lives server-side in discipline.clinician — this header
 *      just annotates the request class.
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
  if (!roles.includes('clinician')) {
    const url = req.nextUrl.clone();
    url.pathname = '/forbidden';
    return NextResponse.rewrite(url);
  }

  const intlResponse = intl(req);
  const response = intlResponse ?? NextResponse.next();

  if (isPhiBoundary(req)) {
    response.headers.set('X-Phi-Boundary', '1');
  }
  return response;
});

export const config = {
  matcher: ['/((?!api/webhooks|_next|_vercel|.*\\..*).*)', '/'],
};
