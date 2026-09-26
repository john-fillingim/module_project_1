# When the Survey and the Death Certificate Disagree

## Overview

The CDC counts chronic disease three ways: a phone survey (how many adults
say they have it), Medicare hospital claims (how many are admitted for it),
and death certificates (how many die of it). This project asks what it means
when those counts disagree. For each condition we regress state mortality on
survey prevalence, treat the residual as "unexpected" mortality, and check
whether hospitalization explains it.

**Finding.** For COPD, states that hospitalize more have *lower* mortality
than their prevalence predicts (r = −0.44 in 2021; r = −0.38 in the 2019
replication). For cardiovascular disease there is no consistent relationship
(r = 0.04 in 2021, 0.22 in 2019). This is a state-level association and is
consistent with, but does not prove, hospital care reducing COPD deaths.

**Public communication piece:** TODO link

## Dataset

Centers for Disease Control and Prevention. *U.S. Chronic Disease Indicators
(CDI)*. Available at https://data.cdc.gov/ (dataset "U.S. Chronic Disease
Indicators"), full CSV export.
TODO: download date and portal dataset ID / release version.

`data/raw/export.csv.gz` — 398,793 rows × 34 columns, 55 jurisdictions
(50 states, DC, Guam, Puerto Rico, US Virgin Islands) plus a `US` national
row, 14 data sources, 19 topics. The file covers 2015–2023 overall, but the
four conditions used here (COPD, cardiovascular, diabetes, asthma) are
present only for 2019–2023, and the mortality (NVSS) and hospitalization
(CMS) instruments end in 2022. The raw export is 127 MB, so it is committed
gzipped (9.6 MB); the scripts read the `.gz` directly.
`gunzip -k data/raw/export.csv.gz` if you want the plain CSV.

Three instruments are used, all age-adjusted, `Overall` stratification for
the headline analysis:

| Instrument | `DataSource` | What it measures | Unit |
|---|---|---|---|
| Survey | BRFSS | Self-reported diagnosed prevalence among adults; treatment among the diagnosed | % |
| Claims | CMS Part A Claims Data | Hospitalization, principal diagnosis, Medicare beneficiaries 65+ | per 1,000 |
| Death certificates | NVSS | Mortality, underlying cause (COPD: adults 45+) | per 100,000 |

The exact `QuestionID` → condition crosswalk, with the reason for every
choice, is in [src/normalize.py](src/normalize.py) (`CROSSWALK`). What was
verified in the file before writing it is in
[docs/data_profile.md](docs/data_profile.md).

### Cleaned data (`data/clean/`, committed)

| File | Grain | Produced by |
|---|---|---|
| `normalized_long.csv` | one row per state × year × question × stratification group (25,464 rows) | `build_panel.py` |
| `panel.csv` | one row per state × year × condition, Overall only (1,074 rows) | `build_panel.py` |
| `panel_fixture.csv` | 28-row subset of `panel.csv` for developing downstream code | `build_panel.py` |
| `attrition_log.txt` | row count after every filter; every value type and question seen | `build_panel.py` |
| `suppression_summary.csv` | suppression share and CI width per condition × instrument × stratification group | `suppression.py` |
| `suppression_by_state.csv` | suppression counts per state × condition × stratification category | `suppression.py` |
| `panel_verify.csv` | one row per state × year × condition, wide: prevalence / mortality / hospitalization with CI bounds (1,057 rows). **Input to the analysis.** | `verify_panel.py` |

Attrition through the pipeline (from `attrition_log.txt`):

```
raw                                398,793
Topic in 4 conditions              115,826
DataSource in BRFSS/NVSS/CMS       114,528
DataValueType age-adjusted only     39,232
LocationAbbr != US                  38,496
QuestionID in crosswalk             25,464
```

Suppressed values are kept as NaN with the CDC footnote attached and a
`suppressed` flag. They are never imputed and never treated as zero.

## Reproduce

Python 3.10+.

```bash
pip install -r requirements.txt
gunzip -k data/raw/export.csv.gz          # verify_panel.py reads the plain CSV

# Upstream pipeline and EDA (run from the repository root)
python src/build_panel.py --raw data/raw/export.csv.gz --out data/clean
python src/profile.py     --long data/clean/normalized_long.csv --out figures/eda
python src/suppression.py --long data/clean/normalized_long.csv --out data/clean

# Analysis (run from src/ — these scripts use paths relative to src/)
cd src
python verify_panel.py    # data/raw/export.csv -> data/clean/panel_verify.csv
python analyze.py         # panel_verify.csv    -> figures/analysis/*.png + printed tables
```

`verify_panel.py` rebuilds the wide panel directly from the raw export,
independently of `build_panel.py`, as a cross-check; `analyze.py` reads its
output. `analyze.py` fits one mortality-on-prevalence regression per
condition for 2021 (the primary year, the latest with full BRFSS + NVSS + CMS
coverage) and 2019 (replication), prints the best/worst five states by
residual z-score and the hospitalization–residual correlations, and writes
the eight presentation figures. CMS hospitalization is rescaled from per
1,000 to per 100,000 to match mortality. It calls `plt.show()`, so set
`MPLBACKEND=Agg` to run it headless.

Outputs land in `data/clean/` and `figures/`; both are committed so the repo
is inspectable without running anything. `build_panel.py` raises on any
unrecognised `QuestionID`, any value that fails numeric parsing, and any
duplicate key, so a silent schema change in a re-downloaded export will
stop the pipeline rather than corrupt the panel.

## Repository layout

```
src/
  load.py          read raw CSV.gz, coerce comma-formatted numerics, validate columns   (A)
  normalize.py     age-adjusted filter, QuestionID -> condition crosswalk, attrition log (A)
  build_panel.py   state x year x condition panel; writes data/clean/                   (A)
  profile.py       EDA: coverage, 2020 discontinuity, suppression, CI width figures     (A)
  suppression.py   suppression share and precision by stratification group             (A)
  verify_panel.py  independent rebuild of the wide panel -> panel_verify.csv             (B)
  analyze.py       per-condition regressions, residual z-scores, figures 00-07          (B)
  *.ipynb          exploratory notebooks behind the two scripts above                   (B)
data/raw/          export.csv.gz (committed); export.csv (gitignored, 127 MB)
data/clean/        generated, committed
figures/eda/       generated by profile.py, committed
figures/analysis/  generated by analyze.py, committed
docs/              data_profile.md, ethics_A.md
slides/            presentation outline (A_slides.md)
```

## Team

- John Fillingim — Person A: upstream pipeline, suppression, dataset ethics
- Praful Chunchu — Person B: regression analysis, figures, public piece
