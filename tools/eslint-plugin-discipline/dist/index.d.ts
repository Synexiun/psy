declare const plugin: {
    rules: {
        'no-physical-tailwind-properties': import("@typescript-eslint/utils/ts-eslint").RuleModule<"usePhysicalLogical", [], unknown, import("@typescript-eslint/utils/ts-eslint").RuleListener> & {
            name: string;
        };
        'clinical-numbers-must-format': import("@typescript-eslint/utils/ts-eslint").RuleModule<"wrapClinicalNumber", [], unknown, import("@typescript-eslint/utils/ts-eslint").RuleListener> & {
            name: string;
        };
        'no-llm-on-crisis-route': import("@typescript-eslint/utils/ts-eslint").RuleModule<"noLlmOnCrisisRoute", [], unknown, import("@typescript-eslint/utils/ts-eslint").RuleListener> & {
            name: string;
        };
    };
};
export default plugin;
//# sourceMappingURL=index.d.ts.map