# What Sentinel is

## The one-paragraph version

Sentinel turns application state into **typed, calibrated judgments**. You send a
`state` (any text or JSON) plus typed questions; it returns probabilities over
the answers you defined. It is served by a single forward pass of a fine-tuned
Qwen3.8-27B (the "champion" checkpoint from the openjev project) running
locally on the Radeon R9700 through llama.cpp — no generation loop, no prompt
fragility, no API key, no network.

## How it differs from an LLM

| | LLM (text generation) | Sentinel (System One) |
|---|---|---|
| Output | Prose you must parse | Typed probabilities, schema-valid by construction |
| Failure mode | Hallucination, format drift | Distribution can be uncertain — visible, measurable |
| Latency | Seconds (autoregressive) | 0.4–1.5s (single forward pass) |
| Determinism | Sampling-dependent | Pure function of weights + input (readout is) |
| Calibration | Untuned | Fitted on JevBench (T=1.2, ECE 0.049) |
| Cost per call | Variable token count | Fixed (~0.6k prefill tokens) |

Use an LLM when you need reasoning, drafting, or open-ended planning. Use
Sentinel when code needs a **judgment**: which option, is this true, how good
on this scale. The strongest pattern is both together — an LLM orchestrates,
Sentinel decides.

## Architecture (what actually runs)

```
your code ──POST /v1/systemone──> sentinel_server.py (:8915, FastAPI proxy)
                                     │  builds chat prompt, reads letter logits
                                     ▼
                          llama.cpp Vulkan (:8912, single slot, 8k ctx)
                                     │  Qwen3.8-27B UD-Q4_K_M, 1 forward pass
                                     ▼
                          top-200 next-token logprobs at final position
                                     │  softmax over label letters, T=1.2
                                     ▼
                          probabilities over YOUR options + confidence + abstain
```

Nothing is sampled. `output_tokens` is 0 on every call. The distribution comes
from the model's own next-token logits restricted to the option letters — the
same mechanism that made it score 87.9% on JevBench.

## Origin

Sentinel is the open rebuild of TypeSafe's Jev ("System One") built in the
openjev project: same wire format, open weights, local hardware, and — on the
public JevBench panel — a higher score (77.0 vs 75.4) with accuracy 87.9% vs
86.6%.
