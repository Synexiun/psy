/**
 * Domain-specific schema barrel.
 * The root `schemas.ts` exports shared primitive schemas (locale, user profile, etc.).
 * This barrel re-exports all domain schemas so consumers can do:
 *
 *   import { StreakStateSchema, PatternSchema } from '@disciplineos/api-client/schemas';
 */

export * from './streak';
export * from './pattern';
export * from './state';
export * from './urge';
export * from './relapse';
export * from './assessment';
