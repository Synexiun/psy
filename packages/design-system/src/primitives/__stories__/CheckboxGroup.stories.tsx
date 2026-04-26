import type { Meta, StoryObj } from '@storybook/react';
import { CheckboxGroup } from '../CheckboxGroup';

const EN_OPTIONS = [
  { value: 'mood', label: 'Mood tracking', description: 'Daily mood check-ins' },
  { value: 'urge', label: 'Urge logging', description: 'Track urge intensity' },
  { value: 'sleep', label: 'Sleep data', description: 'Optional sleep quality' },
];

const AR_OPTIONS = [
  { value: 'mood', label: 'تتبع المزاج', description: 'تسجيل المزاج اليومي' },
  { value: 'urge', label: 'تسجيل الرغبة', description: 'قياس شدة الرغبة' },
  { value: 'sleep', label: 'بيانات النوم', description: 'جودة النوم الاختيارية' },
];

const meta: Meta<typeof CheckboxGroup> = {
  title: 'Design System / Primitives / CheckboxGroup',
  component: CheckboxGroup,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based CheckboxGroup primitive with Quiet Strength tokens. Supports controlled and uncontrolled modes, vertical and horizontal orientations, per-option descriptions, and full RTL via a `dir="rtl"` wrapper.',
      },
    },
  },
  argTypes: {
    orientation: { control: 'select', options: ['vertical', 'horizontal'] },
    disabled: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof CheckboxGroup>;

export const Default: Story = {
  name: 'Default',
  args: { options: EN_OPTIONS, defaultValue: ['mood', 'urge'] },
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
  args: { options: EN_OPTIONS, defaultValue: ['mood'] },
};

export const AllDisabled: Story = {
  name: 'All disabled',
  args: { options: EN_OPTIONS, defaultValue: ['mood'], disabled: true },
};

export const RTLContext: Story = {
  name: 'RTL context (ar)',
  render: () => (
    <div dir="rtl" className="w-72">
      <CheckboxGroup
        options={AR_OPTIONS}
        defaultValue={['mood']}
        ariaLabel="إعدادات التتبع"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context the checkbox and label order are automatically mirrored via logical CSS properties. Wrap the CheckboxGroup in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
