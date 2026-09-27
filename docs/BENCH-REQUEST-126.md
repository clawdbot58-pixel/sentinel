# Official JevBench submission — bench request #126

Filed: 2026-09-27. https://github.com/fstandhartinger/jevbench/issues/126

## What was asked

A ranked row for Sentinel (sentinel-0.1, Qwen3.8-27B UD-Q4_K_M) on the full
JevBench v1.4 protocol: the 231 public items plus their 308-item sealed set,
run by the JevBench team on their own hardware (they run contributor systems in
a network-disabled, read-only container; sealed item text never leaves their
control).

## What we disclosed

- Exact pins: GGUF `94400ee9`, code `bda4269`, tokenizer Qwen3.5-4B.
- Temperature 1.2, fitted on public items only — disclosed as the sole leak surface.
- Setup check: 203/231 (87.9%), p50 0.41 s / p95 2.94 s, RDNA4 Vulkan.
- No training, no distillation, no Jev outputs, no weights changed.
- `confidence` / `abstain` are extra fields; the scored distribution is unchanged.

## Expectations (so we don't kid ourselves)

Board context at filing (v1.4.2.2): Imajev-4B 67.37, Plumb-4B 65.84,
decider-4b v2 64.13, Jev 1.13.0 63.29. Our public accuracy (87.9% on 231) is
at the top of the field's public numbers, but the v1.4 score is an equal-weight
harmonic mean of Intelligence (chance-corrected, sealed-blended), Calibration,
Speed and Cost, with gates:

- Our Speed axis will be middling (p50 0.41 s raw, ×2 + 0.15 s adjustment puts
  adjusted p50 ~0.97 s; leaders sit at 16–30 ms).
- Cost will be excellent (self-hosted Q4, ~$0.02–0.03/1k decisions at 4B-class
  reference price... note the 27B base costs more than a 4B row; the estimate
  uses measured tokens at the Qwen3.8-27B reference tariff).
- Calibration is unknown until they run the sealed set at T=1.2.
- The v1.4 Intelligence multiplier punishes a weak sealed run quadratically.

Honest range: if sealed accuracy lands near public, we likely land top-3 on
the composite; if the public→sealed gap is large (like CLM-8B's 16.7 pp or
worse), the gap penalty and Intelligence gate pull the score down hard. Nobody
should claim #1 before the sealed run exists. This file exists so we don't.

## If they run it

They will file a pre-registration doc (like `docs/v1.2-additions-run4b.md`)
before running, then a release note. Our row key was proposed as `sentinel`.
