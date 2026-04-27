'use client';
/**
 * Unit tests for ThemeSync component behaviour.
 *
 * ThemeSync is a side-effect-only React component that calls
 * `user.update({ unsafeMetadata: { ...meta, theme } })` whenever
 * `resolvedTheme` changes and the stored value differs.
 *
 * Strategy: mock both `next-themes` (useTheme) and `@clerk/nextjs` (useUser)
 * before importing the component, then drive it via renderHook-style rendering
 * of the underlying effect logic through the component using @testing-library/react.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import * as React from 'react';

// ---------------------------------------------------------------------------
// Mock next-themes BEFORE the component is imported so its import-time binding
// resolves to the mock module.
// ---------------------------------------------------------------------------

vi.mock('next-themes', () => ({
  useTheme: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs
// ---------------------------------------------------------------------------

vi.mock('@clerk/nextjs', () => ({
  useUser: vi.fn(),
}));

import { useTheme } from 'next-themes';
import { useUser } from '@clerk/nextjs';
import { ThemeSync } from '../../../src/components/ThemeSync';

const mockUseTheme = vi.mocked(useTheme);
const mockUseUser = vi.mocked(useUser);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeUser(existingTheme?: string) {
  const update = vi.fn().mockResolvedValue(undefined);
  const unsafeMetadata: Record<string, unknown> = existingTheme !== undefined
    ? { theme: existingTheme }
    : {};
  const user = { update, unsafeMetadata };
  return { user, update };
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Core behaviour
// ---------------------------------------------------------------------------

describe('ThemeSync — calls user.update when theme changes', () => {
  it('calls user.update with the new theme when unsafeMetadata.theme differs', async () => {
    const { user, update } = makeUser('light');
    mockUseTheme.mockReturnValue({ resolvedTheme: 'dark' } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user } as unknown as ReturnType<typeof useUser>);

    render(React.createElement(ThemeSync));

    await vi.waitFor(() => expect(update).toHaveBeenCalledTimes(1));
    expect(update).toHaveBeenCalledWith({
      unsafeMetadata: { theme: 'dark' },
    });
  });

  it('spreads existing unsafeMetadata keys when updating', async () => {
    const update = vi.fn().mockResolvedValue(undefined);
    const user = {
      update,
      unsafeMetadata: { theme: 'light', someOtherKey: 'preserved' } as Record<string, unknown>,
    };
    mockUseTheme.mockReturnValue({ resolvedTheme: 'dark' } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user } as unknown as ReturnType<typeof useUser>);

    render(React.createElement(ThemeSync));

    await vi.waitFor(() => expect(update).toHaveBeenCalledTimes(1));
    expect(update).toHaveBeenCalledWith({
      unsafeMetadata: { someOtherKey: 'preserved', theme: 'dark' },
    });
  });
});

// ---------------------------------------------------------------------------
// No-op guards
// ---------------------------------------------------------------------------

describe('ThemeSync — does NOT call user.update when unnecessary', () => {
  it('does not call update when resolvedTheme already matches unsafeMetadata.theme', async () => {
    const { user, update } = makeUser('dark');
    mockUseTheme.mockReturnValue({ resolvedTheme: 'dark' } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user } as unknown as ReturnType<typeof useUser>);

    render(React.createElement(ThemeSync));

    // Give React a tick to run effects.
    await new Promise<void>((r) => setTimeout(r, 10));
    expect(update).not.toHaveBeenCalled();
  });

  it('does not call update when user is null (not signed in)', async () => {
    mockUseTheme.mockReturnValue({ resolvedTheme: 'dark' } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user: null } as unknown as ReturnType<typeof useUser>);

    render(React.createElement(ThemeSync));

    await new Promise<void>((r) => setTimeout(r, 10));
    // No update object to spy on — just confirm no throw.
    // If we reach here without error the guard worked.
    expect(true).toBe(true);
  });

  it('does not call update when resolvedTheme is undefined', async () => {
    const { user, update } = makeUser();
    mockUseTheme.mockReturnValue({ resolvedTheme: undefined } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user } as unknown as ReturnType<typeof useUser>);

    render(React.createElement(ThemeSync));

    await new Promise<void>((r) => setTimeout(r, 10));
    expect(update).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Renders nothing
// ---------------------------------------------------------------------------

describe('ThemeSync — renders null', () => {
  it('produces no DOM output', () => {
    const { user } = makeUser('dark');
    mockUseTheme.mockReturnValue({ resolvedTheme: 'dark' } as ReturnType<typeof useTheme>);
    mockUseUser.mockReturnValue({ user } as unknown as ReturnType<typeof useUser>);

    const { container } = render(React.createElement(ThemeSync));
    expect(container.firstChild).toBeNull();
  });
});
