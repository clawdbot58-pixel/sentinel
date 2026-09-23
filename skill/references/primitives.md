# Primitives reference

All three primitives share `type` and `instructions`; each adds its own
`criteria`. `instructions` may be a string, an object, or an array — use an
object to hold the question in one field and data it references in others,
pointing at fields by backticked name.

## Choice — pick one of a defined set

Returns the chosen option and the full probability distribution over all
options. Use when exactly one option should be selected and the relative
probabilities of the alternatives are informative.

```json
{
  "type": "choice",
  "instructions": "Which team should handle this?",
  "criteria": {
    "billing":   "Payments, invoicing, refunds",
    "technical": "Bugs, outages, integrations",
    "sales":     "Pricing, upgrades, new accounts"
  }
}
```

Answer:

```json
{"type": "choice", "choice": "technical",
 "probabilities": {"billing": 0.08, "technical": 0.86, "sales": 0.06},
 "confidence": 0.78, "abstain": false}
```

- Up to 255 options (one per letter). Option keys are your own labels.
- `choice` is the argmax; `probabilities` always covers all keys.
- Distribution spread across alternatives is information, not noise.

## Noul — probability that something is true

Returns the probability that the answer is yes. Use for independent
yes/no judgments; when several labels may apply, use one Noul per label.

```json
{
  "type": "noul",
  "instructions": "Does this convey urgency?",
  "criteria": {
    "true":  "Explicitly time-sensitive",
    "false": "No urgency expressed"
  }
}
```

Answer:

```json
{"type": "noul", "noul": 0.94,
 "probabilities": {"no": 0.06, "yes": 0.94},
 "confidence": 0.88, "abstain": false}
```

- `noul` near 0.5 = yes/no equally likely, not medium intensity.
- 0.5 exactly can mean the state was insufficient — check your facts.

## Score — degree on an ordered rubric

Returns a probability-weighted position across ordered levels. Use for
comparable per-item ratings; the expected value `sum(level × probability)`
is the graded score.

```json
{
  "type": "score",
  "instructions": "How readable is this error message?",
  "criteria": [
    "Jargon, no recovery hint",
    "Technical but parseable",
    "Plain language with next step",
    "Plain language, exact recovery step, linked docs"
  ]
}
```

Answer:

```json
{"type": "score",
 "probabilities": {"1": 0.05, "2": 0.15, "3": 0.60, "4": 0.20},
 "confidence": 0.45, "abstain": false}
```

- Levels must describe concrete situations that stand alone; never bare
  adjectives ("good").
- Comparable items should share the rubric — that is what makes scores
  rankable.

## State and instructions

`state` may be a string, object, or array. Structured instructions may hold
the question in one field and data it references in others:

```json
"instructions": {
  "potential_duplicate": {"name": "John Smith", "last_employer": "Google"},
  "question": "Is the resume for the same person as `potential_duplicate`?"
}
```

The oracle is stateless between calls: every fact the judgment needs must be
in `state` (or in the question). Computed, neutral facts (distances, counts,
danger flags) written into the criteria dramatically improve ranking quality
in dense domains — compute them in code.
