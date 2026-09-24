"""
Build the clean state level panel from the raw CDC Chronic Disease Indicators export.

Reads data/raw/export.csv, filters to the 4 diseases and 3 data sources we care about,
picks the specific question per (disease, measurement) combination, pivots to a wide
format where each row is one state year disease with columns for prevalence, mortality,
hospitalization and their CI bounds, and writes to data/clean/panel.csv.

Personal note: BRFSS and NVSS cover all 4 diseases but CMS only has hospitalization
data for CVD and COPD. Kept all 4 diseases in the panel so we can compare, with the
understanding that hospitalization will be null for Asthma and Diabetes.
"""

import os
import pandas as pd


# paths
RAW_PATH = "../data/raw/export.csv"
OUT_PATH = "../data/clean/panel_verify.csv"

# scope of the analysis
DISEASES_FOCUS = [
    'Asthma',
    'Cardiovascular Disease',
    'Chronic Obstructive Pulmonary Disease',
    'Diabetes',
]

DATA_SOURCES = ['BRFSS', 'NVSS', 'CMS Part A Claims Data']

# specific question per disease and measurement.
# these were picked by looking at the crosstab of Question by DataSource for each disease.
# CMS only covers CVD (heart failure) and COPD (COPD principal diagnosis).
CONDITIONS = {
    'Asthma': {
        'prevalence': {'source': 'BRFSS', 'question': 'Current asthma among adults'},
        'mortality': {'source': 'NVSS', 'question': 'Asthma mortality among all people, underlying cause'},
        'hospitalization': None,
    },
    'Cardiovascular Disease': {
        'prevalence': {'source': 'BRFSS', 'question': 'High blood pressure among adults'},
        'mortality': {'source': 'NVSS', 'question': 'Diseases of the heart mortality among all people, underlying cause'},
        'hospitalization': {'source': 'CMS Part A Claims Data', 'question': 'Hospitalization for heart failure as principal diagnosis, Medicare-beneficiaries aged 65 years and older'},
    },
    'Chronic Obstructive Pulmonary Disease': {
        'prevalence': {'source': 'BRFSS', 'question': 'Chronic obstructive pulmonary disease among adults'},
        'mortality': {'source': 'NVSS', 'question': 'Chronic obstructive pulmonary disease mortality among adults aged 45 years and older, underlying cause'},
        'hospitalization': {'source': 'CMS Part A Claims Data', 'question': 'Hospitalization for chronic obstructive pulmonary disease as principal diagnosis, Medicare-beneficiaries aged 65 years and older'},
    },
    'Diabetes': {
        'prevalence': {'source': 'BRFSS', 'question': 'Diabetes among adults'},
        'mortality': {'source': 'NVSS', 'question': 'Diabetes mortality among all people, underlying or contributing cause'},
        'hospitalization': None,
    },
}

# columns from the raw file we do not need in the panel
COLS_TO_DROP = [
    'YearEnd', 'LocationDesc', 'Response', 'DataValueUnit', 'DataValue',
    'DataValueFootnoteSymbol', 'DataValueFootnote',
    'StratificationCategory1', 'StratificationCategory2', 'Stratification2',
    'StratificationCategory3', 'Stratification3',
    'Geolocation', 'LocationID', 'TopicID', 'QuestionID', 'ResponseID',
    'DataValueTypeID',
    'StratificationCategoryID1', 'StratificationID1',
    'StratificationCategoryID2', 'StratificationID2',
    'StratificationCategoryID3', 'StratificationID3',
]


def load_raw(path):
    """Load the raw CDC export."""
    df = pd.read_csv(path)
    print(f"Raw shape: {df.shape}")
    return df


def apply_filters(df):
    """Filter to our 4 diseases, 3 sources, age adjusted overall stratification, states only."""
    cleaned = df.loc[df['Topic'].isin(DISEASES_FOCUS)]
    cleaned = cleaned.loc[cleaned['DataSource'].isin(DATA_SOURCES)]

    # keep only age adjusted overall values so state comparisons are apples to apples
    cleaned = cleaned.loc[
        cleaned['DataValueType'].isin(['Age-adjusted Rate', 'Age-adjusted Prevalence'])
        & (cleaned['Stratification1'] == 'Overall')
    ]

    # drop columns we do not need
    cleaned = cleaned.drop(columns=COLS_TO_DROP)

    # drop US aggregate rows, keep state and territory rows only
    cleaned = cleaned.loc[cleaned['LocationAbbr'] != 'US']

    cleaned = cleaned.reset_index(drop=True)
    print(f"After filtering: {cleaned.shape}")
    return cleaned


def select_specific_questions(cleaned_df):
    """
    For each (disease, measurement) combination in CONDITIONS, pull the specific
    question we picked and tag it with a 'measurement' column so it can be pivoted.
    """
    pieces = []
    for disease, measurements in CONDITIONS.items():
        for measurement_name, spec in measurements.items():
            if spec is None:
                continue
            slice_df = cleaned_df.loc[
                (cleaned_df['Topic'] == disease)
                & (cleaned_df['DataSource'] == spec['source'])
                & (cleaned_df['Question'] == spec['question'])
            ].copy()
            slice_df['measurement'] = measurement_name
            pieces.append(slice_df)

    filtered = pd.concat(pieces, ignore_index=True)
    print(f"After picking specific questions: {filtered.shape}")
    print(filtered['measurement'].value_counts())
    return filtered


def to_numeric_columns(df):
    """Coerce value and CI columns to numeric. Suppressed values become NaN."""
    df['DataValueAlt'] = pd.to_numeric(df['DataValueAlt'], errors='coerce')
    df['LowConfidenceLimit'] = pd.to_numeric(df['LowConfidenceLimit'], errors='coerce')
    df['HighConfidenceLimit'] = pd.to_numeric(df['HighConfidenceLimit'], errors='coerce')
    return df


def pivot_to_wide(filtered):
    """
    Pivot the long form filtered data into the wide panel.
    One row per (state, year, disease). Columns are prevalence, mortality,
    hospitalization and their _lo, _hi CI bounds.
    """
    index_cols = ['LocationAbbr', 'YearStart', 'Topic']

    val = filtered.pivot_table(index=index_cols, columns='measurement', values='DataValueAlt')
    lo = filtered.pivot_table(index=index_cols, columns='measurement', values='LowConfidenceLimit')
    hi = filtered.pivot_table(index=index_cols, columns='measurement', values='HighConfidenceLimit')

    # tag the CI columns so they do not collide with the point estimate names
    lo = lo.add_suffix('_lo')
    hi = hi.add_suffix('_hi')

    panel = pd.concat([val, lo, hi], axis=1)
    panel = panel.reset_index()
    return panel


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    df = load_raw(RAW_PATH)
    cleaned = apply_filters(df)
    filtered = select_specific_questions(cleaned)
    filtered = to_numeric_columns(filtered)
    panel = pivot_to_wide(filtered)

    print(f"\nFinal panel shape: {panel.shape}")
    print(f"Unique locations: {panel['LocationAbbr'].nunique()}")
    print(f"US aggregate present: {'US' in panel['LocationAbbr'].values}")
    print(f"\nFirst 5 rows:")
    print(panel.head())

    panel.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()