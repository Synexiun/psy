import { RuleTester } from '@typescript-eslint/rule-tester';
import { afterAll, describe, it } from 'vitest';
import { rule } from '../src/rules/clinical-numbers-must-format.js';

RuleTester.afterAll = afterAll;
RuleTester.it = it;
RuleTester.itOnly = it.only;
RuleTester.describe = describe;

const ruleTester = new RuleTester({
  languageOptions: {
    parserOptions: {
      ecmaFeatures: { jsx: true },
    },
  },
});

ruleTester.run('clinical-numbers-must-format', rule, {
  valid: [
    // 1. Wrapped in formatNumberClinical()
    { code: '<div>{formatNumberClinical(score)}</div>' },
    // 2. Exact token "clinical-number" in className
    { code: '<div className="clinical-number">{score}</div>' },
    // 3. Token in multi-class string
    { code: '<div className="text-lg clinical-number font-semibold">{score}</div>' },
    // 4. Unrelated identifier — not a clinical numeric pattern
    { code: '<div>{regularCount}</div>' },
    // 5. Boolean suffix deny-list: phq9Skipped
    { code: '<div>{phq9Skipped}</div>' },
    // 6. Boolean suffix deny-list: auditCompleted matches ^auditC but has "Completed"
    { code: '<div>{auditCompleted}</div>' },
  ],
  invalid: [
    // 1. Bare identifier matching ^phq9
    {
      code: '<div>{phq9Score}</div>',
      errors: [
        {
          messageId: 'wrapClinicalNumber',
          data: { name: 'phq9Score' },
        },
      ],
    },
    // 2. Bare keyword matching ^score$
    {
      code: '<div>{score}</div>',
      errors: [
        {
          messageId: 'wrapClinicalNumber',
          data: { name: 'score' },
        },
      ],
    },
    // 3. Matches ^auditC
    {
      code: '<div>{auditCScore}</div>',
      errors: [
        {
          messageId: 'wrapClinicalNumber',
          data: { name: 'auditCScore' },
        },
      ],
    },
    // 4. Matches ^rci[A-Z]
    {
      code: '<div>{rciDelta}</div>',
      errors: [
        {
          messageId: 'wrapClinicalNumber',
          data: { name: 'rciDelta' },
        },
      ],
    },
    // 5. Member expression: property "intensity" matches ^intensity$
    {
      code: '<span>{user.intensity}</span>',
      errors: [
        {
          messageId: 'wrapClinicalNumber',
          data: { name: 'intensity' },
        },
      ],
    },
  ],
});
