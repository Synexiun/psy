import type { StorybookConfig } from '@storybook/experimental-nextjs-vite';

const config: StorybookConfig = {
  stories: [
    '../../../packages/design-system/src/**/*.stories.@(ts|tsx)',
    '../src/components/**/*.stories.@(ts|tsx)',
  ],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-themes',
    '@storybook/addon-interactions',
  ],
  framework: {
    name: '@storybook/experimental-nextjs-vite',
    options: {},
  },
};

export default config;
