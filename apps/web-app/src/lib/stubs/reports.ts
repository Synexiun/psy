'use client';

import { registerStubs } from './index';

export type ReportPeriod = {
  period_id: string;       // e.g. '2026-q1'
  label: string;           // e.g. 'Q1 2026'
  start_date: string;      // ISO date string
  end_date: string;
  phq9_start: number;
  phq9_end: number;
  phq9_rci_delta: number;  // positive = improvement
  gad7_start: number;
  gad7_end: number;
  gad7_rci_delta: number;
  resilience_days: number;
  urges_handled: number;
};

export type ReportsStubs = {
  periods: ReportPeriod[];
};

export const reportsStubs: ReportsStubs = {
  periods: [
    {
      period_id: '2026-q1',
      label: 'Q1 2026',
      start_date: '2026-01-01',
      end_date: '2026-03-31',
      phq9_start: 18,
      phq9_end: 11,
      phq9_rci_delta: 7,
      gad7_start: 15,
      gad7_end: 9,
      gad7_rci_delta: 6,
      resilience_days: 78,
      urges_handled: 31,
    },
    {
      period_id: '2025-q4',
      label: 'Q4 2025',
      start_date: '2025-10-01',
      end_date: '2025-12-31',
      phq9_start: 21,
      phq9_end: 18,
      phq9_rci_delta: 3,
      gad7_start: 17,
      gad7_end: 15,
      gad7_rci_delta: 2,
      resilience_days: 61,
      urges_handled: 24,
    },
  ],
};

registerStubs('reports', reportsStubs);
