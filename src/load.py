"""Read data/raw/export.csv.gz, coerce types, validate expected columns.

DataValueAlt, LowConfidenceLimit and HighConfidenceLimit are strings with
thousands separators ("1,015.8") in this export -- strip commas before
pd.to_numeric or ~190 cells silently become NaN. See docs/data_profile.md.

Owner: Person A
Input:  data/raw/export.csv.gz
Output: pandas.DataFrame (raw, typed); logs row count
"""
