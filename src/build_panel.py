"""Pivot to one row per state x year x condition (Overall stratification)
and write the contract files.

Owner: Person A
Input:  data/raw/export.csv.gz (via load + normalize)
Output: data/clean/normalized_long.csv   (Contract 2, all strata)
        data/clean/panel.csv             (Contract 1, Overall only)
        data/clean/panel_fixture.csv     (subset of panel.csv for downstream dev)
        data/clean/attrition_log.txt
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from load import load_raw
from normalize import normalize

log = logging.getLogger(__name__)

CONDITIONS = ["copd", "cardiovascular", "diabetes", "asthma"]

# Contract 1 column order. Frozen; see WORK_SPLIT.md.
PANEL_COLUMNS = [
    "state", "year", "condition",
    "brfss_prevalence_aa", "brfss_prevalence_lo", "brfss_prevalence_hi",
    "nvss_mortality_aa", "nvss_mortality_lo", "nvss_mortality_hi",
    "cms_hospitalization_aa", "cms_hospitalization_lo", "cms_hospitalization_hi",
    "brfss_treatment_rate", "brfss_treatment_lo", "brfss_treatment_hi",
    "brfss_treatment_question",
    "n_suppressed",
]

INSTRUMENT_PREFIX = {
    ("brfss", "prevalence"): "brfss_prevalence",
    ("nvss", "mortality"): "nvss_mortality",
    ("cms", "hospitalization"): "cms_hospitalization",
    ("brfss", "treatment"): "brfss_treatment",
}


def build_panel(long: pd.DataFrame) -> pd.DataFrame:
    ov = long[long["strat_category"] == "Overall"].copy()
    log.info("build_panel: Overall rows=%d", len(ov))

    # Orientation: COPD02 measures smoking among COPD patients, i.e. treatment
    # FAILURE. Store 100 - value so brfss_treatment_rate means "share well
    # treated" for every condition. The CI flips too: lo' = 100 - hi.
    inv = ov["orientation"] == "inverse_treatment"
    n_inv = int(inv.sum())
    lo, hi = ov.loc[inv, "ci_lo"].copy(), ov.loc[inv, "ci_hi"].copy()
    ov.loc[inv, "value"] = 100 - ov.loc[inv, "value"]
    ov.loc[inv, "ci_lo"] = 100 - hi
    ov.loc[inv, "ci_hi"] = 100 - lo
    log.info("build_panel: inverted %d inverse_treatment rows (100 - value, CI flipped)", n_inv)

    ov["prefix"] = [INSTRUMENT_PREFIX[k] for k in zip(ov["instrument"], ov["measure"])]
    key = ["state", "year", "condition"]

    def pivot(col, suffix):
        w = ov.pivot(index=key, columns="prefix", values=col)
        w.columns = [f"{c}_{suffix}" for c in w.columns]
        return w

    wide = pd.concat([pivot("value", "aa"), pivot("ci_lo", "lo"), pivot("ci_hi", "hi")], axis=1)
    # Contract names: the point estimate for treatment is `_rate`, not `_aa`.
    wide = wide.rename(columns={"brfss_treatment_aa": "brfss_treatment_rate"})

    tq = ov[ov["measure"] == "treatment"].set_index(key)["question_id"]
    wide["brfss_treatment_question"] = tq.reindex(wide.index)

    n_sup = ov.groupby(key)["suppressed"].sum().astype(int)
    wide["n_suppressed"] = n_sup.reindex(wide.index).fillna(0).astype(int)

    wide = wide.reset_index()
    for c in PANEL_COLUMNS:
        if c not in wide.columns:
            wide[c] = np.nan
    panel = wide[PANEL_COLUMNS].copy()
    panel["condition"] = pd.Categorical(panel["condition"], CONDITIONS, ordered=True)
    panel = panel.sort_values(["condition", "state", "year"]).reset_index(drop=True)
    panel["condition"] = panel["condition"].astype(str)

    assert not panel.duplicated(key).any(), "panel key not unique"
    assert not panel["state"].eq("US").any(), "US row leaked into panel"
    log.info("build_panel: panel rows=%d states=%d years=%s",
             len(panel), panel["state"].nunique(), sorted(panel["year"].unique()))
    for cond in CONDITIONS:
        p = panel[panel["condition"] == cond]
        both = p["brfss_prevalence_aa"].notna() & p["nvss_mortality_aa"].notna()
        log.info("build_panel: %-15s rows=%d  with prevalence+mortality=%d  suppressed cells=%d",
                 cond, len(p), int(both.sum()), int(p["n_suppressed"].sum()))
    return panel


def make_fixture(panel: pd.DataFrame) -> pd.DataFrame:
    """A small, real subset for Person B to develop against. Includes GU 2022
    (widest COPD CI in the file), a state with suppressed asthma mortality,
    and consistently high- and low-residual COPD states."""
    states = ["OK", "WY", "TN", "NJ", "GU", "VT", "CA"]
    fx = panel[panel["state"].isin(states) & panel["year"].isin([2021, 2022])]
    fx = fx[fx["condition"].isin(["copd", "asthma"])]
    return fx.reset_index(drop=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", default="data/raw/export.csv.gz")
    parser.add_argument("--out", default="data/clean")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    raw = load_raw(args.raw)
    long, attrition = normalize(raw)
    panel = build_panel(long)
    fixture = make_fixture(panel)

    (out / "attrition_log.txt").write_text(attrition.render(), encoding="utf-8")
    long.to_csv(out / "normalized_long.csv", index=False)
    panel.to_csv(out / "panel.csv", index=False)
    fixture.to_csv(out / "panel_fixture.csv", index=False)
    log.info("build_panel: wrote %s (%d), %s (%d), %s (%d), attrition_log.txt",
             "normalized_long.csv", len(long), "panel.csv", len(panel), "panel_fixture.csv", len(fixture))


if __name__ == "__main__":
    main()
