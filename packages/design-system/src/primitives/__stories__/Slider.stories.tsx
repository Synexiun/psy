import type { Meta, StoryObj } from '@storybook/react';
import { Slider } from '../Slider';

const meta: Meta<typeof Slider> = {
  title: 'Design System / Primitives / Slider',
  component: Slider,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Slider primitive. Passes `dir` to Radix Root so thumb drag direction mirrors automatically in RTL locales (ar/fa).',
      },
    },
  },
  argTypes: {
    min: { control: 'number' },
    max: { control: 'number' },
    step: { control: 'number' },
    disabled: { control: 'boolean' },
    dir: { control: 'select', options: ['ltr', 'rtl'] },
  },
};

export default meta;
type Story = StoryObj<typeof Slider>;

export const Default: Story = {
  name: 'Default',
  args: { defaultValue: [50], min: 0, max: 100 },
  render: (args) => <div className="w-64"><Slider {...args} /></div>,
};

export const Disabled: Story = {
  name: 'Disabled',
  args: { defaultValue: [30], disabled: true },
  render: (args) => <div className="w-64"><Slider {...args} /></div>,
};

export const RTLContext: Story = {
  name: 'RTL context (ar/fa)',
  render: () => (
    <div dir="rtl" className="w-64">
      <p className="mb-3 text-sm text-ink-secondary">شدت میل</p>
      <Slider defaultValue={[70]} dir="rtl" ariaLabel="شدت میل" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context, Radix mirrors the thumb drag direction. Pass `dir="rtl"` explicitly to the Slider when the containing element is RTL.',
      },
    },
  },
};
