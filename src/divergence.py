"""Regress age-adjusted mortality on age-adjusted prevalence per condition;
residuals, within-condition-year z-scores, CI propagation, three-bucket
classification, CMS triangulation. Residuals, not ratios (design rule 2).
Carry uncertainty through (rule 3). Three buckets, not a leaderboard (rule 5).

Owner: Person B
Input:  data/clean/panel.csv (or panel_fixture.csv while developing)
Output: data/clean/divergence.csv (see WORK_SPLIT.md Contract 3)
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # TODO: add --raw / --panel / --out arguments per CLAUDE.md "Reproduce"
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
