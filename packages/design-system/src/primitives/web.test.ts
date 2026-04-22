import { describe, it, expect } from 'vitest';
import { buildButtonClasses } from './web';

describe('buildButtonClasses', () => {
  it('returns primary/md by default', () => {
    const classes = buildButtonClasses();
    expect(classes).toContain('bg-[hsl(217,91%,60%)]');
    expect(classes).toContain('h-10');
  });

  it('returns crisis variant', () => {
    const classes = buildButtonClasses('crisis', 'crisis');
    expect(classes).toContain('bg-[hsl(0,84%,60%)]');
    expect(classes).toContain('min-h-[56px]');
  });

  it('returns calm variant', () => {
    const classes = buildButtonClasses('calm', 'lg');
    expect(classes).toContain('bg-[hsl(173,58%,39%)]');
    expect(classes).toContain('h-12');
  });
});
