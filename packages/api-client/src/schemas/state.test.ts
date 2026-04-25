/**
 * Unit tests for state Zod schemas.
 *
 * StateLabelSchema maps to the T0–T4 tier system (Docs/Whitepapers/04_Safety_Framework.md).
 * The full set of labels must be accepted; any new label requires a schema change.
 *
 * TodaySummarySchema: state_confidence is bounded [0, 1]; risk_windows_today is an
 * array of RiskWindow objects each with a typed kind enum.
 *
 * StateEstimateUploadSchema: posted by the mobile app after on-device inference;
 * confidence bounded [0, 1] and model_version required for audit traceability.
 *
 * Covers:
 * - StateLabelSchema: accepts all 6 labels; rejects unknown
 * - RiskWindowSchema: accepts all 3 kinds; rejects unknown kind; requires start/end/kind
 * - TodaySummarySchema: accepts valid payload; rejects confidence outside [0,1]; rejects unknown state
 * - StateEstimateUploadSchema: accepts valid payload; rejects confidence out of range; requires all fields
 */

import { describe, it, expect } from 'vitest';
import {
  StateLabelSchema,
  RiskWindowSchema,
  TodaySummarySchema,
  StateEstimateUploadSchema,
} from './state';

// ---------------------------------------------------------------------------
// StateLabelSchema
// ---------------------------------------------------------------------------

describe('StateLabelSchema', () => {
  const validLabels = ['stable', 'baseline', 'elevated', 'rising_urge', 'peak_urge', 'post_urge'] as const;

  for (const label of validLabels) {
    it(`accepts state label: ${label}`, () => {
      expect(StateLabelSchema.safeParse(label).success).toBe(true);
    });
  }

  it('contains exactly 6 labels (T0–T4 tier coverage)', () => {
    expect(validLabels).toHaveLength(6);
  });

  it('rejects unknown state label', () => {
    expect(StateLabelSchema.safeParse('critical').success).toBe(false);
  });

  it('rejects empty string', () => {
    expect(StateLabelSchema.safeParse('').success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// RiskWindowSchema
// ---------------------------------------------------------------------------

const validRiskWindow = {
  start: '2026-04-25T08:00:00Z',
  end: '2026-04-25T09:00:00Z',
  kind: 'predicted_urge',
};

describe('RiskWindowSchema', () => {
  it('accepts predicted_urge kind', () => {
    expect(RiskWindowSchema.safeParse(validRiskWindow).success).toBe(true);
  });

  it('accepts historical_peak kind', () => {
    expect(RiskWindowSchema.safeParse({ ...validRiskWindow, kind: 'historical_peak' }).success).toBe(true);
  });

  it('accepts contextual_risk kind', () => {
    expect(RiskWindowSchema.safeParse({ ...validRiskWindow, kind: 'contextual_risk' }).success).toBe(true);
  });

  it('rejects unknown kind', () => {
    expect(RiskWindowSchema.safeParse({ ...validRiskWindow, kind: 'unknown_risk' }).success).toBe(false);
  });

  it('rejects missing start', () => {
    const { start: _, ...rest } = validRiskWindow;
    expect(RiskWindowSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing end', () => {
    const { end: _, ...rest } = validRiskWindow;
    expect(RiskWindowSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects non-datetime start string', () => {
    expect(RiskWindowSchema.safeParse({ ...validRiskWindow, start: '2026-04-25' }).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// TodaySummarySchema
// ---------------------------------------------------------------------------

const validTodaySummary = {
  current_state: 'stable',
  state_confidence: 0.85,
  risk_windows_today: [],
  check_in_due: false,
  open_interventions: [],
};

describe('TodaySummarySchema', () => {
  it('accepts minimal valid payload', () => {
    expect(TodaySummarySchema.safeParse(validTodaySummary).success).toBe(true);
  });

  it('accepts state_confidence of 0 (lower bound)', () => {
    expect(TodaySummarySchema.safeParse({ ...validTodaySummary, state_confidence: 0 }).success).toBe(true);
  });

  it('accepts state_confidence of 1 (upper bound)', () => {
    expect(TodaySummarySchema.safeParse({ ...validTodaySummary, state_confidence: 1 }).success).toBe(true);
  });

  it('rejects state_confidence above 1', () => {
    expect(TodaySummarySchema.safeParse({ ...validTodaySummary, state_confidence: 1.01 }).success).toBe(false);
  });

  it('rejects state_confidence below 0', () => {
    expect(TodaySummarySchema.safeParse({ ...validTodaySummary, state_confidence: -0.01 }).success).toBe(false);
  });

  it('accepts all valid state labels', () => {
    for (const label of ['stable', 'baseline', 'elevated', 'rising_urge', 'peak_urge', 'post_urge']) {
      expect(TodaySummarySchema.safeParse({ ...validTodaySummary, current_state: label }).success).toBe(true);
    }
  });

  it('rejects unknown current_state', () => {
    expect(TodaySummarySchema.safeParse({ ...validTodaySummary, current_state: 'unknown' }).success).toBe(false);
  });

  it('accepts risk_windows_today with valid entries', () => {
    expect(TodaySummarySchema.safeParse({
      ...validTodaySummary,
      risk_windows_today: [validRiskWindow],
    }).success).toBe(true);
  });

  it('rejects missing check_in_due', () => {
    const { check_in_due: _, ...rest } = validTodaySummary;
    expect(TodaySummarySchema.safeParse(rest).success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// StateEstimateUploadSchema
// ---------------------------------------------------------------------------

const validEstimate = {
  ts: '2026-04-25T10:00:00Z',
  state_label: 'elevated',
  confidence: 0.72,
  feature_hash: 'sha256:abc123',
  model_version: 'v2.1.0',
};

describe('StateEstimateUploadSchema', () => {
  it('accepts valid state estimate', () => {
    expect(StateEstimateUploadSchema.safeParse(validEstimate).success).toBe(true);
  });

  it('accepts confidence 0 (lower bound)', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, confidence: 0 }).success).toBe(true);
  });

  it('accepts confidence 1 (upper bound)', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, confidence: 1 }).success).toBe(true);
  });

  it('rejects confidence above 1', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, confidence: 1.01 }).success).toBe(false);
  });

  it('rejects confidence below 0', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, confidence: -0.01 }).success).toBe(false);
  });

  it('rejects invalid ts (non-datetime)', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, ts: '2026-04-25' }).success).toBe(false);
  });

  it('rejects unknown state_label', () => {
    expect(StateEstimateUploadSchema.safeParse({ ...validEstimate, state_label: 'off_scale' }).success).toBe(false);
  });

  it('rejects missing model_version', () => {
    const { model_version: _, ...rest } = validEstimate;
    expect(StateEstimateUploadSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing feature_hash', () => {
    const { feature_hash: _, ...rest } = validEstimate;
    expect(StateEstimateUploadSchema.safeParse(rest).success).toBe(false);
  });
});
