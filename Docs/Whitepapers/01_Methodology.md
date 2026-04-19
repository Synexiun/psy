# Methodology — How Discipline OS Works

**Version:** 1.0
**Audience:** Clinicians, researchers, partners, clinical advisory board
**Abstract:** Discipline OS is a closed-loop, edge-first behavioral intervention system designed to reduce the probability that a person acts on an urge that contradicts their stated goals. It integrates **Relapse Prevention (RP)**, **Just-in-Time Adaptive Intervention (JITAI)**, and **implementation-intention** frameworks with contemporary mobile sensing and on-device machine learning. This document describes the theoretical foundation, the system architecture, and the mechanism by which intervention is delivered.

---

## 1. The Problem

Across addiction, compulsive behavior, and impulse-related goal failure, the key moment is not the *desire* to change but the *interval* between a triggering cue and the compulsive response. This interval — seconds to minutes — is when the intervention must land. In that interval:

- Traditional therapy is typically unavailable (weekly sessions leave 167 hours uncovered).
- Community-based programs (AA, SMART) are high-value but schedule-bound.
- Consumer wellness apps are typically engagement-optimized: they are designed to be opened daily, not to arrive in a crisis.

The measurable consequence: **most behavior-change apps show a D30 retention below 5%** [Baumel et al., 2019], and retention is not the same as outcome. A user can open an app for 30 days and still relapse in the 2-second interval when it matters most.

Discipline OS is designed to reverse this framing. The system is not trying to maximize app opens; it is trying to be present, correctly, at the moment of decision. Engagement is an instrument of that goal, not the goal itself.

---

## 2. Theoretical Foundation

### 2.1 Relapse Prevention (Marlatt & Gordon, 1985)

The Relapse Prevention (RP) model [Marlatt & Gordon, 1985; Witkiewitz & Marlatt, 2004] describes relapse as a dynamic process beginning well before the observable behavior. A *high-risk situation* — intrapersonal (negative affect, craving) or interpersonal (conflict, social pressure) — engages the person's coping repertoire. If coping is adequate, self-efficacy increases and the probability of the next high-risk situation decreases. If coping is inadequate, self-efficacy decreases, and the person enters an **abstinence violation effect (AVE)** — a conflict between goal and behavior that, without intervention, amplifies into full relapse.

Discipline OS makes three commitments that derive directly from the RP model:

1. **The system must intervene *before* the behavior, not after** — by detecting elevated risk from behavioral and physiological signals and deploying an appropriate coping tool.
2. **After a relapse, the intervention must disrupt the AVE spiral** — via a compassion-first response rather than a shame-based "you lost your streak" framing.
3. **Coping is a multi-tool repertoire, not a single prescribed protocol** — because the fit between tool and moment is variable and must be learned per individual.

The mindfulness-based extension of RP, **MBRP** [Bowen, Chawla, & Marlatt, 2011; Witkiewitz et al., 2014], adds **urge surfing** as a core skill, which we include in the v1.0 toolkit.

### 2.2 Just-in-Time Adaptive Intervention (JITAI)

The JITAI framework [Nahum-Shani et al., 2018] formalizes intervention design around four components:

1. **Distal outcome** — the long-term goal (e.g. reduction in drinking episodes)
2. **Proximal outcome** — the short-term state the intervention immediately affects (e.g. de-escalation of current craving)
3. **Decision points** — when the system can choose to intervene
4. **Tailoring variables** — the state information that determines *whether* and *which* intervention to deploy

Discipline OS instantiates each:

| JITAI component | Discipline OS |
|---|---|
| Distal outcome | Reduction in behavioral lapses over a meaningful horizon (90 days+); measured via user-reported urge counts, lapse counts, and psychometric trajectories (PHQ-9, GAD-7, WHO-5). |
| Proximal outcome | Urge intensity reduction over a 15-minute post-intervention window. |
| Decision points | Evaluated every 5 minutes foreground / 20 minutes background; elevated when signals cross learned personal thresholds. |
| Tailoring variables | Urge intensity, 2-hour trajectory, HALT state, time-of-day × day-of-week, location class, HRV and sleep signals from wearables, recent outcome history. |

A key JITAI design principle we adopt: the intervention must be **commensurate** with the state. Under-intervention (a push notification when a full-screen crisis flow is required) fails; over-intervention (a crisis flow triggered by a minor craving) fatigues and is ignored.

### 2.3 Implementation Intentions (Gollwitzer, 1999)

Gollwitzer's implementation-intention research shows that pre-specifying if-then plans ("if situation X arises, I will do Y") reliably closes the **intention-behavior gap** [Gollwitzer, 1999; Gollwitzer & Sheeran, 2006]. The meta-analytic effect size is d ≈ 0.65 across domains — comparable to or exceeding the effect of goal-setting alone.

In Discipline OS, the user builds a small library of personal if-then plans during onboarding and adds more as patterns emerge. At decision points the system surfaces the relevant plan, turning a momentary decision into the execution of a pre-committed rule.

### 2.4 Complementary frameworks

- **Cognitive Behavioral Therapy (CBT)** [Beck, 1979; Hofmann et al., 2012 for efficacy meta-analysis]: structures the awareness journal and functional analysis workflow.
- **Dialectical Behavior Therapy (DBT)** [Linehan, 1993; Neacsiu et al., 2010]: contributes the TIPP skill (Temperature, Intense exercise, Paced breathing, Paired muscle relaxation) for crisis-grade distress tolerance.
- **Acceptance and Commitment Therapy (ACT)** [Hayes, Strosahl, & Wilson, 1999]: contributes cognitive-defusion practices.
- **Self-Compassion** [Neff, 2003; Breines & Chen, 2012]: shapes the post-relapse response design; shame-based framing has been shown to worsen relapse trajectory.
- **Mindfulness-Based Stress Reduction (MBSR)** [Kabat-Zinn, 1990]: source of the body-scan skill.
- **Reliable Change Index (RCI)** [Jacobson & Truax, 1991]: governs when we surface a psychometric trajectory to the user — only when the change exceeds measurement error.

---

## 3. System Architecture

The system is a closed loop over four layers:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Signals   │───►│    State    │───►│Intervention │───►│  Outcome    │
│  (passive + │    │  estimation │    │ orchestrator│    │  capture    │
│   active)   │    │  (on-device)│    │   (4-tier)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                                         │
       └─────────────────── learning loop ──────────────────────┘
```

### 3.1 Signals

**Passive** (permission-based, opt-in per signal):
- HealthKit / Health Connect: heart rate, HRV, sleep duration + stage, active energy, workouts
- Wearable SDKs (optional): Oura, Whoop, Fitbit for richer HRV and stress proxies
- On-device phone telemetry: screen unlocks per hour, app-switching entropy, typing cadence variance
- Location class (not raw coordinates): home / work / risk-zone / transit / other
- Calendar density (event count, free blocks)
- Time-of-day × day-of-week
- Weather (by location bucket)

**Active:**
- Urge dial (0–10, haptic-snapped, ≤ 3-second capture)
- Emotion picker (craving / anxiety / anger / sadness / boredom / shame)
- 1-line text note (optional)
- Voice note (≤ 15s, optional, transcribed on-device)
- HALT (Hungry / Angry / Lonely / Tired) quad-toggle

All passive biometric signals are processed **on-device**. Cloud receives only low-cardinality state estimates, not raw biometric streams.

### 3.2 State estimation

An on-device recurrent model (LSTM, 72-hour sequence length) outputs a continuous state vector at every decision point:

- `urge_intensity` ∈ [0, 10] with volatility and 2-hour trajectory
- `relapse_risk_next_2h` ∈ [0, 1] (also 8h and 24h horizons)
- `emotion_state` (categorical + intensity)
- `halt_state` (4 bools)
- `baseline_distance` — σ units from personal 30-day rolling baseline
- `context_class` (home / work / risk-zone / transit / other)

Each output surfaces its top-2 contributing signals for explainability. Personal baselines are maintained locally; population priors are shared via opt-in federated learning, never via raw data upload.

### 3.3 Intervention orchestrator (4-tier)

| Tier | Trigger | UI | Max frequency |
|------|---------|----|--------------:|
| T0 | Ambient | Subtle home-screen indicator, no interruption | — |
| T1 | Urge rising | Push: "quick 60s?" | Budget-capped per day (default 4) |
| T2 | Urge elevated | Structured 90–180s workflow | User-initiated or predicted high-risk |
| T3 | Crisis / SOS | Full-screen, 1-button, deterministic flow | Always available |
| T4 | Self-harm ideation | Deterministic handoff to crisis line + per-country hotline directory | Immediate |

**T3 and T4 are never LLM-generated and never require a network round-trip.** The crisis catalog is bundled on-device (mobile) and pre-rendered on the static `crisis.disciplineos.com` surface. This is an architectural commitment: the safety path must not degrade when the network does.

Within T2, tool selection is governed by a **contextual bandit** (see §4). At T3 the bandit is not consulted — the highest-confidence tool is always used.

### 3.4 Outcome capture

After every intervention, the system captures:
- A 2-tap self-reported helpfulness rating (helped / neutral / didn't help / made worse)
- The urge dial re-reading at 15 minutes (where user is willing)
- Next-24-hour behavior outcome (user-reported)
- Optional voice note

These outcome tuples feed the learning loop: the bandit updates its tool-selection posterior, the state estimator is re-fit weekly from aggregated outcomes, and per-user if-then plans are refined.

---

## 4. Personalization: Contextual Bandit

Tool selection at T2 is framed as a **contextual multi-armed bandit problem** [Li et al., 2010 — LinUCB; Agrawal & Goyal, 2013 — Thompson sampling]. Arms are coping tools; context is the state vector; reward is a weighted combination of (a) self-reported helpfulness, (b) urge subsidence over 15 minutes, and (c) the absence of relapse over 24 hours.

Three guardrails:

1. **Never explore at T3.** At crisis tier the best-known tool is selected deterministically. Exploration belongs to lower tiers.
2. **Exploration cap.** At any tier, exploration deviates by at most 15% from the best-known tool in that context, to prevent ablation of known-good responses.
3. **Respect user preferences.** A "don't suggest this" vote on a tool removes it from the arm set for that user in that context.

The bandit starts with a **population prior** derived from cohort aggregates. As per-user history accumulates, the posterior shifts toward personal evidence. Weekly retraining cadence.

---

## 5. Relapse Response — Compassion, Not Shame

The relapse flow is one of the highest-stakes design surfaces in the product. The evidence is clear: shame-based framing worsens the AVE spiral, whereas self-compassion interventions reduce it [Breines & Chen, 2012; Kelly et al., 2014 in addiction contexts].

Design commitments in Discipline OS:

- **Dual-metric streak.** A `continuous_streak` (days since last lapse) is honestly reset on lapse. A `resilience_streak` — count of urges handled — **never resets**, because the act of handling an urge is exactly what the system is trying to teach.
- **No loss-aversion framing.** "Don't lose your progress" copy is forbidden by the content linter.
- **Immediate compassion screen.** First thing after a reported lapse is a single-screen compassion message; the functional-analysis workflow comes later, when emotional state allows.
- **24–72 hour reduced-friction mode.** Targets are lowered, tone softens, check-ins space out. The post-lapse period is when re-engagement is most fragile.
- **Functional analysis within 48h.** Because this is when the memory of the lapse is clear enough for pattern extraction.

---

## 6. Privacy as a Methodological Constraint

Privacy in Discipline OS is not a UX overlay but a constraint on what methodology we can adopt. Specifically:

- We do not transmit raw biometric streams. We lose fine-grained cross-user modeling of physiological signatures and gain a system that can be operated in an edge-first deployment.
- We use **federated learning** (opt-in, Phase 3+) to update the population prior without centralizing raw data.
- We apply **k-anonymity ≥ 5** and **differential privacy** on any enterprise-facing aggregate (see `03_Privacy_Architecture.md`).
- Journals and voice notes are **end-to-end encrypted**; server processing is metadata-only.

These constraints define the methodological envelope. The safety path, the signal layer, and the outcome capture are all designed to operate **within** these constraints — not despite them.

---

## 7. Limitations and What This System Is Not

We state these plainly:

1. **This is not a treatment.** Discipline OS is a between-sessions support tool. It does not diagnose, does not prescribe, does not replace a clinician. The FDA SaMD pathway is a Phase-4 initiative; the v1.0 product is positioned as a wellness tool.

2. **Population prior ≠ personal outcome.** Even with perfect personalization, the system cannot guarantee any specific user outcome. Clinical RCTs (planned, see `05_Research_Roadmap.md`) will establish effect sizes at the population level.

3. **Signal quality varies.** Not every user has a wearable; not every user grants HealthKit. The system degrades gracefully — coping tools work without any passive signal — but prediction quality improves with data density.

4. **Cultural adaptation is partial.** We launch in four locales (en/fr/ar/fa) with validated translations of core psychometric instruments, clinician-translator workflow for all safety content, and culturally-appropriate hotline directories. We are not claiming that intervention preferences that emerge from North American training data generalize perfectly to all four markets — an ongoing research question.

5. **No community features at v1.0.** We think community is high-value in recovery contexts; we also think building it inside a clinical-grade product is a distinct design problem with its own risk model. We defer it rather than ship it imperfectly.

---

## 8. References

(Selected core references; the full annotated bibliography is in `02_Clinical_Evidence_Base.md`.)

- **Agrawal, S., & Goyal, N. (2013).** Thompson sampling for contextual bandits with linear payoffs. *ICML 2013*.
- **Baumel, A., Muench, F., Edan, S., & Kane, J. M. (2019).** Objective user engagement with mental health apps: systematic search and panel-based usage analysis. *Journal of Medical Internet Research*, 21(9), e14567. https://doi.org/10.2196/14567
- **Beck, A. T. (1979).** *Cognitive therapy and the emotional disorders*. Penguin.
- **Bowen, S., Chawla, N., & Marlatt, G. A. (2011).** *Mindfulness-Based Relapse Prevention for Addictive Behaviors: A Clinician's Guide*. Guilford Press.
- **Breines, J. G., & Chen, S. (2012).** Self-compassion increases self-improvement motivation. *Personality and Social Psychology Bulletin*, 38(9), 1133–1143. https://doi.org/10.1177/0146167212445599
- **Gollwitzer, P. M. (1999).** Implementation intentions: Strong effects of simple plans. *American Psychologist*, 54(7), 493–503. https://doi.org/10.1037/0003-066X.54.7.493
- **Gollwitzer, P. M., & Sheeran, P. (2006).** Implementation intentions and goal achievement: A meta-analysis of effects and processes. *Advances in Experimental Social Psychology*, 38, 69–119. https://doi.org/10.1016/S0065-2601(06)38002-1
- **Hayes, S. C., Strosahl, K. D., & Wilson, K. G. (1999).** *Acceptance and Commitment Therapy: An experiential approach to behavior change*. Guilford Press.
- **Hofmann, S. G., Asnaani, A., Vonk, I. J., Sawyer, A. T., & Fang, A. (2012).** The efficacy of cognitive behavioral therapy: A review of meta-analyses. *Cognitive Therapy and Research*, 36(5), 427–440. https://doi.org/10.1007/s10608-012-9476-1
- **Jacobson, N. S., & Truax, P. (1991).** Clinical significance: A statistical approach to defining meaningful change in psychotherapy research. *Journal of Consulting and Clinical Psychology*, 59(1), 12–19. https://doi.org/10.1037/0022-006X.59.1.12
- **Kabat-Zinn, J. (1990).** *Full catastrophe living: Using the wisdom of your body and mind to face stress, pain, and illness*. Delacorte Press.
- **Kelly, A. C., Zuroff, D. C., Foa, C. L., & Gilbert, P. (2014).** Who benefits from training in self-compassionate self-regulation? A study of smoking reduction. *Journal of Social and Clinical Psychology*, 33(7), 727–755. https://doi.org/10.1521/jscp.2014.33.7.727
- **Li, L., Chu, W., Langford, J., & Schapire, R. E. (2010).** A contextual-bandit approach to personalized news article recommendation. *WWW 2010*. https://doi.org/10.1145/1772690.1772758
- **Linehan, M. M. (1993).** *Cognitive-behavioral treatment of borderline personality disorder*. Guilford Press.
- **Marlatt, G. A., & Gordon, J. R. (Eds.). (1985).** *Relapse prevention: Maintenance strategies in the treatment of addictive behaviors*. Guilford Press.
- **Nahum-Shani, I., Smith, S. N., Spring, B. J., Collins, L. M., Witkiewitz, K., Tewari, A., & Murphy, S. A. (2018).** Just-in-time adaptive interventions (JITAIs) in mobile health: Key components and design principles for ongoing health behavior support. *Annals of Behavioral Medicine*, 52(6), 446–462. https://doi.org/10.1007/s12160-016-9830-8
- **Neacsiu, A. D., Rizvi, S. L., & Linehan, M. M. (2010).** Dialectical behavior therapy skills use as a mediator and outcome of treatment for borderline personality disorder. *Behaviour Research and Therapy*, 48(9), 832–839. https://doi.org/10.1016/j.brat.2010.05.017
- **Neff, K. D. (2003).** Self-compassion: An alternative conceptualization of a healthy attitude toward oneself. *Self and Identity*, 2(2), 85–101. https://doi.org/10.1080/15298860309032
- **Witkiewitz, K., & Marlatt, G. A. (2004).** Relapse prevention for alcohol and drug problems: That was Zen, this is Tao. *American Psychologist*, 59(4), 224–235. https://doi.org/10.1037/0003-066X.59.4.224
- **Witkiewitz, K., Bowen, S., Harrop, E. N., Douglas, H., Enkema, M., & Sedgwick, C. (2014).** Mindfulness-based treatment to prevent addictive behavior relapse: Theoretical models and hypothesized mechanisms of change. *Substance Use & Misuse*, 49(5), 513–524. https://doi.org/10.3109/10826084.2014.891845
