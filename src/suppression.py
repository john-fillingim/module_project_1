"""Secondary analysis: suppression share and CI width by stratification group.
Suppressed != zero; count it, report it, exclude it (design rule 4).

Owner: Person A
Input:  data/clean/normalized_long.csv
Output: data/clean/suppression_summary.csv
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # TODO: add --raw / --panel / --out arguments per CLAUDE.md "Reproduce"
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
