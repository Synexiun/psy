'use client';
// Re-exports the patterns query hook so patterns pages have a clean import path.
// In Phase 5, this may add patterns-specific query params (filter by status, pagination).
export { usePatterns } from '@/hooks/useDashboardData';
export type { PatternData } from '@/hooks/useDashboardData';
