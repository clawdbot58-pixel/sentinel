# Designing judgments

Start from the behavior you want — what should the application do, select,
show, or hand off? — and work backward to the judgment it needs.

## Keep code in charge

Known rules, arithmetic, exact lookups, and execution belong in **your code**.
Sentinel supplies semantic understanding: which option is better, whether a
condition holds, where something falls on a scale.

## The decomposition test

For each feature, ask: "What would a careful human judge, given exactly this
state?" Each answerable unit is one question. Examples:

| Feature | Judgment |
|---|---|
| Support ticket triage | choice: department (with a `unsure` option) |
| Discount request | noul: does policy X permit this? |
| Message safety | noul: does this contain abuse? + score: severity 1-4 |
| Search ranking | score per candidate: relevance to the query |
| Game AI move | choice: which move (with per-move facts you computed) |

## Give the judgment everything it needs

The oracle is stateless between calls. If a fact matters, it must be in
`state` (or in the question's structured fields). Compact, structured state
beats prose. For games and grids: an ASCII rendering plus computed per-option
facts (distances, danger flags) massively outperforms raw coordinates —
compute those in code, let Sentinel rank.

## One narrow judgment per question

- Split independently useful dimensions ("is it urgent" ≠ "is it angry").
- But don't shred related structure: "which of these 3 candidates is the
  intended one" is one judgment, not three noul calls — the distribution over
  alternatives is information.
- Include a no-match option when nothing may fit.

## Instructions and criteria

`instructions` = the question, complete and self-contained. `criteria` =
descriptions of each option/level, concrete enough to stand alone. For score
levels, describe situations, not adjectives ("plain language with a next step"
beats "good").

## When the answer is uncertain

`confidence` and `abstain` exist so your code can route: high → act; low →
double-check with more state, ask a second question, or escalate. Thresholds
are yours to tune on your data — evaluate them like any classifier metric.
