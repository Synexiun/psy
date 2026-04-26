'use client';
/**
 * Switch — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Composes @radix-ui/react-switch so keyboard interaction, ARIA role="switch",
 * and pointer events are handled by the library layer.
 *
 * Token mapping:
 *   Off track background  : bg-surface-tertiary
 *   On track background   : bg-accent-bronze
 *   Thumb background      : bg-surface-primary
 *   Focus ring            : ring-accent-bronze/30
 *   Label text            : text-ink-primary
 *   Description text      : text-ink-tertiary
 *   Transition easing     : ease-default  (--ease-default in @theme)
 *
 * RTL: Radix Switch handles thumb translation direction automatically via its
 * internal direction context — no `dir` prop needed here. Wrap the component
 * in a `dir="rtl"` container and logical CSS properties handle label/track
 * mirroring automatically.
 *
 * Logical properties only; no ml-*/mr-*/pl-*/pr-* classes anywhere in this file.
 */
import * as React from 'react';
import { useId } from 'react';
import * as RadixSwitch from '@radix-ui/react-switch';

export interface SwitchProps {
  /** Controlled checked state */
  checked?: boolean;
  /** Uncontrolled initial checked state */
  defaultChecked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  /** Visible label — associates with the switch via htmlFor */
  label?: React.ReactNode;
  /** Optional description rendered below the label */
  description?: React.ReactNode;
  /** aria-label for the switch root when no visible label is provided */
  ariaLabel?: string;
  className?: string;
}

export function Switch({
  checked,
  defaultChecked,
  onCheckedChange,
  disabled = false,
  label,
  description,
  ariaLabel,
  className = '',
}: SwitchProps): React.ReactElement {
  const switchId = useId();

  // exactOptionalPropertyTypes: only spread props when defined so Radix
  // does not receive the key set to undefined.
  const optionalRootProps = {
    ...(checked !== undefined && { checked }),
    ...(defaultChecked !== undefined && { defaultChecked }),
    ...(onCheckedChange !== undefined && { onCheckedChange }),
  };

  const root = (
    <RadixSwitch.Root
      id={switchId}
      disabled={disabled}
      // When a visible label is present, htmlFor provides the accessible name.
      // When no label is present, aria-label on Root provides it instead.
      aria-label={label !== undefined ? undefined : ariaLabel}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-fast ease-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-accent-bronze data-[state=unchecked]:bg-surface-tertiary`.trim()}
      {...optionalRootProps}
    >
      <RadixSwitch.Thumb className="pointer-events-none block size-5 rounded-full bg-surface-primary shadow-sm transition-transform duration-fast ease-default data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
    </RadixSwitch.Root>
  );

  if (!label && !description) {
    return root;
  }

  return (
    <div className={`flex items-start gap-3 ${className}`.trim()}>
      {root}
      <div className="flex flex-col gap-0.5">
        {label && (
          <label
            htmlFor={switchId}
            className={`cursor-pointer text-sm font-medium leading-none text-ink-primary ${disabled ? 'cursor-not-allowed opacity-50' : ''}`.trim()}
          >
            {label}
          </label>
        )}
        {description && (
          <p className="text-xs text-ink-tertiary">{description}</p>
        )}
      </div>
    </div>
  );
}
