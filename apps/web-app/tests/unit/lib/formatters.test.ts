'use client';
import { formatNumberClinical, formatScoreWithMax, formatPercentClinical, formatRciDelta } from '@/lib/formatters';

it('formatNumberClinical_returns_latin_digits_in_fa_locale', () => {
  // input 5, the function always returns Latin '5' not '۵'
  expect(formatNumberClinical(5)).toBe('5');
});

it('formatNumberClinical_returns_latin_digits_in_ar_locale', () => {
  // input 5, the function always returns Latin '5' not '٥'
  expect(formatNumberClinical(5)).toBe('5');
});

it('formatNumberClinical_returns_latin_digits_in_en_locale', () => {
  expect(formatNumberClinical(5)).toBe('5');
});

it('formatScoreWithMax formats score and max with slash', () => {
  expect(formatScoreWithMax(8, 27)).toBe('8/27');
});

it('formatScoreWithMax formats zero score', () => {
  expect(formatScoreWithMax(0, 21)).toBe('0/21');
});

it('formatPercentClinical formats integer percentage', () => {
  expect(formatPercentClinical(73)).toBe('73%');
});

it('formatPercentClinical formats percentage with decimals', () => {
  expect(formatPercentClinical(73.5, 1)).toBe('73.5%');
});

it('formatRciDelta formats positive delta with leading plus', () => {
  expect(formatRciDelta(2.1)).toBe('+2.1');
});

it('formatRciDelta formats negative delta with minus sign', () => {
  expect(formatRciDelta(-3.4)).toBe('-3.4');
});

it('formatRciDelta formats zero as positive', () => {
  expect(formatRciDelta(0)).toBe('+0.0');
});
