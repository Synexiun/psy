/**
 * Structured API errors.
 *
 * The server is the source of truth for error codes (see Docs/Technicals/03_API_Specification.md §Error envelope).
 * The client preserves the server-provided `code` verbatim so callers can branch on it without parsing strings.
 */

export type ApiErrorCode =
  | 'auth.invalid_credentials'
  | 'auth.token_expired'
  | 'auth.step_up_required'
  | 'auth.account_locked'
  | 'validation.invalid_payload'
  | 'validation.missing_field'
  | 'rate_limited'
  | 'not_found'
  | 'forbidden'
  | 'conflict'
  | 'server_error'
  | 'network_error'
  | 'timeout'
  | 'safety.crisis_content_blocked'
  | 'safety.minor_protection';

export interface ApiErrorPayload {
  code: ApiErrorCode;
  message: string;
  requestId?: string;
  retryAfterSeconds?: number;
  details?: Record<string, unknown>;
}

export class ApiError extends Error {
  public readonly code: ApiErrorCode;
  public readonly status: number;
  public readonly requestId: string | undefined;
  public readonly retryAfterSeconds: number | undefined;
  public readonly details: Record<string, unknown> | undefined;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message);
    this.name = 'ApiError';
    this.code = payload.code;
    this.status = status;
    this.requestId = payload.requestId;
    this.retryAfterSeconds = payload.retryAfterSeconds;
    this.details = payload.details;
  }

  isRetryable(): boolean {
    if (this.status >= 500) return true;
    if (this.code === 'rate_limited') return true;
    if (this.code === 'network_error' || this.code === 'timeout') return true;
    return false;
  }

  requiresStepUp(): boolean {
    return this.code === 'auth.step_up_required';
  }
}

export const isApiError = (e: unknown): e is ApiError => e instanceof ApiError;
