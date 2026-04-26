/**
 * Contract tests for packages/design-system/src/primitives/Textarea.tsx
 *
 * These live in the web-app test suite because jsdom + @testing-library/react
 * are available here; the design-system package itself only runs pure
 * class-builder unit tests.
 *
 * Coverage target: default render, rows, resize variants (none/vertical/horizontal),
 * disabled, aria-invalid variants, readOnly, forwardRef, className passthrough,
 * token hygiene (no hsl()).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { Textarea } from '@disciplineos/design-system/primitives/Textarea';

// ---------------------------------------------------------------------------
// Rendering — defaults
// ---------------------------------------------------------------------------

describe('Textarea — default rendering', () => {
  it('renders without throwing', () => {
    expect(() => render(<Textarea aria-label="test" />)).not.toThrow();
  });

  it('renders as a <textarea> element', () => {
    render(<Textarea aria-label="test" />);
    expect(screen.getByRole('textbox', { name: /test/i })).toBeInTheDocument();
  });

  it('applies base classes including rounded-lg and transition-colors', () => {
    const { container } = render(<Textarea aria-label="base" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-lg');
    expect(cls).toContain('transition-colors');
  });

  it('applies min-h-[88px] for minimum textarea height', () => {
    const { container } = render(<Textarea aria-label="minheight" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('min-h-[88px]');
  });

  it('defaults to rows=3', () => {
    render(<Textarea aria-label="rows-default" />);
    const el = screen.getByLabelText('rows-default');
    expect(el).toHaveAttribute('rows', '3');
  });

  it('defaults to resize=vertical (applies resize-y)', () => {
    const { container } = render(<Textarea aria-label="resize-default" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('resize-y');
  });
});

// ---------------------------------------------------------------------------
// Rendering — rows prop
// ---------------------------------------------------------------------------

describe('Textarea — rows prop', () => {
  it('sets the rows attribute when provided', () => {
    render(<Textarea rows={6} aria-label="rows-6" />);
    expect(screen.getByLabelText('rows-6')).toHaveAttribute('rows', '6');
  });

  it('uses rows=3 when not provided', () => {
    render(<Textarea aria-label="rows-none" />);
    expect(screen.getByLabelText('rows-none')).toHaveAttribute('rows', '3');
  });
});

// ---------------------------------------------------------------------------
// Rendering — resize variants
// ---------------------------------------------------------------------------

describe('Textarea — resize variants', () => {
  it('applies resize-none when resize="none"', () => {
    const { container } = render(<Textarea resize="none" aria-label="resize-none" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('resize-none');
    expect(cls).not.toContain('resize-y');
    expect(cls).not.toContain('resize-x');
  });

  it('applies resize-y when resize="vertical"', () => {
    const { container } = render(<Textarea resize="vertical" aria-label="resize-vertical" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('resize-y');
    expect(cls).not.toContain('resize-none');
    expect(cls).not.toContain('resize-x');
  });

  it('applies resize-x when resize="horizontal"', () => {
    const { container } = render(<Textarea resize="horizontal" aria-label="resize-horizontal" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('resize-x');
    expect(cls).not.toContain('resize-none');
    expect(cls).not.toContain('resize-y');
  });
});

// ---------------------------------------------------------------------------
// Rendering — disabled prop
// ---------------------------------------------------------------------------

describe('Textarea — disabled prop', () => {
  it('is disabled when disabled=true', () => {
    render(<Textarea disabled aria-label="disabled textarea" />);
    expect(screen.getByLabelText('disabled textarea')).toBeDisabled();
  });

  it('applies cursor-not-allowed and opacity-50 when disabled', () => {
    const { container } = render(<Textarea disabled aria-label="disabled" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('cursor-not-allowed');
    expect(cls).toContain('opacity-50');
  });

  it('applies bg-surface-tertiary when disabled', () => {
    const { container } = render(<Textarea disabled aria-label="disabled-bg" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-tertiary');
  });

  it('is not disabled by default', () => {
    render(<Textarea aria-label="active textarea" />);
    expect(screen.getByLabelText('active textarea')).not.toBeDisabled();
  });

  it('does not apply disabled classes when enabled', () => {
    const { container } = render(<Textarea aria-label="enabled" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('cursor-not-allowed');
    expect(cls).not.toContain('bg-surface-tertiary');
  });
});

// ---------------------------------------------------------------------------
// Rendering — aria-invalid prop
// ---------------------------------------------------------------------------

describe('Textarea — aria-invalid prop', () => {
  it('applies border-signal-crisis when aria-invalid=true (boolean)', () => {
    const { container } = render(<Textarea aria-invalid={true} aria-label="invalid-bool" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-signal-crisis');
  });

  it('applies focus:ring-signal-crisis/30 when aria-invalid=true (boolean)', () => {
    const { container } = render(<Textarea aria-invalid={true} aria-label="invalid-focus" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:ring-signal-crisis/30');
  });

  it('applies border-signal-crisis when aria-invalid="true" (string)', () => {
    const { container } = render(<Textarea aria-invalid="true" aria-label="invalid-str" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-signal-crisis');
  });

  it('does not apply invalid classes when aria-invalid="false" (string)', () => {
    const { container } = render(<Textarea aria-invalid="false" aria-label="valid-str" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('border-signal-crisis');
    expect(cls).not.toContain('focus:ring-signal-crisis/30');
  });

  it('does not apply invalid classes when aria-invalid is omitted', () => {
    const { container } = render(<Textarea aria-label="no-invalid" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('border-signal-crisis');
    expect(cls).not.toContain('focus:ring-signal-crisis/30');
  });

  it('forwards aria-invalid attribute to the DOM element', () => {
    render(<Textarea aria-invalid={true} aria-label="aria-fwd" />);
    const el = screen.getByLabelText('aria-fwd');
    expect(el).toHaveAttribute('aria-invalid', 'true');
  });

  it('forwards aria-invalid="false" attribute to the DOM element', () => {
    render(<Textarea aria-invalid="false" aria-label="aria-false" />);
    const el = screen.getByLabelText('aria-false');
    expect(el).toHaveAttribute('aria-invalid', 'false');
  });
});

// ---------------------------------------------------------------------------
// Rendering — readOnly prop
// ---------------------------------------------------------------------------

describe('Textarea — readOnly prop', () => {
  it('sets the readOnly attribute when readOnly=true', () => {
    render(<Textarea readOnly aria-label="readonly textarea" />);
    expect(screen.getByLabelText('readonly textarea')).toHaveAttribute('readonly');
  });

  it('does not set readOnly when readOnly is omitted', () => {
    render(<Textarea aria-label="writable textarea" />);
    expect(screen.getByLabelText('writable textarea')).not.toHaveAttribute('readonly');
  });
});

// ---------------------------------------------------------------------------
// forwardRef
// ---------------------------------------------------------------------------

describe('Textarea — forwardRef', () => {
  it('attaches ref to the underlying <textarea> element', () => {
    const ref = createRef<HTMLTextAreaElement>();
    render(<Textarea ref={ref} aria-label="ref test" />);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe('TEXTAREA');
  });

  it('ref element has the correct rows attribute', () => {
    const ref = createRef<HTMLTextAreaElement>();
    render(<Textarea ref={ref} rows={5} aria-label="rows ref" />);
    expect(ref.current?.rows).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// className passthrough
// ---------------------------------------------------------------------------

describe('Textarea — className passthrough', () => {
  it('merges additional className onto the textarea element', () => {
    const { container } = render(<Textarea className="custom-class" aria-label="custom" />);
    expect(container.firstElementChild?.className).toContain('custom-class');
  });

  it('preserves base classes alongside custom className', () => {
    const { container } = render(<Textarea className="extra" aria-label="preserve" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('rounded-lg');
    expect(cls).toContain('extra');
  });
});

// ---------------------------------------------------------------------------
// Token hygiene — no hardcoded hsl() values in className output
// ---------------------------------------------------------------------------

describe('Textarea — token hygiene', () => {
  it('no hardcoded hsl() in className in default state', () => {
    const { container } = render(<Textarea aria-label="default-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className when disabled', () => {
    const { container } = render(<Textarea disabled aria-label="disabled-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className when aria-invalid=true', () => {
    const { container } = render(<Textarea aria-invalid={true} aria-label="invalid-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className for resize=none', () => {
    const { container } = render(<Textarea resize="none" aria-label="resize-none-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('no hardcoded hsl() in className for resize=horizontal', () => {
    const { container } = render(<Textarea resize="horizontal" aria-label="resize-horizontal-token" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).not.toContain('hsl(');
  });

  it('uses border-border-subtle token (not hardcoded border colour) in default state', () => {
    const { container } = render(<Textarea aria-label="token-border" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('border-border-subtle');
  });

  it('uses bg-surface-primary token (not bg-white) in default state', () => {
    const { container } = render(<Textarea aria-label="token-bg" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('bg-surface-primary');
    expect(cls).not.toContain('bg-white');
  });

  it('uses text-ink-primary token (not hardcoded text colour)', () => {
    const { container } = render(<Textarea aria-label="token-text" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('text-ink-primary');
  });

  it('uses placeholder:text-ink-tertiary token', () => {
    const { container } = render(<Textarea placeholder="Enter value" aria-label="token-placeholder" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('placeholder:text-ink-tertiary');
  });

  it('uses focus:ring-accent-bronze/30 for focus ring', () => {
    const { container } = render(<Textarea aria-label="token-focus" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:ring-accent-bronze/30');
  });

  it('uses focus:border-accent-bronze for focus border', () => {
    const { container } = render(<Textarea aria-label="token-focus-border" />);
    const cls = container.firstElementChild?.className ?? '';
    expect(cls).toContain('focus:border-accent-bronze');
  });
});
