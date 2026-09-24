# Person A slides — 2, 3, 4, 7 (~3.5 min total)

Slide numbering follows WORK_SPLIT.md. B has 1, 5, 6, 8. Every number here
is in a file under `data/clean/` or `figures/eda/`; sources in brackets.

---

## Slide 2 — Dataset and topic (45 s)

**Title:** One table, twelve ways of counting

- CDC Chronic Disease Indicators: 398,793 rows, 55 jurisdictions, 19
  topics, 14 data collection systems, 2015–2023. [attrition_log.txt]
- We use three of those systems, because they measure the *same*
  conditions through *different* doors:
  - **BRFSS** — phone survey. "Has a doctor ever told you…"
  - **CMS Part A** — Medicare hospital claims. You were admitted.
  - **NVSS** — death certificates. It was the cause of death.
- Four conditions have at least two of the three: COPD, cardiovascular,
  diabetes, asthma. COPD has all three and is the flagship.
- Speak: "In most states these agree. Our question is what it means when
  they don't."

Visual: three icons (phone / hospital / certificate) over one row of the
table. Keep it to one bullet block.

---

## Slide 3 — What the data actually covers (60 s)

**Title:** What we could and couldn't compare

Visual: `figures/eda/coverage.png`

- Our four conditions exist only for 2019–2023; mortality and claims stop
  at 2022. Usable panel: four years, not nine. [coverage.txt]
- Hypertension (the cardiovascular survey item) is asked in odd years
  only, so cardiovascular has two usable years. [coverage.txt]
- No self-reported "heart disease" question exists — cardiovascular pairs
  a risk factor (high BP) with an outcome (heart-disease death). We
  report it, but COPD and diabetes are the clean comparisons.
- Asthma mortality is suppressed in 50 of 204 state-years (25%) — too
  rare to model. [suppression_summary.txt]
- Speak: "Half of EDA was learning what the file *doesn't* have. That's
  the finding for this slide."

---

## Slide 4 — Two things the raw data taught us (60 s)

**Title:** The survey moved in 2020. The small groups are missing.

Left visual: `figures/eda/discontinuity_2020.png` (COPD01 and AST02 panels
only if space is tight).

- 2020 COPD prevalence sits 0.16 pts below its neighbours; asthma 0.19
  below; two-thirds of states lower. Diabetes unchanged. Small vs a ~1.4
  pt CI, but real. [discontinuity_2020.txt]

Right visual: `figures/eda/suppression_by_group.png`

- Race/ethnicity cells suppressed: NH/Pacific Islander 94%, AI/AN 68%,
  Asian 67% … White 5%. [suppression_by_group.txt]
- For COPD, NH/PI is 98% suppressed. In most states there is no number.
- Speak: "Suppression protects individuals. It also means the groups we
  know least about are the smallest ones in every state."

Hand-off to B: "So when we build the comparison, we carry the confidence
intervals with us — B will show what that looks like."

---

## Slide 7 — Ethics of the measurement itself (45 s)

(B has just presented the finding on slide 6.)

**Title:** A low number can mean healthy — or uncounted

Visual: `figures/eda/ci_width_by_group.png`

- Self-reported prevalence = who answered the phone and who has seen a
  doctor. Non-response varies by state and by group; age adjustment
  doesn't fix that.
- Death certificates are filled in by people; coding practice varies. We
  used "underlying cause" everywhere it existed, but it's still a
  judgement.
- Precision: the 95% CI is 19% of the estimate statewide, 22% for White
  respondents, 50% Black, 61% Hispanic, 75–83% for AI/AN, Asian,
  Multiracial. [ci_width_by_group.txt] An interval that wide can't support
  a decision — so we put those states in "insufficient data", not in a
  ranking.
- Never "state X hides its sick people". Two instruments disagree; that
  is the whole claim.

Hand-off to B for takeaways (slide 8).

---

## Timing check

| Slide | Target | Owner |
|---|---|---|
| 2 | 0:45 | A |
| 3 | 1:00 | A |
| 4 | 1:00 | A |
| 7 | 0:45 | A |
| **A total** | **3:30** | |

If over: cut the diabetes/asthma bullets on slide 3 first, then the
discontinuity detail on slide 4 (keep the suppression heatmap).
