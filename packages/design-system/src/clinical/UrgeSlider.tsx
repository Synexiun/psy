'use client';
/**
 * UrgeSlider — clinical 0–10 urge intensity slider.
 *
 * Used in the just-in-time intervention flow (60–180 s window between urge
 * and action). Differs from the generic Slider primitive in three ways:
 *
 * 1. Fixed domain: 0–10, step 1.
 * 2. Latin digit display (Rule #9): the current value is always formatted with
 *    `toLocaleString('en', …)` so Eastern Arabic digits (٧) and Extended
 *    Arabic-Indic digits (۷) are never shown, regardless of locale.
 * 3. RTL: the `dir` prop is forwarded to the Slider primitive which passes it
 *    to Radix Slider.Root — Radix handles thumb drag direction natively.
 *
 * Layout:
 *   root div (flex-col gap-2)
 *     Slider (full width)
 *     value label row (flex justify-between, text-xs, text-ink-tertiary)
 *       <span>0</span>
 *       <span aria-live="polite" data-testid="urge-value">{formattedValue}</span>
 *       <span>10</span>
 */

import * as React from 'react';
import { Slider } from '../primitives/Slider';

export interface UrgeSliderProps {
  /** Controlled value, 0–10 */
  value: number;
  onValueChange: (v: number) => void;
  /** 'en' | 'ar' | 'fa' — used only to document intent; display is always Latin digits */
  locale?: string;
  /** Text direction — pass 'rtl' for ar/fa; forwarded to Slider/Radix for thumb inversion */
  dir?: 'ltr' | 'rtl';
  disabled?: boolean;
  /** Accessible label for the thumb (default: 'Urge intensity') */
  ariaLabel?: string;
  className?: string;
}

export function UrgeSlider({
  value,
  onValueChange,
  locale: _locale,
  dir,
  disabled,
  ariaLabel = 'Urge intensity',
  className,
}: UrgeSliderProps): React.ReactElement {
  // Rule #9: always Latin digits regardless of locale / system locale settings.
  const formattedValue = value.toLocaleString('en', { useGrouping: false });

  // Wrap onValueChange: Slider uses number[], UrgeSlider exposes number.
  const handleValueChange = React.useCallback(
    (vals: number[]) => {
      const next = vals[0];
      if (next !== undefined) {
        onValueChange(next);
      }
    },
    [onValueChange],
  );

  // exactOptionalPropertyTypes: only spread optional props when defined.
  const optionalSliderProps = {
    ...(dir !== undefined && { dir }),
    ...(disabled !== undefined && { disabled }),
  };

  return (
    <div className={`flex flex-col gap-2${className ? ` ${className}` : ''}`}>
      <Slider
        min={0}
        max={10}
        step={1}
        value={[value]}
        onValueChange={handleValueChange}
        ariaLabel={ariaLabel}
        {...optionalSliderProps}
      />
      <div className="flex justify-between text-xs text-ink-tertiary">
        <span>0</span>
        <span aria-live="polite" data-testid="urge-value">
          {formattedValue}
        </span>
        <span>10</span>
      </div>
    </div>
  );
}
