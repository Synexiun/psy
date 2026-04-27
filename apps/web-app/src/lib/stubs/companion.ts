import { registerStubs } from './index';

export type CompanionStubs = {
  current: { templateId: string; text: string };
};

export const companionStubs: CompanionStubs = {
  current: {
    templateId: 'compassion-001',
    text: 'You took a hard step by coming here. That matters.',
  },
};

registerStubs('companion', companionStubs);
