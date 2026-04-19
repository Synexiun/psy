# 15 — Internationalization, Localization & RTL

**Document:** i18n/l10n architecture, launch locales, and right-to-left support
**Status:** Authoritative, production target
**Audience:** Mobile, web, backend, content, clinical, QA
**Launch locales (v1):** English (`en`), French (`fr`), Arabic (`ar`), Persian/Farsi (`fa`)

---

## 1. Purpose

The product launches in **four locales simultaneously**: English, French, Arabic, and Persian. Two are right-to-left. This document is the authoritative specification for:

- Locale negotiation and per-surface selection
- RTL layout and mirroring rules
- Font and typography strategy per script
- Number, date, time, currency, and unit formatting
- Translation workflow for clinical-grade content
- Validated-translation constraint for psychometric instruments
- Safety and crisis-path content requirements per locale
- Testing and QA posture

This is **not** a string-table management document. Strings are a small part of doing this correctly.

---

## 2. Why these four locales

- **English (`en`)** — primary product language; baseline.
- **French (`fr`)** — validated psychometric translations exist for every primary instrument (PHQ-9, GAD-7, AUDIT-C, AUDIT, DAST-10, PSS-10, WHO-5, DTCQ-8); large addressable population in Canada, France, Maghreb, and francophone Africa.
- **Arabic (`ar`)** — MENA market has severe undersupply of validated behavioral-health digital tools; Arabic Modern Standard ("MSA") used for clinical/formal copy, with dialect considerations noted in §10.
- **Persian/Farsi (`fa`)** — large Persian-speaking population in Iran, Afghanistan (Dari), Tajikistan (Tajik), and diaspora; validated instruments exist but coverage is narrower than Arabic.

Every locale after launch requires the same rigor; there is no "machine translate everything else" path (see §10).

---

## 3. Locale negotiation

### 3.1 Identifiers

BCP 47 tags with region where meaningful:

| Internal tag | Display | Script | Direction |
|---|---|---|---|
| `en` | English | Latn | ltr |
| `en-US` | English (US) | Latn | ltr |
| `en-GB` | English (UK) | Latn | ltr |
| `fr` | Français | Latn | ltr |
| `fr-FR` | Français (France) | Latn | ltr |
| `fr-CA` | Français (Canada) | Latn | ltr |
| `ar` | العربية | Arab | rtl |
| `ar-SA` | العربية (السعودية) | Arab | rtl |
| `ar-EG` | العربية (مصر) | Arab | rtl |
| `fa` | فارسی | Arab (Persian variant) | rtl |
| `fa-IR` | فارسی (ایران) | Arab | rtl |

For v1, regional variants of `en` and `fr` share the same content pack; regional variants of `ar` share MSA content. Regional variants of `fa` share Persian (not Dari/Tajik, which are separate future locales).

### 3.2 Selection order

Client selects locale by precedence:
1. **Explicit user preference** in Settings (persisted server-side on `users.locale`).
2. **Device OS locale** at first launch (if matches a supported locale).
3. **Accept-Language** header fallback (web).
4. **Default**: `en`.

Selected locale is written to the session JWT and to every audit/safety log entry so we can reconstruct what copy a user saw.

### 3.3 Server-side negotiation

Every authenticated request carries `Accept-Language` and the server also reads `users.locale`. Server-rendered strings (email, push notifications, PDF reports) use the server-side stored preference — not the request header — because the user's current device may be misconfigured, and an urgent push with wrong-language copy is a safety regression.

---

## 4. RTL support

Arabic and Persian require right-to-left layout. This is a layout-engine concern, not a strings concern, and touches every screen.

### 4.1 Layout mirroring

- **Mobile (React Native):** `I18nManager.isRTL` drives layout mirroring globally. Every flexbox layout uses start/end rather than left/right. `Image` and `Icon` components that carry directional meaning (back arrow, progress chevron, "tap here") are passed through a `mirror-on-rtl` helper that flips them for RTL locales. Direction-neutral icons (heart, brain, moon) are not flipped.
- **Web (Next.js):** `<html dir="rtl">` is set from server-rendered layout based on locale; CSS uses logical properties (`margin-inline-start`, `padding-block-end`, `text-align: start`) throughout; Tailwind is configured with `rtl:`/`ltr:` variants and the RTL plugin.
- **Design tokens:** Directional tokens are exposed as `space-inline-start`, `space-inline-end`. No raw `marginLeft` / `paddingRight` anywhere in the codebase. Lint rule `no-physical-direction` enforces.

### 4.2 What flips and what does not

| Element | LTR | RTL | Reason |
|---|---|---|---|
| Text flow | left→right | right→left | Script direction |
| Reading flow of cards, rows | top-left first | top-right first | Script direction |
| Back arrow, forward chevron | → | ← (mirrored) | Directional meaning |
| Progress bar fill | fills right | fills left | Directional meaning |
| Charts' x-axis (time) | oldest left → newest right | oldest right → newest left | Time mirrors |
| Clock, calendar grids | standard | **standard, not mirrored** | Clocks don't mirror; Arabic/Persian calendars read LTR for numerals in a mirrored page frame |
| Numbers | Latin 0–9 | **Latin 0–9 for scores, Arabic-Indic 0–9 for user-facing dates when locale prefers** | Clinical scores are always Latin digits for clinician reproducibility |
| Logos, brand marks | not flipped | not flipped | Brand identity |
| Play button ▶ | points right | points right | Playback direction is not linguistic |
| Video scrubber | progresses right | progresses right | Playback direction is not linguistic |
| Swipe-to-dismiss gesture | swipe left | swipe right | Matches reading direction |

### 4.3 Chart direction

Trajectory charts (PHQ-9 over time, sleep over time) are **time-on-x**. In RTL, the x-axis flips so "earliest" is on the right and "now" is on the left. This is the correct convention for time-series in Arabic and Persian print materials. Bar chart categorical axes are also mirrored. Y-axis direction is unchanged (up = more).

### 4.4 Input

- Numeric inputs accept Latin and locale-native digits; both normalized to Latin internally.
- Phone inputs default to E.164 and accept locale-preferred national formats.
- Password inputs: no restriction on Unicode; we do not block entering Arabic/Persian characters in passwords. Password strength meter is script-aware (character diversity is measured across scripts).

### 4.5 Bidi text (mixed content)

Any string that mixes LTR content (e.g., "PHQ-9: 7") inside an RTL paragraph uses Unicode bidi isolates (`\u2068`...`\u2069`) at the boundaries. The string-rendering helper inserts these automatically when a template slot contains Latin characters inside an RTL context.

---

## 5. Typography

### 5.1 Font stack per script

| Script | Primary | Fallback |
|---|---|---|
| Latin | Inter v4 | system-ui |
| Arabic | IBM Plex Sans Arabic | Noto Sans Arabic, system-ui-arabic |
| Persian | Vazirmatn v33 | IBM Plex Sans Arabic, Noto Sans Arabic, system-ui-arabic |

Persian and Arabic share the Arabic script but Persian uses additional letters (پ چ ژ گ) and stylistic preferences (kashida handling, digit shapes). Using a Persian-specific primary (Vazirmatn) rather than an Arabic-first font is the correct practice — it is not optional.

### 5.2 Font loading

- Mobile: all required font files bundled into the app binary per locale; no runtime font download. Per-locale font subsets are used to keep binary size manageable (Arabic glyph set is ~3× Latin; full subset would bloat the bundle).
- Web: `@font-face` with `font-display: swap`; preload current-locale fonts only. `unicode-range` is used to split Latin and Arabic subsets so browsers only download what the page needs.

### 5.3 Sizing & spacing

Arabic and Persian glyphs sit with different baselines and vertical rhythm than Latin. Body copy in Arabic and Persian is set **1.15× the pt size of Latin equivalents** (so 16pt Latin ≈ 18.5pt Arabic) and **line-height 1.6** (vs 1.5 for Latin). This is a published typographic best practice for Arabic script legibility on screen, and we apply it as a per-locale theme token override.

### 5.4 Digit system

Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) and Persian digits (۰۱۲۳۴۵۶۷۸۹) exist. User-facing dates, times, and non-clinical numbers in Arabic/Persian use locale digits. **Psychometric scores, adherence counts, and numbers that appear in clinical exports always use Latin 0–9** regardless of locale, because clinicians across regions expect Latin digits in scores and because scores are also exchanged with FHIR/HL7 systems that require Latin digits. This is enforced at the formatter level.

---

## 6. Date, time, and number formatting

- All formatting uses platform ICU libraries (`Intl.*` on web, `NSLocale`/`android.icu` on mobile) with the user's selected locale.
- Dates in user-facing copy use locale conventions (e.g., `١٨ أبريل ٢٠٢٦` vs `18 avril 2026` vs `April 18, 2026`).
- Dates in clinical exports (PDF clinical summary, FHIR, HL7) use **ISO 8601** exclusively regardless of locale.
- Times are 12h or 24h per locale default; users can override. All times are stored UTC with the user's tz captured at the event.
- Calendar: Gregorian is the default across all launch locales. **Hijri** (Islamic) and **Shamsi / Jalali** (Persian) calendars are supported as **secondary display** in `ar` and `fa` respectively — the user's Settings lets them choose Gregorian-only, or Gregorian with secondary Hijri/Shamsi annotations on dates. Internal storage is always Gregorian UTC.
- Currency: shown in the user's locale (EUR, USD, GBP, MAD, AED, SAR, IRR-symbol-only since IRR is blocked from Stripe) — billing occurs in USD/EUR/GBP per Stripe availability.
- Units: sleep is `hours + minutes`; body metrics use metric in every locale except `en-US` which uses imperial for weight (if ever collected; in v1 we do not).

---

## 7. Translation workflow

### 7.1 Content classes

| Class | Examples | Process |
|---|---|---|
| **Safety-critical** | Crisis screen copy, hotline scripts, T3 content, safety plan | Clinical translator (native-speaker licensed clinician) → back-translator → clinical reviewer in target country → **sign-off before deploy** |
| **Clinical-framing** | Weekly Reflection copy, intervention tool explanations, psychometric introductions | Clinical translator → clinical reviewer → sign-off |
| **Product UI** | Buttons, navigation, settings | Professional translator specializing in health/wellness → in-context review |
| **Marketing / help** | Help articles, website | Professional translator → editorial review |
| **Legal** | Privacy policy, ToS, consents | Legal translator + local counsel review |

Safety-critical and clinical-framing copy changes are **gated by sign-off from a clinical reviewer per target locale**. No PR that modifies safety-critical copy can merge without the sign-off check.

### 7.2 Tooling

- **String catalog format:** ICU MessageFormat (`.xliff` at rest, compiled to platform formats at build).
- **Translation management:** Lokalise (or Crowdin) with Enterprise BAA; translators do not see production data, only the string catalog.
- **Placeholders:** Typed. A `{count, plural, one {…} few {…} many {…} other {…}}` is validated against the source before commit.
- **In-context screenshots:** For every screen, an automated storybook run captures screenshots per locale and attaches them to the translation workspace. Translators see the screen, not just the string.
- **Back-translation:** Safety-critical strings are back-translated to English by a second translator; divergence from source flagged for clinical review.

### 7.3 Pluralization and gender

ICU plural categories differ across languages:

| Language | Categories |
|---|---|
| English | one, other |
| French | one, many, other |
| Arabic | zero, one, two, few, many, other |
| Persian | one, other |

Arabic's six categories must be handled for every count-bearing string. The string catalog enforces this — a French source string without explicit `many` handling is flagged, and an Arabic target missing any of the required plural branches cannot be merged.

Grammatical gender: French and Arabic have gendered verbs/adjectives. The user model captures an optional gender field **(pronouns, not binary)** used only for copy personalization in gendered languages. If not provided, we use the neutral/plural form (which exists for both French and Arabic and is linguistically appropriate in professional/clinical contexts).

---

## 8. Psychometric instruments: validated translations only

This is the hardest constraint in the i18n plan.

A psychometric instrument in translation is **a different instrument** until it has been psychometrically validated in that language. The original English validation does not carry over. Using a machine translation or even a professional non-clinical translation of PHQ-9 produces a tool that cannot be scored against published severity bands and cannot be presented to a clinician as "PHQ-9 score = 12".

### 8.1 What translations we can use

Per launch locale, the instrument coverage is:

| Instrument | English | French | Arabic | Persian |
|---|:-:|:-:|:-:|:-:|
| PHQ-9 | ✓ validated | ✓ validated (Carballeira et al. 2007; Houzard et al. Fr-Canadian) | ✓ validated (AlHadi et al. 2017, Saudi Arabic) | ✓ validated (Dadfar & Kabir 2016, Persian) |
| GAD-7 | ✓ | ✓ (Micoulaud-Franchi 2016) | ✓ (Sawaya et al. 2016) | ✓ (Naeinian et al. 2011) |
| AUDIT-C | ✓ | ✓ (Gache et al. 2005) | ✓ (WHO-released Arabic AUDIT) | ✓ (Moradi et al.) |
| AUDIT (full) | ✓ | ✓ | ✓ (WHO Arabic) | ✓ |
| DAST-10 | ✓ | ✓ (Bergeron et al.) | limited — investigate before ship | limited — investigate before ship |
| PSS-10 | ✓ | ✓ (Lesage et al. 2012) | ✓ (Almadi et al. 2012) | ✓ (Maroufizadeh et al. 2014) |
| WHO-5 | ✓ | ✓ (official WHO FR) | ✓ (official WHO AR) | ✓ (published Persian validation) |
| DTCQ-8 | ✓ | limited | limited | limited |
| URICA | ✓ | ✓ | limited | limited |
| Readiness Ruler | ✓ | ✓ | ✓ (with local idiom review) | ✓ |
| C-SSRS | ✓ | ✓ (official Fr) | ✓ (official Ar) | ✓ (official Fa) |
| PHQ-2, GAD-2 | ✓ | ✓ | ✓ | ✓ |

Citations are authoritative references used during scoring-function construction. Full citations live in `Docs/Whitepapers/02_Clinical_Evidence_Base.md`.

### 8.2 What happens when no validated translation exists

For an instrument-language pair with no validated translation (e.g., DTCQ-8 in Arabic as of 2026):

1. **The instrument is not presented** in that locale. The scheduler skips it for that user's active locale.
2. The user is not disadvantaged: the psychometric module has enough cross-coverage (WHO-5, PSS-10, PHQ-9, GAD-7) that core clinical signal is still captured.
3. Clinical research roadmap includes funding validation studies for missing locale-instrument pairs (see `Docs/Whitepapers/05_Research_Roadmap.md`).

### 8.3 Safety items

The PHQ-9 item 9 positive-endorsement trigger and the C-SSRS itself are **always** presented in a validated translation if the user's locale is supported. The hotline directory per locale (see §11) is the other half of this.

---

## 9. Clinical and safety content per locale

### 9.1 Launch gate

The product does not launch in a locale until:

1. Every safety-critical string is translated by a clinical translator, back-translated, clinically reviewed, and signed off.
2. Every intervention tool (urge surfing, TIPP, box breathing) script is adapted to the locale — not word-for-word translated. Idioms, metaphors, and examples are culturally grounded.
3. The hotline directory (§11) for that locale is populated with verified, in-country resources.
4. Typography is validated: sample assessment screens render correctly without orphaned bidi characters, without kashida misfires, without digit mismatches.
5. A native-speaking QA pass is completed on all 20 Detox golden flows.

Until all five are green, the locale toggle is not offered in the product.

### 9.2 Crisis path (T3)

The crisis path copy is **pre-rendered per locale on the device** as part of the app bundle. No network dependency. No translation-service call on the hot path. Missing locale at T3 time → fallback to `en`, but this is treated as a P0 bug, not as the design.

### 9.3 Arabic dialect policy

v1 uses Modern Standard Arabic (MSA) for all clinical content because:
- MSA is universally readable across MENA.
- Clinical instrument validations are all MSA-based.
- Dialect (Egyptian, Gulf, Levantine, Maghrebi) is linguistically diverse and risks clinical mistranslation.

However, intervention copy (not instruments) is written in a **plain, conversational MSA register** — not formal literary Arabic — which is closer to educated spoken Arabic in every region. Reviewers check for dialect-neutral phrasing.

### 9.4 Persian dialect policy

v1 uses Iranian Persian (Farsi). Dari (Afghanistan) and Tajik (Tajikistan) are separate locales that will require their own validation passes — the instruments do not automatically carry.

---

## 10. Strict rules on machine translation

**No machine-translated content ships to the user in any locale, period.** This rule covers:

- No MT of clinical copy. Ever.
- No MT of intervention scripts. Ever.
- No MT of psychometric items. Ever. (This would be a clinical and regulatory violation.)
- No MT of UI that touches safety (crisis plan, safety contacts, hotline directory).

Machine translation is allowed **only** for internal tooling (translator-facing memory suggestions) and must be explicitly reviewed and edited by a human before any string enters the catalog.

LLMs (Claude, GPT, etc.) are never used to translate live content in production. They may be used internally to draft first-pass translator suggestions that are then reviewed; a human translator is always in the loop and signs off.

---

## 11. Hotline & safety resource directory per locale

The safety resource directory is structured data, not copy. Each locale has a resource table:

```yaml
- locale: ar-SA
  country: SA
  hotlines:
    - name: "الخط الساخن للصحة النفسية"
      number: "920033360"
      hours: "24/7"
      languages: [ar]
      verified_at: 2026-03-01
  text_lines:
    - name: "خط نجد"
      sms_number: "1919"
      hours: "24/7"
  in_person:
    - name: "مستشفى الأمل للصحة النفسية"
      url: "https://..."
```

The directory is versioned, verified monthly, and updates are independently gated for release (a wrong phone number in a crisis screen is a P0 safety bug). The user's detected country (not locale — a Persian-speaker in Germany gets German hotlines in their language preference if possible, otherwise German hotlines in English) drives the shown directory. The 988 Lifeline is shown only to US users.

---

## 12. Data model touches

`users.locale` — stored BCP 47 tag.
`users.calendar_preference` — `gregorian` | `gregorian_with_hijri` | `gregorian_with_shamsi`.
`users.tz` — IANA time zone identifier.
`users.digit_preference` — `auto` (locale default) | `latin` (always Latin digits for non-clinical numbers).

All copy-bearing rows in operational tables (intervention content, pattern explanations) carry a `locale` field and rows are keyed `(content_id, locale)`.

---

## 13. Testing

| Test | What it asserts |
|---|---|
| **Snapshot per locale** | Every screen snapshot-tested in all 4 locales + RTL flip; changes require visual review |
| **Bidi isolation** | Every dynamic string slot with a Latin token inside RTL context has proper bidi markers |
| **Plural coverage** | Every count-bearing string has all required plural branches per locale |
| **Digit system correctness** | Clinical score displays use Latin digits in all locales; dates use locale digits when `digit_preference: auto` |
| **Font availability** | Required glyphs render without `.notdef` boxes on every target device |
| **RTL gesture correctness** | Swipe-to-dismiss and back gestures reverse in RTL; detox tests pass |
| **Safety content present** | Per locale: every crisis string, every hotline, every intervention script has a non-empty, reviewed entry. Missing entry in a supported locale fails CI |
| **MT detection** | A linting step scans new translations against a machine-translation fingerprint and flags suspiciously MT-looking additions for review |

---

## 14. Backend module structure

```
services/api/src/discipline/shared/i18n/
├── negotiation.py           # Accept-Language + user pref resolution
├── formatters.py            # date/time/number locale-aware formatters
├── bidi.py                  # bidi isolate helpers
├── catalog.py               # server-side string catalog (for emails, push, PDF)
└── tests/
services/api/src/discipline/content/
├── safety_directory.py      # per-locale hotline directory loader
├── intervention_content.py  # per-locale intervention scripts
└── tests/
```

Mobile / Web i18n libraries:

- Mobile: `i18next` + `i18next-icu` + `react-i18next`, string catalog pre-compiled at build.
- Web: `next-intl` with ICU support and locale-aware routing (`/en/...`, `/fr/...`, `/ar/...`, `/fa/...`).

---

## 15. Out of scope for v1

- Sign language content (a v2 commitment, with careful clinical advisor involvement).
- Locales beyond the four above (Spanish, German, Dari, Tajik, Urdu, Turkish — all tracked in the future-locale roadmap).
- Voice-interface localization of Whisper-small for Arabic/Persian is enabled (Whisper supports both); TTS in Arabic/Persian is not in v1.

---

## 16. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-18 | Initial authoritative specification |
