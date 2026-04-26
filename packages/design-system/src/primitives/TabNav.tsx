'use client';
/**
 * TabNav — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Composes @radix-ui/react-tabs so keyboard interaction (arrow-key navigation,
 * Home/End, tab roving focus), ARIA roles, and RTL direction are handled by the
 * library layer.
 *
 * Token mapping:
 *   List container        : border-b border-border-subtle bg-surface-primary
 *   Inactive trigger      : text-ink-tertiary hover:text-ink-secondary hover:border-b-2 hover:border-border-emphasis
 *   Active trigger        : text-ink-primary border-b-2 border-accent-bronze font-medium
 *   Focus ring            : focus-visible:ring-2 focus-visible:ring-accent-bronze/30
 *   Content panel         : text-ink-primary
 *   Transition easing     : ease-default  (--ease-default in @theme)
 *
 * RTL: pass `dir="rtl"` to the component — Radix Tabs propagates it to Root
 * which causes arrow-key navigation to mirror correctly. Logical properties
 * (`px-*`, `py-*`) handle inline-axis spacing safely across LTR and RTL.
 * No physical `ml-`/`mr-`/`pl-`/`pr-` anywhere in this file.
 */
import * as React from 'react';
import * as RadixTabs from '@radix-ui/react-tabs';

export interface TabItem {
  value: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface TabNavProps {
  /** Tab definitions: each item provides a value, label, and content panel. */
  tabs: TabItem[];
  /** Controlled active tab value. */
  value?: string;
  /** Uncontrolled initial active tab value. Falls back to `tabs[0].value` when omitted. */
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  /** Text direction — pass "rtl" for Arabic (ar) and Persian (fa) locales. */
  dir?: 'ltr' | 'rtl';
  /** aria-label for the tab list. */
  ariaLabel?: string;
  className?: string;
}

export function TabNav({
  tabs,
  value,
  defaultValue,
  onValueChange,
  dir,
  ariaLabel,
  className = '',
}: TabNavProps): React.ReactElement {
  if (process.env.NODE_ENV !== 'production' && value !== undefined && onValueChange === undefined) {
    console.warn(
      '[TabNav] `value` is controlled but `onValueChange` was not provided. The selected tab will be read-only. Pass `onValueChange` to make the component interactive, or use `defaultValue` for uncontrolled mode.',
    );
  }

  // exactOptionalPropertyTypes: build optional root props conditionally so
  // Radix does not receive any key set to undefined.
  // When neither `value` nor `defaultValue` is provided, fall back to the
  // first tab's value so something is always selected on mount.
  if (process.env.NODE_ENV !== 'production' && defaultValue === '') {
    console.warn('[TabNav] `defaultValue` was provided as an empty string. No tab will be selected. Pass a valid tab value or omit the prop to auto-select the first tab.');
  }

  const resolvedDefaultValue =
    defaultValue ?? (value === undefined ? (tabs[0]?.value ?? '') : undefined);

  const optionalRootProps = {
    ...(value !== undefined && { value }),
    ...(resolvedDefaultValue !== undefined &&
      resolvedDefaultValue !== '' && { defaultValue: resolvedDefaultValue }),
    ...(onValueChange !== undefined && { onValueChange }),
    ...(dir !== undefined && { dir }),
  };

  return (
    <RadixTabs.Root
      className={`w-full ${className}`.trim()}
      {...optionalRootProps}
    >
      <RadixTabs.List
        aria-label={ariaLabel}
        className="flex border-b border-border-subtle bg-surface-primary"
      >
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.value}
            value={tab.value}
            disabled={tab.disabled}
            className="relative -mb-px px-4 py-2.5 text-sm font-medium text-ink-tertiary transition-colors duration-fast ease-default hover:border-b-2 hover:border-border-emphasis hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent-bronze/30 disabled:cursor-not-allowed disabled:opacity-50 data-[state=active]:border-b-2 data-[state=active]:border-accent-bronze data-[state=active]:font-medium data-[state=active]:text-ink-primary"
          >
            {tab.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {tabs.map((tab) => (
        <RadixTabs.Content
          key={tab.value}
          value={tab.value}
          className="mt-4 text-ink-primary focus-visible:outline-none"
        >
          {tab.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}
