'use client';

/**
 * ThemeSync — side-effect-only Client Component.
 *
 * Watches the resolved theme from next-themes and mirrors it to the Clerk
 * user's `unsafeMetadata.theme` so the preference can be restored server-side
 * on the next authenticated session.
 *
 * Renders null — no DOM output.
 */

import { useEffect } from 'react';
import { useTheme } from 'next-themes';
import { useUser } from '@clerk/nextjs';

export function ThemeSync(): null {
  const { resolvedTheme } = useTheme();
  const { user } = useUser();

  useEffect(() => {
    // Guard: user not yet loaded or not signed in.
    if (!user || resolvedTheme === undefined) return;

    // Guard: metadata already matches — skip the unnecessary write.
    const storedTheme = user.unsafeMetadata['theme'];
    if (typeof storedTheme === 'string' && storedTheme === resolvedTheme) return;

    // Fire-and-forget: theme preference is non-critical UI state.
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    void user.update({
      unsafeMetadata: { ...user.unsafeMetadata, theme: resolvedTheme },
    });
  }, [resolvedTheme, user]);

  return null;
}
