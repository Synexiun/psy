import type { Meta, StoryObj } from '@storybook/react';
import { Switch } from '../Switch';

const meta: Meta<typeof Switch> = {
  title: 'Design System / Primitives / Switch',
  component: Switch,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'Radix-based Switch primitive with Quiet Strength tokens. Supports controlled and uncontrolled modes, optional visible label with description, and full RTL via a `dir="rtl"` wrapper.',
      },
    },
  },
  argTypes: {
    checked: { control: 'boolean' },
    disabled: { control: 'boolean' },
    label: { control: 'text' },
    description: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof Switch>;

export const Default: Story = {
  name: 'Default',
  args: { ariaLabel: 'Toggle setting' },
};

export const WithLabel: Story = {
  name: 'With label and description',
  args: {
    label: 'Push notifications',
    description: 'Receive intervention reminders',
    defaultChecked: false,
  },
};

export const Checked: Story = {
  name: 'Checked',
  args: { label: 'Enabled', defaultChecked: true },
};

export const Disabled: Story = {
  name: 'Disabled',
  args: { label: 'Notifications', disabled: true, defaultChecked: false },
};

export const DisabledChecked: Story = {
  name: 'Disabled + checked',
  args: { label: 'Notifications', disabled: true, defaultChecked: true },
};

export const RTLContext: Story = {
  name: 'RTL context (ar)',
  render: () => (
    <div dir="rtl" className="w-72">
      <Switch
        label="الإشعارات"
        description="تلقي تذكيرات التدخل"
        defaultChecked
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'In a `dir="rtl"` context, Radix mirrors the thumb translation direction automatically. The label and description order is also mirrored via logical CSS properties. Wrap the Switch in a `dir="rtl"` element for Arabic (ar) and Persian (fa) locales.',
      },
    },
  },
};
