"""Raw-data EDA: coverage by DataSource x condition x year, missingness,
and the 2020-21 BRFSS discontinuity check. Discovery figures, not story
figures (those are eda.py, Person B).

Owner: Person A
Input:  data/clean/normalized_long.csv
Output: figures/eda/*.png + figures/eda/*.txt
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # TODO: --long data/clean/normalized_long.csv --out figures/eda
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
