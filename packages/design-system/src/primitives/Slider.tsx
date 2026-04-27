'use client';
/**
 * Slider — Radix-based, Quiet Strength–tokenised primitive.
 *
 * Wraps @radix-ui/react-slider so keyboard interaction, ARIA role="slider",
 * pointer events, and RTL thumb drag direction are all handled by the library
 * layer. Pass `dir="rtl"` when the containing element has dir="rtl" — Radix
 * mirrors the thumb drag direction automatically.
 *
 * Token mapping:
 *   Track background : bg-surface-tertiary
 *   Range fill       : bg-accent-bronze
 *   Thumb background : bg-surface-primary
 *   Thumb border     : border-accent-bronze
 *   Focus ring       : ring-accent-bronze/30
 *   Transition easing: ease-default  (--ease-default in @theme)
 *
 * RTL: `dir` prop is forwarded directly to RadixSlider.Root — no wrapper div
 * workaround needed. Logical properties only; no ml-[x]/mr-[x]/pl-[x]/pr-[x] classes.
 */
import * as React from 'react';
import * as RadixSlider from '@radix-ui/react-slider';

export interface SliderProps {
  value?: number[];
  defaultValue?: number[];
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  onValueChange?: (value: number[]) => void;
  onValueCommit?: (value: number[]) => void;
  ariaLabel?: string;
  /** Pass 'rtl' when the containing element has dir="rtl" — thumb drag direction mirrors accordingly */
  dir?: 'ltr' | 'rtl';
  className?: string;
}

const THUMB_CLASS =
  'block size-5 rounded-full border-2 border-accent-bronze bg-surface-primary shadow transition-colors duration-fast ease-default hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:pointer-events-none';

export function Slider({
  value,
  defaultValue,
  min = 0,
  max = 100,
  step = 1,
  disabled = false,
  onValueChange,
  onValueCommit,
  ariaLabel,
  dir,
  className = '',
}: SliderProps): React.ReactElement {
  // Resolve the thumb count from whichever mode is active; fall back to [0].
  const thumbValues = value ?? defaultValue ?? [0];

  // exactOptionalPropertyTypes: only include optional props when defined so
  // Radix does not receive the key set to undefined.
  const optionalRootProps = {
    ...(value !== undefined && { value }),
    ...(defaultValue !== undefined && { defaultValue }),
    ...(onValueChange !== undefined && { onValueChange }),
    ...(onValueCommit !== undefined && { onValueCommit }),
    ...(dir !== undefined && { dir }),
  };

  return (
    <RadixSlider.Root
      className={`relative flex w-full touch-none select-none items-center ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`.trim()}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      {...optionalRootProps}
    >
      <RadixSlider.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-surface-tertiary">
        <RadixSlider.Range className="absolute h-full bg-accent-bronze" />
      </RadixSlider.Track>
      {thumbValues.map((_v, i) => (
        <RadixSlider.Thumb key={i} aria-label={thumbValues.length === 1 ? ariaLabel : `${ariaLabel ?? 'Value'} ${i + 1}`} className={THUMB_CLASS} />
      ))}
    </RadixSlider.Root>
  );
}
