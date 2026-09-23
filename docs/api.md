# The API

## Endpoint

```
POST http://127.0.0.1:8915/v1/systemone
Content-Type: application/json
```

Top-level request:

```json
{
  "state": "…anything the decision needs…",
  "model": "sentinel",
  "questions": {
    "my_question_id": { "type": "…", "instructions": "…", "criteria": { … } }
  }
}
```

- `state` — string or structured JSON. Prefer named JSON fields when the
  context has several parts; reference them in `instructions` with backticked
  paths like `ticket.messages[0].text`.
- `model` — accepted for wire compatibility, ignored (any string).
- `questions` — a map you name; answers come back under the same keys.
  Multiple questions are answered in one request (sequentially server-side,
  ~1 call each).

## Response

```json
{
  "model": "sentinel-0.1-qwen38-27b",
  "answers": { "my_question_id": { … } },
  "usage": {"input_tokens": 1846, "output_tokens": 0},
  "latency_ms": 412.7,
  "probs_source": "native_letter_logits",
  "temperature": 1.2
}
```

## The three primitives

### Choice — pick one of a defined set

```json
{"type": "choice",
 "instructions": "Which team should handle this?",
 "criteria": {
   "billing":   "Payments, invoicing, refunds",
   "technical": "Bugs, outages, integrations",
   "sales":     "Pricing, upgrades, new accounts"
 }}
```

Answer:

```json
{"type": "choice",
 "choice": "technical",
 "probabilities": {"billing": 0.08, "technical": 0.86, "sales": 0.06},
 "confidence": 0.78,
 "abstain": false}
```

`probabilities` covers exactly your keys and sums to 1. `choice` is the argmax.
Up to 255 options (one per letter A..). Options are letter-mapped internally in
presentation order; probabilities come back keyed by YOUR labels.

### Noul — probability that something is true

```json
{"type": "noul",
 "instructions": "Does this message threaten to cancel?",
 "criteria": {"true": "Explicit cancellation threat", "false": "No threat"}}
```

Answer: `{"type": "noul", "noul": 0.93, "probabilities": {"no": 0.07, "yes": 0.93}, …}`

`noul` near 0.5 means yes/no are equally likely — not medium intensity.

### Score — degree on an ordered rubric

```json
{"type": "score",
 "instructions": "How readable is this error message?",
 "criteria": [
   "Jargon, no recovery hint",
   "Technical but parseable",
   "Plain language with next step",
   "Plain language, exact recovery step, linked docs"
 ]}
```

Answer: `{"type": "score", "probabilities": {"1": 0.05, "2": 0.15, "3": 0.60, "4": 0.20}, …}`

Levels are 1..N (str keys), your criteria describe what each level MEANS
(concrete situations, standing alone). The expected value
`sum(level × prob)` is your graded score.

## Extra fields (not in TypeSafe)

- `confidence` — top1−top2 probability gap. High = committed; low = torn.
  Use it to route: act when high, escalate to code/LLM/human when low.
- `abstain` — true when the gap is below a safety floor (default 0.02).
- `latency_ms` — measured server-side for this request.

## Errors

HTTP 500 with `{"error": "…"}` on backend failure (e.g. llama.cpp down).
HTTP 401 only if `SENTINEL_API_KEY` was set at server start. Unknown question
type → 500 with the reason. Always check `answers` keys exist before use.
