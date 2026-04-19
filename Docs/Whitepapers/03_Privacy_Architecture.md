# Privacy Architecture — Data Flow, Cryptography, and Controls

**Version:** 1.0
**Audience:** External auditors, privacy engineers, enterprise customers' privacy officers, informed users
**Abstract:** Discipline OS holds sensitive mental-health data for a population that is, by construction, in vulnerable states. This document describes the privacy architecture in sufficient detail that an external auditor can verify the claims and a privacy-literate user can evaluate whether the posture meets their threshold. The core design commitments — edge-first processing, envelope encryption with per-user data encryption keys, end-to-end encryption for journal and voice content, k-anonymity and differential privacy on any aggregated output, and tamper-evident audit logging — are enumerated and justified.

---

## 1. Principles

1. **Minimization.** Data we don't collect can't be leaked, subpoenaed, or mis-handled. We resist the temptation to "collect in case we need it." Every field on every schema has a stated purpose, retention, and deletion path.

2. **Edge-first processing.** Signal processing, state estimation, and inference run on-device. Raw biometric streams (heart rate samples, HRV windows, typing cadence traces) never leave the user's device. Cloud sees low-cardinality state estimates, not raw signals.

3. **Cryptographic separation of concerns.** Different data classes have different keys, different custodians, and different access patterns. A breach of one class does not cascade.

4. **Tamper-evident auditing.** Security-relevant events (PHI reads, consent changes, auth failures, safety escalations) are written to immutable audit logs; tampering is detectable via cryptographic chain and storage-level object lock.

5. **Protective framing in aggregates.** Even de-identified aggregates can re-identify. We apply k-anonymity ≥ 5 and differential privacy on all enterprise and research-facing aggregates, and we enforce these thresholds in the database view layer — not the application — so application bugs cannot leak.

6. **User agency.** Export, quick-erase, and account deletion are first-class product features, not hidden settings.

---

## 2. Data Classification

Every field in every table is classified. Classification determines key, retention, and access policy.

| Class | Example fields | Key | Cloud retention | Notes |
|-------|----------------|-----|------------------|-------|
| **A — Identifying** | email, phone, legal name | Server KMS CMK (per-user DEK) | Account lifetime + 30d grace on deletion | Minimum set; many users never provide more than email |
| **B — PHI (structured)** | psychometric scores, urge logs, intervention outcomes, assessment responses | Per-user DEK under KMS CMK | 7y on account close (HIPAA) | Stored in Postgres with column-level encryption for sensitive fields |
| **C — PHI (content)** | journal text, voice notes | **Client-side key** (user passphrase + device secret) | Cipher-only on server; server cannot decrypt | End-to-end encrypted; server sees metadata only |
| **D — Behavioral signals (cloud)** | state estimates, 1-min summaries | Per-user DEK | 180 days default (user-configurable) | Not raw biometric streams |
| **E — Behavioral signals (on-device only)** | raw HRV, typing cadence, unlock counts | Device keystore (Keychain / Android Keystore) | **Never uploaded** | Used as input to on-device LSTM only |
| **F — Audit/Safety** | who read what when, safety classifier output, consent events | Dedicated KMS CMK, IAM-isolated | 7y (audit); 10y + legal hold (safety) | S3 Object Lock compliance mode |
| **G — Aggregate analytics** | enterprise dashboard rows | Not encrypted (already de-identified) | 2y | K-anonymity ≥ 5 + differential privacy enforced at view layer |
| **H — Operational logs** | request traces, infra logs | Not encrypted (no PHI permitted) | 90d hot / 2y cold | Source-level + sink-level redaction |

---

## 3. Cryptography

### 3.1 Key hierarchy

- **AWS KMS Customer Master Keys (CMKs)** — one per data class, one per environment, with key rotation and access policies enforced by IAM. KMS CMKs never leave AWS; we never hold the raw master key material.
- **Per-user Data Encryption Keys (DEKs)** — one per (user × data class) pair, generated on account creation, wrapped under the KMS CMK. Wrapped DEK is stored alongside the user record; unwrapping requires an authenticated KMS call.
- **Column-level encryption** for the highest-risk Class B columns (e.g. `c_ssrs_response`) — adds a second key layer so a raw DB export without KMS access is insufficient.
- **Client-side keys for Class C content** — derived from user passphrase (Argon2id KDF) bound to a device secret stored in Keychain (iOS) / Android Keystore. Server has **no** ability to decrypt Class C.

### 3.2 At rest

- **Database:** Postgres with AWS RDS default AES-256 at rest plus per-column envelope encryption for Class B sensitive columns.
- **Object storage:** S3 with SSE-KMS (customer-managed keys). Audit and safety buckets additionally have S3 **Object Lock in compliance mode** — even an admin with root credentials cannot delete within the retention period.
- **Log streams:** see `../Technicals/14_Authentication_Logging.md §9`. Four streams with distinct writer roles and destinations.
- **Backups:** encrypted; decryption requires a KMS call that emits an `audit.log` entry.

### 3.3 In transit

- TLS 1.3 externally with HSTS preload on all hostnames.
- mTLS between backend services inside the VPC.
- Certificate pinning on mobile clients (with pinning-rotation plan to prevent cert-rotation bricking).

### 3.4 Authentication tokens

- Session tokens are EdDSA (Ed25519) signed JWTs, signed by an AWS KMS key — the signing key never leaves KMS.
- Access tokens: 15-minute lifetime.
- Refresh tokens: 30-day rolling with family rotation; reuse detection forcibly revokes the entire family and logs to `security.log`.
- Step-up authentication required for sensitive actions (5-minute freshness).
- See `../Technicals/14_Authentication_Logging.md` for the full spec.

---

## 4. End-to-End Encryption for Journal and Voice

Journal text and voice notes (Class C) are encrypted with a user-derived key before leaving the device. The server stores ciphertext. This has concrete consequences:

- **A subpoena for journal content** yields ciphertext plus metadata (timestamps, sizes). Discipline OS cannot produce cleartext.
- **Password reset** requires re-entering the client-side passphrase, or the user accepts loss of pre-reset journal access. The product warns explicitly and offers an optional device-stored recovery key.
- **Server-side analytics on Class C are impossible**. Pattern extraction runs on-device; only the extracted metadata (never the raw content) is uploaded to build population priors.

The cryptographic scheme: AES-256-GCM with a 256-bit key derived via Argon2id (memory cost 64 MiB, time cost 3, parallelism 4) from the user passphrase, combined with a 256-bit device secret stored in secure enclave. Random 96-bit nonce per entry. AAD includes the entry's `user_id` and `created_at` to prevent replay across accounts.

---

## 5. Aggregate Privacy — k-Anonymity and Differential Privacy

Enterprise customers receive aggregate dashboards. Research collaborators (Phase 5) will receive a de-identified warehouse extract. Both carry re-identification risk if naïvely implemented.

### 5.1 k-anonymity

Any slice in the enterprise dashboard that covers fewer than **k = 5** members returns "not enough data" rather than a number. This applies to every intersected filter (department × tenure bucket × outcome bracket × etc.). The enforcement lives in the SQL view layer:

```sql
CREATE VIEW enterprise_report_weekly AS
SELECT dimensions, metric
FROM raw_weekly_aggregates
WHERE cohort_size >= 5;
```

The application cannot query the underlying table (IAM denies it). A bug in the application layer cannot bypass the gate.

### 5.2 Differential privacy

For numerical aggregates (counts, means), we add Laplace noise calibrated to ε = 1.0 per report × quarter, with ε budget accounted per customer to prevent composition attacks. The noise parameters are recorded with each report so that an auditor can verify what was shipped.

### 5.3 Quarterly re-identification red-team

Every quarter, a designated red-team attempts to re-identify individuals from the enterprise reports using plausibly-obtainable side information (org charts, LinkedIn metadata, tenure). Findings are fed back into gate design. This exercise is documented and its history reviewed in the SOC 2 audit.

---

## 6. Audit and Tamper Evidence

Safety-relevant and PHI-relevant events are written to append-only streams:

| Stream | Retention | Storage | Writer role |
|--------|-----------|---------|-------------|
| `app.log` | 90d hot / 2y cold | CloudWatch + S3 | `app` role |
| `audit.log` | 7 years | S3 with Object Lock (compliance mode) | `compliance` role |
| `safety.log` | 10 years + legal hold | S3 with Object Lock | `shared.logging` role |
| `security.log` | 2 years | S3 + SIEM export | `security` role |

**IAM isolation:** The four writer roles are distinct. Code in `app` cannot acquire credentials to write to `audit.log`. This is enforced at service-role boundary, not library boundary.

**Merkle chain:** Each `audit.log` and `safety.log` entry includes a hash linking to the previous entry's hash. A batch job computes chain roots daily and writes them to a separate bucket with its own writer role. Any entry modification or deletion breaks the chain; verification runs nightly.

**Writer cannot delete.** The `compliance` and `shared.logging` roles have `s3:PutObject` but not `s3:DeleteObject`. Combined with Object Lock in compliance mode, there is no admin path to silent modification within the retention period.

---

## 7. User Rights and Controls

### 7.1 Access and portability

- **Export my data** produces a JSON bundle (structured data) + decrypted journal content (decryption performed client-side). Delivered as a downloadable archive.
- **PDF summary export** for clinician handoff.
- **FHIR R4 Observation export** for interoperability.

### 7.2 Deletion

- **Account deletion:** 30-day grace period (reversible), then cryptographic erasure — the per-user DEK is destroyed in KMS, rendering all Class A/B/D ciphertext undecipherable.
- **Audit trail survives deletion.** This is a legal compliance requirement (HIPAA, GDPR permits retention for legal obligations). The audit entries are minimization-reviewed — they contain what is required, not more.
- **Quick-erase** (mobile app): 3-tap full local data wipe. Does not delete the cloud account; is a local-presence reducer.

### 7.3 No-cloud mode

Users may opt out of cloud sync entirely. In this mode the app operates as a local tool with no remote learning, no clinician sharing, no enterprise reporting. The tradeoff is disclosed transparently.

### 7.4 Right to be Forgotten (GDPR Art. 17)

Supported. Deletion request is logged (without identifying content), and the subject is removed from all non-audit data stores. Analytics warehouses periodically re-scan and purge per the latest forget-list.

### 7.5 Granular permissions

Each signal can be toggled independently — HealthKit on, Oura off, location off, calendar on. The product does not bundle permissions.

---

## 8. Threat Model

We design against the following threats:

1. **Passive network observer** → TLS 1.3 + certificate pinning + HSTS preload.
2. **Compromised device (mobile)** → secure enclave for device secret; biometric/PIN app-lock; quick-erase; hidden-from-recents.
3. **Compromised single cloud service** → envelope encryption + cryptographic separation of classes; a breach of Postgres does not yield Class C content; a breach of S3 does not yield DEKs.
4. **Malicious insider (our engineers)** → IAM-role-based access with mandatory audit; PHI access requires break-glass flow with justification; step-up auth on admin endpoints; no production PHI in logs (two-layer redaction — source + sink).
5. **Subpoena / compelled disclosure** → we can produce what we have, which for Class C is ciphertext. Data minimization means we have less to produce than competitor systems.
6. **Side-channel via metadata** → journal entry counts, timing, and sizes are still observable to an inside attacker. We document this; users who require stronger protection are offered the no-cloud mode.
7. **Re-identification of aggregates** → k-anonymity + DP + quarterly red-team.
8. **Supply chain compromise** → signed dependencies; dependency updates gated on security review; SBOM maintained; runtime SCA.
9. **Safety classifier adversarial manipulation** → dual-signal (classifier + keyword); monthly advisor review of false-negative samples; recall ≥ 98% held-out validation.
10. **Credential stuffing / brute force** → per-identity and per-IP rate limits; passkey-first flow; forced step-up on anomalous patterns.

---

## 9. Compliance Mapping

| Regulation | Posture |
|-----------|---------|
| **HIPAA (US)** | BAA signed with every processor that touches PHI. Minimum necessary rule enforced via scoped access tokens. 7-year audit retention. Breach-notification runbook tested. |
| **GDPR (EU)** | Lawful basis per processing activity (consent for most; contract for paid tier; legal obligation for audit). DPO appointed. DPIA on record. Subject Access and Erasure paths. Data-residency in eu-central-1 for EU users. |
| **UK DPA 2018 / UK GDPR** | Aligned with GDPR. ICO registration where required. |
| **SOC 2** | Type I at launch; Type II by end of Phase 3. All Common Criteria addressed; Privacy Trust Service Criterion included. |
| **FDA SaMD (Phase 4+)** | Separate regulated-product track. QMS under ISO 13485; risk management under ISO 14971; software lifecycle under IEC 62304. |
| **FTC Section 5 / Health Breach Notification Rule** | Health Breach Notification Rule applies as of 2024 updates; our breach-notification runbook covers the FTC path even absent HIPAA scope. |
| **State-level (e.g. California CMIA, Washington My Health My Data)** | Reviewed per-state; enhanced consent flows where required. |

---

## 10. Transparency Commitments

- **Annual privacy audit scope expands each year.** External auditor report made available to enterprise customers under NDA.
- **Privacy ledger for new integrations** — every third-party integration is reviewed and recorded with its data flow and risk assessment.
- **Privacy posture tightens, never loosens.** If the product changes a default in a less-private direction, the change is announced, the rationale is documented, and the old default remains available.
- **No sale of data, ever.** This is a contractual commitment, reinforced at every enterprise contract.
- **No advertising identifiers, no third-party analytics SDKs that egress PHI-adjacent data.** Internal analytics go through a PHI-free event layer (PostHog + server-side ClickHouse), configured per `../Technicals/13_Analytics_Reporting.md`.

---

## 11. References

- **NIST SP 800-53 Rev. 5.** *Security and Privacy Controls for Information Systems and Organizations.*
- **NIST SP 800-57.** *Recommendation for Key Management.*
- **HIPAA Privacy, Security, and Breach Notification Rules.** 45 CFR Parts 160, 162, and 164.
- **GDPR.** Regulation (EU) 2016/679.
- **AICPA Trust Services Criteria (TSC).** For SOC 2.
- **Dwork, C., & Roth, A. (2014).** The algorithmic foundations of differential privacy. *Foundations and Trends in Theoretical Computer Science*, 9(3-4), 211–407.
- **Sweeney, L. (2002).** k-anonymity: A model for protecting privacy. *International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems*, 10(5), 557–570.
- **Biryukov, A., Dinu, D., & Khovratovich, D. (2016).** Argon2: the memory-hard function for password hashing and other applications. IETF draft leading to RFC 9106.
