/**
 * Contract tests for packages/design-system/src/primitives/Card.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage target: every prop combination — as, padding, shadow, tone, hover,
 * forwardRef, className passthrough, children rendering, token hygiene (no hsl()).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { Card } from '@disciplineos/design-system/primitives/Card';

// ---------------------------------------------------------------------------
// Rendering — default element
// ---------------------------------------------------------------------------

describe('Card — default rendering', () => {
  it('renders without throwing', () => {
    expect(() => render(<Card>Content</Card>)).not.toThrow();
  });

  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders as a <div> by default', () => {
    const { container } = render(<Card>Default</Card>);
    expect(container.firstElementChild?.tagName).toBe('DIV');
  });

  it('applies base classes including rounded-xl and transition-all', () => {
    const { container } = render(<Card>Base</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-xl');
    expect(cls).toContain('transition-all');
  });
});

// ---------------------------------------------------------------------------
// Rendering — as prop (polymorphic)
// ---------------------------------------------------------------------------

describe('Card — as prop', () => {
  it('renders as <article> when as="article"', () => {
    const { container } = render(<Card as="article">Article card</Card>);
    expect(container.firstElementChild?.tagName).toBe('ARTICLE');
  });

  it('renders as <section> when as="section"', () => {
    const { container } = render(<Card as="section">Section card</Card>);
    expect(container.firstElementChild?.tagName).toBe('SECTION');
  });

  it('renders as <div> when as="div"', () => {
    const { container } = render(<Card as="div">Div card</Card>);
    expect(container.firstElementChild?.tagName).toBe('DIV');
  });
});

// ---------------------------------------------------------------------------
// Rendering — padding prop
// ---------------------------------------------------------------------------

describe('Card — padding prop', () => {
  const paddings = ['sm', 'md', 'lg'] as const;

  it.each(paddings)('renders padding="%s" without throwing', (padding) => {
    expect(() => render(<Card padding={padding}>Padding {padding}</Card>)).not.toThrow();
  });

  it('applies p-4 for padding="sm"', () => {
    const { container } = render(<Card padding="sm">Small</Card>);
    expect(container.firstElementChild?.className).toContain('p-4');
  });

  it('applies p-5 for padding="md"', () => {
    const { container } = render(<Card padding="md">Medium</Card>);
    expect(container.firstElementChild?.className).toContain('p-5');
  });

  it('applies p-6 for padding="lg"', () => {
    const { container } = render(<Card padding="lg">Large</Card>);
    expect(container.firstElementChild?.className).toContain('p-6');
  });

  it('defaults to padding="md" (p-5 class present)', () => {
    const { container } = render(<Card>Default padding</Card>);
    expect(container.firstElementChild?.className).toContain('p-5');
  });
});

// ---------------------------------------------------------------------------
// Rendering — shadow prop
// ---------------------------------------------------------------------------

describe('Card — shadow prop', () => {
  const shadows = ['none', 'sm', 'md'] as const;

  it.each(shadows)('renders shadow="%s" without throwing', (shadow) => {
    expect(() => render(<Card shadow={shadow}>Shadow {shadow}</Card>)).not.toThrow();
  });

  it('applies no shadow class for shadow="none"', () => {
    const { container } = render(<Card shadow="none">No shadow</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('shadow-sm');
    expect(cls).not.toContain('shadow-md');
  });

  it('applies shadow-sm for shadow="sm"', () => {
    const { container } = render(<Card shadow="sm">Small shadow</Card>);
    expect(container.firstElementChild?.className).toContain('shadow-sm');
  });

  it('applies shadow-md for shadow="md"', () => {
    const { container } = render(<Card shadow="md">Medium shadow</Card>);
    expect(container.firstElementChild?.className).toContain('shadow-md');
  });

  it('defaults to shadow="sm"', () => {
    const { container } = render(<Card>Default shadow</Card>);
    expect(container.firstElementChild?.className).toContain('shadow-sm');
  });
});

// ---------------------------------------------------------------------------
// Rendering — tone prop
// ---------------------------------------------------------------------------

describe('Card — tone prop', () => {
  const tones = ['neutral', 'calm', 'warning', 'crisis'] as const;

  it.each(tones)('renders tone="%s" without throwing', (tone) => {
    expect(() => render(<Card tone={tone}>Tone {tone}</Card>)).not.toThrow();
  });

  it('applies border-border-subtle for tone="neutral"', () => {
    const { container } = render(<Card tone="neutral">Neutral</Card>);
    expect(container.firstElementChild?.className).toContain('border-border-subtle');
  });

  it('applies accent-teal-soft classes for tone="calm"', () => {
    const { container } = render(<Card tone="calm">Calm</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('accent-teal-soft');
  });

  it('applies signal-warning classes for tone="warning"', () => {
    const { container } = render(<Card tone="warning">Warning</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('signal-warning');
  });

  it('applies signal-crisis classes for tone="crisis"', () => {
    const { container } = render(<Card tone="crisis">Crisis</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('signal-crisis');
  });

  it('applies no tone-specific override when tone is omitted', () => {
    const { container } = render(<Card>No tone</Card>);
    const cls = container.firstElementChild?.className ?? '';
    // Should not include tone-specific signal or teal classes beyond the base border token
    expect(cls).not.toContain('signal-warning');
    expect(cls).not.toContain('signal-crisis');
    expect(cls).not.toContain('accent-teal-soft');
  });
});

// ---------------------------------------------------------------------------
// Rendering — hover prop
// ---------------------------------------------------------------------------

describe('Card — hover prop', () => {
  it('applies hover lift classes when hover=true', () => {
    const { container } = render(<Card hover>Hoverable</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('hover:-translate-y-0.5');
    expect(cls).toContain('cursor-pointer');
  });

  it('does not apply hover lift classes when hover=false (default)', () => {
    const { container } = render(<Card>Not hoverable</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('cursor-pointer');
    expect(cls).not.toContain('-translate-y-0.5');
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Card — forwardRef', () => {
  it('attaches ref to the underlying DOM element', () => {
    const ref = createRef<HTMLDivElement>();
    render(<Card ref={ref}>Ref test</Card>);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('DIV');
  });

  it('attaches ref when as="article"', () => {
    const ref = createRef<HTMLDivElement>();
    render(<Card ref={ref} as="article">Ref article</Card>);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('ARTICLE');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Card — className passthrough', () => {
  it('merges additional className onto the element', () => {
    const { container } = render(<Card className="custom-test-class">Extra</Card>);
    expect(container.firstElementChild?.className).toContain('custom-test-class');
  });

  it('preserves base classes alongside custom className', () => {
    const { container } = render(<Card className="extra">Base preserved</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-xl');
    expect(cls).toContain('extra');
  });
});

// ---------------------------------------------------------------------------
// children rendering
// ---------------------------------------------------------------------------

describe('Card — children', () => {
  it('renders string children', () => {
    render(<Card>Hello world</Card>);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('renders nested element children', () => {
    render(
      <Card>
        <h2>Title</h2>
        <p>Body text</p>
      </Card>,
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Body text')).toBeInTheDocument();
  });

  it('renders multiple children', () => {
    render(
      <Card>
        <span>First</span>
        <span>Second</span>
      </Card>,
    );
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Card — token hygiene', () => {
  const tones = ['neutral', 'calm', 'warning', 'crisis'] as const;

  it('no hardcoded hsl() in className with no tone', () => {
    const { container } = render(<Card>No tone</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it.each(tones)('no hardcoded hsl() in className for tone="%s"', (tone) => {
    const { container } = render(<Card tone={tone}>{tone}</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('uses border-border-subtle token (not hardcoded border colour)', () => {
    const { container } = render(<Card>Token check</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-border-subtle');
  });

  it('uses bg-surface-primary token (not bg-white)', () => {
    const { container } = render(<Card>Token check</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-primary');
    expect(cls).not.toContain('bg-white');
  });

  it('uses ease-default token (not ease-standard)', () => {
    const { container } = render(<Card>Token check</Card>);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('ease-default');
    expect(cls).not.toContain('ease-standard');
  });
});
