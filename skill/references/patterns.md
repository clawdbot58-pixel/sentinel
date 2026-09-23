# Patterns

Starting points for combining primitives. Each is a real architecture; several
have been validated end-to-end on this deployment.

## Route and fill known arguments

A request selects a handler and its typed parameters. Ask useful
branch-specific questions up front and consume only the relevant answers.

```
state -> choice(handler) -> per-branch questions -> execute
```

Add an `unsure` option and route low-confidence traffic to review.

## Select instead of generate

Find candidate values in code (search, regex, retrieval), ask Sentinel which
candidate is the intended one, then copy or normalize it — never have the model
re-emit the value.

```
candidates from code -> choice(among candidates) -> code copies the winner
```

This is where schema-validity pays: the oracle cannot invent a value you did
not offer.

## Gate and verify

Check specific claims against their evidence; escalate uncertain cases.

```
state -> noul(claim) -> high: act | low: escalate to code / LLM / human
```

Cascades work too: cheap gate first (noul), expensive verification only on
passes.

## Rerank and hierarchical classification

Retrieve candidates in code, ask a choice judgment to select relevant ones, or
classify top-level then sub-classify per class with focused questions.

## Composite scoring

Score dimensions independently (readability, urgency, risk), then let code
combine with weights — changing a weight re-scores without re-running
inference, because raw distributions are reusable.

## Adaptive game / agent loops

An LLM (or any controller) writes the instruction and the option set; the
oracle decides each step with calibrated probabilities; code executes and
feeds telemetry back. Validated pattern: a Snake-playing agent where the code
computes per-move facts (death flags, path distances, free space) and the
oracle ranks the moves each tick — the LLM iterates the instruction, the code
compiles the tactics, the oracle decides. Keep the per-tick question stable so
prefix caching holds (~0.2s/tick steady state).

## Fan-out

Independent judgments over the same state go in ONE request (batched, they
answer in parallel server-side). Speculative questions — premises you may not
act on — are cheap to include; ignore uncertainty on unused branches.

## Anti-patterns

- Asking Sentinel to generate text, JSON, or reasoning — it returns
  distributions only; the answer shape is the interface.
- Chaining many sequential calls where one batched call would do.
- Hiding needed facts in the instruction instead of the state.
- Using bare adjectives as score levels ("good") — describe concrete
  situations.
- Making the oracle re-derive things code already knows (compute distances,
  counts, flags; ask for the judgment over them).
