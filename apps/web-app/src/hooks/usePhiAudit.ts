'use client';
import { useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import { logPhiRead } from '@/lib/api';

/**
 * Fire-and-forget PHI read audit hook.
 *
 * Fires once on mount for any PHI route. Records a PHI read event via
 * POST /api/audit/phi-read so the audit log correlator can cross-reference
 * the audit stream (6-year retention per CLAUDE.md Rule #6) with the app stream.
 *
 * Errors are silently swallowed — audit failures must not disrupt the user.
 */
export function usePhiAudit(routePath: string): void {
  const { getToken } = useAuth();
  useEffect(() => {
    let cancelled = false;
    async function fire(): Promise<void> {
      try {
        const token = await getToken();
        if (!cancelled && token !== null) {
          await logPhiRead(token, routePath);
        }
      } catch {
        // fire-and-forget: audit failures are non-fatal to UX
      }
    }
    void fire();
    return () => {
      cancelled = true;
    };
  }, [routePath, getToken]);
}
