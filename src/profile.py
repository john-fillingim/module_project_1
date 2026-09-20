"""Raw-data EDA: coverage by instrument x condition x year, missingness,
and the 2020-21 BRFSS discontinuity check. Discovery figures, not story
figures (those are eda.py, Person B).

Every number drawn is also written to a .txt next to the PNG.

Owner: Person A
Input:  data/clean/normalized_long.csv
Output: figures/eda/coverage.png + .txt
        figures/eda/discontinuity_2020.png + .txt
        figures/eda/suppression_by_group.png + .txt
        figures/eda/ci_width_by_group.png + .txt
"""

import argparse
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

log = logging.getLogger(__name__)

# Reference palette (dataviz skill). Categorical slots in fixed order; blue
# sequential ramp for magnitude.
SERIES = {"brfss": "#2a78d6", "nvss": "#eb6834", "cms": "#1baf7a"}
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
CONDITIONS = ["copd", "cardiovascular", "diabetes", "asthma"]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlesize": 10, "axes.titlelocation": "left",
})


def _write(path: Path, title: str, df: pd.DataFrame) -> None:
    path.write_text(f"# {title}\n\n{df.to_string()}\n", encoding="utf-8")


# --------------------------------------------------------------------------
def fig_coverage(long: pd.DataFrame, out: Path) -> None:
    """Which instrument reports which condition in which year (Overall rows)."""
    ov = long[long["strat_category"] == "Overall"]
    tab = ov.groupby(["condition", "instrument", "measure", "year"])["value"].agg(
        n_states="count", n_null=lambda s: s.isna().sum()).reset_index()
    _write(out / "coverage.txt", "States reporting a non-null Overall age-adjusted value, by instrument and year", tab)

    rows = [(c, i, m) for c in CONDITIONS for (i, m) in
            [("brfss", "prevalence"), ("brfss", "treatment"), ("cms", "hospitalization"), ("nvss", "mortality")]]
    years = sorted(ov["year"].unique())
    grid = np.full((len(rows), len(years)), np.nan)
    for r, (c, i, m) in enumerate(rows):
        for k, y in enumerate(years):
            sub = tab[(tab.condition == c) & (tab.instrument == i) & (tab.measure == m) & (tab.year == y)]
            if len(sub):
                grid[r, k] = sub["n_states"].iloc[0]

    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    cmap = matplotlib.colors.ListedColormap(SEQ)
    im = ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, vmin=0, vmax=55, aspect="auto")
    ax.set_xticks(range(len(years)), years)
    ax.set_yticks(range(len(rows)), [f"{c} · {i} {m}" for c, i, m in rows])
    ax.grid(False)
    for r in range(len(rows)):
        for k in range(len(years)):
            v = grid[r, k]
            ax.text(k, r, "—" if np.isnan(v) else f"{int(v)}", ha="center", va="center",
                    color="white" if (not np.isnan(v) and v > 30) else INK, fontsize=8)
    for y in [3.5, 7.5, 11.5]:
        ax.axhline(y, color="white", lw=2)
    ax.set_title("Coverage: states reporting a value (Overall, age-adjusted)")
    ax.set_xlabel("Year")
    fig.text(0.01, 0.01, "— = instrument does not report this condition-year. Max is 54 (50 states + DC + GU/PR/VI; US excluded). "
             "Hypertension (cardiovascular · brfss) is an odd-year module.", color=INK2, fontsize=7, wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(out / "coverage.png")
    plt.close(fig)


# --------------------------------------------------------------------------
def fig_discontinuity(long: pd.DataFrame, out: Path) -> None:
    """Did 2020 BRFSS collection break the every-year prevalence series?

    Test per question: for each state, the 2020 value vs the 2019/2021 mean.
    A collection artifact shows up as a systematic shift across states, not
    just noise. Uses only questions asked every year (COPD01, DIA01, AST02,
    COPD02); CVD01 is odd-year and cannot be tested.
    """
    b = long[(long["strat_category"] == "Overall") & (long["instrument"] == "brfss")]
    qs = [q for q in ["COPD01", "DIA01", "AST02", "COPD02"] if q in set(b["question_id"])]
    rows = []
    for q in qs:
        w = b[b["question_id"] == q].pivot(index="state", columns="year", values="value")
        if not {2019, 2020, 2021}.issubset(w.columns):
            continue
        w = w.dropna(subset=[2019, 2020, 2021])
        neighbour = (w[2019] + w[2021]) / 2
        diff = w[2020] - neighbour
        # Reference: how much does a normal year-to-year step vary? Use 2021->2022.
        ref = (w[2022] - w[2021]).dropna() if 2022 in w.columns else pd.Series(dtype=float)
        rows.append(dict(question_id=q, n_states=len(w), mean_2020_minus_neighbours=diff.mean(),
                         median=diff.median(), sd=diff.std(), share_states_lower_in_2020=(diff < 0).mean(),
                         ref_mean_2022_minus_2021=ref.mean(), ref_sd=ref.std(),
                         t_stat=diff.mean() / (diff.std() / np.sqrt(len(diff)))))
    tab = pd.DataFrame(rows)
    _write(out / "discontinuity_2020.txt",
           "2020 minus mean(2019, 2021), per state, BRFSS Overall age-adjusted prevalence. "
           "t_stat = mean/SE across states; |t|>2 suggests a systematic shift.", tab.round(3))

    fig, axes = plt.subplots(1, len(qs), figsize=(2.4 * len(qs) + 1, 3.6), sharey=False)
    axes = np.atleast_1d(axes)
    for ax, q in zip(axes, qs):
        w = b[b["question_id"] == q].pivot(index="state", columns="year", values="value").dropna(subset=[2019, 2020, 2021])
        diff = w[2020] - (w[2019] + w[2021]) / 2
        ax.hist(diff, bins=15, color=SERIES["brfss"], edgecolor="white", linewidth=0.8)
        ax.axvline(0, color=INK2, lw=1)
        ax.axvline(diff.mean(), color=SERIES["nvss"], lw=2)
        ax.set_title(q)
        ax.set_xlabel("2020 − mean(2019, 2021), pts")
        ax.text(0.98, 0.95, f"mean {diff.mean():+.2f}\nn={len(diff)}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color=INK2)
    axes[0].set_ylabel("States")
    fig.suptitle("2020 discontinuity check — orange line = mean shift across states", x=0.01, ha="left",
                 fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(out / "discontinuity_2020.png")
    plt.close(fig)


# --------------------------------------------------------------------------
def fig_suppression(long: pd.DataFrame, out: Path) -> None:
    """Share of race/ethnicity cells suppressed, by group and condition."""
    re = long[long["strat_category"] == "Race/Ethnicity"]
    re = re[~re["no_data"]]
    tab = re.groupby(["strat_group", "condition"])["suppressed"].mean().unstack("condition")[CONDITIONS]
    tab["all"] = re.groupby("strat_group")["suppressed"].mean()
    tab = tab.sort_values("all", ascending=False)
    _write(out / "suppression_by_group.txt",
           "Share of race/ethnicity-stratified cells suppressed (excluding module-not-run cells), all instruments", tab.round(3))

    fig, ax = plt.subplots(figsize=(7, 3.8))
    cmap = matplotlib.colors.ListedColormap(SEQ)
    im = ax.imshow(np.ma.masked_invalid(tab[CONDITIONS].values), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CONDITIONS)), CONDITIONS)
    labels = [g.replace(", non-Hispanic", "").replace("Native Hawaiian or Other Pacific Islander", "NH/Pacific Islander")
              .replace("American Indian or Alaska Native", "AI/AN") for g in tab.index]
    ax.set_yticks(range(len(tab)), labels)
    ax.grid(False)
    for r in range(len(tab)):
        for k in range(len(CONDITIONS)):
            v = tab[CONDITIONS].values[r, k]
            ax.text(k, r, "—" if np.isnan(v) else f"{v:.0%}", ha="center", va="center",
                    color="white" if (not np.isnan(v) and v > 0.5) else INK, fontsize=8)
    ax.set_title("Share of race/ethnicity cells suppressed, by group and condition")
    fig.text(0.01, 0.01, "All instruments, all years, excluding cells where the state did not run the module. "
             "'Asian or Pacific Islander' is a legacy NVSS-only category.", color=INK2, fontsize=7)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "suppression_by_group.png")
    plt.close(fig)


# --------------------------------------------------------------------------
def fig_ci_width(long: pd.DataFrame, out: Path) -> None:
    """How precisely is each group's prevalence known? Relative CI width."""
    b = long[(long["instrument"] == "brfss") & (long["measure"] == "prevalence") & long["value"].notna()].copy()
    b["rel_width"] = (b["ci_hi"] - b["ci_lo"]) / b["value"]
    # Rows with a value but no CI (footnote ##, "0.0% because no cases") and
    # zero-valued estimates have no defined relative width; drop them here.
    b = b[np.isfinite(b["rel_width"])]
    b["group"] = np.where(b["strat_category"] == "Overall", "Overall",
                          np.where(b["strat_category"] == "Sex", "Sex: " + b["strat_group"],
                                   b["strat_group"].str.replace(", non-Hispanic", "", regex=False)))
    order = b.groupby("group")["rel_width"].median().sort_values()
    tab = b.groupby("group")["rel_width"].describe()[["count", "25%", "50%", "75%"]].loc[order.index]
    _write(out / "ci_width_by_group.txt",
           "Relative 95% CI width (hi - lo) / estimate, BRFSS age-adjusted prevalence, all conditions, reported cells only", tab.round(3))

    fig, ax = plt.subplots(figsize=(7, 4))
    data = [b.loc[b["group"] == g, "rel_width"].values for g in order.index]
    bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=1.5), boxprops=dict(facecolor=SERIES["brfss"], edgecolor="white", lw=0.8),
                    whiskerprops=dict(color=INK2, lw=1), capprops=dict(color=INK2, lw=1))
    ax.set_yticks(range(1, len(order) + 1), [g.replace("Native Hawaiian or Other Pacific Islander", "NH/Pacific Islander")
                                             .replace("American Indian or Alaska Native", "AI/AN") for g in order.index])
    ax.set_xlabel("95% CI width as a share of the estimate")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("Precision inequality: 95% CI width relative to each group's estimate")
    fig.tight_layout()
    fig.savefig(out / "ci_width_by_group.png")
    plt.close(fig)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--long", default="data/clean/normalized_long.csv")
    parser.add_argument("--out", default="figures/eda")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    long = pd.read_csv(args.long)
    log.info("profile: read %d rows", len(long))
    for fn in (fig_coverage, fig_discontinuity, fig_suppression, fig_ci_width):
        fn(long, out)
        log.info("profile: wrote %s", fn.__name__.replace("fig_", ""))


if __name__ == "__main__":
    main()
