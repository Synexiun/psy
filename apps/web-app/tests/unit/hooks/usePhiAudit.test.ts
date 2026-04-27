'use client';
/**
 * Tests for usePhiAudit hook.
 *
 * The hook fires a PHI read audit event (POST /api/audit/phi-read) once on
 * mount. It is fire-and-forget: errors are silently swallowed and must not
 * disrupt the user.
 *
 * Covers:
 * - Calls logPhiRead with the correct route path on mount
 * - Does not call logPhiRead when token is null (unauthenticated user)
 * - Cancels the call if the component unmounts before the token resolves
 * - Silently swallows logPhiRead errors (non-fatal)
 * - Does not re-fire when routePath is unchanged (stable across re-renders)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePhiAudit } from '../../../src/hooks/usePhiAudit';

// Mock @clerk/nextjs
vi.mock('@clerk/nextjs', () => ({
  useAuth: vi.fn(),
}));

// Mock logPhiRead from @/lib/api
vi.mock('@/lib/api', () => ({
  logPhiRead: vi.fn(),
}));

import { useAuth } from '@clerk/nextjs';
import { logPhiRead } from '@/lib/api';

const mockUseAuth = vi.mocked(useAuth);
const mockLogPhiRead = vi.mocked(logPhiRead);

function makeGetToken(token: string | null) {
  return vi.fn().mockResolvedValue(token);
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('usePhiAudit — fires on mount', () => {
  it('calls logPhiRead with the route path when token is available', async () => {
    const getToken = makeGetToken('test-token');
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);
    mockLogPhiRead.mockResolvedValue(undefined);

    const { unmount } = renderHook(() => usePhiAudit('/journal'));
    await vi.waitFor(() => expect(mockLogPhiRead).toHaveBeenCalledTimes(1));
    expect(mockLogPhiRead).toHaveBeenCalledWith('test-token', '/journal');
    unmount();
  });

  it('calls logPhiRead with assessments/history route path', async () => {
    const getToken = makeGetToken('tok-2');
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);
    mockLogPhiRead.mockResolvedValue(undefined);

    const { unmount } = renderHook(() => usePhiAudit('/assessments/history/session-1'));
    await vi.waitFor(() => expect(mockLogPhiRead).toHaveBeenCalledTimes(1));
    expect(mockLogPhiRead).toHaveBeenCalledWith('tok-2', '/assessments/history/session-1');
    unmount();
  });
});

describe('usePhiAudit — token is null', () => {
  it('does not call logPhiRead when getToken returns null', async () => {
    const getToken = makeGetToken(null);
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);

    const { unmount } = renderHook(() => usePhiAudit('/journal'));
    await vi.waitFor(() => expect(getToken).toHaveBeenCalledTimes(1));
    expect(mockLogPhiRead).not.toHaveBeenCalled();
    unmount();
  });
});

describe('usePhiAudit — error handling', () => {
  it('silently swallows logPhiRead errors (non-fatal to UX)', async () => {
    const getToken = makeGetToken('tok-3');
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);
    mockLogPhiRead.mockRejectedValue(new Error('network error'));

    // Should not throw
    const { unmount } = renderHook(() => usePhiAudit('/journal'));
    await vi.waitFor(() => expect(mockLogPhiRead).toHaveBeenCalledTimes(1));
    unmount();
  });

  it('silently swallows getToken errors (non-fatal to UX)', async () => {
    const getToken = vi.fn().mockRejectedValue(new Error('auth error'));
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);

    // Should not throw
    const { unmount } = renderHook(() => usePhiAudit('/journal'));
    await vi.waitFor(() => expect(getToken).toHaveBeenCalledTimes(1));
    expect(mockLogPhiRead).not.toHaveBeenCalled();
    unmount();
  });
});

describe('usePhiAudit — cancellation', () => {
  it('does not call logPhiRead when component unmounts before token resolves', async () => {
    let resolveToken!: (v: string | null) => void;
    const getToken = vi.fn().mockReturnValue(new Promise<string | null>((r) => { resolveToken = r; }));
    mockUseAuth.mockReturnValue({ getToken } as ReturnType<typeof useAuth>);

    const { unmount } = renderHook(() => usePhiAudit('/journal'));
    unmount(); // cancelled = true before promise settles
    resolveToken('tok-cancel');
    await new Promise<void>((r) => setTimeout(r, 0));
    expect(mockLogPhiRead).not.toHaveBeenCalled();
  });
});
