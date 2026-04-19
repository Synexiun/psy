# Research Roadmap — Evidence Generation, RCTs, and Academic Collaboration

**Version:** 1.0
**Audience:** Clinical Advisory Board, prospective academic collaborators, regulators, informed enterprise customers
**Abstract:** Discipline OS is built on published behavior-change research, but the product itself is a new intervention and must generate its own evidence. This document describes the planned research program: observational studies at v1.0, a pragmatic RCT in Phase 3, a confirmatory RCT toward FDA SaMD submission in Phase 4, the IRB and data-governance posture, and the mechanisms by which academic collaborators can access data without compromising privacy.

---

## 1. Research Posture by Phase

| Phase | Regulatory posture | Research activity |
|-------|-------------------|---------------------|
| 0–1 (Bedrock, Closed Loop) | Wellness / non-medical | Internal methodological validation; no claims of clinical efficacy; weekly cohort analysis |
| 2 (Launch) | Wellness / non-medical | Launch observational study (N ≥ 1,000 over 90 days); publication target: methodology + retention paper in a peer-reviewed digital-health venue |
| 3 (Expand) | Wellness / non-medical | Pragmatic RCT (N ≥ 1,500) on alcohol primary endpoint; published externally; second vertical preliminary effect estimates |
| 4 (Clinical) | SaMD submission | Pivotal RCT (N ≥ 3,000) under FDA-guided protocol; ISO 14155 compliance; publication in peer-reviewed clinical venue; regulatory submission |
| 5 (Platform) | Mixed: wellness + SaMD | Post-market study; cross-vertical federated learning studies; academic API program |

---

## 2. v1.0 Observational Study

### 2.1 Aims

1. **Retention and engagement.** D30, D90, D180 per surface, per locale.
2. **Proximal outcomes.** Per-episode urge reduction (15-minute post-intervention dial drop).
3. **Distal outcomes.** Psychometric trajectories (PHQ-9, GAD-7, AUDIT-C) over 90 days with RCI analysis.
4. **Intervention efficacy heterogeneity.** Which tools work best for whom (contextual-bandit posteriors).
5. **Safety signal detection.** T4 trigger rate; false-negative review outcomes.

### 2.2 Design

- **Observational cohort** — not randomized, not controlled. No efficacy claim.
- **Enrollment:** all Phase-2 users who opt into research-aggregate use (opt-in at onboarding; not required for product use).
- **Duration:** 180 days.
- **Primary endpoint:** D30 retention + mean PHQ-9 change from baseline.
- **Secondary endpoints:** proximal urge reduction, tool-efficacy ranking, self-report helpfulness distribution, per-locale comparison.

### 2.3 Protections

- No individual data published. All reporting at cohort level with k-anonymity ≥ 5 and differential privacy on any sub-group breakdown.
- Opt-out at any time; subsequent data excluded from the analysis.
- Pre-registered analysis plan (OSF Registries) before Phase 2 launch.
- External statistical review before publication.

### 2.4 Expected output

- Peer-reviewed manuscript targeting *JMIR Mental Health* or *NPJ Digital Medicine* within 12 months of launch.
- Accompanying analysis code released under a permissive license (not the trained models or production data).

---

## 3. Phase 3 Pragmatic RCT

### 3.1 Research question

In adults with problem drinking (AUDIT-C ≥ 3 women / ≥ 4 men), does randomization to Discipline OS + treatment-as-usual (TAU) produce greater reduction in heavy drinking days over 12 weeks compared to TAU alone?

### 3.2 Design

- **Pragmatic RCT** — real-world delivery, not tightly controlled lab conditions.
- **Parallel groups**, 1:1 randomization to (Discipline OS + TAU) or (TAU alone).
- **Primary endpoint:** change in self-reported heavy drinking days (Timeline Followback method; Sobell & Sobell, 1992) from baseline to 12 weeks.
- **Secondary endpoints:** PHQ-9, GAD-7, AUDIT-C, self-reported quality of life (WHO-5); retention.
- **Safety monitoring:** C-SSRS and safety-event review by a Data and Safety Monitoring Board (DSMB).

### 3.3 Sample size

- Powered at 80% to detect a standardized difference of d = 0.2 between groups on the primary endpoint, two-sided α = 0.05.
- After attrition adjustment (expected 25% at 12 weeks), enroll ≥ 1,500.

### 3.4 Governance

- **IRB approval** at an accredited US academic medical center partner.
- **Pre-registration** on ClinicalTrials.gov.
- **DSMB** with authority to pause the trial on safety grounds; independent of Discipline OS management.
- **Statistical analysis plan (SAP)** finalized before first participant enrolls; reviewed by independent biostatistician.
- **Publication policy:** null or negative findings are published on equivalent priority to positive findings. This is contractual with the academic partner.

### 3.5 Why pragmatic, not explanatory

An explanatory RCT (N=100 in a research clinic with dedicated staff) would show what the product *can* do; a pragmatic RCT (N=1,500 in the field) shows what it *does* do. For a product that is going to be deployed by the tens of thousands, the second is what matters. We also plan explanatory sub-studies (mechanism-of-change, cognitive-fatigue interactions) in parallel.

---

## 4. Phase 4 Pivotal RCT (toward FDA SaMD)

### 4.1 Scope

- **Confirmatory RCT** under FDA pre-submission guidance.
- Adequate powering for the FDA-agreed primary endpoint.
- Compliant with ISO 14155 (clinical investigation of medical devices for human subjects).
- Conducted at multiple sites to ensure generalizability.

### 4.2 Regulatory track

- Pre-submission meeting (Q-Sub) with FDA to align on pathway (De Novo vs 510(k) vs PMA).
- Investigational Device Exemption (IDE) if required.
- Submission of full technical and clinical evidence.
- Post-market surveillance plan.

### 4.3 Quality Management

- ISO 13485 QMS in place before trial start.
- Risk management file (ISO 14971) submitted.
- Software lifecycle under IEC 62304, Class B or C as determined.
- Clinical evaluation report (per MEDDEV 2.7/1 Rev 4 / EU MDR equivalent) for international readiness.

---

## 5. Academic Collaboration Program

### 5.1 Opportunity

Discipline OS collects one of the richer longitudinal datasets of in-the-wild behavioral-health intervention outcomes. Academic collaborators stand to learn from it. We want this, with strict governance.

### 5.2 Access models (Phase 5)

| Model | Access | Governance |
|-------|--------|------------|
| **Aggregate API** | Differentially-private aggregate queries on a BAA-scope warehouse; no individual-level data | Lightweight — academic agreement + privacy training |
| **Secure enclave analysis** | Full de-identified dataset analyzed inside our VPC; no extraction | IRB + data-use agreement + privacy training + code review |
| **Federated study** | Pre-registered analysis runs against de-identified data; only results exit | IRB + pre-registration + SAP review |
| **Recruitment partnership** | Our users with consent opt into academic studies via in-app flow | IRB at both sides; user-level consent |

**All four models require real IRB oversight and a written data-use agreement.** None involves bulk PHI export.

### 5.3 Researcher qualifications

- Affiliation with an institution that maintains an IRB or equivalent ethics review.
- Published track record in behavioral health, digital mental health, or addiction research.
- Privacy and security training on our specific data environment.

### 5.4 What we will not do

- No sale of data to researchers, marketers, or any third party.
- No sharing of data outside BAA scope.
- No sharing with jurisdictions whose privacy protections are materially weaker than those of the subjects' jurisdiction.
- No sharing that would enable re-identification even for legitimate research, without additional ethical review.

---

## 6. Open Research Questions We're Interested In

(These are not commitments, but signals to prospective collaborators.)

1. **Cross-locale generalization of intervention preferences.** Does the population prior for tool efficacy transfer across locales, or do we need per-locale priors?
2. **Heterogeneity of response.** Can we identify sub-populations where the product works substantially better or worse, pre-intervention, from baseline characteristics?
3. **Proximal → distal linkage.** How well do 15-minute urge-reduction outcomes predict 90-day PHQ-9 trajectory?
4. **Comparative efficacy.** How does Discipline OS compare to clinician-delivered CBT for alcohol use disorder, controlling for engagement intensity?
5. **Ecological validity of digital psychometrics.** Are in-app PHQ-9 administrations equivalent to clinician-administered PHQ-9 (already well-studied — we want to replicate in our specific population)?
6. **Mechanism of change.** Does the product work primarily via urge surfing skill acquisition, via if-then-plan rehearsal, via compassion reorientation post-lapse, or via combination?
7. **Long-term safety.** What is the incidence of T4 triggers per 1,000 user-months? Does our post-lapse flow reduce the AVE trajectory compared to baseline expectation?

These questions map to either internal research tracks or potential collaboration projects; the Head of Clinical maintains the current list and prioritizes.

---

## 7. Publication and Transparency

- **Pre-registration:** All studies with inferential claims are pre-registered (OSF, ClinicalTrials.gov, or equivalent).
- **Open methods:** Analysis code for published studies is released under a permissive license, in keeping with reproducibility norms (Nosek et al., 2015 — "Promoting an open research culture").
- **Open data (aggregate):** Where IRB approves, aggregate de-identified data and synthetic-data twins are released alongside publications.
- **Correction culture:** If a published finding does not replicate, we will publish the failure to replicate at equal priority.
- **Competing interests disclosed** in every publication.

---

## 8. Data and Safety Monitoring Board (DSMB)

For every prospective study (RCTs and observational cohorts with > 1,000 participants), we will engage a DSMB with:

- At least one clinician with relevant expertise (addiction psychiatry, clinical psychology).
- At least one biostatistician.
- At least one ethicist or member with lived experience.
- Authority to pause the study on safety grounds.
- Quarterly review cadence during active studies.
- Final review and sign-off before any primary-endpoint publication.

---

## 9. Longitudinal Dataset Stewardship

A recognized risk in digital-health research is the **data-survives-the-company** problem: the longitudinal dataset accumulated during the active product lifetime may remain valuable for decades after the product itself is retired.

Our commitments:

1. **Dataset stewardship plan** maintained independent of product roadmap.
2. **End-of-life plan** — if the product is discontinued, users are given export and deletion options; the research warehouse (BAA-scope) is archived with a pre-committed academic custodian (an accredited university-based repository) rather than sold.
3. **No inheritance-by-acquirer.** In any acquisition scenario, the data governance commitments continue as written or more strictly; they cannot be relaxed by new ownership.

---

## 10. References

- **Nahum-Shani, I., et al. (2018).** Just-in-time adaptive interventions (JITAIs). *Annals of Behavioral Medicine*, 52(6), 446–462.
- **Sobell, L. C., & Sobell, M. B. (1992).** Timeline follow-back: A technique for assessing self-reported alcohol consumption. In R. Z. Litten & J. P. Allen (Eds.), *Measuring alcohol consumption: Psychosocial and biochemical methods* (pp. 41–72). Humana Press.
- **Nosek, B. A., et al. (2015).** Promoting an open research culture. *Science*, 348(6242), 1422–1425. https://doi.org/10.1126/science.aab2374
- **Torous, J., et al. (2021).** The growing field of digital psychiatry. *World Psychiatry*, 20(3), 318–335.
- **Mohr, D. C., Schueller, S. M., Riley, W. T., Brown, C. H., Cuijpers, P., Duan, N., Kwasny, M. J., Stiles-Shields, C., & Cheung, K. (2015).** Trials of intervention principles: Evaluation methods for evolving behavioral intervention technologies. *Journal of Medical Internet Research*, 17(7), e166. https://doi.org/10.2196/jmir.4391
- **Hekler, E. B., Klasnja, P., Riley, W. T., Buman, M. P., Huberty, J., Rivera, D. E., & Martin, C. A. (2016).** Agile science: Creating useful products for behavior change in the real world. *Translational Behavioral Medicine*, 6(2), 317–328. https://doi.org/10.1007/s13142-016-0395-7
- **ISO 14155:2020.** Clinical investigation of medical devices for human subjects — Good clinical practice.
- **FDA.** *Clinical Investigations of Devices Indicated for the Treatment of Urinary Incontinence: Guidance for Industry and Food and Drug Administration Staff* (referenced as exemplar for pragmatic-trial guidance in SaMD contexts).
