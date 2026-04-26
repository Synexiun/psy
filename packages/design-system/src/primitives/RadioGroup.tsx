'use client';
/**
 * RadioGroup — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Wraps @radix-ui/react-radio-group so keyboard interaction, ARIA role="radiogroup",
 * and pointer events are all handled by the library layer.
 *
 * Token mapping:
 *   Unselected border  : border-border-subtle
 *   Selected border    : border-accent-bronze
 *   Selected fill      : bg-accent-bronze
 *   Surface background : bg-surface-primary
 *   Focus ring         : ring-accent-bronze/30
 *   Label text         : text-ink-primary
 *   Description text   : text-ink-tertiary
 *   Transition easing  : ease-default  (--ease-default in @theme)
 *
 * RTL: wrap in a `dir="rtl"` container — Radix picks up direction from DOM context.
 * Logical properties only; no ml-*/mr-*/pl-*/pr-* classes anywhere in this file.
 */
import * as React from 'react';
import { useId } from 'react';
import * as RadixRadioGroup from '@radix-ui/react-radio-group';

export interface RadioOption {
  value: string;
  label: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
}

export interface RadioGroupProps {
  options: RadioOption[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  orientation?: 'horizontal' | 'vertical';
  ariaLabel?: string;
  name?: string;
  className?: string;
}

export function RadioGroup({
  options,
  value,
  defaultValue,
  onValueChange,
  disabled = false,
  orientation = 'vertical',
  ariaLabel,
  name,
  className = '',
}: RadioGroupProps): React.ReactElement {
  const groupId = useId();

  // exactOptionalPropertyTypes: only spread optional props when defined so
  // Radix does not receive the key set to undefined.
  const optionalRootProps = {
    ...(value !== undefined && { value }),
    ...(defaultValue !== undefined && { defaultValue }),
    ...(onValueChange !== undefined && { onValueChange }),
    ...(name !== undefined && { name }),
  };

  return (
    <RadixRadioGroup.Root
      className={`flex ${orientation === 'horizontal' ? 'flex-row flex-wrap gap-4' : 'flex-col gap-3'} ${className}`.trim()}
      disabled={disabled}
      orientation={orientation}
      aria-label={ariaLabel}
      {...optionalRootProps}
    >
      {options.map((option) => {
        const itemId = `${groupId}-${option.value}`;
        return (
          <div key={option.value} className="flex items-start gap-3">
            <RadixRadioGroup.Item
              id={itemId}
              value={option.value}
              disabled={option.disabled ?? disabled}
              className="mt-0.5 size-4 shrink-0 rounded-full border border-border-subtle bg-surface-primary transition-colors duration-fast ease-default hover:border-accent-bronze focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-accent-bronze data-[state=checked]:bg-accent-bronze"
            >
              <RadixRadioGroup.Indicator className="flex items-center justify-center">
                <div className="size-1.5 rounded-full bg-surface-primary" />
              </RadixRadioGroup.Indicator>
            </RadixRadioGroup.Item>
            <div className="flex flex-col gap-0.5">
              <label htmlFor={itemId} className="cursor-pointer text-sm font-medium leading-none text-ink-primary">
                {option.label}
              </label>
              {option.description !== undefined && (
                <p className="text-xs text-ink-tertiary">{option.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </RadixRadioGroup.Root>
  );
}
