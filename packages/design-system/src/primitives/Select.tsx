'use client';
/**
 * Select — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Composes @radix-ui/react-select so keyboard interaction, ARIA roles,
 * portal rendering, and pointer events are handled by the library layer.
 *
 * Token mapping:
 *   Trigger (closed)        : bg-surface-secondary border-border-subtle text-ink-primary
 *   Trigger (focused/open)  : border-accent-bronze
 *   Dropdown content        : bg-surface-secondary border-border-subtle shadow-md
 *   Item                    : text-ink-primary hover:bg-surface-tertiary
 *   Item (selected)         : text-accent-bronze font-medium
 *   Item (disabled)         : text-ink-tertiary opacity-50
 *   Scroll buttons          : text-ink-tertiary
 *   Transition easing       : ease-default  (--ease-default in @theme)
 *
 * RTL: wrap in a `dir="rtl"` container — Radix picks up direction from DOM
 * context. `ps-*`/`pe-*`/`start-*`/`end-*` logical properties handle mirroring.
 * Logical properties only; no ml-*/mr-*/pl-*/pr-*/left-*/right-* classes
 * anywhere in this file (animation utility names like slide-in-from-top-2
 * describe animation origin, not directional padding/margin — they are exempt).
 */
import * as React from 'react';
import { useId } from 'react';
import * as RadixSelect from '@radix-ui/react-select';

export interface SelectOption {
  value: string;
  label: React.ReactNode;
  disabled?: boolean;
}

export interface SelectGroup {
  label: string;
  options: SelectOption[];
}

export interface SelectProps {
  /** Flat list of options — mutually exclusive with `groups` */
  options?: SelectOption[];
  /** Grouped options — rendered with ARIA group labels */
  groups?: SelectGroup[];
  /** Controlled selected value */
  value?: string;
  /** Uncontrolled initial selected value */
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  /** Placeholder shown when no value is selected */
  placeholder?: string;
  /** Visible label — associates with the trigger via htmlFor */
  label?: React.ReactNode;
  /** aria-label for the trigger when no visible label is provided */
  ariaLabel?: string;
  className?: string;
}

export function Select({
  options,
  groups,
  value,
  defaultValue,
  onValueChange,
  disabled = false,
  placeholder = 'Select…',
  label,
  ariaLabel,
  className = '',
}: SelectProps): React.ReactElement {
  const selectId = useId();

  if (process.env.NODE_ENV !== 'production' && label !== undefined && ariaLabel !== undefined) {
    console.warn(
      '[Select] Both `label` and `ariaLabel` were provided. `ariaLabel` is ignored when a visible label is present — the label provides the accessible name via htmlFor.',
    );
  }

  // exactOptionalPropertyTypes: only spread props when defined so Radix does
  // not receive the key set to undefined.
  const optionalRootProps = {
    ...(value !== undefined && { value }),
    ...(defaultValue !== undefined && { defaultValue }),
    ...(onValueChange !== undefined && { onValueChange }),
  };

  const renderOption = (option: SelectOption) => (
    <RadixSelect.Item
      key={option.value}
      value={option.value}
      disabled={option.disabled ?? false}
      className="relative flex cursor-pointer select-none items-center rounded-sm py-1.5 ps-8 pe-2 text-sm text-ink-primary outline-none transition-colors duration-fast ease-default hover:bg-surface-tertiary focus:bg-surface-tertiary data-[state=checked]:text-accent-bronze data-[state=checked]:font-medium data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[disabled]:text-ink-tertiary"
    >
      <RadixSelect.ItemIndicator className="absolute start-2 flex items-center justify-center">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path
            d="M2 6L5 9L10 3"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </RadixSelect.ItemIndicator>
      <RadixSelect.ItemText>{option.label}</RadixSelect.ItemText>
    </RadixSelect.Item>
  );

  const optionalTriggerProps = {
    ...(label !== undefined && { id: selectId }),
    ...(label === undefined && ariaLabel !== undefined && { 'aria-label': ariaLabel }),
  };

  const trigger = (
    <RadixSelect.Trigger
      disabled={disabled}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-border-subtle bg-surface-secondary px-3 py-2 text-sm text-ink-primary transition-colors duration-fast ease-default hover:border-accent-bronze focus:border-accent-bronze focus:outline-none focus:ring-2 focus:ring-accent-bronze/30 disabled:cursor-not-allowed disabled:opacity-50 data-[state=open]:border-accent-bronze data-[placeholder]:text-ink-tertiary ${className}`.trim()}
      {...optionalTriggerProps}
    >
      <RadixSelect.Value placeholder={placeholder} />
      <RadixSelect.Icon className="shrink-0 text-ink-tertiary">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path
            d="M3 4.5L6 7.5L9 4.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </RadixSelect.Icon>
    </RadixSelect.Trigger>
  );

  const content = (
    <RadixSelect.Portal>
      <RadixSelect.Content
        position="popper"
        sideOffset={4}
        className="relative z-50 min-w-[8rem] overflow-hidden rounded-md border border-border-subtle bg-surface-secondary shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=top]:slide-in-from-bottom-2"
      >
        <RadixSelect.ScrollUpButton className="flex cursor-default items-center justify-center py-1 text-ink-tertiary">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path
              d="M3 7.5L6 4.5L9 7.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </RadixSelect.ScrollUpButton>
        <RadixSelect.Viewport className="p-1">
          {options !== undefined && options.map(renderOption)}
          {groups !== undefined &&
            groups.map((group) => (
              <RadixSelect.Group key={group.label}>
                <RadixSelect.Label className="py-1.5 ps-8 pe-2 text-xs font-semibold text-ink-tertiary">
                  {group.label}
                </RadixSelect.Label>
                {group.options.map(renderOption)}
              </RadixSelect.Group>
            ))}
        </RadixSelect.Viewport>
        <RadixSelect.ScrollDownButton className="flex cursor-default items-center justify-center py-1 text-ink-tertiary">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path
              d="M3 4.5L6 7.5L9 4.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </RadixSelect.ScrollDownButton>
      </RadixSelect.Content>
    </RadixSelect.Portal>
  );

  const select = (
    <RadixSelect.Root disabled={disabled} {...optionalRootProps}>
      {trigger}
      {content}
    </RadixSelect.Root>
  );

  if (label === undefined) return select;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={selectId} className="text-sm font-medium text-ink-primary">
        {label}
      </label>
      {select}
    </div>
  );
}
