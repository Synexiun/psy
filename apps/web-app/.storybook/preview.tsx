import React from 'react';
import type { Preview } from '@storybook/react';
import { ThemeProvider } from 'next-themes';
import { NextIntlClientProvider } from 'next-intl';
import '../src/app/globals.css';

const preview: Preview = {
  globalTypes: {
    theme: {
      description: 'Color theme',
      defaultValue: 'dark',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: ['dark', 'light'],
        dynamicTitle: true,
      },
    },
    locale: {
      description: 'Locale',
      defaultValue: 'en',
      toolbar: {
        title: 'Locale',
        icon: 'globe',
        items: [
          { value: 'en', title: 'English (LTR)' },
          { value: 'ar', title: 'Arabic (RTL)' },
        ],
        dynamicTitle: true,
      },
    },
  },
  decorators: [
    (Story, context) => {
      const theme = (context.globals['theme'] as string) ?? 'dark';
      const locale = (context.globals['locale'] as string) ?? 'en';
      const dir = locale === 'ar' ? 'rtl' : 'ltr';
      return (
        <ThemeProvider
          attribute="data-theme"
          defaultTheme={theme}
          forcedTheme={theme}
          themes={['dark', 'light']}
          disableTransitionOnChange
        >
          <NextIntlClientProvider locale={locale} messages={{}}>
            <div dir={dir} lang={locale} style={{ minHeight: '100vh', padding: '1rem' }}>
              <Story />
            </div>
          </NextIntlClientProvider>
        </ThemeProvider>
      );
    },
  ],
};

export default preview;
