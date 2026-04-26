import { ESLintUtils } from '@typescript-eslint/utils';

const createRule = ESLintUtils.RuleCreator(
  (name) => `https://docs.disciplineos.internal/eslint/${name}`,
);

export const rule = createRule({
  name: 'no-llm-on-crisis-route',
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow LLM client imports in crisis or companion routes — these paths must be deterministic',
    },
    messages: {
      noLlmOnCrisisRoute:
        'LLM client must not be imported in crisis or companion routes — these paths are deterministic',
    },
    schema: [],
  },
  defaultOptions: [],
  create(context) {
    return {
      ImportDeclaration(node) {
        // Normalize backslashes for Windows path compatibility
        const filename = context.filename.replace(/\\/g, '/');

        // Match /app/ as a path segment — handles both absolute paths (/project/app/...)
        // and relative paths (app/...) that start directly with the app directory.
        const inAppDir =
          filename.includes('/app/') || filename.startsWith('app/');
        const isCrisisRoute    = /(?:^|\/)crisis(?:\/|$)/.test(filename);
        const isCompanionRoute = /(?:^|\/)companion(?:\/|$)/.test(filename);
        const inCrisisOrCompanion = inAppDir && (isCrisisRoute || isCompanionRoute);

        if (!inCrisisOrCompanion) {
          return;
        }

        const importSource = node.source.value;
        const isLlmImport =
          importSource === '@disciplineos/llm-client' ||
          importSource.includes('llm-client');

        if (isLlmImport) {
          context.report({
            node,
            messageId: 'noLlmOnCrisisRoute',
          });
        }
      },
    };
  },
});
