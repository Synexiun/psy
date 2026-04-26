import { rule as noPhysicalTailwindProperties } from './rules/no-physical-tailwind-properties.js';
import { rule as clinicalNumbersMustFormat } from './rules/clinical-numbers-must-format.js';

const plugin = {
  rules: {
    'no-physical-tailwind-properties': noPhysicalTailwindProperties,
    'clinical-numbers-must-format': clinicalNumbersMustFormat,
  },
};

export default plugin;
