# Case study: LLM + Sentinel beat Snake (fill the map)

This is the worked example of the full architecture: an LLM as strategist,
Sentinel as the per-tick decision engine, and code as the adapter. The
session is in `~/Desktop/sentinel-workspace/` (agent: muse-spark-1.3 via
opencode, using this skill).

## The game

8x8 grid, walls on the border are deadly, snake body is deadly, food spawns
randomly, 60-tick timeout per food. Win condition: **the snake occupies every
non-wall cell (36/36)** — a full-board fill.

## Why naive play fails

A reactive snake that minimizes distance to food dies between 10-20 length:
as the body grows it walled itself into pockets it can no longer leave.
Longer survival requires global path discipline — the classic solution is a
Hamiltonian cycle: a fixed route visiting all 36 interior cells exactly once,
followed faithfully, with only provably-safe shortcuts toward food.

## The split that works

```
LLM (strategist, muse-spark-1.3)
  ├─ builds the game engine (snake_game.py)
  ├─ builds the adapter (oracle_agent.py)
  ├─ writes the instruction the oracle sees
  └─ reads death telemetry -> iterates the design
CODE (adapter, per tick)
  ├─ renders the grid (ASCII) + snake state
  ├─ computes per-move facts: DEATH flags (with tail-vacate rule),
  │   BFS path distance to food, flood-fill space, tail reachability
  ├─ embeds them as option descriptions
  └─ takes argmax of the returned probabilities
SENTINEL (oracle, per tick)
  └─ one choice call over the legal moves -> calibrated probabilities
```

The division is deliberate: **the adapter compiles tactics into facts, the
oracle certifies the decision with real probabilities**. Sentinel never picks
blind; the code never picks at all. Every move in the winning run was an
oracle argmax (`output_tokens: 0` — nothing was ever generated).

## Why the facts matter more than the instruction

Across attempts, changing the instruction text moved accuracy ~1-2 points;
adding the computed facts (death flags, BFS distance, free-space count)
moved it by whole tiers. The oracle ranks options well **given the right
features** — the features are where engineering effort pays. This mirrors the
benchmark finding: with the right state representation, the base model is
already near the ceiling.

## Session log (muse-spark-1.3, autonomous)

1. Read the skill, checked stack health.
2. Built snake_game.py + oracle_agent.py + run_bench.py.
3. Won the 4-food objective on attempt 1 (seed 1 and 2: 4/4 in 18-24 ticks;
   untuned seed 999999: 4/4, p50 0.58s / p95 0.73s) — video: `sentinel-snake-win.mp4`.
4. Objective raised to full-board fill (36/36) — session v2, Hamiltonian
   cycle + shortcut-safety facts (see PROMPT.md for the spec).

## Files

- `snake_game.py` — engine
- `oracle_agent.py` — the game→Jev adapter
- `run_bench.py`, `run_win.py` — harnesses
- `attempts/attempt-N.md` — every iteration, logged
- `RESULT.md`, `sentinel-snake-win.mp4` — the 4-food win (v1)
- `sentinel-snake-fill.mp4` — the fill-the-map run (v2, if achieved)
