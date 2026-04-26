import { ESLintUtils } from '@typescript-eslint/utils';

const createRule = ESLintUtils.RuleCreator(
  (name) => `https://docs.disciplineos.internal/eslint/${name}`,
);

const PREFIX_REPLACEMENTS: Record<string, (suffix: string) => string> = {
  'ml-': (s) => `ms-${s}`,
  'mr-': (s) => `me-${s}`,
  'pl-': (s) => `ps-${s}`,
  'pr-': (s) => `pe-${s}`,
  'left-': (s) => `start-${s}`,
  'right-': (s) => `end-${s}`,
};

const EXACT_REPLACEMENTS: Record<string, string> = {
  'text-left': 'text-start',
  'text-right': 'text-end',
};

export const rule = createRule({
  name: 'no-physical-tailwind-properties',
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow physical Tailwind properties; use logical equivalents for RTL support',
    },
    messages: {
      usePhysicalLogical: "Use '{{good}}' instead of '{{bad}}' for RTL support",
    },
    schema: [],
  },
  defaultOptions: [],
  create(context) {
    return {
      JSXAttribute(node) {
        if (node.name.type !== 'JSXIdentifier' || node.name.name !== 'className') {
          return;
        }
        const value = node.value;
        if (!value || value.type !== 'Literal' || typeof value.value !== 'string') {
          return;
        }
        const tokens = value.value.split(/\s+/).filter((t) => t.length > 0);
        for (const token of tokens) {
          const exact = EXACT_REPLACEMENTS[token];
          if (exact !== undefined) {
            context.report({
              node,
              messageId: 'usePhysicalLogical',
              data: { bad: token, good: exact },
            });
            continue;
          }
          for (const [prefix, replacer] of Object.entries(PREFIX_REPLACEMENTS)) {
            if (token.startsWith(prefix) && token.length > prefix.length) {
              const good = replacer(token.slice(prefix.length));
              context.report({
                node,
                messageId: 'usePhysicalLogical',
                data: { bad: token, good },
              });
              break;
            }
          }
        }
      },
    };
  },
});
