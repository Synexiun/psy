'use client';
// Returns stub report periods. In Phase 5, replace with useQuery against /v1/reports/periods.
import { reportsStubs } from '@/lib/stubs/reports';
import type { ReportPeriod } from '@/lib/stubs/reports';

export function useReports(): { periods: ReportPeriod[]; isLoading: boolean } {
  return { periods: reportsStubs.periods, isLoading: false };
}

export function useReportDetail(periodId: string): { period: ReportPeriod | undefined; isLoading: boolean } {
  const period = reportsStubs.periods.find((p) => p.period_id === periodId);
  return { period, isLoading: false };
}
