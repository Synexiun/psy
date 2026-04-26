import type { Meta, StoryObj } from '@storybook/react';
import { Select } from '../Select';

const EN_OPTIONS = [
  { value: 'calm', label: 'Calm' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'intense', label: 'Intense' },
  { value: 'severe', label: 'Severe', disabled: true },
];

const EN_GROUPS = [
  {
    label: 'Mood',
    options: [
      { value: 'calm', label: 'Calm' },
      { value: 'moderate', label: 'Moderate' },
    ],
  },
  {
    label: 'Urge Intensity',
    options: [
      { value: 'low', label: 'Low urge' },
      { value: 'high', label: 'High urge' },
      { value: 'crisis', label: 'Crisis level', disabled: true },
    ],
  },
];

const AR_OPTIONS = [
  { value: 'calm', label: 'هادئ' },
  { value: 'moderate', label: 'معتدل' },
  { value: 'intense', label: 'مكثف' },
  { value: 'severe', label: 'شديد', disabled: true },
];

const meta: Meta<typeof Select> = {
  title: 'Design System / Primitives / Select',
  component: Select,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Select primitive with Quiet Strength tokens. Supports flat and grouped option lists, controlled and uncontrolled modes, optional visible label with htmlFor association, and full RTL via a `dir="rtl"` wrapper.',
      },
    },
  },
  argTypes: {
    disabled: { control: 'boolean' },
    placeholder: { control: 'text' },
    label: { control: 'text' },
    ariaLabel: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof Select>;

export const Default: Story = {
  name: 'Default',
  args: {
    options: EN_OPTIONS,
    ariaLabel: 'Urge intensity',
    placeholder: 'Select intensity…',
  },
};

export const WithLabel: Story = {
  name: 'With label',
  args: {
    options: EN_OPTIONS,
    label: 'Urge intensity',
    placeholder: 'Select intensity…',
  },
};

export const WithGroups: Story = {
  name: 'With groups',
  args: {
    groups: EN_GROUPS,
    label: 'Assessment category',
    placeholder: 'Select category…',
  },
};

export const Disabled: Story = {
  name: 'Disabled',
  args: {
    options: EN_OPTIONS,
    label: 'Urge intensity',
    defaultValue: 'calm',
    disabled: true,
  },
};

export const RTLContext: Story = {
  name: 'RTL context (ar)',
  render: () => (
    <div dir="rtl" className="w-64">
      <Select
        options={AR_OPTIONS}
        label="شدة الرغبة"
        placeholder="اختر الشدة…"
        defaultValue="calm"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context the trigger chevron, item check indicator, and group label padding are automatically mirrored via logical CSS properties (`ps-*`/`pe-*`/`start-*`). Wrap the Select in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
