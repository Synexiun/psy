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
 * workaround needed. Logical properties only; no ml-*/mr-*/pl-*/pr-* classes.
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

export function Slider({
  value,
  defaultValue = [0],
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
  return (
    <RadixSlider.Root
      className={`relative flex w-full touch-none select-none items-center ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      value={value}
      defaultValue={defaultValue}
      min={min}
      max={max}
      step={step}
      disabled={disabled}
      onValueChange={onValueChange}
      onValueCommit={onValueCommit}
      aria-label={ariaLabel}
      dir={dir}
    >
      <RadixSlider.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-surface-tertiary">
        <RadixSlider.Range className="absolute h-full bg-accent-bronze" />
      </RadixSlider.Track>
      <RadixSlider.Thumb className="block size-5 rounded-full border-2 border-accent-bronze bg-surface-primary shadow transition-colors duration-fast ease-default hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 disabled:pointer-events-none" />
    </RadixSlider.Root>
  );
}
