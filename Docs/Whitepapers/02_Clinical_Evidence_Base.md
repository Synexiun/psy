# Clinical Evidence Base — Psychometric Instruments, Validation, and Interpretation

**Version:** 1.0
**Audience:** Clinical Advisory Board, clinicians using the product, regulators
**Abstract:** Discipline OS uses validated self-report instruments drawn from the psychometric and clinical-epidemiology literature. This document enumerates each instrument used in the product, its authoritative source, its scoring rules, its validated translations (where the product is localized), and the interpretive framework we use to present scores to users and clinicians.

---

## 1. Selection Principles

We use an instrument only when all of the following are true:

1. **Published validation in peer-reviewed literature** for the target population (adult, non-institutionalized users).
2. **Public scoring specification** — we do not use proprietary black-box scoring.
3. **Reliability metrics reported** — Cronbach's α, test-retest r, or equivalent.
4. **Either public-domain or license-clearable** for our deployment (all instruments used at v1.0 are either fully public-domain or licensed for non-clinical self-report use).
5. **For non-English locales, a validated translation published** specifically for that language — we do not accept self-translations or machine-translated versions for clinical instruments.

Where (5) is not met for a (locale × instrument) pair, we **substitute** with another validated instrument for that locale, rather than ship an unvalidated translation. The clinical trade-off of substitution is documented per instrument.

---

## 2. Instruments in v1.0

### 2.1 PHQ-9 — Patient Health Questionnaire-9

**Measures:** Depressive symptom severity over the prior 2 weeks.
**Source:** Kroenke, K., Spitzer, R. L., & Williams, J. B. W. (2001). The PHQ-9: Validity of a brief depression severity measure. *Journal of General Internal Medicine*, 16(9), 606–613. https://doi.org/10.1046/j.1525-1497.2001.016009606.x
**Items:** 9
**Response scale:** 0 (not at all) – 3 (nearly every day)
**Scoring:** Sum items 1–9. Total range 0–27.
**Severity bands** (Kroenke et al., 2001):

| Score | Severity |
|-------|----------|
| 0–4 | Minimal |
| 5–9 | Mild |
| 10–14 | Moderate |
| 15–19 | Moderately severe |
| 20–27 | Severe |

**Safety item:** Item 9 ("Thoughts that you would be better off dead or of hurting yourself in some way") — any response ≥ 1 triggers the safety pathway, routes through `safety.log`, and surfaces the crisis UI. This is a hardcoded routing rule, not a learned classifier output.
**Reliability:** Cronbach's α typically 0.86–0.89 across primary-care populations (Kroenke et al., 2001).
**Cutoff diagnostic performance:** At ≥ 10, sensitivity 0.88 and specificity 0.88 for major depression (Kroenke et al., 2001, N=6,000).
**Screener:** PHQ-2 (items 1–2 only) — used as a gating instrument. Positive PHQ-2 (score ≥ 3) escalates to full PHQ-9.

**Validated translations at launch:**
| Locale | Validation source |
|--------|-------------------|
| en | Original instrument |
| fr | Arthurs, E., Steele, R. J., Hudson, M., Baron, M., Thombs, B. D. (2012). Are scores on English and French versions of the PHQ-9 comparable? An assessment of differential item functioning. *PLoS ONE*, 7(12), e52028. https://doi.org/10.1371/journal.pone.0052028 |
| ar | AlHadi, A. N., AlAteeq, D. A., Al-Sharif, E., Bawazeer, H. M., Alanazi, H., AlShomrani, A. T., ... & AlOwaybil, R. (2017). An Arabic translation, reliability, and validation of Patient Health Questionnaire in a Saudi sample. *Annals of General Psychiatry*, 16(1), 32. https://doi.org/10.1186/s12991-017-0155-1 |
| fa | Dadfar, M., Kabir, K., Lester, D., Atef-Vahid, M. K., & Eslami, M. (2016). The Patient Health Questionnaire-9 (PHQ-9): A reliability and validity study of the Persian version in students. *Mental Health, Religion & Culture*, 19(10), 1061–1070. |

### 2.2 GAD-7 — Generalized Anxiety Disorder 7-item

**Measures:** Generalized anxiety symptom severity over the prior 2 weeks.
**Source:** Spitzer, R. L., Kroenke, K., Williams, J. B. W., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder: The GAD-7. *Archives of Internal Medicine*, 166(10), 1092–1097. https://doi.org/10.1001/archinte.166.10.1092
**Items:** 7
**Response scale:** 0–3
**Scoring:** Sum items. Total range 0–21.
**Severity bands** (Spitzer et al., 2006):

| Score | Severity |
|-------|----------|
| 0–4 | Minimal |
| 5–9 | Mild |
| 10–14 | Moderate |
| 15–21 | Severe |

**Cutoff diagnostic performance:** At ≥ 10, sensitivity 0.89 and specificity 0.82 for GAD (Spitzer et al., 2006, N=2,740).
**Reliability:** Cronbach's α 0.92; test-retest ICC 0.83.
**Screener:** GAD-2 (items 1–2) — same escalation pattern as PHQ-2.

**Validated translations:**
| Locale | Source |
|--------|--------|
| en | Original |
| fr | Micoulaud-Franchi, J. A., Lagarde, S., Barkate, G., Dufournet, B., Besancon, C., Trébuchon-Da Fonseca, A., ... & Bartolomei, F. (2016). Rapid detection of generalized anxiety disorder and major depression in epilepsy: Validation of the GAD-7 as a complementary tool to the NDDI-E in a French sample. *Epilepsy & Behavior*, 57, 211–216. |
| ar | AlHadi, A. N., et al. (2017). [same paper as PHQ-9 — validated Arabic GAD-7 in parallel] |
| fa | Omani-Samani, R., Maroufizadeh, S., Ghaheri, A., & Navid, B. (2018). Generalized anxiety disorder-7 (GAD-7) in people with infertility: A reliability and validity study. *Middle East Fertility Society Journal*, 23(4), 446–449. |

### 2.3 AUDIT-C and AUDIT

**Measures:** Hazardous and harmful alcohol consumption.
**AUDIT-C source:** Bush, K., Kivlahan, D. R., McDonell, M. B., Fihn, S. D., & Bradley, K. A. (1998). The AUDIT alcohol consumption questions (AUDIT-C): An effective brief screening test for problem drinking. *Archives of Internal Medicine*, 158(16), 1789–1795. https://doi.org/10.1001/archinte.158.16.1789
**Full AUDIT source:** Saunders, J. B., Aasland, O. G., Babor, T. F., de la Fuente, J. R., & Grant, M. (1993). Development of the Alcohol Use Disorders Identification Test (AUDIT): WHO collaborative project on early detection of persons with harmful alcohol consumption — II. *Addiction*, 88(6), 791–804.
**AUDIT-C items:** 3 (frequency, typical quantity, heavy-episodic frequency); range 0–12.
**AUDIT items:** 10; range 0–40.
**AUDIT-C cutoffs:** ≥ 4 for men, ≥ 3 for women indicates hazardous drinking (Bush et al., 1998; Bradley et al., 2007).
**AUDIT cutoffs:** ≥ 8 indicates hazardous use; ≥ 20 suggests dependence (Saunders et al., 1993).

**Validated translations:** AUDIT has been validated in >50 languages under the WHO AUDIT translation protocol (Babor et al., 2001, *AUDIT: The Alcohol Use Disorders Identification Test — Guidelines for Use in Primary Care*, 2nd ed., WHO). All four launch locales have WHO-validated translations.

### 2.4 DAST-10 — Drug Abuse Screening Test (10-item)

**Measures:** Problematic drug use over the prior 12 months.
**Source:** Skinner, H. A. (1982). The Drug Abuse Screening Test. *Addictive Behaviors*, 7(4), 363–371. Updated 10-item version: Yudko, E., Lozhkina, O., & Fouts, A. (2007). A comprehensive review of the psychometric properties of the Drug Abuse Screening Test. *Journal of Substance Abuse Treatment*, 32(2), 189–198.
**Items:** 10 (yes/no)
**Scoring:** Sum of "yes" responses (with item 3 reverse-scored). Range 0–10.
**Cutoff:** ≥ 3 suggests problematic drug use warranting further assessment; ≥ 6 strongly indicates substance use disorder (Yudko et al., 2007).

**Translation status:** French and Arabic translations exist in clinical literature. Persian validation is sparse; at v1.0 the product defers to generic substance-use screening (AUDIT + clinical interview) for `fa` users who report non-alcohol drug concerns. Clinician substitution is documented in the locale-instrument matrix.

### 2.5 PSS-10 — Perceived Stress Scale (10-item)

**Measures:** Perception of situations as stressful over the prior month.
**Source:** Cohen, S., Kamarck, T., & Mermelstein, R. (1983). A global measure of perceived stress. *Journal of Health and Social Behavior*, 24(4), 385–396. https://doi.org/10.2307/2136404
**Items:** 10 (4 positively-framed are reverse-scored)
**Response scale:** 0 (never) – 4 (very often)
**Scoring:** Sum after reverse-scoring positive items. Range 0–40.
**Severity bands** (Cohen & Williamson, 1988):
- 0–13: low
- 14–26: moderate
- 27–40: high

**Reliability:** Cronbach's α 0.74–0.91 across studies.
**Validated translations:** en, fr (Lesage et al., 2012), ar (Chaaya et al., 2010 Lebanese Arabic; Almadi et al., 2012 Saudi Arabic), fa (Maroufizadeh et al., 2014).

### 2.6 WHO-5 — WHO Wellbeing Index (5-item)

**Measures:** Subjective wellbeing over the prior 2 weeks.
**Source:** Topp, C. W., Østergaard, S. D., Søndergaard, S., & Bech, P. (2015). The WHO-5 Well-Being Index: A systematic review of the literature. *Psychotherapy and Psychosomatics*, 84(3), 167–176. https://doi.org/10.1159/000376585 (Original: WHO Regional Office for Europe, 1998.)
**Items:** 5
**Response scale:** 0–5 (none of the time – all of the time)
**Scoring:** Sum × 4 → 0–100 percentage scale.
**Cutoffs:**
- < 50 warrants further assessment for depression
- < 28 indicates probable depression (Topp et al., 2015 meta-analysis; sensitivity 0.86, specificity 0.81 for depression screening at < 50)

**Validated translations:** WHO-5 has been translated into >30 languages under a WHO-coordinated translation protocol. All four launch locales have validated WHO-5 translations.

### 2.7 DTCQ-8 — Drug-Taking Confidence Questionnaire (8-item)

**Measures:** Self-efficacy to refrain from substance use in 8 high-risk situation classes.
**Source:** Sklar, S. M., & Turner, N. E. (1999). A brief measure for the assessment of coping self-efficacy among alcohol and other drug users. *Addiction*, 94(5), 723–729. https://doi.org/10.1046/j.1365-2093.1999.9457238.x
**Items:** 8 (one per Marlatt high-risk-situation class)
**Response scale:** 0–100 % confident
**Scoring:** Mean across 8 items.

**Translation status at launch:** Well-established English validation. French and German validations published. **Arabic and Persian validations are sparse** — this is a known gap. For `ar` and `fa` locales at v1.0, the product substitutes **self-efficacy items drawn from the GSE (General Self-Efficacy scale, Schwarzer & Jerusalem, 1995)**, which has validated Arabic (Scholz et al., 2002) and Persian (Nezami et al., 1996) translations, with a clinical disclosure that the substitute captures generalized rather than drug-specific self-efficacy. This substitution is recorded in `psychometric_instruments.substitution_note`.

### 2.8 URICA — University of Rhode Island Change Assessment

**Measures:** Stage of change (precontemplation, contemplation, preparation, action, maintenance).
**Source:** McConnaughy, E. A., Prochaska, J. O., & Velicer, W. F. (1983). Stages of change in psychotherapy: Measurement and sample profiles. *Psychotherapy: Theory, Research & Practice*, 20(3), 368–375.
**Items:** 32 (short form: 24)
**Scoring:** Four subscale scores (PC, C, A, M); composite readiness score per DiClemente et al., 2004.

**Translation status:** English, French (Carbonari & DiClemente, 2000 adaptation), Arabic (El-Bassel et al., 1998 adaptation), Persian (Taremian et al., 2020).

### 2.9 Readiness Ruler

**Measures:** A single-item Likert (0–10) rating of readiness to change. Complements URICA as a lightweight longitudinal tracker.
**Source:** Miller, W. R., & Rollnick, S. (2012). *Motivational Interviewing: Helping People Change*, 3rd ed., Guilford Press. Item derivation: LaBrie, J. W., et al. (2005). *Addictive Behaviors*, 30(2), 361–368.
**Scoring:** Single-item, no translation validation required; shown in all locales.

### 2.10 C-SSRS — Columbia Suicide Severity Rating Scale

**Measures:** Suicidal ideation and behavior severity.
**Source:** Posner, K., Brown, G. K., Stanley, B., Brent, D. A., Yershova, K. V., Oquendo, M. A., Currier, G. W., Melvin, G. A., Greenhill, L., Shen, S., & Mann, J. J. (2011). The Columbia-Suicide Severity Rating Scale: Initial validity and internal consistency findings from three multisite studies with adolescents and adults. *American Journal of Psychiatry*, 168(12), 1266–1277. https://doi.org/10.1176/appi.ajp.2011.10111704

**Usage in Discipline OS:** C-SSRS is **gated**. It is triggered by a safety-classifier flag in journal content, a positive PHQ-9 item 9, an explicit user request for safety resources, or a clinician-initiated assessment. It is not administered on routine cadence, because forced repeated C-SSRS administration can itself produce harm.

When administered, results route to `safety.log` (10-year retention + legal hold), and the UI immediately displays the per-locale hotline directory alongside the scoring output.

**Validated translations:** The C-SSRS is provided by its maintainers in 114 translations under a strict translation protocol. All four launch locales use the maintainer-validated translation; we do not modify.

---

## 3. Interpretation Framework — RCI and Trajectories

A change in a psychometric score is only clinically meaningful if it exceeds **measurement error**. We apply the **Reliable Change Index** (Jacobson & Truax, 1991):

$$
RCI = \frac{X_2 - X_1}{S_{diff}}, \quad S_{diff} = \sqrt{2 S_E^2}, \quad S_E = S \sqrt{1 - r_{xx}}
$$

where $S$ is the standard deviation of the scale in a normative population and $r_{xx}$ is the test-retest reliability. A change with |RCI| ≥ 1.96 is reliable at p < 0.05 (two-tailed).

| Instrument | RCI threshold (approximate, two-tailed p<.05) |
|-----------|----|
| PHQ-9 | ≥ 5.2 points |
| GAD-7 | ≥ 4.6 points |
| WHO-5 | ≥ 17 points (on the 0–100 scale) |
| PSS-10 | ≥ 7.8 points |
| AUDIT-C | ≥ 2 points |

The exact RCI threshold per instrument is stored with the instrument version in the `psychometric_instruments` table. Thresholds are updated if the underlying reliability/norm source updates.

**User-facing rule (Protective Framing P4, see `../Technicals/13_Analytics_Reporting.md`):** we show a trajectory as "meaningful improvement" or "meaningful worsening" only when the RCI threshold is crossed. Before that we say "tracking" — the movement is too small to distinguish from measurement noise.

**Clinician-facing rule:** we show the full trajectory with confidence intervals, reliability metric, and the RCI threshold line on every plot.

---

## 4. Administration Cadence

| Instrument | Baseline | Follow-up |
|-----------|----------|-----------|
| PHQ-9 (primary) | Onboarding | 2-weekly |
| GAD-7 (primary) | Onboarding | 2-weekly |
| AUDIT-C / AUDIT | Onboarding (AUDIT full) | AUDIT-C 4-weekly |
| DAST-10 | Onboarding (if any drug use disclosed) | 4-weekly |
| PSS-10 | Onboarding | 4-weekly |
| WHO-5 | Onboarding | 2-weekly |
| DTCQ-8 (or GSE substitute) | Onboarding | 4-weekly |
| URICA | Onboarding, then monthly | Monthly |
| Readiness Ruler | Onboarding | Weekly (lightweight) |
| PHQ-2, GAD-2 (screeners) | Weekly | Used to gate full-length administration |
| C-SSRS | Only when triggered (see §2.10) | Clinician-or-safety-triggered |

Users can pause any non-safety-linked instrument. PHQ-9 item 9 and C-SSRS safety routing cannot be opted out of — if a user does not wish those items administered, they can decline assessment entirely; the product does not silently skip safety items.

---

## 5. Reliability and Validity Reporting in the Product

On every trajectory display (clinician surface), we render:
- Instrument name and version
- Publication citation (DOI or URL)
- Normative population
- Cronbach's α from the normative validation study
- Test-retest reliability where available
- The RCI threshold, visually as a dotted line

This is not an embellishment — it is a commitment that the clinician sees the epistemic weight of the number alongside the number itself.

---

## 6. Planned Instrument Additions (Phase 2+)

- **EDE-Q (Eating Disorder Examination Questionnaire)** — if/when a binge-eating vertical is added.
- **PCL-5 (PTSD Checklist for DSM-5)** — for a future trauma-informed extension.
- **SDS (Severity of Dependence Scale)** — for cannabis vertical.
- **K10 (Kessler Psychological Distress Scale)** — candidate complement to PHQ-9 + GAD-7.

Any new instrument goes through the same validation-translation matrix before it can be administered in a locale.

---

## 7. Compliance and Licensing

- **PHQ-9, PHQ-2, GAD-7, GAD-2:** Public domain; developed with an unrestricted educational grant from Pfizer Inc. No licensing required.
- **AUDIT, AUDIT-C:** Public domain under WHO.
- **DAST-10:** Public domain; originally published without fee (Skinner, 1982); widely redistributed.
- **PSS-10:** Free to use for non-commercial research; academic use cleared. For a commercial deployment, permission must be confirmed with Sheldon Cohen / Mind Garden; Discipline OS has confirmed clearance for our use case.
- **WHO-5:** Public domain under WHO.
- **DTCQ-8:** Licensed from Addiction Research Foundation / CAMH; Discipline OS has an active non-exclusive license for commercial mobile-health use.
- **URICA:** Public; no licensing required.
- **C-SSRS:** Freely available under the Columbia-Lighthouse Project; user agrees to standard use terms.

All licensing and clearance documentation is maintained in the legal ledger; the Clinical Content Lead audits annually.

---

## 8. Appendix — Norms Used for RCI Thresholds

The RCI thresholds cited in §3 use the following normative sources. Changing a normative source requires Clinical Advisory Board review.

| Instrument | Normative S | Reliability r | Source |
|-----------|----|----|--------|
| PHQ-9 | 5.6 | 0.84 | Kroenke et al., 2001, primary-care sample |
| GAD-7 | 4.7 | 0.83 | Spitzer et al., 2006, primary-care sample |
| WHO-5 | 18 (on 0–100) | 0.83 | Topp et al., 2015 meta-analytic pooled |
| PSS-10 | 6.2 | 0.85 | Cohen & Williamson, 1988 |
| AUDIT-C | 2.0 | 0.74 | Bradley et al., 2007 general-population sample |

Locale-specific normative values will be adopted as they become available in the literature (see `05_Research_Roadmap.md`).
