import { RuleTester } from '@typescript-eslint/rule-tester';
import { afterAll, describe, it } from 'vitest';
import { rule } from '../src/rules/no-physical-tailwind-properties.js';

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

ruleTester.run('no-physical-tailwind-properties', rule, {
  valid: [
    { code: '<div className="ms-4" />' },
    { code: '<div className="me-2 ps-4 pe-1" />' },
    { code: '<div className="text-start" />' },
    { code: '<div className="m-4 p-2" />' },
    { code: '<div className="grid grid-cols-2" />' },
    { code: '<div className="text-lg font-semibold" />' },
  ],
  invalid: [
    {
      code: '<div className="ml-4" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'ml-4', good: 'ms-4' },
        },
      ],
    },
    {
      code: '<div className="mr-2" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'mr-2', good: 'me-2' },
        },
      ],
    },
    {
      code: '<div className="pl-4 pr-2" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'pl-4', good: 'ps-4' },
        },
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'pr-2', good: 'pe-2' },
        },
      ],
    },
    {
      code: '<div className="text-left" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'text-left', good: 'text-start' },
        },
      ],
    },
    {
      code: '<div className="text-right" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'text-right', good: 'text-end' },
        },
      ],
    },
    {
      code: '<div className="absolute left-0 top-0" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'left-0', good: 'start-0' },
        },
      ],
    },
    {
      code: '<div className="right-4" />',
      errors: [
        {
          messageId: 'usePhysicalLogical',
          data: { bad: 'right-4', good: 'end-4' },
        },
      ],
    },
  ],
});
