# Compose and verify

## Independent questions travel together

Questions in one request cannot see each other's answers — batch every
judgment that depends only on the current state (routing + urgency + severity
in one call). Use a second request only when an earlier answer is needed to
build new state, fetch evidence, or determine the next options.

## Reading probabilities honestly

- Choice confidence = distribution concentration, not workflow correctness.
  Several acceptable options can legitimately spread probability; low
  confidence on a harmless preference is fine.
- A noul near 0.5 means yes/no are balanced — not "medium true".
- Score probabilities give you the whole shape: use the expected value for
  ranking, the spread for flagging disagreement.
- Ignore uncertainty on branches you won't act on.

## Keep policy in code

Weighted decisions belong in your code: ask for the raw judgments ("safety
violation? severity?"), apply weights, thresholds and any-rule logic in
Python. Changing a weight then costs nothing and never re-runs inference.
Typed output guarantees the interface — not truth. Validate on your domain.

## Debugging failures

Inspect in this order:
1. The exact `state` and question you sent (echo them; don't reconstruct).
2. Whether the needed fact was even present in the state.
3. The full probability distribution (was it torn, or confidently wrong?).
4. Your composition (did you read the right answer key, the right level?).

Classify: missing evidence (fix the state), model error (change the question
or add facts), code error, service error (health check). The `raw` top-200
logprobs are available server-side if you need to audit a distribution.

## Measuring

Every call returns `latency_ms`; the backend prefix-caches when your state
shares a stable prefix (steady-state game loops drop from ~0.4-0.6s to
~0.2s/tick). For throughput, note the current server runs one slot — batch
requests queue. Budget accordingly in realtime loops.
