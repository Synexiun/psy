# Security Policy

## Supported Versions

Only the latest production release receives security updates.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Email: security@disciplineos.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix

We will acknowledge within 24 hours and provide a timeline within 72 hours.

## Clinical Safety Issues

Bugs that affect the T3/T4 crisis path or psychometric scoring accuracy are treated as P0 and
escalated to clinical QA immediately, regardless of security severity. These issues have a
pre-agreed fast lane targeting a deployed fix within 60 minutes of problem identification.

## Severity Tiers

| Tier | Definition | Response SLA |
|------|-----------|-------------|
| S0 | Confirmed PHI breach, active exploit | Immediate page; CISO + CEO within 1h |
| S1 | High-risk exposure, no confirmed exfil | 2h response; full team within 4h |
| S2 | Elevated risk, containment in progress | 6h response |
| S3 | Low-risk; non-PHI | Standard business hours |

## Disclosure Policy

We follow responsible disclosure. We ask for 90 days to remediate before public disclosure.
For vulnerabilities affecting the crisis path or PHI, we will communicate a more aggressive
internal timeline on a case-by-case basis.

## Bug Bounty

A formal bug bounty program (HackerOne or Intigriti) is planned post-launch (Month 16+).
Reward range: $100 – $25,000 based on severity and scope.
