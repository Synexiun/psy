import { describe, it, expect } from 'vitest';
import { ApiError, isApiError } from './errors';

describe('ApiError', () => {
  it('stores status, code, and message', () => {
    const err = new ApiError(404, { code: 'not_found', message: 'Missing' });
    expect(err.status).toBe(404);
    expect(err.code).toBe('not_found');
    expect(err.message).toBe('Missing');
    expect(err.name).toBe('ApiError');
  });

  it('identifies retryable errors', () => {
    expect(new ApiError(503, { code: 'server_error', message: 'Down' }).isRetryable()).toBe(true);
    expect(new ApiError(429, { code: 'rate_limited', message: 'Slow' }).isRetryable()).toBe(true);
    expect(new ApiError(0, { code: 'network_error', message: 'Offline' }).isRetryable()).toBe(true);
    expect(new ApiError(400, { code: 'validation.invalid_payload', message: 'Bad' }).isRetryable()).toBe(false);
  });

  it('identifies step-up requirement', () => {
    expect(new ApiError(403, { code: 'auth.step_up_required', message: 'Step up' }).requiresStepUp()).toBe(true);
    expect(new ApiError(403, { code: 'forbidden', message: 'Nope' }).requiresStepUp()).toBe(false);
  });

  it('isApiError narrows correctly', () => {
    expect(isApiError(new ApiError(500, { code: 'server_error', message: 'x' }))).toBe(true);
    expect(isApiError(new Error('plain'))).toBe(false);
  });
});
