"""Read data/raw/export.csv.gz, coerce types, validate expected columns.

DataValueAlt, LowConfidenceLimit and HighConfidenceLimit are strings with
thousands separators ("1,015.8") in this export -- strip commas before
pd.to_numeric or ~190 cells silently become NaN. See docs/data_profile.md.

Owner: Person A
Input:  data/raw/export.csv.gz
Output: pandas.DataFrame (raw, typed); logs row count
"""

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "YearStart", "YearEnd", "LocationAbbr", "LocationDesc", "DataSource",
    "Topic", "Question", "Response", "DataValueUnit", "DataValueType",
    "DataValue", "DataValueAlt", "DataValueFootnoteSymbol", "DataValueFootnote",
    "LowConfidenceLimit", "HighConfidenceLimit",
    "StratificationCategory1", "Stratification1",
    "StratificationCategory2", "Stratification2",
    "StratificationCategory3", "Stratification3",
    "Geolocation", "LocationID", "TopicID", "QuestionID", "ResponseID",
    "DataValueTypeID", "StratificationCategoryID1", "StratificationID1",
    "StratificationCategoryID2", "StratificationID2",
    "StratificationCategoryID3", "StratificationID3",
]

NUMERIC_COLUMNS = ["DataValueAlt", "LowConfidenceLimit", "HighConfidenceLimit"]

# Empty for every row in this export (verified in docs/data_profile.md).
# YearEnd is kept: some topics (cancer, cognitive health) use multi-year
# windows; normalize.py asserts YearStart == YearEnd for the topics we use.
DROP_COLUMNS = [
    "Response", "ResponseID",
    "StratificationCategory2", "Stratification2",
    "StratificationCategoryID2", "StratificationID2",
    "StratificationCategory3", "Stratification3",
    "StratificationCategoryID3", "StratificationID3",
]


def _to_numeric_strict(s: pd.Series, name: str) -> pd.Series:
    """Coerce a comma-formatted string column to float.

    Anything that was non-null before and NaN after is a parse failure, not a
    suppressed cell, so we raise rather than let it through.
    """
    raw_null = s.isna()
    out = pd.to_numeric(s.astype("string").str.replace(",", "", regex=False), errors="coerce")
    new_null = out.isna() & ~raw_null
    if new_null.any():
        examples = s[new_null].unique()[:5].tolist()
        raise ValueError(f"{name}: {int(new_null.sum())} values failed numeric parse, e.g. {examples}")
    return out.astype(float)


def load_raw(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path, compression="infer", low_memory=False)
    log.info("load: %s rows=%d cols=%d", path.name, len(df), df.shape[1])

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        raise ValueError(f"load: missing expected columns {missing}")
    if extra:
        log.warning("load: unexpected extra columns %s (kept)", extra)

    for c in NUMERIC_COLUMNS:
        df[c] = _to_numeric_strict(df[c], c)
    df["YearStart"] = df["YearStart"].astype(int)
    df["YearEnd"] = df["YearEnd"].astype(int)
    multi = int((df["YearStart"] != df["YearEnd"]).sum())
    log.info("load: %d rows use multi-year windows (YearStart != YearEnd); normalize.py rejects any in scope", multi)

    for c in DROP_COLUMNS:
        if df[c].notna().any():
            log.warning("load: column %s expected empty but has %d values (kept)", c, int(df[c].notna().sum()))
    df = df.drop(columns=[c for c in DROP_COLUMNS if df[c].isna().all()])

    log.info("load: done rows=%d cols=%d", len(df), df.shape[1])
    return df


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", default="data/raw/export.csv.gz")
    args = parser.parse_args()
    df = load_raw(args.raw)
    print(df.dtypes)
