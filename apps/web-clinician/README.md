# web-clinician

Clinician portal for Discipline OS. **Alpha at launch** (Phase 2). Role-gated access to opt-in patient data, subject to the strongest privacy and audit requirements in the system.

## Access model

- Clerk identity provider.
- Authentication MUST present a `clinician` role claim. Role is assigned via the admin console and logged.
- Step-up re-authentication (passkey or hardware key) required before any individual-level PHI view.
- Every PHI-boundary request is marked `X-Phi-Boundary: 1` by middleware for audit-log correlation.

## Patient data boundary

- Clinicians only see data the patient has *actively opted into sharing* via the mobile/web app.
- Patients can revoke sharing at any time; revocation propagates inside 60 seconds.
- Journals and voice notes are end-to-end encrypted and **never** visible to clinicians unless the patient has explicitly shared a specific entry, decrypted on the patient's device and uploaded as a clinician-only ciphertext.

See `Docs/Whitepapers/03_Privacy_Architecture.md §Sharing model` and `Docs/Technicals/07_Security_Privacy.md`.

## Non-goals at alpha

- Not a full EHR integration yet — FHIR R4 export is read-only and triggered by the patient.
- No diagnosis or prescribing workflow.
- No group/practice billing.

## Scripts

- `pnpm dev` — local dev at http://localhost:3030
- `pnpm test:e2e` — Playwright
- `pnpm typecheck`

## Compliance

- Every access to `/clients/*` produces an audit-log row with a justification field.
- Session timeout: 15 minutes idle, 8 hours absolute.
- Export is logged and rate-limited.
