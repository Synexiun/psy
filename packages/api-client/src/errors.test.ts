/**
 * Unit tests for ApiError and isApiError.
 *
 * isRetryable() is the client retry-policy gate:
 *   - True:  status >= 500, rate_limited, network_error, timeout
 *   - False: everything else (auth errors, validation, not_found, conflict, safety codes)
 *
 * Safety error codes (crisis_content_blocked, minor_protection) must NOT be
 * retryable — retrying a safety-blocked request would spam the safety filter.
 *
 * requiresStepUp() is true only for auth.step_up_required (not all 403s).
 */

import { describe, it, expect } from 'vitest';
import { ApiError, isApiError } from './errors';

describe('ApiError — construction', () => {
  it('stores status, code, and message', () => {
    const err = new ApiError(404, { code: 'not_found', message: 'Missing' });
    expect(err.status).toBe(404);
    expect(err.code).toBe('not_found');
    expect(err.message).toBe('Missing');
    expect(err.name).toBe('ApiError');
  });

  it('stores optional requestId', () => {
    const err = new ApiError(400, { code: 'validation.invalid_payload', message: 'Bad', requestId: 'req-abc' });
    expect(err.requestId).toBe('req-abc');
  });

  it('stores optional retryAfterSeconds', () => {
    const err = new ApiError(429, { code: 'rate_limited', message: 'Slow', retryAfterSeconds: 30 });
    expect(err.retryAfterSeconds).toBe(30);
  });

  it('stores undefined for absent optional fields', () => {
    const err = new ApiError(404, { code: 'not_found', message: 'Gone' });
    expect(err.requestId).toBeUndefined();
    expect(err.retryAfterSeconds).toBeUndefined();
    expect(err.details).toBeUndefined();
  });
});

describe('ApiError.isRetryable() — retryable codes', () => {
  it('503 server_error → retryable (5xx)', () => {
    expect(new ApiError(503, { code: 'server_error', message: 'Down' }).isRetryable()).toBe(true);
  });

  it('500 server_error → retryable (5xx boundary)', () => {
    expect(new ApiError(500, { code: 'server_error', message: 'Error' }).isRetryable()).toBe(true);
  });

  it('429 rate_limited → retryable', () => {
    expect(new ApiError(429, { code: 'rate_limited', message: 'Slow' }).isRetryable()).toBe(true);
  });

  it('network_error (status 0) → retryable', () => {
    expect(new ApiError(0, { code: 'network_error', message: 'Offline' }).isRetryable()).toBe(true);
  });

  it('timeout → retryable (poor network — transparent retry expected)', () => {
    expect(new ApiError(0, { code: 'timeout', message: 'Timed out' }).isRetryable()).toBe(true);
  });
});

describe('ApiError.isRetryable() — non-retryable codes', () => {
  it('400 validation.invalid_payload → not retryable', () => {
    expect(new ApiError(400, { code: 'validation.invalid_payload', message: 'Bad' }).isRetryable()).toBe(false);
  });

  it('401 auth.invalid_credentials → not retryable (user must re-auth)', () => {
    expect(new ApiError(401, { code: 'auth.invalid_credentials', message: 'Bad creds' }).isRetryable()).toBe(false);
  });

  it('401 auth.token_expired → not retryable (client must refresh token)', () => {
    expect(new ApiError(401, { code: 'auth.token_expired', message: 'Expired' }).isRetryable()).toBe(false);
  });

  it('403 auth.account_locked → not retryable', () => {
    expect(new ApiError(403, { code: 'auth.account_locked', message: 'Locked' }).isRetryable()).toBe(false);
  });

  it('404 not_found → not retryable', () => {
    expect(new ApiError(404, { code: 'not_found', message: 'Gone' }).isRetryable()).toBe(false);
  });

  it('409 conflict → not retryable (re-sending idempotency-key with different body)', () => {
    expect(new ApiError(409, { code: 'conflict', message: 'Conflict' }).isRetryable()).toBe(false);
  });

  it('403 safety.crisis_content_blocked → not retryable (must not spam safety filter)', () => {
    expect(new ApiError(403, { code: 'safety.crisis_content_blocked', message: 'Blocked' }).isRetryable()).toBe(false);
  });

  it('403 safety.minor_protection → not retryable', () => {
    expect(new ApiError(403, { code: 'safety.minor_protection', message: 'Blocked' }).isRetryable()).toBe(false);
  });
});

describe('ApiError.requiresStepUp()', () => {
  it('auth.step_up_required → true', () => {
    expect(new ApiError(403, { code: 'auth.step_up_required', message: 'Step up' }).requiresStepUp()).toBe(true);
  });

  it('forbidden (plain) → false', () => {
    expect(new ApiError(403, { code: 'forbidden', message: 'Nope' }).requiresStepUp()).toBe(false);
  });

  it('auth.invalid_credentials → false (not a step-up scenario)', () => {
    expect(new ApiError(401, { code: 'auth.invalid_credentials', message: 'Bad' }).requiresStepUp()).toBe(false);
  });
});

describe('isApiError type guard', () => {
  it('returns true for ApiError instances', () => {
    expect(isApiError(new ApiError(500, { code: 'server_error', message: 'x' }))).toBe(true);
  });

  it('returns false for plain Error', () => {
    expect(isApiError(new Error('plain'))).toBe(false);
  });

  it('returns false for null', () => {
    expect(isApiError(null)).toBe(false);
  });

  it('returns false for string', () => {
    expect(isApiError('error string')).toBe(false);
  });
});
