# FAQ

The questions we get most often.

## About the app

### Is this a replacement for therapy?

No. Discipline OS is a between-sessions support tool and a tool for the moments that sit in the long gaps between therapy appointments. If you are working with a clinician or a program, this app is designed to complement that. If you are not in therapy and you think you might benefit, we can point you toward resources in [Safety resources](13_safety_resources.md).

### Does the app work offline?

The crisis path (SOS and safety resources) is fully offline — the content is on your phone. You can reach the hotline for your country and get the immediate coping tools without a network connection. Other features (syncing your journal to the cloud, updating patterns, sharing with your clinician) require a connection, but they queue up locally until a connection is available.

### Does it work on my watch?

Yes on Apple Watch (iOS). Yes on Wear OS for Android, on supported devices. The watch complication gives you SOS access in two taps.

### Do I need a wearable?

No. The app works without any wearable. If you have one and grant access, the passive signal layer has more to work with, and predictions get more accurate. Without one, the active-signal side (your check-ins, urge dials, journal entries) still drives a full product experience.

### Is there a free version?

Yes. The free tier includes the core coping tools, the T3 crisis path, the assessments, and the basic pattern view. Paid tier unlocks the full personalization (contextual bandit, extended trajectory views), advanced if-then plan library, voice journal transcription, and — when available — clinician sharing and enterprise features.

## About your data

### Can you read my journal?

**No.** Journals and voice notes are end-to-end encrypted with a key derived from your passphrase plus a secret on your device. Our servers store ciphertext only. A subpoena, a breach, or a rogue employee cannot yield readable journal content.

### Does my employer see what I do in the app?

No, not at the individual level. If your company offers this through an employee benefit, they see aggregate organization-level statistics only, subject to a minimum cohort size of 5. An admin cannot see that *you* logged an urge or that you had a rough day. This is enforced at the database level, not in the application — there is no code path that produces individual-level data to an enterprise account. Full detail in [Privacy and your data](14_privacy_and_data.md).

### What happens if I delete my account?

There is a 30-day grace period during which deletion is reversible. After that, we destroy the decryption key for your data, which cryptographically erases the remaining ciphertext (it becomes permanently unreadable). The audit log, which we are legally required to keep under HIPAA, retains a minimum-necessary record of procedural events like "user X deleted their account" — but never your journal or your scores.

### Can I export my data?

Yes. From Settings → Export, at any time, for any reason. You get a JSON archive (structured data) and a PDF summary. Your journal is decrypted locally in the export.

### Can I use the app anonymously?

Sort of. You need an email to create an account, but you do not need to provide a real name, a phone number, or any demographic data. If you want more anonymity than that, you can use the no-cloud mode — the app becomes a fully local tool with no remote component.

## About the science

### Is this evidence-based?

Yes. The coping tools are drawn from well-studied clinical traditions (Relapse Prevention / MBRP, DBT, CBT, ACT, MBSR). The psychometric instruments we use are validated and published. The intervention timing model follows the JITAI framework. Our full research basis is documented in [Methodology](../Whitepapers/01_Methodology.md) and [Clinical Evidence Base](../Whitepapers/02_Clinical_Evidence_Base.md).

That said, the *product* (Discipline OS as a specific combination of these approaches) is new. We are running our own studies to measure what it does, and we publish the results. Phase 3 includes a randomized controlled trial.

### Is it FDA-cleared?

Not at launch. Discipline OS v1.0 is a wellness product, not an FDA-regulated medical device. We have a clinical-grade software product as a separate track toward FDA SaMD clearance — the plan is documented in [Research Roadmap](../Whitepapers/05_Research_Roadmap.md).

### Can I trust the PHQ-9 score the app shows me?

Yes. We use the standard PHQ-9 scoring, cross-checked against the published reference values in the original validation paper (Kroenke, Spitzer, Williams, 2001). Scoring fidelity is a tested property of every build — if the numbers are not exactly right, the build does not ship.

### Why the specific instruments you use?

They have all been published and validated, they cover the domains most relevant to our launch population (depression, anxiety, alcohol use, stress, wellbeing, readiness to change), and they have validated translations into all four of our launch locales (with one gap, DTCQ-8 in Arabic/Persian, which we handle by substitution — see [Assessments explained](11_assessments_explained.md)).

## About safety

### What if I start to feel suicidal while using the app?

The safety path is designed exactly for this. The PHQ-9 administration will route you to safety resources if item 9 (self-harm ideation) is positive. A safety classifier running on-device watches for concerning content in journals. An explicit "I'm having thoughts of self-harm" button is never more than a couple of taps away from any screen.

When any of these trigger, you immediately see the hotline directory for your country, the local emergency number, and your pre-configured emergency contact if you have one. See [Safety resources](13_safety_resources.md).

### Will the app call for help on my behalf?

No. We make the right numbers available, clearly, one tap away. Who you call and whether you call is your decision. This is deliberate — unilateral emergency calls have been documented to produce additional harm in some situations, and we take that seriously.

### Does the app replace a clinician for a crisis?

No. If you are in an acute mental health crisis, please reach out to a crisis line or emergency services. The app is not the right tool for the most serious moments; the people on the other end of those numbers are.

## About using the app

### How much time does this take per day?

Most days, a few minutes of check-ins is plenty. Some days more if you want to use the journal or if you have an urge that needs a tool. The design goal is that the app is present when it is useful and quiet when it is not. If it feels like too much, open Settings and reduce the nudge budget — the system will listen.

### What if I keep dismissing notifications?

That is fine. If the app notices you dismiss two nudges in a row in a similar context, it will suppress that context for a week. The system is designed to learn when it is helpful and when it is not.

### What if a coping tool made me feel worse?

That is useful information — tell the app. The two-tap feedback at the end of every tool includes a "made worse" option. That feedback updates your personalization. The app will stop offering that tool in contexts where it has not worked for you.

### Can I use more than one tool in a moment?

Yes. Many people stack: a minute of box breathing into two minutes of urge surfing. There is no wrong combination.

### Why two streaks instead of one?

Because one streak — the traditional "days clean" — teaches a damaging lesson. It frames a lapse as a total reset, which is not what is actually happening. The resilience streak (urges handled) tells the truer story of what you are building, and it does not reset when a lapse happens. Full detail in [What happens after a lapse](12_after_a_lapse.md).

## About the business

### Who owns Discipline OS?

Discipline OS is built by a private company. We are venture-backed. We have a clinical advisory board with clinical veto power over safety-relevant product decisions.

### Will you get acquired by a big health company?

We plan to build independently. If an acquisition ever happened, the data governance commitments in our privacy policy and whitepapers would transfer as-is or more strictly — they cannot be relaxed by new ownership. This is written into our contracts as a condition.

### How do you make money?

Subscriptions. A paid consumer tier. An enterprise tier where companies pay per-member-per-month for their employees to have access, under the privacy protections described above. A clinician tier. None of our revenue comes from data sales or advertising.

### What about AI?

We use on-device machine learning for state estimation, pattern detection, and safety classification. We use large language models to assist with non-safety-critical operations like summarizing your journal into structured CBT fields (where you then review before saving). **We never use a large language model on the crisis path or on the safety-classification path.** See [Safety Framework](../Whitepapers/04_Safety_Framework.md) for details.

## Didn't find your question?

You can reach us through in-app support. We read every message. Your question might also become a new entry here.
