/**
 * Render tests for new design-system primitives (Input, Textarea, Spinner, Divider,
 * and extended Card / Badge APIs).
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are only installed here; the design-system package itself only runs pure
 * class-builder unit tests (see packages/design-system/src/primitives/web.test.ts).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Input,
  Textarea,
  Spinner,
  Divider,
  Card,
  Badge,
} from '@disciplineos/design-system';

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

describe('Input', () => {
  it('renders a text input by default', () => {
    render(<Input aria-label="Email address" />);
    expect(screen.getByRole('textbox', { name: /email address/i })).toBeInTheDocument();
  });

  it('respects type prop', () => {
    render(<Input type="email" aria-label="Email" />);
    const input = screen.getByRole('textbox', { name: /email/i });
    expect(input).toHaveAttribute('type', 'email');
  });

  it('is disabled when disabled prop is set', () => {
    render(<Input aria-label="Disabled" disabled />);
    expect(screen.getByRole('textbox', { name: /disabled/i })).toBeDisabled();
  });

  it('applies aria-invalid attribute', () => {
    render(<Input aria-label="Bad input" aria-invalid="true" />);
    expect(screen.getByRole('textbox', { name: /bad input/i })).toHaveAttribute(
      'aria-invalid',
      'true',
    );
  });

  it('passes aria-describedby through', () => {
    render(<Input aria-label="Input" aria-describedby="hint-text" />);
    expect(screen.getByRole('textbox', { name: /input/i })).toHaveAttribute(
      'aria-describedby',
      'hint-text',
    );
  });

  it('forwards placeholder', () => {
    render(<Input aria-label="Search" placeholder="Search..." />);
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Textarea
// ---------------------------------------------------------------------------

describe('Textarea', () => {
  it('renders a textarea element', () => {
    render(<Textarea aria-label="Notes" />);
    expect(screen.getByRole('textbox', { name: /notes/i })).toBeInTheDocument();
  });

  it('respects rows prop', () => {
    render(<Textarea aria-label="Bio" rows={5} />);
    expect(screen.getByRole('textbox', { name: /bio/i })).toHaveAttribute('rows', '5');
  });

  it('is disabled when disabled prop is set', () => {
    render(<Textarea aria-label="Disabled text" disabled />);
    expect(screen.getByRole('textbox', { name: /disabled text/i })).toBeDisabled();
  });

  it('applies aria-invalid attribute', () => {
    render(<Textarea aria-label="Error area" aria-invalid="true" />);
    expect(screen.getByRole('textbox', { name: /error area/i })).toHaveAttribute(
      'aria-invalid',
      'true',
    );
  });

  it('respects maxLength prop', () => {
    render(<Textarea aria-label="Limited" maxLength={500} />);
    expect(screen.getByRole('textbox', { name: /limited/i })).toHaveAttribute('maxLength', '500');
  });
});

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------

describe('Spinner', () => {
  it('renders with default aria-label "Loading"', () => {
    render(<Spinner />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
  });

  it('accepts a custom label', () => {
    render(<Spinner label="Submitting form" />);
    expect(screen.getByRole('status', { name: /submitting form/i })).toBeInTheDocument();
  });

  it('renders an SVG element', () => {
    const { container } = render(<Spinner />);
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('renders sm size (16px)', () => {
    const { container } = render(<Spinner size="sm" />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '16');
    expect(svg).toHaveAttribute('height', '16');
  });

  it('renders lg size (32px)', () => {
    const { container } = render(<Spinner size="lg" />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '32');
    expect(svg).toHaveAttribute('height', '32');
  });
});

// ---------------------------------------------------------------------------
// Divider
// ---------------------------------------------------------------------------

describe('Divider', () => {
  it('renders a horizontal separator by default', () => {
    render(<Divider />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('renders label text when provided', () => {
    render(<Divider label="or" />);
    expect(screen.getByText('or')).toBeInTheDocument();
  });

  it('renders vertical separator with correct aria-orientation', () => {
    render(<Divider orientation="vertical" />);
    const sep = screen.getByRole('separator');
    expect(sep).toHaveAttribute('aria-orientation', 'vertical');
  });

  it('renders horizontal separator as an hr element', () => {
    const { container } = render(<Divider orientation="horizontal" />);
    // The plain horizontal divider renders as <hr> — no aria-orientation needed
    // because <hr> has an implicit separator role that is always horizontal.
    expect(container.querySelector('hr')).not.toBeNull();
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Card — extended API
// ---------------------------------------------------------------------------

describe('Card (extended API)', () => {
  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders as article when as="article"', () => {
    const { container } = render(<Card as="article">Article card</Card>);
    expect(container.querySelector('article')).not.toBeNull();
  });

  it('renders as section when as="section"', () => {
    const { container } = render(<Card as="section">Section card</Card>);
    expect(container.querySelector('section')).not.toBeNull();
  });

  it('applies lg padding class', () => {
    const { container } = render(<Card padding="lg">Padded</Card>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('p-6');
  });

  it('applies sm padding class', () => {
    const { container } = render(<Card padding="sm">Compact</Card>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('p-4');
  });

  it('applies shadow-md class when shadow="md"', () => {
    const { container } = render(<Card shadow="md">Shadowed</Card>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('shadow-md');
  });

  it('omits shadow classes when shadow="none"', () => {
    const { container } = render(<Card shadow="none">Flat</Card>);
    const el = container.firstElementChild;
    expect(el?.className).not.toContain('shadow-sm');
    expect(el?.className).not.toContain('shadow-md');
  });

  it('still accepts legacy tone prop', () => {
    render(<Card tone="calm">Calm card</Card>);
    expect(screen.getByText('Calm card')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Badge — extended API
// ---------------------------------------------------------------------------

describe('Badge (extended API)', () => {
  it('renders children', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('uses default variant classes without props', () => {
    const { container } = render(<Badge>Tag</Badge>);
    const el = container.firstElementChild;
    // default variant: bg-accent-bronze/15 (Quiet Strength token)
    expect(el?.className).toContain('bg-accent-bronze/15');
  });

  it('applies success variant classes', () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('bg-signal-stable/15');
  });

  it('applies danger variant classes', () => {
    const { container } = render(<Badge variant="danger">Danger</Badge>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('bg-signal-crisis/15');
  });

  it('applies warning variant classes', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('bg-signal-warning/15');
  });

  it('applies md size classes', () => {
    const { container } = render(<Badge size="md">Tag</Badge>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('text-sm');
    expect(el?.className).toContain('px-2.5');
  });

  it('applies sm size classes by default', () => {
    const { container } = render(<Badge>Tag</Badge>);
    const el = container.firstElementChild;
    expect(el?.className).toContain('text-xs');
    expect(el?.className).toContain('px-2');
  });

  it('still accepts legacy tone prop', () => {
    render(<Badge tone="calm">Calm</Badge>);
    expect(screen.getByText('Calm')).toBeInTheDocument();
  });

  it('prefers variant over legacy tone when both provided', () => {
    const { container } = render(
      <Badge variant="danger" tone="calm">
        Priority
      </Badge>,
    );
    const el = container.firstElementChild;
    // danger bg (signal-crisis token) should be present, not calm (teal) bg
    expect(el?.className).toContain('bg-signal-crisis/15');
    expect(el?.className).not.toContain('bg-accent-teal');
  });
});
