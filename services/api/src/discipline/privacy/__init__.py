"""Privacy module — DSAR export and account deletion.

Endpoints:
- ``POST /v1/privacy/export``         — DSAR: collect and return all user data as JSON
- ``POST /v1/privacy/delete-account`` — soft-delete account + schedule 30-day hard-delete

Both endpoints are authenticated and step-up gated (per 07_Security_Privacy §3 and
14_Authentication_Logging §2.8).  Every call emits an audit-stream entry; the export
endpoint also sets ``X-Phi-Boundary: 1`` because the response carries PHI.
"""
