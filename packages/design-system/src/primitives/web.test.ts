import { describe, it, expect } from 'vitest';
import { buildButtonClasses, buildInputClasses } from './web';

// Note: React component render tests (Input, Textarea, Card, Badge, Spinner, Divider)
// live in the consuming app test suites (apps/web-app/tests/unit) where jsdom + RTL
// are available. This file covers the pure class-builder helpers exported from web.ts,
// plus inline-extracted pure math from the ProgressRing and Sparkline components.

// ---------------------------------------------------------------------------
// ProgressRing pure geometry (inline from web.tsx)
// These formulas drive the SVG strokeDashoffset that renders the ring fill.
// A regression here would produce visually incorrect streak progress rings.
// ---------------------------------------------------------------------------

function progressRingGeometry(
  value: number,
  max: number,
  size: number,
  strokeWidth: number,
): { radius: number; circumference: number; dashoffset: number; pct: number } {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(value, max));
  const pct = max === 0 ? 0 : clamped / max;
  const dashoffset = circumference * (1 - pct);
  return { radius, circumference, dashoffset, pct };
}

// ---------------------------------------------------------------------------
// Sparkline geometry (inline from web.tsx)
// ---------------------------------------------------------------------------

type SparkPoint = { x: number; y: number };

function sparklinePoints(
  data: number[],
  width: number,
  height: number,
): SparkPoint[] | null {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  return data.map((v, i) => ({
    x: (i / (data.length - 1)) * width,
    y: height - ((v - min) / range) * height,
  }));
}

// ---------------------------------------------------------------------------
// Tooltip side-classes (inline from web.tsx)
// ---------------------------------------------------------------------------

const sideClasses: Record<string, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

// ---------------------------------------------------------------------------
// ProgressRing geometry tests
// ---------------------------------------------------------------------------

describe('ProgressRing — radius and circumference', () => {
  it('radius equals (size - strokeWidth) / 2', () => {
    const { radius } = progressRingGeometry(50, 100, 120, 10);
    expect(radius).toBe((120 - 10) / 2);
  });

  it('circumference equals 2π × radius', () => {
    const { radius, circumference } = progressRingGeometry(50, 100, 120, 10);
    expect(circumference).toBeCloseTo(2 * Math.PI * radius, 5);
  });

  it('dashoffset is 0 when value === max (full ring)', () => {
    const { dashoffset } = progressRingGeometry(100, 100, 120, 10);
    expect(dashoffset).toBeCloseTo(0, 5);
  });

  it('dashoffset equals circumference when value is 0 (empty ring)', () => {
    const { circumference, dashoffset } = progressRingGeometry(0, 100, 120, 10);
    expect(dashoffset).toBeCloseTo(circumference, 5);
  });

  it('dashoffset is half circumference at 50%', () => {
    const { circumference, dashoffset } = progressRingGeometry(50, 100, 120, 10);
    expect(dashoffset).toBeCloseTo(circumference / 2, 5);
  });

  it('pct is 0.25 when value is 25 out of 100', () => {
    const { pct } = progressRingGeometry(25, 100, 120, 10);
    expect(pct).toBeCloseTo(0.25, 5);
  });
});

describe('ProgressRing — clamping (prevents negative dashoffset)', () => {
  it('value > max clamps to max (no overfill)', () => {
    const at_max = progressRingGeometry(100, 100, 120, 10);
    const over_max = progressRingGeometry(150, 100, 120, 10);
    expect(over_max.dashoffset).toBeCloseTo(at_max.dashoffset, 5);
    expect(over_max.pct).toBeCloseTo(1.0, 5);
  });

  it('negative value clamps to 0 (no underfill below empty)', () => {
    const at_zero = progressRingGeometry(0, 100, 120, 10);
    const below_zero = progressRingGeometry(-10, 100, 120, 10);
    expect(below_zero.dashoffset).toBeCloseTo(at_zero.dashoffset, 5);
    expect(below_zero.pct).toBeCloseTo(0, 5);
  });

  it('value === max gives pct === 1.0', () => {
    const { pct } = progressRingGeometry(60, 60, 100, 8);
    expect(pct).toBeCloseTo(1.0, 5);
  });
});

describe('ProgressRing — zero max guard', () => {
  it('pct is 0 when max is 0 (no division by zero)', () => {
    const { pct } = progressRingGeometry(0, 0, 120, 10);
    expect(pct).toBe(0);
  });

  it('dashoffset equals circumference when max is 0 (empty ring)', () => {
    const { circumference, dashoffset } = progressRingGeometry(0, 0, 120, 10);
    expect(dashoffset).toBeCloseTo(circumference, 5);
  });
});

describe('ProgressRing — size sensitivity', () => {
  it('larger size produces larger circumference', () => {
    const small = progressRingGeometry(50, 100, 80, 8);
    const large = progressRingGeometry(50, 100, 160, 8);
    expect(large.circumference).toBeGreaterThan(small.circumference);
  });

  it('same percentage produces same pct regardless of size', () => {
    const sm = progressRingGeometry(50, 100, 80, 8);
    const lg = progressRingGeometry(50, 100, 160, 8);
    expect(sm.pct).toBeCloseTo(lg.pct, 5);
  });
});

// ---------------------------------------------------------------------------
// Sparkline geometry tests
// ---------------------------------------------------------------------------

describe('Sparkline — null guard', () => {
  it('returns null for empty data', () => {
    expect(sparklinePoints([], 120, 40)).toBeNull();
  });

  it('returns null for single-point data (no line possible)', () => {
    expect(sparklinePoints([5], 120, 40)).toBeNull();
  });

  it('returns points for two data points (minimum valid input)', () => {
    expect(sparklinePoints([3, 7], 120, 40)).not.toBeNull();
  });
});

describe('Sparkline — x axis', () => {
  it('first point x is 0', () => {
    const pts = sparklinePoints([1, 2, 3, 4], 120, 40)!;
    expect(pts[0]!.x).toBe(0);
  });

  it('last point x is width', () => {
    const pts = sparklinePoints([1, 2, 3, 4], 120, 40)!;
    expect(pts[pts.length - 1]!.x).toBe(120);
  });

  it('middle point x is evenly distributed', () => {
    const pts = sparklinePoints([1, 2, 3], 120, 40)!;
    expect(pts[1]!.x).toBeCloseTo(60, 5);
  });
});

describe('Sparkline — y axis', () => {
  it('minimum value maps to bottom (y === height)', () => {
    const pts = sparklinePoints([1, 5, 10], 120, 40)!;
    expect(pts[0]!.y).toBeCloseTo(40, 5);
  });

  it('maximum value maps to top (y === 0)', () => {
    const pts = sparklinePoints([1, 5, 10], 120, 40)!;
    expect(pts[2]!.y).toBeCloseTo(0, 5);
  });

  it('midpoint value maps to mid-height', () => {
    const pts = sparklinePoints([0, 5, 10], 120, 40)!;
    expect(pts[1]!.y).toBeCloseTo(20, 5);
  });
});

describe('Sparkline — zero-range protection', () => {
  it('flat data does not produce NaN or Infinity', () => {
    const pts = sparklinePoints([5, 5, 5, 5], 120, 40)!;
    for (const p of pts) {
      expect(Number.isFinite(p.x)).toBe(true);
      expect(Number.isFinite(p.y)).toBe(true);
    }
  });

  it('returns same number of points as data', () => {
    const data = [3, 4, 3, 5, 4, 6, 5, 7];
    expect(sparklinePoints(data, 240, 48)!).toHaveLength(data.length);
  });
});

// ---------------------------------------------------------------------------
// Tooltip side-classes tests
// ---------------------------------------------------------------------------

describe('Tooltip sideClasses', () => {
  it('has all 4 sides', () => {
    expect(Object.keys(sideClasses)).toHaveLength(4);
  });

  it('top places tooltip above (bottom-full)', () => {
    expect(sideClasses['top']).toContain('bottom-full');
  });

  it('bottom places tooltip below (top-full)', () => {
    expect(sideClasses['bottom']).toContain('top-full');
  });

  it('left places tooltip to the left (right-full)', () => {
    expect(sideClasses['left']).toContain('right-full');
  });

  it('right places tooltip to the right (left-full)', () => {
    expect(sideClasses['right']).toContain('left-full');
  });

  it('all sides have non-empty classes', () => {
    for (const cls of Object.values(sideClasses)) {
      expect(cls.length).toBeGreaterThan(0);
    }
  });
});

// ---------------------------------------------------------------------------
// buildButtonClasses / buildInputClasses (original tests)
// ---------------------------------------------------------------------------

describe('buildButtonClasses', () => {
  it('returns primary/md by default', () => {
    const classes = buildButtonClasses();
    expect(classes).toContain('bg-[hsl(217,91%,60%)]');
    expect(classes).toContain('h-10');
  });

  it('returns crisis variant', () => {
    const classes = buildButtonClasses('crisis', 'crisis');
    expect(classes).toContain('bg-[hsl(0,84%,60%)]');
    expect(classes).toContain('min-h-[56px]');
  });

  it('returns calm variant', () => {
    const classes = buildButtonClasses('calm', 'lg');
    expect(classes).toContain('bg-[hsl(173,58%,39%)]');
    expect(classes).toContain('h-12');
  });

  it('returns ghost variant', () => {
    const classes = buildButtonClasses('ghost', 'md');
    expect(classes).toContain('bg-transparent');
    expect(classes).toContain('text-[hsl(222,47%,11%)]');
  });

  it('returns sm size', () => {
    const classes = buildButtonClasses('primary', 'sm');
    expect(classes).toContain('h-8');
    expect(classes).toContain('px-3');
    expect(classes).toContain('text-sm');
  });
});

// ---------------------------------------------------------------------------
// Spinner geometry (inline from web.tsx)
// px map: sm=16, md=24, lg=32 — strokeWidth is hardcoded 3.
// Quarter-arc: dash = 25% of circumference, gap = remainder.
// These values drive the SVG strokeDasharray that animates the loading arc.
// ---------------------------------------------------------------------------

type SpinnerSize = 'sm' | 'md' | 'lg';

function spinnerGeometry(size: SpinnerSize): {
  dim: number;
  radius: number;
  circumference: number;
  dash: number;
  gap: number;
} {
  const px: Record<SpinnerSize, number> = { sm: 16, md: 24, lg: 32 };
  const dim = px[size];
  const radius = (dim - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * 0.25;
  const gap = circumference - dash;
  return { dim, radius, circumference, dash, gap };
}

describe('Spinner — radius per size (strokeWidth=3, 1.5px inset per side)', () => {
  it('sm (16px): radius = (16 - 6) / 2 = 5', () => {
    expect(spinnerGeometry('sm').radius).toBe(5);
  });

  it('md (24px): radius = (24 - 6) / 2 = 9', () => {
    expect(spinnerGeometry('md').radius).toBe(9);
  });

  it('lg (32px): radius = (32 - 6) / 2 = 13', () => {
    expect(spinnerGeometry('lg').radius).toBe(13);
  });
});

describe('Spinner — circumference = 2π × radius', () => {
  it('sm circumference ≈ 31.416', () => {
    expect(spinnerGeometry('sm').circumference).toBeCloseTo(2 * Math.PI * 5, 3);
  });

  it('md circumference ≈ 56.549', () => {
    expect(spinnerGeometry('md').circumference).toBeCloseTo(2 * Math.PI * 9, 3);
  });

  it('lg circumference ≈ 81.681', () => {
    expect(spinnerGeometry('lg').circumference).toBeCloseTo(2 * Math.PI * 13, 3);
  });
});

describe('Spinner — quarter-arc dash (25% of circumference)', () => {
  it('dash + gap equals circumference for sm', () => {
    const { circumference, dash, gap } = spinnerGeometry('sm');
    expect(dash + gap).toBeCloseTo(circumference, 10);
  });

  it('dash + gap equals circumference for md', () => {
    const { circumference, dash, gap } = spinnerGeometry('md');
    expect(dash + gap).toBeCloseTo(circumference, 10);
  });

  it('dash + gap equals circumference for lg', () => {
    const { circumference, dash, gap } = spinnerGeometry('lg');
    expect(dash + gap).toBeCloseTo(circumference, 10);
  });

  it('dash is exactly 25% of circumference (quarter arc)', () => {
    for (const size of ['sm', 'md', 'lg'] as SpinnerSize[]) {
      const { circumference, dash } = spinnerGeometry(size);
      expect(dash / circumference).toBeCloseTo(0.25, 10);
    }
  });

  it('gap is exactly 75% of circumference (three-quarter gap)', () => {
    for (const size of ['sm', 'md', 'lg'] as SpinnerSize[]) {
      const { circumference, gap } = spinnerGeometry(size);
      expect(gap / circumference).toBeCloseTo(0.75, 10);
    }
  });
});

describe('Spinner — size ordering', () => {
  it('radius increases from sm to md to lg', () => {
    expect(spinnerGeometry('sm').radius).toBeLessThan(spinnerGeometry('md').radius);
    expect(spinnerGeometry('md').radius).toBeLessThan(spinnerGeometry('lg').radius);
  });

  it('circumference increases from sm to md to lg', () => {
    expect(spinnerGeometry('sm').circumference).toBeLessThan(
      spinnerGeometry('md').circumference,
    );
    expect(spinnerGeometry('md').circumference).toBeLessThan(
      spinnerGeometry('lg').circumference,
    );
  });

  it('dim values are 16 / 24 / 32', () => {
    expect(spinnerGeometry('sm').dim).toBe(16);
    expect(spinnerGeometry('md').dim).toBe(24);
    expect(spinnerGeometry('lg').dim).toBe(32);
  });
});

// ---------------------------------------------------------------------------

describe('buildInputClasses', () => {
  it('returns base classes by default', () => {
    const classes = buildInputClasses();
    expect(classes).toContain('w-full');
    expect(classes).toContain('rounded-lg');
    expect(classes).toContain('border-[hsl(220,14%,82%)]');
    expect(classes).toContain('min-h-[44px]');
  });

  it('includes focus ring classes by default', () => {
    const classes = buildInputClasses();
    expect(classes).toContain('focus:ring-[hsl(217,91%,52%)]');
    expect(classes).toContain('focus:border-[hsl(217,91%,52%)]');
  });

  it('adds disabled classes when disabled=true', () => {
    const classes = buildInputClasses({ disabled: true });
    expect(classes).toContain('cursor-not-allowed');
    expect(classes).toContain('opacity-50');
    expect(classes).toContain('bg-[hsl(220,14%,96%)]');
  });

  it('does not add disabled classes when disabled=false', () => {
    const classes = buildInputClasses({ disabled: false });
    expect(classes).not.toContain('cursor-not-allowed');
    expect(classes).not.toContain('opacity-50');
  });

  it('adds invalid border and ring when invalid=true', () => {
    const classes = buildInputClasses({ invalid: true });
    expect(classes).toContain('border-[hsl(0,84%,60%)]');
    expect(classes).toContain('focus:ring-[hsl(0,84%,60%)]');
  });

  it('does not add invalid classes when invalid=false', () => {
    const classes = buildInputClasses({ invalid: false });
    expect(classes).not.toContain('border-[hsl(0,84%,60%)]');
  });

  it('can combine disabled and invalid', () => {
    const classes = buildInputClasses({ disabled: true, invalid: true });
    expect(classes).toContain('cursor-not-allowed');
    expect(classes).toContain('border-[hsl(0,84%,60%)]');
  });

  it('returns same base classes regardless of options shape', () => {
    const withEmpty = buildInputClasses({});
    const withUndefined = buildInputClasses(undefined);
    // Both should include the base token
    expect(withEmpty).toContain('rounded-lg');
    expect(withUndefined).toContain('rounded-lg');
  });
});
