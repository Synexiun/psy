'use client';
/**
 * CheckboxGroup — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Composes @radix-ui/react-checkbox items so keyboard interaction, ARIA roles,
 * and pointer events are handled by the library layer.
 *
 * Token mapping:
 *   Unselected border  : border-border-subtle
 *   Checked border     : border-accent-bronze
 *   Checked fill       : bg-accent-bronze
 *   Surface background : bg-surface-primary
 *   Focus ring         : ring-accent-bronze/30
 *   Label text         : text-ink-primary
 *   Description text   : text-ink-tertiary
 *   Transition easing  : ease-default  (--ease-default in @theme)
 *
 * RTL: wrap in a `dir="rtl"` container — logical CSS properties handle mirroring.
 * Logical properties only; no ml-*/mr-*/pl-*/pr-* classes anywhere in this file.
 */
import * as React from 'react';
import { useId, useRef } from 'react';
import * as RadixCheckbox from '@radix-ui/react-checkbox';
import type { CheckedState as RadixCheckedState } from '@radix-ui/react-checkbox';

export interface CheckboxOption {
  value: string;
  label: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
}

export interface CheckboxGroupProps {
  options: CheckboxOption[];
  /** Controlled: array of checked values */
  value?: string[];
  /** Uncontrolled: initial checked values */
  defaultValue?: string[];
  onValueChange?: (value: string[]) => void;
  disabled?: boolean;
  orientation?: 'horizontal' | 'vertical';
  ariaLabel?: string;
  className?: string;
}

export function CheckboxGroup({
  options,
  value,
  defaultValue,
  onValueChange,
  disabled = false,
  orientation = 'vertical',
  ariaLabel,
  className = '',
}: CheckboxGroupProps): React.ReactElement {
  const groupId = useId();

  // Internal state for uncontrolled mode
  const [internalChecked, setInternalChecked] = React.useState<string[]>(
    defaultValue ?? [],
  );

  const isControlled = value !== undefined;
  const checkedValues = isControlled ? value : internalChecked;

  // Guard against controlled ↔ uncontrolled switches at runtime (dev only).
  const wasControlledRef = useRef(isControlled);
  if (process.env.NODE_ENV !== 'production' && wasControlledRef.current !== isControlled) {
    console.warn('[CheckboxGroup] Component is changing between controlled and uncontrolled mode.');
  }

  const handleCheckedChange = (optionValue: string, checked: RadixCheckedState) => {
    if (checked === 'indeterminate') return;
    const next = checked
      ? [...checkedValues, optionValue]
      : checkedValues.filter((v) => v !== optionValue);

    if (!isControlled) {
      setInternalChecked(next);
    }
    onValueChange?.(next);
  };

  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={`flex ${orientation === 'horizontal' ? 'flex-row flex-wrap gap-4' : 'flex-col gap-3'} ${className}`.trim()}
    >
      {options.map((option) => {
        const itemId = `${groupId}-${option.value}`;
        const isDisabled = disabled || (option.disabled ?? false);
        const isChecked = checkedValues.includes(option.value);

        return (
          <div key={option.value} className="flex items-start gap-3">
            <RadixCheckbox.Root
              id={itemId}
              checked={isChecked}
              disabled={isDisabled}
              onCheckedChange={(checked) => handleCheckedChange(option.value, checked)}
              className="mt-0.5 size-4 shrink-0 rounded border border-border-subtle bg-surface-primary transition-colors duration-fast ease-default hover:border-accent-bronze focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-accent-bronze data-[state=checked]:bg-accent-bronze"
            >
              <RadixCheckbox.Indicator className="flex items-center justify-center text-surface-primary">
                <svg
                  width="10"
                  height="8"
                  viewBox="0 0 10 8"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M1 4L3.5 6.5L9 1"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </RadixCheckbox.Indicator>
            </RadixCheckbox.Root>
            <div className="flex flex-col gap-0.5">
              <label
                htmlFor={itemId}
                className={`cursor-pointer text-sm font-medium leading-none text-ink-primary ${isDisabled ? 'cursor-not-allowed opacity-50' : ''}`.trim()}
              >
                {option.label}
              </label>
              {option.description !== undefined && (
                <p className="text-xs text-ink-tertiary">{option.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
