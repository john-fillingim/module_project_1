"""Filter DataValueType to age-adjusted values; map Question -> condition.
THE question->condition crosswalk lives here and only here. Write the
rationale for every mapping inline. Log row count after every filter.
Unrecognised DataValueType / Question values are logged and counted,
never silently dropped (design rule 6).
Recommended QuestionID crosswalk: docs/data_profile.md. Exclude LocationAbbr == 'US'.

Owner: Person A
Input:  raw DataFrame from load.py
Output: long DataFrame, age-adjusted only, with `condition` column
"""
