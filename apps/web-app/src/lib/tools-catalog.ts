'use client';

export type ToolCategory = 'breathing' | 'grounding' | 'body' | 'mindfulness';

export type ToolCatalogKey =
  | 'boxBreathing'
  | 'grounding54321'
  | 'pmr'
  | 'coldWater'
  | 'urgeSurfing'
  | 'stopTechnique'
  | 'compassionMeditation'
  | 'delayDistract';

export interface CopingTool {
  id: string;
  catalogKey: ToolCatalogKey;
  category: ToolCategory;
  featured?: boolean;
}

export const TOOLS: CopingTool[] = [
  { id: 'box-breathing', catalogKey: 'boxBreathing', category: 'breathing', featured: true },
  { id: '5-4-3-2-1-grounding', catalogKey: 'grounding54321', category: 'grounding' },
  { id: 'progressive-muscle-relaxation', catalogKey: 'pmr', category: 'body' },
  { id: 'cold-water-reset', catalogKey: 'coldWater', category: 'body' },
  { id: 'urge-surfing', catalogKey: 'urgeSurfing', category: 'mindfulness' },
  { id: 'stop-technique', catalogKey: 'stopTechnique', category: 'mindfulness' },
  { id: 'compassion-meditation', catalogKey: 'compassionMeditation', category: 'mindfulness' },
  { id: 'delay-and-distract', catalogKey: 'delayDistract', category: 'grounding' },
];

export const TOOL_IDS = TOOLS.map((t) => t.id);
