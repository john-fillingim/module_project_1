# Work split

Two people, one seam: the `data/clean/` directory.

- **Person A — upstream.** Owns everything that touches `data/raw/export.csv.gz`.
  Produces the clean tables, the raw-data EDA, and the suppression analysis.
- **Person B — downstream.** Owns everything that reads from `data/clean/`.
  Produces the finding, the story figures, and the public piece.

Neither person imports from the other's modules. The only thing that crosses
the seam is the CSV contracts below. This is the rule CLAUDE.md already sets
for `eda.py` ("reads panel only, no upstream imports"), applied to the whole
project.

**Hard deadline: in-class presentation Tue Sep 22.** Dated milestones at the
bottom.

**Read `docs/data_profile.md` first.** The raw file differs from the spec in
several ways (2019–2022 only, string-typed numerics, CMS per 1,000, CVD
odd-years only, a `US` row). The contracts below already reflect the data.

---

## Rubric checklist → owner

The assignment grades three deliverables. Every line item has an owner.

### Deliverable 1 — Public communication piece (link)

**Format: blog post** (recommended — it is the writeup we already have to
produce, and a draft on Byline or a GitHub Pages `docs/index.md` is the least
extra work in five days). If the team prefers infographic + short explainer,
B still owns it and the figures are the same.

| Rubric item | Owner |
|---|---|
| Clear, engaging title | B drafts, A approves |
| Why it matters + who the audience is | B |
| Key findings with visualizations and examples | B (figures 1, 2); A (figure 3, suppression) |
| Data limitations, bias, ethics — in plain language | A: survey non-response, death-certificate coding, suppression. B: "consistent with, never proves", the five alternative explanations from CLAUDE.md |
| Narrative arc — what surprised us, what to take away | B writes, A reviews for accuracy against pipeline |

### Deliverable 2 — GitHub repository (link)

| Rubric item | Owner |
|---|---|
| All preprocessing / EDA / feature-engineering code as **scripts** | A: `load.py`, `normalize.py`, `build_panel.py`, `profile.py`, `suppression.py`. B: `divergence.py`, `eda.py` |
| README — project overview | B |
| README — dataset description + citation, download date, portal version | A |
| README — step-by-step reproduce instructions | A writes, B verifies by running from a fresh clone |
| Branches + pull requests; **each member ≥ 1 PR**; reviews | Both — see Git workflow below |
| Raw and cleaned data committed | A commits `data/raw/export.csv.gz` (9.6 MB; the 127 MB `.csv` is gitignored) and `data/clean/*.csv`. B commits `data/clean/divergence.csv` |

**Raw file size note.** `export.csv` is 127 MB, over GitHub's 100 MB limit.
Resolved: `export.csv.gz` (9.6 MB) is committed, `load.py` reads it with
`compression="gzip"`, and the README says `gunzip` if you want the plain file.

### Deliverable 3 — Presentation (8 min, Sep 22)

Split 4 / 4. Slide order follows the rubric's list exactly.

| Rubric item | Slide | Presenter |
|---|---|---|
| Audience and why this story matters | 1 | B |
| Dataset and topic | 2 | A |
| Key trends and visualizations from EDA | 3–4 | A (coverage, 2020 break, suppression map) |
| Engineered features that shaped the analysis | 5 | B (residual, z, CI-overlap flag, bucket) |
| The story the data tells + ethical implications | 6–7 | B (finding) then A (measurement ethics) |
| Final takeaways | 8 | B |

Timing: A has ~3.5 min across slides 2–4 and 7; B has ~4.5 min. Rehearse once
on Sep 21 with a timer; cut, don't speed up.

---

## Engineered features — say this phrase out loud

The rubric grades feature engineering explicitly. These are ours, and the
writeup and slide 5 must call them "engineered features" by name:

| Feature | Built in | Owner | Why it exists |
|---|---|---|---|
| `condition` | `normalize.py` | A | Crosswalk collapsing ~dozens of `Question` strings into four comparable conditions |
| `brfss_treatment_rate` | `build_panel.py` | A | Treatment-among-diagnosed, the lever that separates undiagnosis from undertreatment |
| `n_suppressed` | `build_panel.py` | A | Suppression carried as a count, not silently as NaN |
| `ci_width`, `suppression_share` by stratum | `suppression.py` | A | Precision inequality — how well each group's health is actually known |
| `mortality_predicted`, `divergence_residual` | `divergence.py` | B | The finding — mortality relative to what reported prevalence predicts |
| `divergence_z` | `divergence.py` | B | Cross-condition comparability |
| `ci_overlaps_zero` | `divergence.py` | B | Carries instrument uncertainty into the ranking |
| `bucket` | `divergence.py` | B | Three-way classification instead of a leaderboard |
| `cms_pattern` | `divergence.py` | B | Triangulation with the third instrument |

---

## File ownership

Every file has exactly one owner. If you need something from the other half,
ask for it in the contract — don't edit their file.

| Path | Owner | What it does |
|---|---|---|
| `src/load.py` | A | Read `export.csv.gz`; strip thousands separators and coerce `DataValueAlt` / CI limits to float; validate columns; log row count |
| `src/normalize.py` | A | Filter `DataValueType` to age-adjusted; question → condition crosswalk (**the single config module**, A is sole editor); log attrition per filter |
| `src/build_panel.py` | A | Pivot to state × year × condition; write `panel.csv` and `normalized_long.csv` |
| `src/profile.py` | A | Raw-data EDA: coverage by source/condition/year, missingness, 2020–21 discontinuity check. Writes `figures/eda/*` |
| `src/suppression.py` | A | Suppression share + CI width by stratification group; write `suppression_summary.csv` |
| `src/divergence.py` | B | Regression, residuals, z-scores, CI-aware confidence, three-bucket classification, CMS triangulation; write `divergence.csv` |
| `src/eda.py` | B | Story figures 1–3 + the numbers-alongside text files in `figures/` |
| `data/clean/panel_fixture.csv` | A | Hand-made fixture, day 1 (see Milestones) |
| `README.md` | A (dataset, reproduce) / B (overview) | |
| `docs/` or blog draft | B | The public piece |
| `slides/` | both, own slides | |

### Design rules by owner

| Rule | Owner |
|---|---|
| 1. Age-adjusted only | A |
| 4. Suppressed ≠ zero | A |
| 6. Fail loudly / log attrition | A |
| 2. Residuals, not ratios | B |
| 3. Carry uncertainty through | B |
| 5. Three buckets, not one leaderboard | B |

---

## Git workflow (rubric: branches, PRs, reviews)

- `main` is never committed to directly. Turn on branch protection requiring
  one review.
- Branch names: `a/<topic>` and `b/<topic>`, e.g. `a/normalize-crosswalk`,
  `b/divergence-regression`.
- One PR per milestone below, minimum. That guarantees each member has several
  PRs, not just the required one.
- **The other person reviews.** Review means: pull the branch, run the script,
  check the row-count log or output CSV against the contract, leave at least
  one substantive comment. Approve, then the author merges.
- Commit messages: imperative, one logical change each, e.g.
  `Add question->condition crosswalk with rationale`. No `wip`, no `fix`.
- Because ownership is by file, PRs from A and B should never touch the same
  file. If one does, stop and talk before merging.

---

## Contract 1 — `data/clean/panel.csv`  ✅ shipped (1,074 rows, 54 states, 2019–2023)

One row per `(state, year, condition)`. Overall stratification only.
Age-adjusted only. Frozen — changing a column name or dtype requires both
people agreeing in the same conversation.

| Column | dtype | Notes |
|---|---|---|
| `state` | str | `LocationAbbr`, 2-letter |
| `year` | int | `YearStart`; 2019–2022 (2023 is BRFSS-only, keep rows but NVSS/CMS will be NaN) |
| `condition` | str | one of `copd`, `cardiovascular`, `diabetes`, `asthma`. `US` row excluded |
| `brfss_prevalence_aa` | float | age-adjusted %; NaN if missing or suppressed |
| `brfss_prevalence_lo` | float | `LowConfidenceLimit` |
| `brfss_prevalence_hi` | float | `HighConfidenceLimit` |
| `nvss_mortality_aa` | float | age-adjusted rate per 100k; NaN if missing/suppressed. COPD is among adults 45+ |
| `nvss_mortality_lo` | float | |
| `nvss_mortality_hi` | float | |
| `cms_hospitalization_aa` | float | age-adjusted **per 1,000 Medicare beneficiaries 65+**; NaN for diabetes/asthma |
| `cms_hospitalization_lo` | float | |
| `cms_hospitalization_hi` | float | |
| `brfss_treatment_rate` | float | treatment-among-diagnosed %, oriented so **high = well treated**. CVD: CVD02 as-is. COPD: `100 − COPD02` (smoking among COPD is an *under*treatment signal). NaN for diabetes/asthma |
| `brfss_treatment_lo` | float | |
| `brfss_treatment_hi` | float | |
| `brfss_treatment_question` | str | QuestionID that fed `brfss_treatment_rate` (`CVD02`, `COPD02`) so the inversion is auditable |
| `n_suppressed` | int | count of instrument cells that were suppressed for this row |

Suppressed is NaN plus a count, never zero, never imputed.

## Contract 2 — `data/clean/normalized_long.csv`  ✅ shipped

Long format, **all** stratifications kept, age-adjusted only, questions
already mapped to `condition`. This exists because suppression and CI-width
analysis need the race/ethnicity/sex/age strata, which the Overall-only panel
deliberately drops. 25,464 rows.

| Column | dtype |
|---|---|
| `state` | str |
| `year` | int |
| `condition` | str |
| `instrument` | str — `brfss`, `nvss`, `cms` |
| `measure` | str — `prevalence`, `mortality`, `hospitalization`, `treatment` |
| `question_id` | str — CDC `QuestionID`, so every value is traceable |
| `orientation` | str — `direct` or `inverse_treatment` (COPD02); values here are **not** inverted, panel.csv does that |
| `strat_category` | str — `StratificationCategory1` |
| `strat_group` | str — `Stratification1` |
| `value` | float — `DataValueAlt`, NaN if suppressed or no data |
| `ci_lo`, `ci_hi` | float |
| `unit` | str — `%`, `cases per 100,000`, `cases per 1,000` |
| `suppressed` | bool — footnote `****` or `~` (value withheld) |
| `no_data` | bool — footnote `*`, `#`, `~~`, `~~~~` (state did not collect it) |
| `caution` | bool — footnote `###` or `&` (value present, wide CI / n<60) |
| `footnote_symbol`, `footnote` | str |

## Contract 3 — `data/clean/divergence.csv` (B → writeup/figures)

One row per `(state, year, condition)`, joined back to the panel columns plus:

| Column | dtype | Notes |
|---|---|---|
| `mortality_predicted` | float | fitted value from the regression |
| `divergence_residual` | float | observed − predicted |
| `divergence_z` | float | residual standardised within condition-year |
| `residual_ci_lo`, `residual_ci_hi` | float | residual band propagated from the instrument CIs |
| `ci_overlaps_zero` | bool | if true, the state cannot be confidently ranked |
| `bucket` | str | `undiagnosis`, `undertreatment`, `insufficient_data`, or `no_signal` |
| `cms_pattern` | str | for COPD/CVD only: `survey_artifact`, `outside_system`, `consistent`, or NaN |
| `model_spec` | str | e.g. `per_condition_year` or `pooled_year_fe`, so the writeup can say which |

## Contract 4 — `data/clean/suppression_summary.csv` (A → figure 3)  ✅ shipped

One row per `(condition, instrument, measure, strat_category, strat_group)`:
`n_cells`, `n_suppressed`, `n_no_data`, `n_reported`, `median_value`,
`median_ci_width`, `median_ci_rel_width`, `n_states_any_suppressed`,
`suppression_share` (= suppressed / (cells − no_data)).

Also `suppression_by_state.csv` (state × condition × strat_category) for a
map, and `suppression_summary.txt` with the headline numbers.

---

## Milestones (dated — presentation is Tue Sep 22)

Order matters: B must never be blocked waiting on A. Each milestone is one PR.

| When | A | B |
|---|---|---|
| **Thu Sep 17** | ✅ `export.csv.gz`, `panel_fixture.csv` (28 real rows: OK/WY/TN/NJ/GU/VT/CA × 2021–22 × copd/asthma): ~5 states × 2 years × 2 conditions, exact Contract 1 schema, at least one suppressed cell and one wide CI. | Pick blog platform; write title + audience paragraph; set up `divergence.py` skeleton against the fixture. |
| **Fri Sep 18** | ✅ `load.py` + `normalize.py` + `build_panel.py`; `data/clean/attrition_log.txt` is the PR deliverable. | `divergence.py` end-to-end on fixture: residuals, z, CI propagation, buckets, CMS pattern → `divergence.csv`. |
| **Sat Sep 19** | ✅ done early: `panel.csv`, `normalized_long.csv`, `profile.py` → `figures/eda/`. | Re-run on real panel — same code, no changes. Figures 1 and 2 with numbers-alongside `.txt`. Start blog body. |
| **Sun Sep 20** | ✅ done early: `suppression.py`, README dataset + reproduce, `docs/ethics_A.md`. Remaining: confirm portal version/ID in README. | Figure 3 from A's summary. Blog draft complete incl. limitations section. README overview. |
| **Mon Sep 21** | Verify B's blog numbers against pipeline output. Slides 2–4, 7 (outline in `slides/A_slides.md`). | Fresh-clone reproduce test of README. Slides 1, 5, 6, 8. **Joint: timed rehearsal, hedging-language pass on blog.** |
| **Tue Sep 22** | Present. | Present. Submit blog link + repo link. |

If A's real panel breaks B's code on Sep 19, the fixture was wrong — fix the
fixture, not the contract.

---

## Things that will cause a merge conflict if ignored

- The crosswalk lives only in `normalize.py`. B does not add conditions or
  questions; B asks A.
- `eda.py` reads `panel.csv`, `divergence.csv`, `suppression_summary.csv`.
  Nothing else. No `from load import ...`.
- Column names are the contract. Rename in a shared conversation or not at all.
- `data/clean/` and `figures/` are generated **and committed** (rubric requires
  cleaned data in the repo). Regenerate, don't hand-edit; commit the regenerated
  output in the same PR as the code change that produced it.
