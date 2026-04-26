import { rule as noPhysicalTailwindProperties } from './rules/no-physical-tailwind-properties.js';

const plugin = {
  rules: {
    'no-physical-tailwind-properties': noPhysicalTailwindProperties,
  },
};

export default plugin;
