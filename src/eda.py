"""Figures 1-3. Reads ONLY data/clean/*.csv. No imports from load/normalize/
build_panel. Every number that appears in a figure is also written to a
text file next to it in figures/.

Owner: Person B
Input:  data/clean/panel.csv, data/clean/divergence.csv, data/clean/suppression_summary.csv
Output: figures/*.png + figures/*.txt
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # TODO: add --raw / --panel / --out arguments per CLAUDE.md "Reproduce"
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
