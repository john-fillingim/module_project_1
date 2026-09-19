# When the Survey and the Death Certificate Disagree

<!-- Owner: B -->
## Overview

TODO (B): 3-5 sentences. What the story is, who it is for, what the one-line
finding is. Link to the blog post.

**Public communication piece:** TODO link

<!-- Owner: A -->
## Dataset

Centers for Disease Control and Prevention. *U.S. Chronic Disease Indicators.*
TODO (A): portal URL, portal version, download date.

`data/raw/export.csv.gz` — 398,793 rows, 34 columns, 55 jurisdictions (50
states, DC, GU, PR, VI) plus a US national row, 14 data sources, 19 topics.
The file covers 2015-2023 overall, but the four conditions used here
(COPD, cardiovascular, diabetes, asthma) are present only for 2019-2023.
The raw export is 127 MB, so it is committed gzipped (9.6 MB); the scripts
read the `.gz` directly. `gunzip -k data/raw/export.csv.gz` if you want the
plain CSV. TODO (A): how the export was filtered on the portal, if at all.

See `docs/data_profile.md` for what was verified in the file.

Instruments used: BRFSS (self-reported prevalence), NVSS (mortality), CMS
Part A (Medicare hospitalization).

<!-- Owner: A writes, B verifies from a fresh clone -->
## Reproduce

```bash
pip install -r requirements.txt
python src/build_panel.py --raw data/raw/export.csv.gz --out data/clean
python src/profile.py     --long data/clean/normalized_long.csv --out figures/eda
python src/suppression.py --long data/clean/normalized_long.csv --out data/clean
python src/divergence.py  --panel data/clean/panel.csv --out data/clean
python src/eda.py         --clean data/clean --out figures
```

Outputs land in `data/clean/` and `figures/`; both are committed so the repo
is inspectable without running anything.

## Repository layout

See `WORK_SPLIT.md` for file ownership and the column contracts between
pipeline stages. See `CLAUDE.md` for the method and design rules.

## Team

- Person A (upstream pipeline, suppression, dataset ethics): TODO name
- Person B (divergence analysis, figures, public piece): TODO name
