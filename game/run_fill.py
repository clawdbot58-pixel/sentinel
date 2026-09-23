"""Sentinel fill-the-map run: until length 36/36 (or death), with frame capture."""
import os
import sys
import time
import statistics

from PIL import Image, ImageDraw

from snake_game import SnakeGame, SIZE, LO, HI, FILL_LENGTH
from oracle_agent import decide

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 999999
MAX_STEPS = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
FRAMES_DIR = sys.argv[3] if len(sys.argv) > 3 else "frames_fill"
CELL = 40
M = CELL * SIZE


def render_frame(game, step, move=None, outdir=FRAMES_DIR):
    img = Image.new("RGB", (M, M + 30), (20, 20, 24))
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        for x in range(SIZE):
            c = (x * CELL, y * CELL)
            if x == 0 or x == SIZE - 1 or y == 0 or y == SIZE - 1:
                d.rectangle([c, (c[0] + CELL - 1, c[1] + CELL - 1)], fill=(90, 90, 100))
            else:
                d.rectangle([c, (c[0] + CELL - 1, c[1] + CELL - 1)], fill=(34, 34, 40))
    if game.food:
        fx, fy = game.food
        d.rectangle([(fx * CELL + 6, fy * CELL + 6),
                     ((fx + 1) * CELL - 6, (fy + 1) * CELL - 6)], fill=(220, 60, 60))
    for i, (x, y) in enumerate(game.snake):
        col = (80, 220, 100) if i == 0 else (45, 140, 70)
        d.rectangle([(x * CELL + 2, y * CELL + 2),
                     ((x + 1) * CELL - 2, (y + 1) * CELL - 2)], fill=col)
    d.text((8, M + 8), f"seed {SEED} tick {step} len {len(game.snake)}/{FILL_LENGTH}"
           + (f" move {move}" if move else ""), fill=(230, 230, 230))
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, f"frame_{step:04d}.png")
    img.save(p)
    return p


def main():
    game = SnakeGame(SEED)
    lats = []
    cyc = trap = eats = 0
    step = 0
    render_frame(game, step)
    t0 = time.time()
    while game.alive and not game.filled and step < MAX_STEPS:
        move, ans, dt, facts = decide(game)
        lats.append(dt)
        f = facts[move]
        cyc += bool(f["on_cycle"])
        trap += bool(not f["shortcut_safe"])
        ate, died, cause = game.step(move)
        eats += bool(ate)
        step += 1
        render_frame(game, step, move)
        print(f"t={step} move={move} on_cyc={f['on_cycle']} safe={f['shortcut_safe']} "
              f"ate={ate} len={len(game.snake)} conf={ans.get('confidence', 0):.2f} "
              f"lat={dt:.2f}s probs={ans.get('probabilities')}", flush=True)
    ok = game.filled and game.alive
    print(f"RESULT seed={SEED} len={len(game.snake)}/{FILL_LENGTH} foods={game.foods} "
          f"ticks={game.ticks} {'FILL' if ok else 'dead:' + str(game.death)} "
          f"frames={step + 1} cycle={cyc}/{step} trap_picks={trap} eats={eats} "
          f"wall={time.time() - t0:.0f}s")
    if lats:
        s = sorted(lats)
        print(f"decisions={len(lats)} p50={statistics.median(s):.3f}s "
              f"p95={s[max(0, int(0.95 * len(s)) - 1)]:.3f}s")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
