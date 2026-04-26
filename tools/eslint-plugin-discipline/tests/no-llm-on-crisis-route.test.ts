import { RuleTester } from '@typescript-eslint/rule-tester';
import { afterAll, describe, it } from 'vitest';
import { rule } from '../src/rules/no-llm-on-crisis-route.js';

RuleTester.afterAll = afterAll;
RuleTester.it = it;
RuleTester.itOnly = it.only;
RuleTester.describe = describe;

const ruleTester = new RuleTester({
  languageOptions: {
    parserOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
    },
  },
});

ruleTester.run('no-llm-on-crisis-route', rule, {
  valid: [
    // 1. Same LLM import from a non-crisis, non-companion path
    {
      code: "import llm from '@disciplineos/llm-client';",
      filename: 'app/[locale]/journal/page.tsx',
    },
    // 2. Safe non-LLM import from inside a crisis route
    {
      code: "import { tel } from '@disciplineos/safety-directory';",
      filename: 'app/[locale]/crisis/page.tsx',
    },
    // 3. Named import of LLM client from a journal component (not crisis/companion)
    {
      code: "import { ask } from '@disciplineos/llm-client';",
      filename: 'app/[locale]/journal/components/JournalEntry.tsx',
    },
  ],
  invalid: [
    // 1. Crisis route × default import of @disciplineos/llm-client
    {
      code: "import llm from '@disciplineos/llm-client';",
      filename: 'app/[locale]/crisis/page.tsx',
      errors: [{ messageId: 'noLlmOnCrisisRoute' }],
    },
    // 2. Crisis route × named import of @disciplineos/llm-client
    {
      code: "import { ask } from '@disciplineos/llm-client';",
      filename: 'app/[locale]/crisis/components/CrisisCard.tsx',
      errors: [{ messageId: 'noLlmOnCrisisRoute' }],
    },
    // 3. Companion route × default import of @disciplineos/llm-client
    {
      code: "import llm from '@disciplineos/llm-client';",
      filename: 'app/[locale]/companion/page.tsx',
      errors: [{ messageId: 'noLlmOnCrisisRoute' }],
    },
    // 4. Companion route × named import of @disciplineos/llm-client
    {
      code: "import { ask } from '@disciplineos/llm-client';",
      filename: 'app/[locale]/companion/components/CompanionThread.tsx',
      errors: [{ messageId: 'noLlmOnCrisisRoute' }],
    },
    // 5. Windows backslash path — verifies cross-platform normalization
    {
      code: "import llm from '@disciplineos/llm-client';",
      filename: 'app\\[locale]\\crisis\\page.tsx',
      errors: [{ messageId: 'noLlmOnCrisisRoute' }],
    },
  ],
});
