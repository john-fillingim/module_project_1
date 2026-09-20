"""Filter DataValueType to age-adjusted values; map Question -> condition.

THE question->condition crosswalk lives here and only here. The rationale for
every mapping is inline. Every filter logs its row count. Unrecognised
DataValueType / QuestionID values are logged and counted, never silently
dropped (design rule 6). Recommended crosswalk source: docs/data_profile.md.

Owner: Person A
Input:  raw DataFrame from load.py
Output: long DataFrame, age-adjusted only, Overall + stratified rows, with
        condition / instrument / measure / suppressed columns; attrition log
"""

import logging

import pandas as pd

log = logging.getLogger(__name__)

TOPICS = [
    "Chronic Obstructive Pulmonary Disease",
    "Cardiovascular Disease",
    "Diabetes",
    "Asthma",
]

SOURCES = {
    "BRFSS": "brfss",
    "NVSS": "nvss",
    "CMS Part A Claims Data": "cms",
}

# Exact-match allowlist. Do NOT use startswith("Age-adjusted"): the file also
# contains "Age-adjusted Mean" and "Adjusted rate by age, sex, race and
# ethnicity", which are different measures (design rule 1).
VALUE_TYPES = ["Age-adjusted Prevalence", "Age-adjusted Rate"]

# National aggregate row; must never enter a cross-state regression.
EXCLUDE_LOCATIONS = ["US"]

# ---------------------------------------------------------------------------
# The crosswalk. One entry per QuestionID we use. `orientation` says how the
# value relates to "good": "direct" = higher is more of the thing measured;
# "inverse_treatment" = the question measures a *failure* of treatment, so
# build_panel stores 100 - value as brfss_treatment_rate.
# ---------------------------------------------------------------------------
CROSSWALK = {
    # --- COPD: flagship. Same condition measured by all three instruments. ---
    "COPD01": dict(condition="copd", instrument="brfss", measure="prevalence", orientation="direct",
                   why="Self-reported physician-diagnosed COPD among adults. The survey instrument."),
    "COPD02": dict(condition="copd", instrument="brfss", measure="treatment", orientation="inverse_treatment",
                   why="Current smoking among adults WITH COPD. The only BRFSS COPD treatment-type item. "
                       "High = poorly managed, so it is inverted to a treatment rate in build_panel."),
    "COPD04": dict(condition="copd", instrument="cms", measure="hospitalization", orientation="direct",
                   why="COPD hospitalization as PRINCIPAL diagnosis, Medicare 65+. Chosen over COPD03 "
                       "(any diagnosis) so it matches CVD06, which is also principal-diagnosis."),
    "COPD05": dict(condition="copd", instrument="nvss", measure="mortality", orientation="direct",
                   why="COPD mortality, adults 45+, UNDERLYING cause. Underlying cause is the stricter "
                       "attribution; COPD06 (underlying-or-contributing) is a sensitivity check only."),
    # --- Cardiovascular: weaker pairing. No BRFSS heart-disease prevalence question
    #     exists, so prevalence is a RISK FACTOR (hypertension) and mortality is the
    #     OUTCOME (heart disease). Documented in the writeup as a limitation. ---
    "CVD01": dict(condition="cardiovascular", instrument="brfss", measure="prevalence", orientation="direct",
                  why="High blood pressure among adults. Odd years only (2019/2021/2023) - BRFSS "
                      "rotating-core module. Closest available self-report proxy for CVD burden."),
    "CVD02": dict(condition="cardiovascular", instrument="brfss", measure="treatment", orientation="direct",
                  why="Taking medicine for high BP among adults with high BP. A direct treatment rate."),
    "CVD06": dict(condition="cardiovascular", instrument="cms", measure="hospitalization", orientation="direct",
                  why="Heart failure hospitalization, principal diagnosis, Medicare 65+."),
    "CVD09": dict(condition="cardiovascular", instrument="nvss", measure="mortality", orientation="direct",
                  why="Diseases of the heart mortality, underlying cause. Broadest heart-disease "
                      "mortality item; CVD08 (coronary) and CVD07 (stroke) are sensitivity checks."),
    # --- Diabetes: same condition, two instruments (no CMS item). ---
    "DIA01": dict(condition="diabetes", instrument="brfss", measure="prevalence", orientation="direct",
                  why="Diagnosed diabetes among adults."),
    "DIA03": dict(condition="diabetes", instrument="nvss", measure="mortality", orientation="direct",
                  why="Diabetes mortality, underlying OR contributing cause. Only all-cause diabetes "
                      "mortality item; DIA04 (ketoacidosis) is too sparse (20/208 suppressed)."),
    # --- Asthma: same condition, two instruments, but mortality is heavily suppressed
    #     (50/208 state-years). Kept so the suppression itself is reported. ---
    "AST02": dict(condition="asthma", instrument="brfss", measure="prevalence", orientation="direct",
                  why="Current asthma among adults."),
    "AST01": dict(condition="asthma", instrument="nvss", measure="mortality", orientation="direct",
                  why="Asthma mortality, underlying cause. Rare event; expect suppression."),
}

# Questions in our topics/sources that we deliberately do not use. Listed so
# the attrition log can distinguish "known and excluded" from "never seen".
KNOWN_UNUSED = {
    "COPD03": "any-diagnosis hospitalization; superseded by COPD04 (principal)",
    "COPD06": "underlying-or-contributing mortality; sensitivity only",
    "CVD03": "high cholesterol prevalence; not paired with a mortality outcome",
    "CVD04": "cholesterol medication; treatment item for CVD03, unused",
    "CVD07": "stroke mortality; sensitivity only",
    "CVD08": "coronary heart disease mortality; sensitivity only",
    "DIA04": "diabetic ketoacidosis mortality; too sparse",
}

# Footnotes that mean "a value exists but was withheld" vs "the state did not
# collect this". Both are NaN in DataValueAlt; they are not the same finding.
SUPPRESSED_SYMBOLS = {"****", "~"}          # denominator/RSE rule, too few cases
NO_DATA_SYMBOLS = {"*", "#", "~~", "~~~~"}  # module not run, cannot be calculated, registry opt-out
CAUTION_SYMBOLS = {"###", "&"}              # value present, wide CI or n<60
ZERO_SYMBOLS = {"##"}                       # value is 0.0 because no cases; CI absent


class AttritionLog:
    """Collects (step, rows) pairs and free-text notes; written to a text file."""

    def __init__(self):
        self.steps: list[tuple[str, int]] = []
        self.notes: list[str] = []

    def step(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        self.steps.append((name, len(df)))
        log.info("normalize: %-45s rows=%d", name, len(df))
        return df

    def note(self, text: str) -> None:
        self.notes.append(text)
        log.info("normalize: %s", text)

    def render(self) -> str:
        lines = ["# Attrition log (normalize.py)", ""]
        prev = None
        for name, n in self.steps:
            delta = "" if prev is None else f"  ({n - prev:+d})"
            lines.append(f"{name:<45} {n:>9,}{delta}")
            prev = n
        lines += ["", "# Notes", ""] + self.notes
        return "\n".join(lines) + "\n"


def normalize(df: pd.DataFrame) -> tuple[pd.DataFrame, AttritionLog]:
    a = AttritionLog()
    a.step("raw", df)

    df = a.step("Topic in 4 conditions", df[df["Topic"].isin(TOPICS)])
    df = a.step("DataSource in BRFSS/NVSS/CMS", df[df["DataSource"].isin(SOURCES)])
    multi = int((df["YearStart"] != df["YearEnd"]).sum())
    if multi:
        raise ValueError(f"normalize: {multi} in-scope rows have multi-year windows (YearStart != YearEnd)")
    a.note("all in-scope rows are single-year (YearStart == YearEnd)")

    # Log every DataValueType seen in-scope, used or not (design rule 6).
    vt_counts = df["DataValueType"].value_counts()
    for vt, n in vt_counts.items():
        tag = "KEPT" if vt in VALUE_TYPES else "excluded"
        a.note(f"DataValueType {tag:<8} {vt!r}: {n:,} rows")
    unknown_vt = set(vt_counts.index) - set(VALUE_TYPES) - {
        "Crude Prevalence", "Crude Rate", "Number"}
    if unknown_vt:
        a.note(f"WARNING unexpected DataValueType values in scope: {sorted(unknown_vt)}")
    before = df["StratificationCategory1"].value_counts()
    df = a.step("DataValueType age-adjusted only", df[df["DataValueType"].isin(VALUE_TYPES)])
    after = df["StratificationCategory1"].value_counts()
    for cat, n in before.items():
        a.note(f"StratificationCategory1 {cat!r}: {n:,} rows before age-adjusted filter, "
               f"{int(after.get(cat, 0)):,} after"
               + ("  (age bands cannot be age-adjusted; dropped entirely)" if after.get(cat, 0) == 0 else ""))

    df = a.step("LocationAbbr != US", df[~df["LocationAbbr"].isin(EXCLUDE_LOCATIONS)])

    # Crosswalk. Log every QuestionID seen, mapped or not.
    q_counts = df.groupby(["QuestionID", "Question"]).size()
    unexpected = []
    for (qid, q), n in q_counts.items():
        if qid in CROSSWALK:
            a.note(f"QuestionID mapped   {qid}: {n:,} rows -> {CROSSWALK[qid]['condition']}/"
                   f"{CROSSWALK[qid]['instrument']}/{CROSSWALK[qid]['measure']}")
        elif qid in KNOWN_UNUSED:
            a.note(f"QuestionID unused   {qid}: {n:,} rows ({KNOWN_UNUSED[qid]}) - {q}")
        else:
            unexpected.append(qid)
            a.note(f"QuestionID UNKNOWN  {qid}: {n:,} rows - {q}")
    if unexpected:
        raise ValueError(f"normalize: QuestionIDs in scope but not in CROSSWALK or KNOWN_UNUSED: {unexpected}")
    df = a.step("QuestionID in crosswalk", df[df["QuestionID"].isin(CROSSWALK)]).copy()

    cw = pd.DataFrame.from_dict(CROSSWALK, orient="index")[["condition", "instrument", "measure", "orientation"]]
    df = df.join(cw, on="QuestionID")
    assert df["instrument"].eq(df["DataSource"].map(SOURCES)).all(), "crosswalk instrument != DataSource"

    # Suppression semantics.
    sym = df["DataValueFootnoteSymbol"]
    df["suppressed"] = sym.isin(SUPPRESSED_SYMBOLS)
    df["no_data"] = sym.isin(NO_DATA_SYMBOLS)
    df["caution"] = sym.isin(CAUTION_SYMBOLS)
    unexplained_null = df["DataValueAlt"].isna() & ~(df["suppressed"] | df["no_data"])
    if unexplained_null.any():
        raise ValueError(f"normalize: {int(unexplained_null.sum())} null values with no suppression/no-data footnote: "
                         f"{sym[unexplained_null].unique().tolist()}")
    unknown_sym = set(sym.dropna().unique()) - SUPPRESSED_SYMBOLS - NO_DATA_SYMBOLS - CAUTION_SYMBOLS - ZERO_SYMBOLS
    if unknown_sym:
        a.note(f"WARNING unrecognised footnote symbols: {sorted(unknown_sym)}")
    a.note(f"null values: suppressed={int(df['suppressed'].sum()):,} no_data={int(df['no_data'].sum()):,} "
           f"(all {int(df['DataValueAlt'].isna().sum()):,} nulls accounted for)")
    a.note(f"values flagged interpret-with-caution: {int(df['caution'].sum()):,}")

    key = ["LocationAbbr", "YearStart", "QuestionID", "StratificationCategory1", "Stratification1"]
    dups = df.duplicated(key).sum()
    if dups:
        raise ValueError(f"normalize: {dups} duplicate rows on {key}")
    a.note(f"key {key} is unique")

    out = pd.DataFrame({
        "state": df["LocationAbbr"],
        "year": df["YearStart"],
        "condition": df["condition"],
        "instrument": df["instrument"],
        "measure": df["measure"],
        "question_id": df["QuestionID"],
        "orientation": df["orientation"],
        "strat_category": df["StratificationCategory1"],
        "strat_group": df["Stratification1"],
        "value": df["DataValueAlt"],
        "ci_lo": df["LowConfidenceLimit"],
        "ci_hi": df["HighConfidenceLimit"],
        "unit": df["DataValueUnit"],
        "suppressed": df["suppressed"],
        "no_data": df["no_data"],
        "caution": df["caution"],
        "footnote_symbol": df["DataValueFootnoteSymbol"],
        "footnote": df["DataValueFootnote"],
    }).sort_values(["condition", "instrument", "measure", "strat_category", "strat_group", "state", "year"])
    out = out.reset_index(drop=True)
    a.step("normalized_long (output)", out)
    return out, a
