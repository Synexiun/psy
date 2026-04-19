"""Reports module tests — FHIR, PDF, user export, enterprise aggregates.

The FHIR suite in particular is a standards-conformance contract: LOINC
codes, URI systems, and payload shape are pinned against the HL7 R4 spec
and the LOINC database.  A failing test means the export has diverged from
the interop contract and downstream EHR systems may reject our bundles.
"""
