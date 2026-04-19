"""Reports module.

Produces:
- Clinical PDFs (pinned fonts, reproducible, digitally signed).
- FHIR R4 Observation bundles for clinician export.
- HL7 v2.5.1 ORU^R01 messages for legacy clinical integrations.
- HIPAA Right-of-Access user exports (JSON archive + PDF).
- Enterprise aggregates (k-anon + DP noise at the view layer).

No LLM in the report generation path — narrative copy is drawn from the
clinical-QA-signed template library.
"""
