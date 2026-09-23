# Local operations

## Starting and stopping

```bash
bash /home/cactus/jev-runs/start-sentinel.sh   # one command: backend + API
# or through the ai CLI:
ai run sentinel                                 # starts the llama.cpp backend on :8912
python /home/cactus/jev-runs/sentinel_server.py # starts the /v1/systemone proxy on :8915
```

Stop: `pkill -f "vk2/bin/llama-serv"` then `pkill -f sentinel_serve[r]`.

## Health

```bash
curl -s http://127.0.0.1:8915/health   # {"status":"ok","llama":true}
```

`llama:false` = proxy up but backend down (start it). `status:degraded` =
same thing. The proxy is a thin FastAPI: if it's up but degraded, only the
backend needs restarting.

## Processes and logs

| piece | port | log |
|---|---|---|
| llama.cpp backend (Qwen3.8-27B UD-Q4_K_M) | 8912 | `~/jev-runs/llama-server-sentinel.log` |
| sentinel_server.py (FastAPI proxy) | 8915 | `~/jev-runs/sentinel.log` |
| benchmark harness + replays | — | `~/jev-runs/` |

The backend is the same llama.cpp binary used for all benchmark runs
(coopmat2 Vulkan build, `~/code/llama.cpp/build-vk2`), model
`~/models/gguf38/Qwen3.8-27B-UD-Q4_K_M.gguf`, 8k context, single slot.

## Resource facts

- VRAM: ~16.5GB of 32GB. The personal 262k-context server (another 16GB+)
  CANNOT run at the same time — VRAM collides at ~33GB. Stop one before the
  other.
- RAM: weights are mmap'd; no anonymous pinning.
- First start after boot: ~40-70s (Vulkan shader cache is warm; weights page
  in from NVMe).

## Limits

- Context 8192 tokens: states up to ~3.5-4k tokens are comfortable (p95 ~3s).
  Longer states raise latency linearly with prefill (~1000 tok/s).
- Single slot: requests queue; a realtime loop should be one decision at a
  time (or ask for --parallel N slots if you need concurrency).
- Calibration T=1.2 is baked into the proxy. Don't add sampling on top.
- Output is distribution-only. If you need text generation, use a different
  model — Sentinel never writes prose, by design.
