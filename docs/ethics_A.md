# Ethics and limitations — Person A's sections

For the blog post's "limitations, bias, and ethics" section and slide 7.
Written for a general reader. Every number below comes from a file in
`data/clean/` or `figures/eda/`; the source is named in brackets so B can
check it. B owns the companion section on how to read the residuals
("consistent with", never "proves") and the five alternative explanations.

---

## 1. "Self-reported prevalence" means "who answered the phone"

BRFSS is a telephone survey. A state's COPD prevalence is not a count of
people with COPD; it is the share of people who picked up, agreed to a
lengthy telephone interview, and said a doctor had told them they have it. That
depends on three things that vary by state: who has a phone number the
survey can reach, who agrees to answer, and who has seen a doctor recently
enough to have been told. The third one is the whole point of this
project. The first two are noise we cannot remove — a state whose response
rate is low among the people most likely to be sick will look healthier
than it is, and the age adjustment we apply does not fix that.

Concretely: the survey did not reach 2020 the way it reached other years.
Across the 50 states, 2020 COPD prevalence sits 0.16 points below the
average of 2019 and 2021, and asthma 0.19 points below; two-thirds of
states are lower in 2020 for both. Diabetes shows no shift. The dip is
small next to the typical confidence interval (about 1.4 points for COPD),
so it does not change any state's position in our analysis, but it is a
reminder that a year-to-year change in a survey number can be a change in
the survey rather than in the population.
[figures/eda/discontinuity_2020.txt; CI width from docs/data_profile.md]

## 2. Death certificates are filled in by people

A death is attributed to COPD when the certifying physician or medical
examiner writes it as the underlying cause. That is a judgement, and
practice differs between states and between hospitals and nursing homes
within a state. We chose the stricter "underlying cause" definition
wherever it existed rather than "underlying or contributing", because the
looser definition is more sensitive to coding habits; but even the strict
one is not a laboratory measurement. Some of the divergence we report
between survey and death certificate may be divergence between two states'
certifying conventions. We cannot tell from this data alone, which is why
the third instrument — hospital claims, where a diagnosis is recorded by a
clinician at the time — matters so much.

## 3. Suppression protects individuals and erases groups

CDC withholds a number when it is based on too few people (fewer than 50
respondents, or a relative standard error over 30%). This is the right
thing to do for privacy. It also means the groups we know least about are
exactly the groups that are smallest in a state.

At the headline level this barely matters: 57 of 2,628 statewide cells are
suppressed (2.2%). In the race/ethnicity breakdown it is the dominant
feature of the data: 8,575 of 22,836 cells are suppressed (37.6%).
[data/clean/suppression_summary.txt]

By group, across all four conditions and all three instruments
[figures/eda/suppression_by_group.txt]:

| Group | Share of cells suppressed |
|---|---|
| Native Hawaiian or Other Pacific Islander | 94% |
| American Indian or Alaska Native | 68% |
| Asian | 67% |
| Multiracial | 59% |
| Hispanic | 37% |
| Black | 32% |
| White | 5% |

For COPD specifically, the Native Hawaiian / Pacific Islander row is 98%
suppressed and the Asian row 85%. For those groups, in most states, there
is no COPD prevalence number at all. Any state ranking, any disparity
analysis, any "our state is doing well" claim is built on the cells that
survived — which are disproportionately White.

## 4. Even where a number exists, it may not be usable

A suppressed cell is at least honest about its absence. A wide confidence
interval is quieter. For statewide BRFSS prevalence, the typical 95%
interval is 19% as wide as the estimate itself — a COPD prevalence of 6%
comes with a range of roughly 5.4 to 6.6. For White respondents it is 22%.
For Black respondents it is 50%; for Hispanic, 61%; for American Indian /
Alaska Native, Asian and Multiracial respondents, over 75% — the interval
is nearly as wide as the number. [figures/eda/ci_width_by_group.txt]

An estimate whose interval is 80% of its value cannot tell you whether a
group's prevalence went up or down, or whether it is higher or lower than
the state average. It exists, it appears in tables, and it cannot support
a decision. This is why the main analysis carries the confidence intervals
through to the final classification and assigns states with wide intervals
to an "insufficient data" bucket rather than ranking them.

## 5. What we did to keep the analysis honest

- **Age-adjusted values only.** States differ enormously in age structure;
  a crude comparison would mostly measure how old a state is.
- **Suppressed is not zero.** Suppressed cells are counted, reported, and
  excluded. Nothing is imputed.
- **Every filter is logged.** `data/clean/attrition_log.txt` records the row
  count after each step and every question or value type the pipeline saw
  and chose not to use, with the reason.
- **The pairing is documented where it is weak.** Cardiovascular disease
  has no self-reported "heart disease" question in BRFSS, so we pair high
  blood pressure prevalence with heart-disease mortality — a risk factor
  against an outcome. COPD and diabetes are the same condition measured
  twice; cardiovascular is not, and we say so.
- **No intent is implied.** A state with low reported prevalence and high
  mortality is not hiding anything. It is a state where two measurement
  systems disagree, and the disagreement is worth investigating.
