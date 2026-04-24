/**
 * Urge and intervention endpoint helpers.
 *
 * SOS RULE: `postSos` is provided here for API completeness but callers MUST
 * render the crisis UI immediately from the on-device pre-cached payload.
 * The network call is fire-and-forget; the UI must never block on its result.
 * See Docs/Whitepapers/04_Safety_Framework.md and CLAUDE.md non-negotiable #1.
 */

import type { ApiClient } from '../index';
import {
  UrgeLogRequestSchema,
  UrgeLogResponseSchema,
  SosRequestSchema,
  SosResponseSchema,
  UrgeResolveRequestSchema,
  InterventionOutcomeRequestSchema,
  InterventionOutcomeResponseSchema,
  NudgeAckRequestSchema,
  type UrgeLogRequest,
  type UrgeLogResponse,
  type SosRequest,
  type SosResponse,
  type UrgeResolveRequest,
  type InterventionOutcomeRequest,
  type InterventionOutcomeResponse,
  type NudgeAck,
} from '../schemas/urge';

/**
 * POST /v1/urges
 * Requires `Idempotency-Key` header (callers must provide via `init`).
 */
export async function logUrge(
  client: ApiClient,
  request: UrgeLogRequest,
  idempotencyKey: string,
): Promise<UrgeLogResponse> {
  const body = UrgeLogRequestSchema.parse(request);
  const data = await client.post<unknown>('v1/urges', body, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return UrgeLogResponseSchema.parse(data);
}

/**
 * POST /v1/sos
 * Fire-and-forget in the crisis path. See module-level SOS RULE.
 * Requires `Idempotency-Key` header.
 */
export async function postSos(
  client: ApiClient,
  request: SosRequest,
  idempotencyKey: string,
): Promise<SosResponse> {
  const body = SosRequestSchema.parse(request);
  const data = await client.post<unknown>('v1/sos', body, {
    headers: { 'Idempotency-Key': idempotencyKey },
  });
  return SosResponseSchema.parse(data);
}

/**
 * POST /v1/urges/{urge_id}/resolve
 */
export async function resolveUrge(
  client: ApiClient,
  urgeId: string,
  request: UrgeResolveRequest,
): Promise<unknown> {
  const body = UrgeResolveRequestSchema.parse(request);
  return client.post<unknown>(`v1/urges/${urgeId}/resolve`, body);
}

/**
 * POST /v1/interventions/{intervention_id}/outcome
 * Requires `Idempotency-Key` header.
 */
export async function recordOutcome(
  client: ApiClient,
  interventionId: string,
  request: InterventionOutcomeRequest,
  idempotencyKey: string,
): Promise<InterventionOutcomeResponse> {
  const body = InterventionOutcomeRequestSchema.parse(request);
  const data = await client.post<unknown>(
    `v1/interventions/${interventionId}/outcome`,
    body,
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return InterventionOutcomeResponseSchema.parse(data);
}

/**
 * POST /v1/interventions/{intervention_id}/ack
 * Returns void on 204.
 */
export async function ackIntervention(
  client: ApiClient,
  interventionId: string,
  ack: NudgeAck,
): Promise<void> {
  const body = NudgeAckRequestSchema.parse({ ack });
  await client.post<unknown>(`v1/interventions/${interventionId}/ack`, body);
}
