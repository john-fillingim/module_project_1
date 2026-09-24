"""
State level analysis of CDC chronic disease indicators.

Reads panel.csv, fits per disease regressions of mortality on prevalence,
computes residuals and z scores, prints best and worst state tables, and
generates the seven figures used in the presentation.

Primary analysis is on 2021 (only recent year with complete BRFSS + NVSS +
CMS coverage). 2019 is used as a robustness check to confirm findings are
not year specific.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


# paths
PANEL_PATH = "../data/clean/panel_verify.csv"
FIG_DIR = "../figures/analysis"

# analysis years
PRIMARY_YEAR = 2021
REPLICATION_YEAR = 2019

# disease and color mapping used across figures
DISEASE_COLORS = [
    ('Asthma', 'tab:blue'),
    ('Cardiovascular Disease', 'tab:orange'),
    ('Chronic Obstructive Pulmonary Disease', 'tab:green'),
    ('Diabetes', 'tab:red'),
]


# ============================================================
# data loading and feature engineering
# ============================================================

def load_panel(path):
    """Load panel.csv and rescale hospitalization from per 1k to per 100k."""
    df = pd.read_csv(path)
    # CMS reports hospitalization per 1,000 beneficiaries.
    # NVSS mortality is per 100,000. Rescale so both are on the same denominator.
    df['hospitalization'] = df['hospitalization'] * 100
    df['hospitalization_lo'] = df['hospitalization_lo'] * 100
    df['hospitalization_hi'] = df['hospitalization_hi'] * 100
    return df


def check_coverage(df):
    """Print how many state rows have both prevalence and mortality for each disease year."""
    print("Rows with both prevalence AND mortality by disease year:\n")
    for topic in df['Topic'].unique():
        d = df[df['Topic'] == topic]
        for year in [2019, 2020, 2021, 2022, 2023]:
            y = d[d['YearStart'] == year]
            both = (y['prevalence'].notna() & y['mortality'].notna()).sum()
            print(f"  {topic:45} {year}  both: {both}")
        print()


def fit_regressions_for_year(df, year):
    """
    Fit one linear regression per disease on the given year.

    Returns a long form results dataframe with prediction, residual, and
    residual z score added for every state that had complete prevalence and
    mortality data.
    """
    output_groups = []
    year_subset = df[df['YearStart'] == year]
    print(f"\nFitting regressions for {year} (subset shape: {year_subset.shape})\n")

    for disease, group in year_subset.groupby('Topic'):
        # need both prevalence and mortality to fit the regression.
        # drop nulls rather than impute, since imputing state level data would
        # fabricate signal we do not actually have.
        clean = group.dropna(subset=["prevalence", "mortality"]).copy()
        print(f"  {disease}: {len(clean)} states with complete data")

        if len(clean) == 0:
            continue

        X = clean[['prevalence']]
        y = clean['mortality']
        model = LinearRegression().fit(X, y)

        clean['prediction'] = model.predict(X)
        clean['residual'] = y - clean['prediction']

        # z score the residuals so states can be compared across diseases
        if clean['residual'].std() > 0:
            clean['residual_z_score'] = (
                (clean['residual'] - clean['residual'].mean())
                / clean['residual'].std()
            )
        else:
            clean['residual_z_score'] = 0.0

        output_groups.append(clean)

    results = pd.concat(output_groups)
    results = results.rename(columns={
        'prevalence': 'prevalence %',
        'mortality': 'mortality per 100k',
    })
    return results


# ============================================================
# printing tables and correlations
# ============================================================

def print_best_worst(results_df, disease, year, include_hospitalization=True):
    """Print the 5 best (lowest z score) and 5 worst (highest z score) states."""
    d = results_df.loc[results_df['Topic'] == disease]

    cols = ['LocationAbbr', 'YearStart', 'prevalence %', 'mortality per 100k',
            'prediction', 'residual', 'residual_z_score']
    if include_hospitalization:
        cols.append('hospitalization')

    agg = d[cols].sort_values('residual_z_score')
    best = agg.head(5)
    worst = agg.tail(5).iloc[::-1]

    print(f"\n{disease} {year} BEST 5 (unexpectedly low mortality):")
    print(best.to_string(index=False))
    print(f"\n{disease} {year} WORST 5 (unexpectedly high mortality):")
    print(worst.to_string(index=False))

    return best, worst


def verify_ok_outlier(df, year):
    """Sanity check: does OK's high mortality fall within CDC's own reported CI?"""
    ok = df.loc[
        (df['LocationAbbr'] == 'OK')
        & (df['Topic'] == 'Cardiovascular Disease')
        & (df['YearStart'] == year)
    ]
    print(f"\nOklahoma CVD {year} mortality with CDC's reported CI:")
    print(ok[['LocationAbbr', 'mortality', 'mortality_lo', 'mortality_hi']].to_string(index=False))


def report_correlation(results_df, disease, year):
    """Print the correlation between hospitalization and residual."""
    d = results_df.loc[results_df['Topic'] == disease]
    corr = d[['hospitalization', 'residual']].corr().iloc[0, 1]
    print(f"{disease} {year} correlation (hospitalization vs residual): r = {corr:.3f}")
    return corr


# ============================================================
# figures
# ============================================================

def save_fig(fname):
    """Save the current figure and show it."""
    path = os.path.join(FIG_DIR, fname)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"Saved: {path}")
    plt.show()
    plt.close()


def fig_00_all_years_scatter(panel_df):
    """
    Slide 7: 4 subplot grid, all years pooled 2019 to 2023, no regression line.
    The visual hook. Dense scatter to show the full data before we zoom in on 2021.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    for ax, (disease, color) in zip(axes.flat, DISEASE_COLORS):
        d = panel_df[panel_df['Topic'] == disease]
        ax.scatter(d['prevalence'], d['mortality'], color=color, alpha=0.6)
        ax.set_xlabel('Prevalence (%)')
        ax.set_ylabel('Mortality (per 100k)')
        title = 'COPD' if disease == 'Chronic Obstructive Pulmonary Disease' else disease
        ax.set_title(title)

    fig.suptitle('Prevalence vs Mortality by Disease, all years pooled (2019 to 2023)',
                 fontsize=14, y=1.02)
    plt.tight_layout()
    save_fig('00_prev_vs_mort_all_years.png')


def fig_01_prev_vs_mort_with_regression(results_2021):
    """Slide 5: 4 subplot grid with fitted regression lines."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    for ax, (disease, color) in zip(axes.flat, DISEASE_COLORS):
        d = results_2021[results_2021['Topic'] == disease].sort_values('prevalence %')
        ax.scatter(d['prevalence %'], d['mortality per 100k'], color=color)
        ax.plot(d['prevalence %'], d['prediction'], color='black', linewidth=1.5)
        ax.set_xlabel('Prevalence (%)')
        ax.set_ylabel('Mortality (per 100k)')
        title = 'COPD' if disease == 'Chronic Obstructive Pulmonary Disease' else disease
        ax.set_title(title)

    fig.suptitle('Prevalence vs Mortality by Disease, 2021 (with fitted regression)',
                 fontsize=14, y=1.02)
    plt.tight_layout()
    save_fig('01_prev_vs_mort_with_regression.png')


def fig_02_cvd_linearity(results_2021):
    """Slide 4: CVD residual plot for linearity check."""
    cvd = results_2021.loc[results_2021['Topic'] == 'Cardiovascular Disease']

    plt.figure(figsize=(8, 5))
    plt.scatter(cvd['prediction'], cvd['residual'], color='tab:orange')
    plt.axhline(0, color='black', linewidth=0.8)
    plt.xlabel('Predicted mortality')
    plt.ylabel('Residual')
    plt.title('CVD residuals vs predictions (linearity check), 2021')
    plt.tight_layout()
    save_fig('02_cvd_linearity_check.png')


def fig_03_copd_linearity(results_2021):
    """Slide 4: COPD residual plot for linearity check."""
    copd = results_2021.loc[results_2021['Topic'] == 'Chronic Obstructive Pulmonary Disease']

    plt.figure(figsize=(8, 5))
    plt.scatter(copd['prediction'], copd['residual'], color='tab:green')
    plt.axhline(0, color='black', linewidth=0.8)
    plt.xlabel('Predicted mortality')
    plt.ylabel('Residual')
    plt.title('COPD residuals vs predictions (linearity check), 2021')
    plt.tight_layout()
    save_fig('03_copd_linearity_check.png')


def fig_04_cvd_hosp_vs_residual_2021(results_2021):
    """Slide 7 left: CVD hospitalization vs residual, 2021."""
    cvd = results_2021.loc[results_2021['Topic'] == 'Cardiovascular Disease']
    corr = cvd[['hospitalization', 'residual']].corr().iloc[0, 1]

    plt.figure(figsize=(8, 5))
    plt.scatter(cvd['hospitalization'], cvd['residual'], color='tab:orange')
    plt.axhline(0, color='black', linewidth=0.5)
    plt.xlabel('Hospitalization per 100k')
    plt.ylabel('Residual (unexpected mortality)')
    plt.title(f'CVD 2021: Hospitalization vs Residual  (r = {corr:.3f})')
    plt.tight_layout()
    save_fig('04_cvd_hosp_vs_residual_2021.png')


def fig_05_copd_hosp_vs_residual_2021(results_2021):
    """Slide 7 right: COPD hospitalization vs residual, 2021."""
    copd = results_2021.loc[results_2021['Topic'] == 'Chronic Obstructive Pulmonary Disease']
    corr = copd[['hospitalization', 'residual']].corr().iloc[0, 1]

    plt.figure(figsize=(8, 5))
    plt.scatter(copd['hospitalization'], copd['residual'], color='tab:green')
    plt.axhline(0, color='black', linewidth=0.5)
    plt.xlabel('Hospitalization per 100k')
    plt.ylabel('Residual (unexpected mortality)')
    plt.title(f'COPD 2021: Hospitalization vs Residual  (r = {corr:.3f})')
    plt.tight_layout()
    save_fig('05_copd_hosp_vs_residual_2021.png')


def fig_06_cvd_year_comparison(results_2019, results_2021):
    """Slide 9: CVD 2019 vs 2021 side by side."""
    cvd_19 = results_2019.loc[results_2019['Topic'] == 'Cardiovascular Disease']
    cvd_21 = results_2021.loc[results_2021['Topic'] == 'Cardiovascular Disease']
    corr_19 = cvd_19[['hospitalization', 'residual']].corr().iloc[0, 1]
    corr_21 = cvd_21[['hospitalization', 'residual']].corr().iloc[0, 1]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].scatter(cvd_19['hospitalization'], cvd_19['residual'], color='tab:orange')
    axes[0].axhline(0, color='black', linewidth=0.5)
    axes[0].set_xlabel('Hospitalization per 100k')
    axes[0].set_ylabel('Residual (unexpected mortality)')
    axes[0].set_title(f'CVD 2019, r = {corr_19:.3f}')

    axes[1].scatter(cvd_21['hospitalization'], cvd_21['residual'], color='tab:orange')
    axes[1].axhline(0, color='black', linewidth=0.5)
    axes[1].set_xlabel('Hospitalization per 100k')
    axes[1].set_ylabel('Residual (unexpected mortality)')
    axes[1].set_title(f'CVD 2021, r = {corr_21:.3f}')

    fig.suptitle('CVD: Hospitalization vs Residual, 2019 vs 2021', fontsize=14, y=1.02)
    plt.tight_layout()
    save_fig('06_cvd_hosp_vs_residual_2019_vs_2021.png')


def fig_07_copd_year_comparison(results_2019, results_2021):
    """Slide 9: COPD 2019 vs 2021 side by side."""
    copd_19 = results_2019.loc[results_2019['Topic'] == 'Chronic Obstructive Pulmonary Disease']
    copd_21 = results_2021.loc[results_2021['Topic'] == 'Chronic Obstructive Pulmonary Disease']
    corr_19 = copd_19[['hospitalization', 'residual']].corr().iloc[0, 1]
    corr_21 = copd_21[['hospitalization', 'residual']].corr().iloc[0, 1]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].scatter(copd_19['hospitalization'], copd_19['residual'], color='tab:green')
    axes[0].axhline(0, color='black', linewidth=0.5)
    axes[0].set_xlabel('Hospitalization per 100k')
    axes[0].set_ylabel('Residual (unexpected mortality)')
    axes[0].set_title(f'COPD 2019, r = {corr_19:.3f}')

    axes[1].scatter(copd_21['hospitalization'], copd_21['residual'], color='tab:green')
    axes[1].axhline(0, color='black', linewidth=0.5)
    axes[1].set_xlabel('Hospitalization per 100k')
    axes[1].set_ylabel('Residual (unexpected mortality)')
    axes[1].set_title(f'COPD 2021, r = {corr_21:.3f}')

    fig.suptitle('COPD: Hospitalization vs Residual, 2019 vs 2021', fontsize=14, y=1.02)
    plt.tight_layout()
    save_fig('07_copd_hosp_vs_residual_2019_vs_2021.png')


# ============================================================
# main
# ============================================================

def main():
    os.makedirs(FIG_DIR, exist_ok=True)

    # load and normalize
    panel_df = load_panel(PANEL_PATH)
    print(f"Panel loaded: {panel_df.shape}\n")

    # data availability
    check_coverage(panel_df)

    # 2021 primary analysis
    results_2021 = fit_regressions_for_year(panel_df, PRIMARY_YEAR)

    # sanity check on OK outlier
    verify_ok_outlier(panel_df, PRIMARY_YEAR)

    # best and worst per disease for 2021
    print("\n" + "=" * 70)
    print(f"{PRIMARY_YEAR} BEST AND WORST BY DISEASE")
    print("=" * 70)
    cvd_best_21, cvd_worst_21 = print_best_worst(results_2021, 'Cardiovascular Disease', PRIMARY_YEAR)
    copd_best_21, copd_worst_21 = print_best_worst(results_2021, 'Chronic Obstructive Pulmonary Disease', PRIMARY_YEAR)
    print_best_worst(results_2021, 'Diabetes', PRIMARY_YEAR, include_hospitalization=False)
    print_best_worst(results_2021, 'Asthma', PRIMARY_YEAR, include_hospitalization=False)

    # the key correlations for 2021
    print("\n" + "=" * 70)
    print(f"{PRIMARY_YEAR} KEY FINDING: HOSPITALIZATION vs RESIDUAL")
    print("=" * 70)
    report_correlation(results_2021, 'Cardiovascular Disease', PRIMARY_YEAR)
    report_correlation(results_2021, 'Chronic Obstructive Pulmonary Disease', PRIMARY_YEAR)

    # 2019 replication check
    print("\n" + "=" * 70)
    print(f"{REPLICATION_YEAR} REPLICATION CHECK")
    print("=" * 70)
    results_2019 = fit_regressions_for_year(panel_df, REPLICATION_YEAR)
    cvd_best_19, cvd_worst_19 = print_best_worst(results_2019, 'Cardiovascular Disease', REPLICATION_YEAR)
    copd_best_19, copd_worst_19 = print_best_worst(results_2019, 'Chronic Obstructive Pulmonary Disease', REPLICATION_YEAR)

    report_correlation(results_2019, 'Cardiovascular Disease', REPLICATION_YEAR)
    report_correlation(results_2019, 'Chronic Obstructive Pulmonary Disease', REPLICATION_YEAR)

    # generate the presentation figures
    print("\n" + "=" * 70)
    print("GENERATING FIGURES")
    print("=" * 70)
    fig_00_all_years_scatter(panel_df)
    fig_01_prev_vs_mort_with_regression(results_2021)
    fig_02_cvd_linearity(results_2021)
    fig_03_copd_linearity(results_2021)
    fig_04_cvd_hosp_vs_residual_2021(results_2021)
    fig_05_copd_hosp_vs_residual_2021(results_2021)
    fig_06_cvd_year_comparison(results_2019, results_2021)
    fig_07_copd_year_comparison(results_2019, results_2021)

    print(f"\nAll figures saved to {FIG_DIR}")
    print("\nDone.")


if __name__ == "__main__":
    main()