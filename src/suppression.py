"""Secondary analysis: suppression share and CI width by stratification group.
Suppressed != zero; count it, report it, exclude it (design rule 4).

Contract 4 output, one row per (condition, instrument, strat_category,
strat_group): n_cells, n_suppressed, n_no_data, suppression_share,
median_ci_width, median_value, n_states_any_suppressed.

Owner: Person A
Input:  data/clean/normalized_long.csv
Output: data/clean/suppression_summary.csv
        data/clean/suppression_by_state.csv   (state x condition x strat_group, for a map)
        data/clean/suppression_summary.txt    (headline numbers, human-readable)
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

KEY = ["condition", "instrument", "measure", "strat_category", "strat_group"]


def summarize(long: pd.DataFrame) -> pd.DataFrame:
    df = long.copy()
    df["ci_width"] = df["ci_hi"] - df["ci_lo"]
    # Relative width is what tells you whether an estimate is usable: a +/-1
    # point interval on 2% prevalence is very different from one on 12%.
    df["ci_rel_width"] = df["ci_width"] / df["value"]

    g = df.groupby(KEY, sort=True)
    out = pd.DataFrame({
        "n_cells": g.size(),
        "n_suppressed": g["suppressed"].sum().astype(int),
        "n_no_data": g["no_data"].sum().astype(int),
        "n_reported": g["value"].count(),
        "median_value": g["value"].median(),
        "median_ci_width": g["ci_width"].median(),
        "median_ci_rel_width": g["ci_rel_width"].median(),
        "n_states_any_suppressed": g.apply(lambda x: x.loc[x["suppressed"], "state"].nunique()),
    })
    # Share is over cells the state actually attempted to report, so "module
    # not run" does not inflate it.
    out["suppression_share"] = out["n_suppressed"] / (out["n_cells"] - out["n_no_data"])
    return out.reset_index()


def by_state(long: pd.DataFrame) -> pd.DataFrame:
    """Suppression counts per state so it can be mapped."""
    df = long[long["strat_category"] != "Overall"]
    g = df.groupby(["state", "condition", "strat_category"])
    out = pd.DataFrame({
        "n_cells": g.size(),
        "n_suppressed": g["suppressed"].sum().astype(int),
        "n_no_data": g["no_data"].sum().astype(int),
    }).reset_index()
    out["suppression_share"] = out["n_suppressed"] / (out["n_cells"] - out["n_no_data"])
    return out


def headline(summary: pd.DataFrame, long: pd.DataFrame) -> str:
    lines = ["# Suppression and precision - headline numbers", ""]
    overall = long[long["strat_category"] == "Overall"]
    strat = long[long["strat_category"] != "Overall"]
    lines.append(f"Overall (headline) cells: {len(overall):,}; suppressed {int(overall['suppressed'].sum()):,} "
                 f"({overall['suppressed'].mean():.1%})")
    lines.append(f"Stratified cells:         {len(strat):,}; suppressed {int(strat['suppressed'].sum()):,} "
                 f"({strat['suppressed'].mean():.1%})")
    lines.append("")
    lines.append("## Suppression share by race/ethnicity group (all conditions, all instruments)")
    re = summary[summary["strat_category"] == "Race/Ethnicity"].groupby("strat_group").agg(
        n_cells=("n_cells", "sum"), n_suppressed=("n_suppressed", "sum"), n_no_data=("n_no_data", "sum"))
    re["share"] = re["n_suppressed"] / (re["n_cells"] - re["n_no_data"])
    for grp, r in re.sort_values("share", ascending=False).iterrows():
        lines.append(f"  {grp:<45} {r['share']:6.1%}  ({int(r['n_suppressed']):,} of {int(r['n_cells'] - r['n_no_data']):,})")
    lines.append("")
    lines.append("## Suppression share by race/ethnicity group, BRFSS prevalence only")
    reb = summary[(summary["strat_category"] == "Race/Ethnicity") & (summary["instrument"] == "brfss")
                  & (summary["measure"] == "prevalence")]
    for cond, sub in reb.groupby("condition"):
        lines.append(f"  {cond}")
        for _, r in sub.sort_values("suppression_share", ascending=False).iterrows():
            lines.append(f"    {r['strat_group']:<43} {r['suppression_share']:6.1%}   median CI width "
                         f"{r['median_ci_width']:.1f} pts ({r['median_ci_rel_width']:.0%} of estimate)")
    lines.append("")
    lines.append("## Median CI width (points) by stratification category, BRFSS prevalence")
    w = summary[(summary["instrument"] == "brfss") & (summary["measure"] == "prevalence")].groupby(
        "strat_category")["median_ci_width"].median()
    for cat, v in w.sort_values().items():
        lines.append(f"  {cat:<20} {v:.2f}")
    lines.append("")
    lines.append("## NVSS mortality suppression by condition (Overall stratification)")
    for cond, sub in overall[overall["instrument"] == "nvss"].groupby("condition"):
        lines.append(f"  {cond:<15} {int(sub['suppressed'].sum()):>3} of {len(sub):>3} state-years suppressed "
                     f"({sub['suppressed'].mean():.0%})")
    return "\n".join(lines) + "\n"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--long", default="data/clean/normalized_long.csv")
    parser.add_argument("--out", default="data/clean")
    args = parser.parse_args()
    out = Path(args.out)

    long = pd.read_csv(args.long)
    log.info("suppression: read %d rows", len(long))
    summary = summarize(long)
    state = by_state(long)
    text = headline(summary, long)

    summary.to_csv(out / "suppression_summary.csv", index=False)
    state.to_csv(out / "suppression_by_state.csv", index=False)
    (out / "suppression_summary.txt").write_text(text, encoding="utf-8")
    log.info("suppression: wrote suppression_summary.csv (%d), suppression_by_state.csv (%d), suppression_summary.txt",
             len(summary), len(state))
    print(text)


if __name__ == "__main__":
    main()
