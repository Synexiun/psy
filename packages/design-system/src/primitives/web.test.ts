import { describe, it, expect } from 'vitest';
import { buildButtonClasses, buildInputClasses } from './web';

// Note: React component render tests (Input, Textarea, Card, Badge, Spinner, Divider)
// live in the consuming app test suites (apps/web-app/tests/unit) where jsdom + RTL
// are available. This file covers the pure class-builder helpers exported from web.ts.

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

  it('returns ghost variant', () => {
    const classes = buildButtonClasses('ghost', 'md');
    expect(classes).toContain('bg-transparent');
    expect(classes).toContain('text-[hsl(222,47%,11%)]');
  });

  it('returns sm size', () => {
    const classes = buildButtonClasses('primary', 'sm');
    expect(classes).toContain('h-8');
    expect(classes).toContain('px-3');
    expect(classes).toContain('text-sm');
  });
});

describe('buildInputClasses', () => {
  it('returns base classes by default', () => {
    const classes = buildInputClasses();
    expect(classes).toContain('w-full');
    expect(classes).toContain('rounded-lg');
    expect(classes).toContain('border-[hsl(220,14%,82%)]');
    expect(classes).toContain('min-h-[44px]');
  });

  it('includes focus ring classes by default', () => {
    const classes = buildInputClasses();
    expect(classes).toContain('focus:ring-[hsl(217,91%,52%)]');
    expect(classes).toContain('focus:border-[hsl(217,91%,52%)]');
  });

  it('adds disabled classes when disabled=true', () => {
    const classes = buildInputClasses({ disabled: true });
    expect(classes).toContain('cursor-not-allowed');
    expect(classes).toContain('opacity-50');
    expect(classes).toContain('bg-[hsl(220,14%,96%)]');
  });

  it('does not add disabled classes when disabled=false', () => {
    const classes = buildInputClasses({ disabled: false });
    expect(classes).not.toContain('cursor-not-allowed');
    expect(classes).not.toContain('opacity-50');
  });

  it('adds invalid border and ring when invalid=true', () => {
    const classes = buildInputClasses({ invalid: true });
    expect(classes).toContain('border-[hsl(0,84%,60%)]');
    expect(classes).toContain('focus:ring-[hsl(0,84%,60%)]');
  });

  it('does not add invalid classes when invalid=false', () => {
    const classes = buildInputClasses({ invalid: false });
    expect(classes).not.toContain('border-[hsl(0,84%,60%)]');
  });

  it('can combine disabled and invalid', () => {
    const classes = buildInputClasses({ disabled: true, invalid: true });
    expect(classes).toContain('cursor-not-allowed');
    expect(classes).toContain('border-[hsl(0,84%,60%)]');
  });

  it('returns same base classes regardless of options shape', () => {
    const withEmpty = buildInputClasses({});
    const withUndefined = buildInputClasses(undefined);
    // Both should include the base token
    expect(withEmpty).toContain('rounded-lg');
    expect(withUndefined).toContain('rounded-lg');
  });
});
