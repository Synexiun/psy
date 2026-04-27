"""Emergency numbers constant — cross-stack source of truth.

IMPORTANT: This file is the authoritative backend source for crisis hotlines.
The frontend mirrors this via `apps/web-app/src/lib/safety/emergency-numbers.ts`.
Both must be byte-equivalent (CI gate: `frontend_emergency_numbers_match_backend_byte_equivalence`).

Rules:
  - Entries older than 90 days (verifiedAt) block the locale from release (Rule #10).
  - Always include ICASA as the international fallback.
  - Never add an entry without a verifiedAt date.
  - Phone numbers use E.164 format where possible; display format in `numberDisplay`.
"""

from __future__ import annotations

# Last reviewed: 2026-04-26
# Next review due: 2026-07-25 (90-day window)
EMERGENCY_NUMBERS: list[dict] = [
    {
        "country": "US",
        "locale": "en",
        "emergency": {"label": "Emergency", "number": "911"},
        "hotlines": [
            {
                "id": "us-988",
                "name": "988 Suicide & Crisis Lifeline",
                "number": "988",
                "sms": "988",
                "web": "https://988lifeline.org",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
            {
                "id": "us-crisis-text",
                "name": "Crisis Text Line",
                "number": None,
                "sms": "HOME to 741741",
                "web": "https://www.crisistextline.org",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "GB",
        "locale": "en",
        "emergency": {"label": "Emergency", "number": "999"},
        "hotlines": [
            {
                "id": "gb-samaritans",
                "name": "Samaritans",
                "number": "116 123",
                "sms": None,
                "web": "https://www.samaritans.org",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
            {
                "id": "gb-shout",
                "name": "Shout",
                "number": None,
                "sms": "SHOUT to 85258",
                "web": "https://giveusashout.org",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "CA",
        "locale": "en",
        "emergency": {"label": "Emergency", "number": "911"},
        "hotlines": [
            {
                "id": "ca-talk-suicide",
                "name": "Talk Suicide Canada",
                "number": "1-833-456-4566",
                "sms": "45645",
                "web": "https://talksuicide.ca",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "FR",
        "locale": "fr",
        "emergency": {"label": "Urgences", "number": "15"},
        "hotlines": [
            {
                "id": "fr-3114",
                "name": "Numéro national de prévention du suicide",
                "number": "3114",
                "sms": None,
                "web": "https://www.3114.fr",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "SA",
        "locale": "ar",
        "emergency": {"label": "طوارئ", "number": "911"},
        "hotlines": [
            {
                "id": "sa-mental-health",
                "name": "خط مساندة الصحة النفسية",
                "number": "920033360",
                "sms": None,
                "web": None,
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "IR",
        "locale": "fa",
        "emergency": {"label": "اورژانس", "number": "115"},
        "hotlines": [
            {
                "id": "ir-social-emergency",
                "name": "اورژانس اجتماعی",
                "number": "123",
                "sms": None,
                "web": None,
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
    {
        "country": "_INTERNATIONAL",
        "locale": "_all",
        "emergency": {"label": "Emergency", "number": "112"},
        "hotlines": [
            {
                "id": "icasa-international",
                "name": "ICASA — International Crisis & Suicide Alliance",
                "number": None,
                "sms": None,
                "web": "https://www.iasp.info/resources/Crisis_Centres/",
                "hours": "24/7",
                "cost": "free",
                "verifiedAt": "2026-04-01",
            },
        ],
    },
]
