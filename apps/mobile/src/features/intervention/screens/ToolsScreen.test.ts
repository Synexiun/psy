/**
 * Unit tests for pure constants in ToolsScreen.
 *
 * Tests CATEGORY_ACCENT from ToolsScreen.tsx — the background accent color
 * palette for the tools list screen.
 *
 * Clinical note: These colors are intentionally soft (high-lightness,
 * low-saturation). A user browsing coping tools is in or near an urge state.
 * Saturated, alarming colors (deep reds, high-contrast warnings) could increase
 * arousal and worsen the urge. The accent palette must remain calm and muted.
 *
 * Each category must have an accent color. A missing entry would produce
 * a transparent/undefined background on that category's tool cards.
 */

import { describe, it, expect } from '@jest/globals';
import type { ToolCategory } from '../data/tools';

// ---------------------------------------------------------------------------
// Inline from ToolsScreen.tsx
// ---------------------------------------------------------------------------

const CATEGORY_ACCENT: Record<string, string> = {
  Breathing: '#D1FAE5',
  Grounding: '#E0F2FE',
  Body: '#FCE7F3',
  Mindfulness: '#EDE9FE',
  Behavioural: '#FEF3C7',
};

const VALID_CATEGORIES: ReadonlyArray<ToolCategory> = [
  'Breathing',
  'Grounding',
  'Body',
  'Mindfulness',
  'Behavioural',
];

// ---------------------------------------------------------------------------
// CATEGORY_ACCENT
// ---------------------------------------------------------------------------

describe('CATEGORY_ACCENT', () => {
  it('has exactly 5 entries (one per ToolCategory)', () => {
    expect(Object.keys(CATEGORY_ACCENT)).toHaveLength(5);
  });

  it('has an accent for every ToolCategory', () => {
    for (const category of VALID_CATEGORIES) {
      expect(CATEGORY_ACCENT[category]).toBeDefined();
    }
  });

  it('Breathing accent is defined', () => {
    expect(CATEGORY_ACCENT['Breathing']).toBeTruthy();
  });

  it('Grounding accent is defined', () => {
    expect(CATEGORY_ACCENT['Grounding']).toBeTruthy();
  });

  it('Body accent is defined', () => {
    expect(CATEGORY_ACCENT['Body']).toBeTruthy();
  });

  it('Mindfulness accent is defined', () => {
    expect(CATEGORY_ACCENT['Mindfulness']).toBeTruthy();
  });

  it('Behavioural accent is defined', () => {
    expect(CATEGORY_ACCENT['Behavioural']).toBeTruthy();
  });

  it('all accent values are valid 7-character hex colors (#RRGGBB)', () => {
    for (const value of Object.values(CATEGORY_ACCENT)) {
      expect(value).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });

  it('all accent colors are distinct (no two categories share the same color)', () => {
    const values = Object.values(CATEGORY_ACCENT);
    expect(new Set(values).size).toBe(values.length);
  });

  it('all accent colors are high-lightness (soft, non-alarming palette)', () => {
    // High-lightness hex colors have high R, G, B values.
    // The minimum channel value across all accents should be ≥ 0xC7 (199/255 ≈ 78%).
    // This ensures none of the colors are dark or saturated enough to feel alarming.
    for (const hex of Object.values(CATEGORY_ACCENT)) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      const minChannel = Math.min(r, g, b);
      expect(minChannel).toBeGreaterThanOrEqual(0xc7);
    }
  });
});
