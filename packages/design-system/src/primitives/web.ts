/**
 * Web UI primitives — thin wrappers around native HTML with design-system tokens applied.
 * These are deliberately stateless and opinionated only where the spec demands.
 * See Docs/Technicals/16_Web_Application.md §8.
 */

import type { ComponentPropsWithoutRef } from 'react';

export type ButtonVariant = 'primary' | 'calm' | 'ghost' | 'crisis';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'crisis';

export interface ButtonProps extends ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export interface CardProps extends ComponentPropsWithoutRef<'div'> {
  tone?: 'neutral' | 'calm' | 'warning';
}

export interface InputProps extends ComponentPropsWithoutRef<'input'> {
  labelText: string;
  description?: string;
  errorText?: string;
}

/**
 * buildButtonClasses returns Tailwind utility classes for a button variant + size.
 * Concrete components are authored in each app so they can compose with per-app Tailwind config.
 */
export const buildButtonClasses = (
  variant: ButtonVariant = 'primary',
  size: ButtonSize = 'md',
): string => {
  const base = 'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:opacity-60 disabled:cursor-not-allowed';
  const sizing: Record<ButtonSize, string> = {
    sm: 'h-8 px-3 text-sm rounded-md',
    md: 'h-10 px-4 text-base rounded-md',
    lg: 'h-12 px-6 text-base rounded-lg',
    crisis: 'min-h-[56px] w-full px-6 text-lg rounded-xl',
  };
  const variants: Record<ButtonVariant, string> = {
    primary: 'bg-[hsl(217,91%,60%)] text-white hover:bg-[hsl(217,91%,52%)]',
    calm: 'bg-[hsl(173,58%,39%)] text-white hover:bg-[hsl(173,58%,34%)]',
    ghost: 'bg-transparent text-[hsl(222,47%,11%)] hover:bg-[hsl(220,14%,96%)]',
    crisis: 'bg-[hsl(0,84%,60%)] text-white hover:bg-[hsl(0,84%,54%)]',
  };
  return `${base} ${sizing[size]} ${variants[variant]}`;
};

/**
 * buildInputClasses returns Tailwind utility classes for an input field state.
 * Mirrors the styling used by the Input and Textarea components in web.tsx.
 */
export const buildInputClasses = (
  options?: { invalid?: boolean; disabled?: boolean },
): string => {
  const base =
    'w-full rounded-lg border border-[hsl(220,14%,82%)] bg-white px-3 py-2.5 text-sm text-[hsl(222,47%,11%)] placeholder:text-[hsl(215,16%,57%)] transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-[hsl(217,91%,52%)]/30 focus:border-[hsl(217,91%,52%)]';

  const disabledCls =
    options?.disabled === true
      ? 'cursor-not-allowed opacity-50 bg-[hsl(220,14%,96%)]'
      : '';

  const invalidCls =
    options?.invalid === true
      ? 'border-[hsl(0,84%,60%)] focus:ring-[hsl(0,84%,60%)]/30'
      : '';

  return `${base} ${disabledCls} ${invalidCls}`.trim();
};
