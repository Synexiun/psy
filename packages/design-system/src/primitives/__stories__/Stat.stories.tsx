import type { Meta, StoryObj } from '@storybook/react';
import { Stat } from '../Stat';

const meta: Meta<typeof Stat> = {
  title: 'Design System / Primitives / Stat',
  component: Stat,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Quiet Strength–tokenised hero-number primitive. Displays a headline metric (streak count, PHQ-9 score, weekly check-ins, etc.) with an optional delta and label. When `clinical` is true the number is rendered with `direction: ltr` and `font-variant-numeric: tabular-nums` to enforce Latin digits across all locales (Rule #9). Pass `formatValue={formatNumberClinical}` from `@disciplineos/i18n-catalog` in clinical contexts.',
      },
    },
  },
  argTypes: {
    value: {
      control: { type: 'number' },
      description: 'The numeric value to display',
    },
    label: {
      control: 'text',
      description: 'Visible label rendered below the number',
    },
    delta: {
      control: { type: 'number' },
      description: 'Change since last period (positive = up, negative = down)',
    },
    deltaDirection: {
      control: 'select',
      options: ['up', 'down', 'neutral'],
      description: 'Explicit delta direction — overrides sign-derived direction',
    },
    deltaLabel: {
      control: 'text',
      description: 'Suffix for the delta line, e.g. "vs last week"',
    },
    clinical: {
      control: 'boolean',
      description: 'Enforce ltr + tabular-nums for clinical number rendering (Rule #9)',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Hero number size preset (sm=text-2xl, md=text-4xl, lg=text-6xl)',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Stat>;

// ---------------------------------------------------------------------------
// 1. Default
// ---------------------------------------------------------------------------

export const Default: Story = {
  name: 'Default',
  args: {
    value: 47,
    label: 'Resilience Days',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default `md` size hero number with a label. No delta. Token: `text-ink-primary`, `font-display`.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 2. WithPositiveDelta
// ---------------------------------------------------------------------------

export const WithPositiveDelta: Story = {
  name: 'With Positive Delta',
  args: {
    value: 47,
    label: 'Resilience Days',
    delta: 3,
    deltaLabel: 'vs last week',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`delta > 0` → `text-signal-stable` (teal) with an up-arrow. Signals improvement.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 3. WithNegativeDelta
// ---------------------------------------------------------------------------

export const WithNegativeDelta: Story = {
  name: 'With Negative Delta',
  args: {
    value: 10,
    label: 'PHQ-9 Score',
    delta: -2,
  },
  parameters: {
    docs: {
      description: {
        story:
          '`delta < 0` → `text-signal-warning` (amber) with a down-arrow. Signals decline.',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 4. Clinical — LTR enforcement
// ---------------------------------------------------------------------------

export const Clinical: Story = {
  name: 'Clinical (LTR enforced)',
  args: {
    value: 14,
    label: 'PHQ-9 Score',
    clinical: true,
    formatValue: (n: number) => n.toString(),
    delta: -3,
    deltaLabel: 'vs baseline',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`clinical=true` enforces `direction: ltr` and `font-variant-numeric: tabular-nums` on the number span. In production pass `formatValue={formatNumberClinical}` from `@disciplineos/i18n-catalog`. This ensures Latin digits are rendered regardless of page locale (Rule #9).',
      },
    },
  },
};

// ---------------------------------------------------------------------------
// 5–8. Dark/Light × EN/AR 2×2 matrix
// ---------------------------------------------------------------------------

export const DarkEn: Story = {
  name: 'Dark — English',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex gap-8 items-start"
      data-theme="dark"
    >
      <Stat value={47} label="Resilience Days" delta={3} deltaLabel="vs last week" />
      <Stat value={14} label="PHQ-9 Score" delta={-2} size="sm" />
      <Stat value={7} label="Weekly Check-ins" size="lg" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Dark theme — English locale. All three size variants side-by-side.',
      },
    },
  },
};

export const DarkAr: Story = {
  name: 'Dark — Arabic (RTL)',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex gap-8 items-start"
      data-theme="dark"
      dir="rtl"
      lang="ar"
    >
      <Stat value={47} label="أيام المرونة" delta={3} deltaLabel="مقارنة بالأسبوع الماضي" />
      <Stat
        value={14}
        label="نتيجة PHQ-9"
        delta={-2}
        size="sm"
        clinical={true}
        formatValue={(n) => n.toString()}
      />
      <Stat value={7} label="تسجيلات أسبوعية" size="lg" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Dark theme — Arabic RTL locale. The `clinical` stat with `direction: ltr` enforces Latin digits even within the RTL flow (Rule #9).',
      },
    },
  },
};

export const LightEn: Story = {
  name: 'Light — English',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex gap-8 items-start"
      data-theme="light"
    >
      <Stat value={47} label="Resilience Days" delta={3} deltaLabel="vs last week" />
      <Stat value={14} label="PHQ-9 Score" delta={-2} size="sm" />
      <Stat value={7} label="Weekly Check-ins" size="lg" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Light theme — English locale. Tokens remap via `[data-theme="light"]` overrides in globals.css.',
      },
    },
  },
};

export const LightAr: Story = {
  name: 'Light — Arabic (RTL)',
  render: () => (
    <div
      className="bg-surface-primary p-8 rounded-2xl flex gap-8 items-start"
      data-theme="light"
      dir="rtl"
      lang="ar"
    >
      <Stat value={47} label="أيام المرونة" delta={3} deltaLabel="مقارنة بالأسبوع الماضي" />
      <Stat
        value={14}
        label="نتيجة PHQ-9"
        delta={-2}
        size="sm"
        clinical={true}
        formatValue={(n) => n.toString()}
      />
      <Stat value={7} label="تسجيلات أسبوعية" size="lg" />
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Light theme — Arabic RTL locale. Clinical stat enforces LTR Latin digits.',
      },
    },
  },
};
