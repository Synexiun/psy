/**
 * Contract tests for packages/design-system/src/primitives/Badge.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests (see packages/design-system/src/primitives/web.test.ts).
 *
 * Coverage target:
 *   - All 6 variants
 *   - Both sizes
 *   - All 5 tone values (backward-compat legacy API)
 *   - variant-wins-over-tone priority
 *   - forwardRef
 *   - className passthrough
 *   - No hsl() in any className output (token hygiene)
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { createRef } from 'react';
import { Badge } from '@disciplineos/design-system/primitives/Badge';

// ---------------------------------------------------------------------------
// Variants
// ---------------------------------------------------------------------------

describe('Badge — variants', () => {
  const variants = ['default', 'success', 'warning', 'danger', 'info', 'neutral'] as const;

  it.each(variants)('renders variant="%s" without throwing', (variant) => {
    expect(() =>
      render(<Badge variant={variant}>{variant}</Badge>),
    ).not.toThrow();
  });

  it('applies accent-bronze token for default variant', () => {
    const { container } = render(<Badge variant="default">Default</Badge>);
    expect(container.firstElementChild?.className).toContain('accent-bronze');
  });

  it('applies signal-stable token for success variant', () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-stable');
  });

  it('applies signal-warning token for warning variant', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-warning');
  });

  it('applies signal-crisis token for danger variant', () => {
    const { container } = render(<Badge variant="danger">Danger</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-crisis');
  });

  it('applies surface-tertiary and ink-secondary for info variant', () => {
    const { container } = render(<Badge variant="info">Info</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('surface-tertiary');
    expect(cls).toContain('ink-secondary');
  });

  it('applies surface-tertiary and ink-tertiary for neutral variant', () => {
    const { container } = render(<Badge variant="neutral">Neutral</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('surface-tertiary');
    expect(cls).toContain('ink-tertiary');
  });
});

// ---------------------------------------------------------------------------
// Sizes
// ---------------------------------------------------------------------------

describe('Badge — sizes', () => {
  const sizes = ['sm', 'md'] as const;

  it.each(sizes)('renders size="%s" without throwing', (size) => {
    expect(() =>
      render(<Badge size={size}>{size}</Badge>),
    ).not.toThrow();
  });

  it('applies text-xs px-2 py-0.5 for sm size', () => {
    const { container } = render(<Badge size="sm">Small</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('text-xs');
    expect(cls).toContain('px-2');
    expect(cls).toContain('py-0.5');
  });

  it('applies text-sm px-2.5 py-1 for md size', () => {
    const { container } = render(<Badge size="md">Medium</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('text-sm');
    expect(cls).toContain('px-2.5');
    expect(cls).toContain('py-1');
  });

  it('defaults to size=sm (text-xs present)', () => {
    const { container } = render(<Badge>Default size</Badge>);
    expect(container.firstElementChild?.className).toContain('text-xs');
  });
});

// ---------------------------------------------------------------------------
// Legacy tone API (backward compat)
// ---------------------------------------------------------------------------

describe('Badge — tone (legacy backward-compat)', () => {
  const tones = ['neutral', 'calm', 'warning', 'crisis', 'success'] as const;

  it.each(tones)('renders tone="%s" without throwing', (tone) => {
    expect(() =>
      render(<Badge tone={tone}>{tone}</Badge>),
    ).not.toThrow();
  });

  it('applies surface-tertiary + ink-secondary for tone=neutral', () => {
    const { container } = render(<Badge tone="neutral">Neutral</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('surface-tertiary');
    expect(cls).toContain('ink-secondary');
  });

  it('applies accent-teal-soft/30 + accent-teal for tone=calm', () => {
    const { container } = render(<Badge tone="calm">Calm</Badge>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('accent-teal');
  });

  it('applies signal-warning for tone=warning', () => {
    const { container } = render(<Badge tone="warning">Warning</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-warning');
  });

  it('applies signal-crisis for tone=crisis', () => {
    const { container } = render(<Badge tone="crisis">Crisis</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-crisis');
  });

  it('applies signal-stable for tone=success', () => {
    const { container } = render(<Badge tone="success">Success</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-stable');
  });
});

// ---------------------------------------------------------------------------
// variant wins over tone
// ---------------------------------------------------------------------------

describe('Badge — variant wins over tone', () => {
  it('uses variant class when both variant and tone are supplied', () => {
    const { container } = render(
      <Badge variant="danger" tone="calm">Both</Badge>,
    );
    const cls = container.firstElementChild?.className ?? '';
    // variant=danger → signal-crisis
    expect(cls).toContain('signal-crisis');
    // tone=calm → accent-teal — must NOT appear since variant wins
    expect(cls).not.toContain('accent-teal');
  });

  it('uses default variant class when neither variant nor tone is supplied', () => {
    const { container } = render(<Badge>Plain</Badge>);
    expect(container.firstElementChild?.className).toContain('accent-bronze');
  });

  it('uses tone class when variant is omitted but tone is set', () => {
    const { container } = render(<Badge tone="crisis">Tone only</Badge>);
    expect(container.firstElementChild?.className).toContain('signal-crisis');
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Badge — forwardRef', () => {
  it('attaches ref to the underlying <span> element', () => {
    const ref = createRef<HTMLSpanElement>();
    render(<Badge ref={ref}>Ref test</Badge>);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('SPAN');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Badge — className passthrough', () => {
  it('merges additional className onto the span element', () => {
    const { container } = render(<Badge className="my-custom-class">Extra</Badge>);
    expect(container.firstElementChild?.className).toContain('my-custom-class');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Badge — token hygiene (no hsl())', () => {
  const variants = ['default', 'success', 'warning', 'danger', 'info', 'neutral'] as const;
  const tones = ['neutral', 'calm', 'warning', 'crisis', 'success'] as const;

  it.each(variants)('no hardcoded hsl() in className for variant="%s"', (variant) => {
    const { container } = render(<Badge variant={variant}>{variant}</Badge>);
    const className = container.firstElementChild?.className ?? '';
    expect(className).not.toContain('hsl(');
  });

  it.each(tones)('no hardcoded hsl() in className for tone="%s"', (tone) => {
    const { container } = render(<Badge tone={tone}>{tone}</Badge>);
    const className = container.firstElementChild?.className ?? '';
    expect(className).not.toContain('hsl(');
  });
});
