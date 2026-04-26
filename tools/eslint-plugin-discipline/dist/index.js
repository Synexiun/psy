import { rule as noPhysicalTailwindProperties } from './rules/no-physical-tailwind-properties.js';
import { rule as clinicalNumbersMustFormat } from './rules/clinical-numbers-must-format.js';
import { rule as noLlmOnCrisisRoute } from './rules/no-llm-on-crisis-route.js';
const plugin = {
    rules: {
        'no-physical-tailwind-properties': noPhysicalTailwindProperties,
        'clinical-numbers-must-format': clinicalNumbersMustFormat,
        'no-llm-on-crisis-route': noLlmOnCrisisRoute,
    },
};
export default plugin;
//# sourceMappingURL=index.js.map