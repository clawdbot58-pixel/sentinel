---
name: sentinel
license: MIT
description: >
  Make calibrated decisions with Sentinel: an open, self-hosted System One
  decision API, wire-compatible with TypeSafe's Jev /v1/systemone. Runs locally
  at http://127.0.0.1:8915 (one prefill forward pass per decision, no text
  generation, real probabilities, ~0.4-1.5s per call). Use when an application
  or agent needs programmable common sense: routing, ranking, selection,
  verification, game logic, interactive experiences. Adapted from the
  typesafe-ai/skills skill (MIT); see the difference section at the end.
---

# Build with Sentinel

Sentinel is a locally-hosted System One decision server. It answers typed
questions (choice / noul / score) about a `state` you provide, returning
**calibrated probabilities instead of generated text**. One call = one forward
pass; it never writes prose, so the answer is schema-valid by construction.

## Endpoint

```
POST http://127.0.0.1:8915/v1/systemone
Content-Type: application/json
```

- Backend: Qwen3.8-27B (JevBench 87.9% — above Jev's 86.6 on the public panel).
- Latency: p50 ~0.4s, p95 ~3s per decision (single prefill).
- No API key required locally. `model` field is ignored (any string).
- Check health first: `curl -s http://127.0.0.1:8915/health`

## The three primitives

| Need | Type | Returns |
| --- | --- | --- |
| One of a defined set | `choice` | `choice` (top option) + full `probabilities` map |
| Whether a condition holds | `noul` | `noul` = probability of yes (0..1) |
| Degree on an ordered rubric | `score` | `probabilities` across levels 1..N |

`state` carries everything the decision needs (text or structured JSON — prefer
named JSON fields). `instructions` is the question. `criteria` describes each
option / level. Extra data referenced in instructions uses backticked names.

## Quick start (curl)

```bash
curl -s http://127.0.0.1:8915/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{
    "state": "Help! My payouts have been failing for 3 days.",
    "model": "sentinel",
    "questions": {
      "is_urgent": {
        "type": "noul",
        "instructions": "Does this convey urgency?",
        "criteria": {"true": "Explicitly time-sensitive", "false": "No urgency"}
      }
    }
  }'
```

Response:

```json
{
  "model": "sentinel-0.1-qwen38-27b",
  "answers": {
    "is_urgent": {
      "type": "noul",
      "noul": 0.94,
      "probabilities": {"no": 0.06, "yes": 0.94},
      "confidence": 0.88,
      "abstain": false
    }
  },
  "usage": {"input_tokens": 131, "output_tokens": 0}
}
```

## Python example (choice)

```python
import json, urllib.request

def sentinel(state, questions):
    body = {"state": state, "model": "sentinel", "questions": questions}
    req = urllib.request.Request(
        "http://127.0.0.1:8915/v1/systemone",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["answers"]

ans = sentinel(
    "Player at (4,4). Food at (2,2). Walls around the edge.",
    {"move": {
        "type": "choice",
        "instructions": "Pick the best move: survive first, then reach food.",
        "criteria": {
            "N": "Move up (y-1): food distance decreases, 3 exits",
            "W": "Move left (x-1): heads toward wall, 2 exits",
        }}})
print(ans["move"]["probabilities"], ans["move"]["confidence"])
```

## Design the decisions

- One narrow judgment per question. Split independently useful dimensions.
- Put known rules, arithmetic, and execution in YOUR code; Sentinel supplies the
  semantic judgment (which option is better, is this safe, how good is X).
- Include all needed context in `state` — the oracle has no memory between calls.
- Add a no-match option when nothing may fit.
- `confidence` (top1-top2 gap): act freely when high, double-check when low.
- `abstain`: true when the oracle is too torn to commit — route those to code
  or a stronger model.

## Game/agent loop pattern (measured)

Per tick: render your world state compactly (ASCII grids work well), give
per-option facts (computed by your code: distances, dangers), ask ONE choice
question, take the argmax or sample from the distribution. Keep the question
text stable across ticks so the backend prefix-caches (~0.2s/tick steady state).
Expect the oracle to be strong at "which option is better given these facts"
and weak at long chains of reasoning — compute the facts in code.

## Verification

Smoke test after any outage:

```bash
curl -s http://127.0.0.1:8915/v1/systemone -H 'Content-Type: application/json' \
  -d '{"state":"2+2","model":"sentinel","questions":{"q":{"type":"noul","instructions":"Is 2+2 equal to 4?"}}}'
# expect answers.q.noul > 0.9
```

## Differences from the TypeSafe skill

Same wire format, three differences: (1) endpoint is local and keyless;
(2) responses add `confidence` + `abstain` fields; (3) temperatures are fitted
(JevBench-calibrated) — do not add sampling. If you need the hosted version,
read the typesafe-ai skill instead and swap the endpoint + key.
