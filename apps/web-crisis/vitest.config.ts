import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    reporters: process.env.CI ? ['default', 'junit'] : 'default',
    outputFile: process.env.CI ? { junit: './tests/unit/junit.xml' } : undefined,
  },
  resolve: {
    alias: {
      '@': __dirname + '/src',
    },
  },
});
