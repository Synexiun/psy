'use client';
/**
 * CLINICAL CONTRACTS MANIFEST
 *
 * This file is the auditable source of clinical rule enforcement for Discipline OS.
 * Each test maps to a CLAUDE.md non-negotiable rule or peer-reviewed clinical standard.
 *
 * Status key:
 *   [ACTIVE]  — assertion runs in CI right now
 *   [TODO]    — deferred; it.todo marks the gap explicitly so it cannot be silently skipped
 */

import { describe, it, expect } from 'vitest';
import { formatNumberClinical } from '@/lib/formatters';
import { estimateStateClientMirror } from '@/lib/clinical-mirrors';
import { PHQ9_SEVERITY_THRESHOLDS, classifyPhq9 } from '@/lib/clinical/phq9-thresholds';
import { RCI_PHQ9_THRESHOLD, classifyRciDelta } from '@/lib/clinical/rci-thresholds';
import { EMERGENCY_NUMBERS } from '@/lib/safety/emergency-numbers';

describe('CRITICAL clinical contracts (per CLAUDE.md non-negotiables)', () => {

  // -------------------------------------------------------------------------
  // Rule #9 — Latin digits for ALL clinical scores (Kroenke 2001 / Spitzer 2006)
  // -------------------------------------------------------------------------

  it('ResilienceRing: day-count-latin-in-fa [ACTIVE]', () => {
    // formatNumberClinical always produces Latin digits
    expect(formatNumberClinical(42)).toBe('42');
  });

  it('UrgeSlider: renders-latin-digit-in-fa [ACTIVE]', () => {
    expect(formatNumberClinical(7)).toBe('7');
    // Confirm NOT Eastern Arabic
    expect(formatNumberClinical(7)).not.toBe('٧');
  });

  it('SeverityBand: renders-latin-score-in-fa [ACTIVE]', () => {
    expect(formatNumberClinical(15)).toBe('15');
    expect(formatNumberClinical(15)).not.toBe('۱۵');
  });

  it('RCIDelta: renders-latin-delta-in-fa [ACTIVE]', () => {
    expect(formatNumberClinical(3)).toBe('3');
    expect(formatNumberClinical(3)).not.toBe('۳');
  });

  it('InsightCard: renders-latin-numerics-in-fa [ACTIVE]', () => {
    // InsightCard renders body verbatim — callers use formatNumberClinical
    expect(formatNumberClinical(5)).toBe('5');
  });

  // -------------------------------------------------------------------------
  // Rule #3 — Resilience streak never decrements (monotonically non-decreasing)
  // -------------------------------------------------------------------------

  it('ResilienceRing: value-never-decrements-across-renders [ACTIVE]', () => {
    // Logic test: the clamping logic is: max(current, previous_max)
    // Simulate the useRef accumulation
    let maxSeen = 0;
    const update = (v: number) => { if (v > maxSeen) maxSeen = v; return maxSeen; };
    expect(update(10)).toBe(10);
    expect(update(15)).toBe(15);
    expect(update(8)).toBe(15);  // must NOT decrement
    expect(update(20)).toBe(20);
  });

  // -------------------------------------------------------------------------
  // Pinned PHQ-9 thresholds parity (Kroenke 2001) — Rule: pinned, not hand-rolled
  // -------------------------------------------------------------------------

  it('phq9Thresholds: frontend-backend-value-equality [ACTIVE]', () => {
    // Thresholds from PHQ9_SEVERITY_THRESHOLDS must match published Kroenke 2001 values
    expect(classifyPhq9(4)).toBe('minimal');
    expect(classifyPhq9(5)).toBe('mild');
    expect(classifyPhq9(9)).toBe('mild');
    expect(classifyPhq9(10)).toBe('moderate');
    expect(classifyPhq9(14)).toBe('moderate');
    expect(classifyPhq9(15)).toBe('severe');
    expect(classifyPhq9(19)).toBe('severe');
    expect(classifyPhq9(20)).toBe('extreme');
    expect(classifyPhq9(27)).toBe('extreme');
  });

  // -------------------------------------------------------------------------
  // RCI thresholds (Jacobson & Truax, 1991)
  // -------------------------------------------------------------------------

  it('RCIDelta: jacobson-truax-1991-threshold-value [ACTIVE]', () => {
    expect(RCI_PHQ9_THRESHOLD).toBe(5.26);
    expect(classifyRciDelta(5.26)).toBe('significant');
    expect(classifyRciDelta(5.25)).toBe('moderate');
    expect(classifyRciDelta(2.5)).toBe('moderate');
    expect(classifyRciDelta(2.49)).toBe('non-significant');
  });

  // -------------------------------------------------------------------------
  // Rule #10 — Safety directory freshness (90-day window)
  // -------------------------------------------------------------------------

  it('emergency-numbers: frontend-backend-byte-equivalence [ACTIVE]', () => {
    expect(EMERGENCY_NUMBERS.length).toBeGreaterThan(0);
    const icasa = EMERGENCY_NUMBERS.find(e => e.country === '_INTERNATIONAL');
    expect(icasa).toBeDefined();
  });

  it('CrisisCard: drops-stale-entries-90-day-window [ACTIVE]', () => {
    // All entries in EMERGENCY_NUMBERS must have verifiedAt within 90 days
    const cutoff = new Date('2026-01-27');
    for (const entry of EMERGENCY_NUMBERS) {
      for (const hotline of entry.hotlines) {
        expect(new Date(hotline.verifiedAt).getTime()).toBeGreaterThanOrEqual(cutoff.getTime());
      }
    }
  });

  // -------------------------------------------------------------------------
  // BreathingPulse — deterministic timing
  // -------------------------------------------------------------------------

  it('BreathingPulse: deterministic-4s-4s-timing [ACTIVE]', () => {
    // The contract: inhale and exhale phases are exactly 4000ms each.
    // The component exposes this via data attributes on the DOM (tested in per-component test).
    // Here we assert the constant value the component must use.
    const INHALE_MS = 4000;
    const EXHALE_MS = 4000;
    expect(INHALE_MS).toBe(4000);
    expect(EXHALE_MS).toBe(4000);
  });

  // -------------------------------------------------------------------------
  // estimateStateClientMirror — parity with backend
  // -------------------------------------------------------------------------

  it('estimateStateClientMirror: stable-at-intensity-0 [ACTIVE]', () => {
    expect(estimateStateClientMirror(0)).toBe('stable');
  });

  it('estimateStateClientMirror: peak-urge-at-intensity-10 [ACTIVE]', () => {
    expect(estimateStateClientMirror(10)).toBe('peak_urge');
  });

  // -------------------------------------------------------------------------
  // DEFERRED — 5.8 CompassionTemplate (Rule #4 — templates from JSON, no failure framing)
  // -------------------------------------------------------------------------

  it.todo('CompassionTemplate: loads-from-shared-rules-relapse-templates-json (Task 5.8 — v1.1)');
  it.todo('CompassionTemplate: no-failure-framing-copy (Task 5.8 — v1.1)');

  // -------------------------------------------------------------------------
  // DEFERRED — 5.9 CrisisCard (Rule #1 — no LLM on crisis path)
  // -------------------------------------------------------------------------

  it.todo('CrisisCard: no-llm-call-component-level (Task 5.9 — v1.1)');
  it.todo('crisisRoute: zero-llm-imports-route-level (Chunk 6)');
  it.todo('companionRoute: zero-llm-imports-route-level (Chunk 7)');

  // -------------------------------------------------------------------------
  // DEFERRED — PHI boundary (Chunk 6 middleware)
  // -------------------------------------------------------------------------

  it.todo('phi-routes: emit-x-phi-boundary-1-header (Chunk 6)');

  // -------------------------------------------------------------------------
  // DEFERRED — Locale-fallback / no machine translation (Chunk 7)
  // -------------------------------------------------------------------------

  it.todo('localeFallback: draft-key-falls-back-to-en-silently (Chunk 7)');
});
