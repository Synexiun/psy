/**
 * Contract tests for packages/design-system/src/primitives/Input.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage target: every InputType, disabled, aria-invalid variants,
 * readOnly, forwardRef, className passthrough, token hygiene (no hsl()).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { Input } from '@disciplineos/design-system/primitives/Input';

// ---------------------------------------------------------------------------
// Rendering — InputType values
// ---------------------------------------------------------------------------

describe('Input — type variants', () => {
  const types = ['text', 'email', 'password', 'number', 'tel', 'search', 'url'] as const;

  it.each(types)('renders type="%s" without throwing', (type) => {
    expect(() =>
      render(<Input type={type} aria-label={`${type} input`} />),
    ).not.toThrow();
  });

  it.each(types)('sets the correct type attribute for type="%s"', (type) => {
    render(<Input type={type} aria-label={`${type} input`} />);
    const input = screen.getByLabelText(`${type} input`);
    expect(input).toHaveAttribute('type', type);
  });

  it('defaults to type="text" when type is not provided', () => {
    render(<Input aria-label="default input" />);
    const input = screen.getByLabelText('default input');
    expect(input).toHaveAttribute('type', 'text');
  });
});

// ---------------------------------------------------------------------------
// Rendering — defaults
// ---------------------------------------------------------------------------

describe('Input — default rendering', () => {
  it('renders without throwing', () => {
    expect(() => render(<Input aria-label="test" />)).not.toThrow();
  });

  it('renders as an <input> element', () => {
    render(<Input aria-label="test" />);
    expect(screen.getByRole('textbox', { name: /test/i })).toBeInTheDocument();
  });

  it('applies base classes including rounded-lg and transition-colors', () => {
    const { container } = render(<Input aria-label="base" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-lg');
    expect(cls).toContain('transition-colors');
  });

  it('applies min-h-[44px] for adequate touch target', () => {
    const { container } = render(<Input aria-label="touch" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('min-h-[44px]');
  });
});

// ---------------------------------------------------------------------------
// Rendering — disabled prop
// ---------------------------------------------------------------------------

describe('Input — disabled prop', () => {
  it('is disabled when disabled=true', () => {
    render(<Input disabled aria-label="disabled input" />);
    expect(screen.getByLabelText('disabled input')).toBeDisabled();
  });

  it('applies cursor-not-allowed and opacity-50 when disabled', () => {
    const { container } = render(<Input disabled aria-label="disabled" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('cursor-not-allowed');
    expect(cls).toContain('opacity-50');
  });

  it('applies bg-surface-tertiary when disabled', () => {
    const { container } = render(<Input disabled aria-label="disabled-bg" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-tertiary');
  });

  it('is not disabled by default', () => {
    render(<Input aria-label="active input" />);
    expect(screen.getByLabelText('active input')).not.toBeDisabled();
  });

  it('does not apply disabled classes when enabled', () => {
    const { container } = render(<Input aria-label="enabled" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('cursor-not-allowed');
    expect(cls).not.toContain('bg-surface-tertiary');
  });
});

// ---------------------------------------------------------------------------
// Rendering — aria-invalid prop
// ---------------------------------------------------------------------------

describe('Input — aria-invalid prop', () => {
  it('applies border-signal-crisis when aria-invalid=true (boolean)', () => {
    const { container } = render(<Input aria-invalid={true} aria-label="invalid-bool" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-signal-crisis');
  });

  it('applies focus:ring-signal-crisis/30 when aria-invalid=true (boolean)', () => {
    const { container } = render(<Input aria-invalid={true} aria-label="invalid-focus" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:ring-signal-crisis/30');
  });

  it('applies border-signal-crisis when aria-invalid="true" (string)', () => {
    const { container } = render(<Input aria-invalid="true" aria-label="invalid-str" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-signal-crisis');
  });

  it('does not apply invalid classes when aria-invalid="false" (string)', () => {
    const { container } = render(<Input aria-invalid="false" aria-label="valid-str" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('border-signal-crisis');
    expect(cls).not.toContain('focus:ring-signal-crisis/30');
  });

  it('does not apply invalid classes when aria-invalid is omitted', () => {
    const { container } = render(<Input aria-label="no-invalid" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('border-signal-crisis');
    expect(cls).not.toContain('focus:ring-signal-crisis/30');
  });

  it('forwards aria-invalid attribute to the DOM element', () => {
    render(<Input aria-invalid={true} aria-label="aria-fwd" />);
    const input = screen.getByLabelText('aria-fwd');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('forwards aria-invalid="false" attribute to the DOM element', () => {
    render(<Input aria-invalid="false" aria-label="aria-false" />);
    const input = screen.getByLabelText('aria-false');
    expect(input).toHaveAttribute('aria-invalid', 'false');
  });
});

// ---------------------------------------------------------------------------
// Rendering — readOnly prop
// ---------------------------------------------------------------------------

describe('Input — readOnly prop', () => {
  it('sets the readOnly attribute when readOnly=true', () => {
    render(<Input readOnly aria-label="readonly input" />);
    expect(screen.getByLabelText('readonly input')).toHaveAttribute('readonly');
  });

  it('does not set readOnly when readOnly is omitted', () => {
    render(<Input aria-label="writable input" />);
    expect(screen.getByLabelText('writable input')).not.toHaveAttribute('readonly');
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Input — forwardRef', () => {
  it('attaches ref to the underlying <input> element', () => {
    const ref = createRef<HTMLInputElement>();
    render(<Input ref={ref} aria-label="ref test" />);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('INPUT');
  });

  it('ref element has the correct type attribute', () => {
    const ref = createRef<HTMLInputElement>();
    render(<Input ref={ref} type="email" aria-label="email ref" />);
    expect(ref.current?.type).toBe('email');
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Input — className passthrough', () => {
  it('merges additional className onto the input element', () => {
    const { container } = render(<Input className="custom-class" aria-label="custom" />);
    expect(container.firstElementChild?.className).toContain('custom-class');
  });

  it('preserves base classes alongside custom className', () => {
    const { container } = render(<Input className="extra" aria-label="preserve" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-lg');
    expect(cls).toContain('extra');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Input — token hygiene', () => {
  const types = ['text', 'email', 'password', 'number', 'tel', 'search', 'url'] as const;

  it.each(types)('no hardcoded hsl() in className for type="%s"', (type) => {
    const { container } = render(<Input type={type} aria-label={`${type}-token`} />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className when disabled', () => {
    const { container } = render(<Input disabled aria-label="disabled-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className when aria-invalid=true', () => {
    const { container } = render(<Input aria-invalid={true} aria-label="invalid-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('uses border-border-subtle token (not hardcoded border colour) in default state', () => {
    const { container } = render(<Input aria-label="token-border" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-border-subtle');
  });

  it('uses bg-surface-primary token (not bg-white) in default state', () => {
    const { container } = render(<Input aria-label="token-bg" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-primary');
    expect(cls).not.toContain('bg-white');
  });

  it('uses text-ink-primary token (not hardcoded text colour)', () => {
    const { container } = render(<Input aria-label="token-text" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('text-ink-primary');
  });

  it('uses placeholder:text-ink-tertiary token', () => {
    const { container } = render(<Input placeholder="Enter value" aria-label="token-placeholder" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('placeholder:text-ink-tertiary');
  });

  it('uses focus:ring-accent-bronze/30 for focus ring', () => {
    const { container } = render(<Input aria-label="token-focus" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:ring-accent-bronze/30');
  });

  it('uses focus:border-accent-bronze for focus border', () => {
    const { container } = render(<Input aria-label="token-focus-border" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:border-accent-bronze');
  });
});
