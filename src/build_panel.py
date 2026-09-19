"""Pivot to one row per state x year x condition (Overall stratification)
and write the two contract files.

Owner: Person A
Input:  data/raw/export.csv.gz (via load + normalize)
Output: data/clean/panel.csv, data/clean/normalized_long.csv (see WORK_SPLIT.md)
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # TODO: add --raw / --panel / --out arguments per CLAUDE.md "Reproduce"
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
