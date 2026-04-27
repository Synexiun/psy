'use client';
/**
 * Returns a deterministically selected compassion template.
 *
 * Selection is by day-of-week (new Date().getDay() % templates.length) to be
 * stable within a day without being truly random. In Phase 5, the backend
 * selects the template server-side via discipline/clinical/compassion_templates.py;
 * this client fallback mirrors that determinism.
 *
 * RULE #4: template text is loaded from the JSON catalog, never hand-rolled here.
 */

import templates from '@/data/relapse_templates.json';

export interface RelapseTemplate {
  id: string;
  text: string;
  tags: string[];
  status: string;
}

export interface CompanionState {
  template: RelapseTemplate;
}

export function useCompanion(): CompanionState {
  const activeTemplates = (templates.templates as RelapseTemplate[]).filter(
    (t) => t.status === 'draft' || t.status === 'active',
  );
  if (activeTemplates.length === 0) {
    return {
      template: {
        id: 'fallback',
        text: 'You are not alone. Take one step at a time.',
        tags: [],
        status: 'active',
      },
    };
  }
  const idx = new Date().getDay() % activeTemplates.length;
  const template = activeTemplates[idx] ?? activeTemplates[0] ?? {
    id: 'fallback',
    text: 'You are not alone. Take one step at a time.',
    tags: [],
    status: 'active',
  };
  return { template };
}
