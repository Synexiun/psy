'use client';
/**
 * Input — standalone Quiet Strength–tokenised primitive.
 *
 * Extracted from packages/design-system/src/primitives/web.tsx so it can be
 * imported tree-shakably without pulling the full primitives bundle.
 *
 * API is intentionally identical to the Input exported from web.tsx;
 * consuming code may import from either location.
 *
 * Token mapping:
 *   border-[hsl(220,14%,82%)]      → border-border-subtle       (neutral input border)
 *   bg-white                        → bg-surface-primary         (Quiet Strength surface base)
 *   text-[hsl(222,47%,11%)]        → text-ink-primary           (primary text colour)
 *   placeholder:text-[hsl(215,16%,57%)] → placeholder:text-ink-tertiary
 *   focus:ring-[hsl(217,91%,52%)]/30    → focus:ring-accent-bronze/30
 *   focus:border-[hsl(217,91%,52%)]    → focus:border-accent-bronze
 *   bg-[hsl(220,14%,96%)] (disabled)   → bg-surface-tertiary
 *   border-[hsl(0,84%,60%)] (invalid)  → border-signal-crisis
 *   focus:ring-[hsl(0,84%,60%)]/30 (invalid focus) → focus:ring-signal-crisis/30
 */
import * as React from 'react';

export type InputType =
  | 'text'
  | 'email'
  | 'password'
  | 'number'
  | 'tel'
  | 'search'
  | 'url';

export interface InputProps {
  id?: string;
  name?: string;
  type?: InputType;
  value?: string | number;
  defaultValue?: string | number;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  autoComplete?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  onFocus?: React.FocusEventHandler<HTMLInputElement>;
  className?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean | 'true' | 'false';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  function Input(
    {
      type = 'text',
      disabled = false,
      className = '',
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref,
  ): React.ReactElement {
    const isInvalid = ariaInvalid === true || ariaInvalid === 'true';

    const base =
      'w-full rounded-lg border border-border-subtle bg-surface-primary px-3 py-2.5 text-sm text-ink-primary placeholder:text-ink-tertiary transition-colors min-h-[44px]';
    const focusCls =
      'focus:outline-none focus:ring-2 focus:ring-accent-bronze/30 focus:border-accent-bronze';
    const disabledCls = disabled
      ? 'cursor-not-allowed opacity-50 bg-surface-tertiary'
      : '';
    const invalidCls = isInvalid
      ? 'border-signal-crisis focus:ring-signal-crisis/30'
      : '';

    return (
      <input
        ref={ref}
        type={type}
        disabled={disabled}
        aria-invalid={ariaInvalid}
        className={`${base} ${focusCls} ${disabledCls} ${invalidCls} ${className}`.trim()}
        {...props}
      />
    );
  },
);
