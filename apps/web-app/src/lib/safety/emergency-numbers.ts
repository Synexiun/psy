// Frontend mirror of services/api/src/discipline/safety/emergency_numbers.py EMERGENCY_NUMBERS.
// Must be kept byte-equivalent (JSON sort_keys=True) — CI gate:
//   frontend_emergency_numbers_match_backend_byte_equivalence
//
// DO NOT edit manually. Update via the backend sprint + re-generate this file.
// verifiedAt dates are 90-day freshness windows (Rule #10).

export interface Hotline {
  id: string;
  name: string;
  number: string | null;
  sms: string | null;
  web: string | null;
  hours: string;
  cost: string;
  verifiedAt: string;
}

export interface EmergencyEntry {
  country: string;
  locale: string;
  emergency: { label: string; number: string };
  hotlines: Hotline[];
}

export const EMERGENCY_NUMBERS: EmergencyEntry[] = [
  {
    country: 'US',
    locale: 'en',
    emergency: { label: 'Emergency', number: '911' },
    hotlines: [
      {
        id: 'us-988',
        name: '988 Suicide & Crisis Lifeline',
        number: '988',
        sms: '988',
        web: 'https://988lifeline.org',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
      {
        id: 'us-crisis-text',
        name: 'Crisis Text Line',
        number: null,
        sms: 'HOME to 741741',
        web: 'https://www.crisistextline.org',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: 'GB',
    locale: 'en',
    emergency: { label: 'Emergency', number: '999' },
    hotlines: [
      {
        id: 'gb-samaritans',
        name: 'Samaritans',
        number: '116 123',
        sms: null,
        web: 'https://www.samaritans.org',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
      {
        id: 'gb-shout',
        name: 'Shout',
        number: null,
        sms: 'SHOUT to 85258',
        web: 'https://giveusashout.org',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: 'CA',
    locale: 'en',
    emergency: { label: 'Emergency', number: '911' },
    hotlines: [
      {
        id: 'ca-talk-suicide',
        name: 'Talk Suicide Canada',
        number: '1-833-456-4566',
        sms: '45645',
        web: 'https://talksuicide.ca',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: 'FR',
    locale: 'fr',
    emergency: { label: 'Urgences', number: '15' },
    hotlines: [
      {
        id: 'fr-3114',
        name: 'Numéro national de prévention du suicide',
        number: '3114',
        sms: null,
        web: 'https://www.3114.fr',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: 'SA',
    locale: 'ar',
    emergency: { label: 'طوارئ', number: '911' },
    hotlines: [
      {
        id: 'sa-mental-health',
        name: 'خط مساندة الصحة النفسية',
        number: '920033360',
        sms: null,
        web: null,
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: 'IR',
    locale: 'fa',
    emergency: { label: 'اورژانس', number: '115' },
    hotlines: [
      {
        id: 'ir-social-emergency',
        name: 'اورژانس اجتماعی',
        number: '123',
        sms: null,
        web: null,
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
  {
    country: '_INTERNATIONAL',
    locale: '_all',
    emergency: { label: 'Emergency', number: '112' },
    hotlines: [
      {
        id: 'icasa-international',
        name: 'ICASA — International Crisis & Suicide Alliance',
        number: null,
        sms: null,
        web: 'https://www.iasp.info/resources/Crisis_Centres/',
        hours: '24/7',
        cost: 'free',
        verifiedAt: '2026-04-01',
      },
    ],
  },
];
