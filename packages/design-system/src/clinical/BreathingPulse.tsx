'use client';
/**
 * BreathingPulse — clinical breathing-exercise guide.
 *
 * Guides the user through a 4s inhale / 4s exhale cycle via a pulsing circle
 * animation. Used in T3/T4 intervention flows (the just-in-time window before
 * relapse). The 4 000 ms phase durations are contract-locked via data attributes
 * so automated tests can always verify them.
 *
 * Accessibility:
 *   - Root: role="img" + aria-label
 *   - Animated circle: aria-hidden="true"
 *   - Reduced-motion: animation is suppressed and a static "Breathe" label
 *     is shown instead. The data-inhale-ms / data-exhale-ms attributes remain
 *     so contract tests still pass in reduced-motion mode.
 */

import * as React from 'react';

// ---------------------------------------------------------------------------
// Keyframe injection
// ---------------------------------------------------------------------------

const BREATHE_STYLE_ID = 'disciplineos-breathe-keyframes';

function injectKeyframes(): void {
  if (typeof document === 'undefined') return;
  if (document.getElementById(BREATHE_STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = BREATHE_STYLE_ID;
  style.textContent = `
@keyframes disciplineos-breathe {
  0%   { transform: scale(1); }
  50%  { transform: scale(1.3); }
  100% { transform: scale(1); }
}
`;
  document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Reduced-motion hook
// ---------------------------------------------------------------------------

function useReducedMotion(): boolean {
  const [reduced, setReduced] = React.useState(false);
  React.useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  return reduced;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface BreathingPulseProps {
  /** Size of the pulse circle in px (default 120) */
  size?: number;
  /** aria-label for the component (default: 'Breathing guide') */
  ariaLabel?: string;
  /** Additional classes on root */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BreathingPulse({
  size = 120,
  ariaLabel = 'Breathing guide',
  className,
}: BreathingPulseProps): React.ReactElement {
  const reduced = useReducedMotion();

  // Inject keyframes once on first animated render
  React.useEffect(() => {
    if (!reduced) {
      injectKeyframes();
    }
  }, [reduced]);

  const animationStyle: React.CSSProperties = reduced
    ? {}
    : {
        animation: 'disciplineos-breathe 8s ease-in-out infinite',
      };

  const innerSize = Math.round(size * 0.35);

  return (
    <div
      role="img"
      aria-label={ariaLabel}
      className={className}
      style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
    >
      {/* Contract element — data attributes always present regardless of reduced-motion */}
      <div
        aria-hidden="true"
        data-inhale-ms="4000"
        data-exhale-ms="4000"
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          backgroundColor: 'var(--color-accent-bronze, rgba(180,140,90,0.2))',
          border: '2px solid var(--color-accent-bronze-40, rgba(180,140,90,0.4))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          ...animationStyle,
        }}
        className="bg-accent-bronze/20 border-2 border-accent-bronze/40 rounded-full"
      >
        {reduced ? (
          /* Static mode: show text label instead of animation */
          <span
            style={{
              fontSize: Math.max(12, Math.round(size * 0.15)),
              color: 'var(--color-accent-bronze, #b48c5a)',
              fontWeight: 500,
              letterSpacing: '0.05em',
            }}
          >
            Breathe
          </span>
        ) : (
          /* Animated mode: inner dot */
          <div
            aria-hidden="true"
            style={{
              width: innerSize,
              height: innerSize,
              borderRadius: '50%',
              backgroundColor: 'var(--color-accent-bronze, #b48c5a)',
            }}
            className="bg-accent-bronze rounded-full"
          />
        )}
      </div>
    </div>
  );
}
