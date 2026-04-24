/**
 * @disciplineos/api-client — typed HTTP client.
 *
 * Design:
 *   - Pluggable token provider (the caller owns auth state; the client never stores secrets).
 *   - Never swallows errors — every non-2xx becomes an `ApiError` with a stable code.
 *   - Locale header + app-version header attached automatically.
 *   - Retries only idempotent GETs on transient failures; everything else is caller-initiated.
 *
 * The safety path (`POST /crisis/*`) MUST bypass this client — those endpoints run over a
 * statically-deployed circuit with its own budget (see Docs/Technicals/16_Web_Application.md §Crisis).
 */

import ky, { type KyInstance, HTTPError, TimeoutError } from 'ky';
import { ApiError, type ApiErrorPayload, type ApiErrorCode } from './errors';
import type { Locale } from './schemas';

export * from './errors';
export * from './schemas';
export * from './schemas/index';
export * from './endpoints/index';

export interface TokenProvider {
  getAccessToken: () => Promise<string | null>;
  onStepUpRequired?: () => Promise<void>;
}

export interface ApiClientOptions {
  baseUrl: string;
  locale: Locale;
  appVersion: string;
  tokenProvider: TokenProvider;
  timeoutMs?: number;
  onRequestId?: (requestId: string) => void;
}

const DEFAULT_TIMEOUT_MS = 10_000;

const toApiError = async (err: unknown): Promise<ApiError> => {
  if (err instanceof HTTPError) {
    let payload: ApiErrorPayload;
    try {
      payload = (await err.response.json()) as ApiErrorPayload;
    } catch {
      payload = {
        code: ('server_error' as ApiErrorCode),
        message: `Unexpected ${err.response.status} response`,
      };
    }
    return new ApiError(err.response.status, payload);
  }
  if (err instanceof TimeoutError) {
    return new ApiError(0, { code: 'timeout', message: 'Request timed out' });
  }
  const message = err instanceof Error ? err.message : 'Network error';
  return new ApiError(0, { code: 'network_error', message });
};

export interface ApiClient {
  get: <T>(path: string, init?: Omit<RequestInit, 'method' | 'body'>) => Promise<T>;
  post: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) => Promise<T>;
  put: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) => Promise<T>;
  patch: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) => Promise<T>;
  del: <T>(path: string, init?: Omit<RequestInit, 'method' | 'body'>) => Promise<T>;
  raw: KyInstance;
}

export const createApiClient = (opts: ApiClientOptions): ApiClient => {
  const client = ky.create({
    prefixUrl: opts.baseUrl,
    timeout: opts.timeoutMs ?? DEFAULT_TIMEOUT_MS,
    retry: {
      limit: 2,
      methods: ['get'],
      statusCodes: [408, 429, 500, 502, 503, 504],
    },
    hooks: {
      beforeRequest: [
        async (request) => {
          const token = await opts.tokenProvider.getAccessToken();
          if (token) request.headers.set('Authorization', `Bearer ${token}`);
          request.headers.set('Accept-Language', opts.locale);
          request.headers.set('X-App-Version', opts.appVersion);
        },
      ],
      afterResponse: [
        async (_request, _options, response) => {
          const requestId = response.headers.get('X-Request-Id');
          if (requestId && opts.onRequestId) opts.onRequestId(requestId);
        },
      ],
      beforeError: [
        async (error) => {
          const apiErr = await toApiError(error);
          if (apiErr.requiresStepUp() && opts.tokenProvider.onStepUpRequired) {
            await opts.tokenProvider.onStepUpRequired();
          }
          throw apiErr;
        },
      ],
    },
  });

  const wrap = <T>(p: Promise<Response>): Promise<T> =>
    p.then((r) => r.json() as Promise<T>).catch(async (e) => {
      throw isApiError(e) ? e : await toApiError(e);
    });

  return {
    get: <T>(path: string, init?: Omit<RequestInit, 'method' | 'body'>) =>
      wrap<T>(client.get(path, init)),
    post: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) =>
      wrap<T>(client.post(path, { ...init, json: body })),
    put: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) =>
      wrap<T>(client.put(path, { ...init, json: body })),
    patch: <T>(path: string, body: unknown, init?: Omit<RequestInit, 'method' | 'body'>) =>
      wrap<T>(client.patch(path, { ...init, json: body })),
    del: <T>(path: string, init?: Omit<RequestInit, 'method' | 'body'>) =>
      wrap<T>(client.delete(path, init)),
    raw: client,
  };
};

const isApiError = (e: unknown): e is ApiError => e instanceof ApiError;
