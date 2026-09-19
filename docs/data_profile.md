# Data profile — what the export actually contains

Profiled 2026-09-17 against `data/raw/export.csv` (398,793 rows × 34 columns).
Read this before writing `normalize.py`. Several assumptions in `CLAUDE.md`
do not hold for this file; the corrections are in bold.

## Confirmed

| Claim | Result |
|---|---|
| 398,793 rows | yes |
| 55 jurisdictions | yes — 50 states + DC + GU, PR, VI **+ a `US` national row** |
| 19 topics | yes |
| `YearStart` 2015–2023 | yes for the whole file, **no for our topics** (see below) |
| Sources present | 14 in the file, not 12; BRFSS / NVSS / CMS all present |
| Suppression marked in `DataValueFootnoteSymbol` | yes — `****` (66,555, "denominator < 50 or RSE > 30%"), `~` (36,607, "too few respondents or cases") |

## Corrections to the spec

1. **The file is `export.csv`, not `export_2.csv`.** 127 MB raw — over GitHub's
   100 MB limit. Committed as `data/raw/export.csv.gz` (9.6 MB);
   `load.py` reads the `.gz` directly (`pd.read_csv(..., compression="gzip")`).
2. **`DataValueAlt`, `LowConfidenceLimit`, `HighConfidenceLimit` are strings**
   with thousands separators (`"1,015.8"`). `load.py` must strip commas and
   `pd.to_numeric`. ~190 CI cells and an unknown number of value cells are
   affected; a naive numeric read silently NaNs them.
3. **Our four conditions only exist for 2019–2023.** No BRFSS / NVSS / CMS rows
   for COPD, CVD, diabetes, or asthma before 2019. The 2015–2018 rows in the
   file belong to other topics. The panel is 2019–2022 (the years where NVSS
   and CMS overlap BRFSS); 2023 is BRFSS-only.
4. **BRFSS core chronic-disease questions are asked every year, but the
   hypertension / cholesterol module is odd-years only** (2019, 2021, 2023).
   For cardiovascular the panel has **two** usable years: 2019 and 2021.
5. **CMS hospitalization is per 1,000 Medicare beneficiaries aged 65+**, not
   per 100k. Contract 1 updated.
6. **NVSS COPD mortality is among adults 45+**, not all ages. Diabetes and
   asthma mortality are all-ages. Note this in the writeup; it does not affect
   within-condition regressions.
7. **Exclude `LocationAbbr == "US"`** from every cross-state regression.
   Territories GU, PR, VI have BRFSS but no NVSS or CMS.
8. **There is no BRFSS "heart disease prevalence" question.** Cardiovascular
   pairs *high blood pressure prevalence* (CVD01) against *diseases-of-the-heart
   mortality* (CVD09). That is a risk-factor-vs-outcome pairing, not the same
   condition measured twice. COPD and diabetes are clean same-condition pairs.
   **COPD stays the flagship; treat CVD as a documented weaker secondary.**

## Recommended crosswalk (for `normalize.py`)

Overall stratification, age-adjusted value types only, `LocationAbbr != "US"`.

| condition | instrument | measure | QuestionID | Question (short) | unit | years | notes |
|---|---|---|---|---|---|---|---|
| copd | brfss | prevalence | COPD01 | COPD among adults | % | 2019–23 | |
| copd | brfss | treatment | COPD02 | Current smoking among adults with COPD | % | 2019–23 | **inverted**: high = *under*treatment. `brfss_treatment_rate = 100 − COPD02` or flag as inverse in the panel |
| copd | cms | hospitalization | COPD04 | COPD hospitalization, *principal* diagnosis, 65+ | per 1,000 | 2019–22 | prefer principal over COPD03 (any diagnosis) to match CVD06 |
| copd | nvss | mortality | COPD05 | COPD mortality 45+, *underlying* cause | per 100k | 2019–22 | COPD06 (underlying-or-contributing) as sensitivity |
| cardiovascular | brfss | prevalence | CVD01 | High blood pressure among adults | % | 2019, 21, 23 | risk factor, not disease |
| cardiovascular | brfss | treatment | CVD02 | Taking medicine for high BP among those with high BP | % | 2019, 21, 23 | direct treatment rate |
| cardiovascular | cms | hospitalization | CVD06 | Heart failure hospitalization, principal, 65+ | per 1,000 | 2019–22 | |
| cardiovascular | nvss | mortality | CVD09 | Diseases of the heart mortality, underlying | per 100k | 2019–22 | CVD08 (CHD) and CVD07 (stroke) as sensitivity |
| diabetes | brfss | prevalence | DIA01 | Diabetes among adults | % | 2019–23 | |
| diabetes | nvss | mortality | DIA03 | Diabetes mortality, underlying *or contributing* | per 100k | 2019–22 | DIA04 (DKA) too sparse — 20/208 suppressed |
| asthma | brfss | prevalence | AST02 | Current asthma among adults | % | 2019–23 | |
| asthma | nvss | mortality | AST01 | Asthma mortality, underlying | per 100k | 2019–22 | **50/208 suppressed** — asthma may not support a regression; report it as a suppression finding instead |

Unused questions in these topics (CVD03/04 cholesterol, COPD03, COPD06, CVD07,
CVD08, DIA04) must be **logged as seen-and-unmapped**, not silently dropped.

## First look at the thesis (Overall, age-adjusted, US excluded)

Quick OLS of mortality on prevalence, single year, no CI weighting — a sanity
check, not the analysis.

| condition | year | n states | r | slope | most + residual (more deaths than prevalence predicts) | most − residual |
|---|---|---|---|---|---|---|
| COPD | 2022 | 51 | 0.82 | 13.9 | OK +56, WY +30, AR +29, NM +27, ID +26, CO +24 | TN −31, DC −26, RI −24, LA −23, NJ −23 |
| COPD | 2021 | 50 | 0.81 | 15.0 | OK +46, WY +37, AR +28, ID +27, MS +25 | DC −44, NJ −29, LA −27, NY −26 |
| diabetes | 2022 | 51 | 0.41 | 5.8 | OK +88, MS +46, KY +38, SD +33 | CT −41, AL −38, NJ −35, MA −34 |

The pattern is stable across years for COPD (OK, WY, AR, ID recur), which is
what we need for the story. Diabetes correlation is much weaker (0.41), so
residuals there are noisier; carry the CIs.

Value ranges for the fixture: COPD prevalence 1–12 % (median 5.7, CI width
median 1.4, max 5.2 for GU 2022); COPD mortality 39–175 per 100k (median 105);
COPD hospitalization 1.6–15.7 per 1,000 (median 5.1).

## Suppression at Overall level

Only 121 of 4,048 Overall × age-adjusted cells are null in our topics. 50 of
those are asthma mortality, 20 are DKA mortality. The suppression story is in
the race/ethnicity strata (`normalized_long.csv`), not the headline panel.
