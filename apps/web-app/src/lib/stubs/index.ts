/**
 * Stub registry — a type-safe in-memory store for deterministic test / Storybook
 * data. Each domain registers its stubs once at import time; components call
 * `getStub(domain, key)` to read them.
 *
 * Adding a new domain:
 *   1. Create `apps/web-app/src/lib/stubs/<domain>.ts` exporting `<Domain>Stubs`.
 *   2. Add the domain key and type to `StubRegistry` below.
 *   3. Call `registerStubs('<domain>', <domain>Stubs)` in the domain file or a
 *      barrel import.
 */

import type { CheckInStubs } from './check-in';
import type { CompanionStubs } from './companion';
import type { ReportsStubs } from './reports';

// ---------------------------------------------------------------------------
// Registry shape
// ---------------------------------------------------------------------------

type StubRegistry = {
  'check-in': CheckInStubs;
  'companion': CompanionStubs;
  'reports': ReportsStubs;
};

// ---------------------------------------------------------------------------
// Internal store
// ---------------------------------------------------------------------------

const registry: Partial<Record<keyof StubRegistry, unknown>> = {};

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Register stubs for a domain. Call once at module load time.
 * Re-registering a domain overwrites the previous value.
 */
export function registerStubs<K extends keyof StubRegistry>(
  domain: K,
  stubs: StubRegistry[K],
): void {
  registry[domain] = stubs;
}

/**
 * Retrieve a single stub value by domain and key.
 *
 * Returns `undefined` if the domain has not been registered yet — callers must
 * handle the undefined case (or call `registerStubs` before `getStub`).
 */
export function getStub<K extends keyof StubRegistry, Key extends keyof StubRegistry[K]>(
  domain: K,
  key: Key,
): StubRegistry[K][Key] | undefined {
  const domainStubs = registry[domain] as StubRegistry[K] | undefined;
  return domainStubs?.[key];
}
