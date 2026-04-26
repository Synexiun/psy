import type { Meta, StoryObj } from '@storybook/react';
import { RadioGroup } from '../RadioGroup';

const EN_OPTIONS = [
  { value: 'calm', label: 'Calm', description: 'Low urge intensity' },
  { value: 'moderate', label: 'Moderate', description: 'Manageable urge' },
  { value: 'intense', label: 'Intense', description: 'High urge intensity' },
];

const AR_OPTIONS = [
  { value: 'calm', label: 'هادئ', description: 'شدة منخفضة' },
  { value: 'moderate', label: 'معتدل', description: 'رغبة قابلة للإدارة' },
  { value: 'intense', label: 'مكثف', description: 'شدة عالية' },
];

const meta: Meta<typeof RadioGroup> = {
  title: 'Design System / Primitives / RadioGroup',
  component: RadioGroup,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based RadioGroup primitive with Quiet Strength tokens. Supports vertical and horizontal orientations, per-option descriptions, and full RTL via a `dir="rtl"` wrapper.',
      },
    },
  },
  argTypes: {
    orientation: { control: 'select', options: ['vertical', 'horizontal'] },
    disabled: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof RadioGroup>;

export const Default: Story = {
  name: 'Default',
  args: { options: EN_OPTIONS, defaultValue: 'calm', orientation: 'vertical' },
};

export const Horizontal: Story = {
  name: 'Horizontal',
  args: {
    options: EN_OPTIONS.map((o) => ({ value: o.value, label: o.label })),
    orientation: 'horizontal',
  },
};

export const WithDescription: Story = {
  name: 'With description',
  args: { options: EN_OPTIONS, defaultValue: 'moderate' },
};

export const Disabled: Story = {
  name: 'Disabled',
  args: { options: EN_OPTIONS, defaultValue: 'calm', disabled: true },
};

export const RTLContext: Story = {
  name: 'RTL context (ar)',
  render: () => (
    <div dir="rtl" className="w-64">
      <RadioGroup options={AR_OPTIONS} defaultValue="calm" ariaLabel="مستوى الرغبة" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context the indicator and label order are automatically mirrored. Wrap the RadioGroup in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
