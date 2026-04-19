# Privacy and your data

What the app knows, where that information lives, what we do and do not do with it, and how you stay in control. In plain language.

## What we collect — and don't

### On your device only

These never leave your phone:

- Raw heart rate samples, HRV measurements, sleep stages, workout details.
- Typing cadence, app-switching patterns, screen unlock frequency.
- Your device's specific location coordinates.

These are used by the on-device model to estimate your state. The model runs locally. The cloud sees only the *results* — low-resolution state categories — not the raw signals.

### In our cloud

- **Account identity:** email, and only what you choose to add (name, phone if enabled).
- **Structured data:** urge dial readings, which tool you used, how it went, assessment scores, if-then plans. These are encrypted at rest with a key that is specific to your account.
- **Your journal and voice notes:** encrypted **on your device, before they leave**, with a key derived from your passphrase plus a secret stored in your phone's secure enclave. **The server stores ciphertext. We cannot read your journal.** This is the meaningful privacy property: even a subpoena, even a breach of our database, yields unreadable content.
- **Location class (not coordinates):** "home," "work," "a place you've flagged as risky," "transit," "other." Not your address.
- **Low-cardinality state estimates:** categories, not values.

### Operational logs

- **App logs and infrastructure logs:** these are kept for operations and debugging. Our logging system has a strict rule — **no personally identifying information or health data is permitted in operational logs**. We use a two-layer redactor (at the source and at the sink) to enforce this. Where an operation needs to reference a user, it uses a hashed, salted identifier, not the real one.

### What we do not collect

- Your contacts list (the contact-a-human list is stored as names you provide, not by syncing your phone's contacts).
- Advertising identifiers — we do not integrate with ad networks.
- Your browsing activity outside the app.
- Third-party analytics SDKs that egress data. Internal analytics go through a PHI-free event layer that's been explicitly vetted.

## What we do with it

### Things we do

- **Run the product for you.** Personalize which tool is surfaced when, adjust check-in cadence, build your pattern view.
- **Support you if something goes wrong.** Our support team can look up the *fact* of your account and the non-content telemetry of how the app has been behaving. Support agents cannot read your journal. Their access is logged, audited, and requires a specific justification.
- **Meet legal obligations.** Things like HIPAA audit logs, which we are required to keep.
- **Improve the product in aggregate.** Anonymous, aggregate cohort analytics, with strict re-identification protections. Individual users are not visible here.

### Things we do not do

- **We do not sell your data.** Ever. This is contractual as well as moral.
- **We do not share your data with advertisers.** Ever.
- **We do not share with your employer.** If you use the app through an enterprise benefit, your employer sees aggregate statistics at the team or organization level, subject to minimum cohort sizes. They do not see individual-level data. They do not see that you logged an urge. They do not see that you had a rough day. **This is enforced in the database, not in the app** — our systems mathematically cannot produce that answer.
- **We do not share with insurers**, unless you explicitly use an insurance-reimbursed pathway that requires it and you have consented.
- **We do not contact emergency services for you.** At the safety-critical T4 level, we show you the right numbers — you make the call.

## Your controls

### Granular permissions

Every passive signal (HealthKit, Health Connect, location, calendar, notifications) can be turned on or off independently. The app does not bundle permissions, and turning a permission off does not lock you out of the app.

### No-cloud mode

You can opt out of cloud sync entirely. Your app becomes a local tool with no remote learning, no clinician sharing, no cross-device sync, and no enterprise reporting. The tradeoff is transparent. If you want the privacy floor, this is it.

### App-lock

Biometric or PIN to open the app. On iOS and Android.

### Alternate icon mode

Your app can appear on your home screen as "Reflect" or "Compass" or similar, without the Discipline OS name. Useful if you share a device or just want another layer of privacy.

### Hidden from recents

The app can be set to not appear in the iOS or Android task switcher.

### Quick-erase

Three taps to wipe all local data. This does not delete your cloud account — it clears your device.

### Export your data

You can export everything — assessment scores, urge logs, journal entries (decrypted locally), if-then plans, patterns — as a JSON archive and a PDF summary. Any time, for any reason.

### Delete your account

Delete your account and all your data is purged. There is a 30-day grace period (reversible), and then we cryptographically erase the decryption key for your data. After that point, the ciphertext still on disk cannot be read by anyone, including us.

One exception: the audit log, which we are legally required to keep under HIPAA, retains the minimum necessary record of access events. This does not include your journal or your scores — only the procedural record of things like "user X deleted their account on date Y." This is reviewed annually to keep the scope minimal.

## Where your data lives

- **By default:** AWS infrastructure in the United States (us-east-1), HIPAA-eligible services only, with BAAs signed.
- **If you are in the EU:** EU-based infrastructure (eu-central-1) as our EU rollout completes. EU user data does not leave the EU by default.

## Who has access inside the company

Internal access is strictly limited. No one at Discipline OS reads your journal content — not engineers, not support, not clinicians. The system is designed so it cannot be read by us.

Structured data access (for support, for engineering operations) goes through an authorization flow that:

- Requires re-authentication with a fresh factor (not just "are you still logged in?").
- Requires a justification written into the audit log.
- Is scoped to the minimum necessary.
- Is reviewed weekly by the compliance team.

## If something happens

If we detect or are notified of a data breach involving your information, you will be notified under the timeline required by law (HIPAA, state breach laws, GDPR). We will tell you what happened, what was affected, and what we are doing.

## Transparency

- Our full privacy architecture is documented in a public whitepaper: [Privacy Architecture](../Whitepapers/03_Privacy_Architecture.md).
- Our privacy policy is available at www.disciplineos.com/privacy.
- An annual external audit covers our privacy and security posture.
- Significant changes are announced, not quietly deployed.

## Questions

You can reach us through in-app support for anything about your data. We answer.
