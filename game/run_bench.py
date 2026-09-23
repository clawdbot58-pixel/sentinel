"""Run N Snake episodes on fixed seeds, print score table. Usage:
python3 run_bench.py [seeds...]  (default: 1 2 3)  or  python3 run_bench.py --seeds 1,2,3 --max-steps 240
"""
import sys
import time
import statistics

from snake_game import SnakeGame, WIN_FOODS
from oracle_agent import decide


def run_episode(seed, verbose=False, max_steps=500):
    game = SnakeGame(seed)
    lats = []
    moves = []
    steps = 0
    while game.alive and not game.won and steps < max_steps:
        move, ans, dt, facts = decide(game)
        lats.append(dt)
        moves.append(move)
        ate, died, cause = game.step(move)
        steps += 1
        if verbose:
            print(f"  t={steps} move={move} ate={ate} foods={game.foods} "
                  f"head={game.head} lat={dt:.2f}s probs={ans.get('probabilities')}")
    # pocket diagnosis: at death, were there zero safe moves? (trapped)
    return {
        "seed": seed,
        "foods": game.foods,
        "won": game.won,
        "ticks": game.ticks,
        "death": game.death if not game.won else None,
        "latencies": lats,
        "moves": moves,
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seeds = [int(s) for s in args] if args else [1, 2, 3]
    verbose = "--verbose" in sys.argv
    results = []
    all_lats = []
    t0 = time.time()
    for s in seeds:
        print(f"seed {s} ...", flush=True)
        r = run_episode(s, verbose=verbose)
        results.append(r)
        all_lats += r["latencies"]
        status = "WIN" if r["won"] else f"dead:{r['death']}"
        print(f"  seed={s} foods={r['foods']}/{WIN_FOODS} ticks={r['ticks']} {status} "
              f"calls={len(r['latencies'])}")
    print("\nseed | foods | ticks | result")
    print("-----|-------|-------|-------")
    for r in results:
        print(f"{r['seed']:4d} | {r['foods']:5d} | {r['ticks']:5d} | "
              f"{'WIN' if r['won'] else r['death']}")
    if all_lats:
        all_lats_sorted = sorted(all_lats)
        p50 = statistics.median(all_lats_sorted)
        p95 = all_lats_sorted[max(0, int(0.95 * len(all_lats_sorted)) - 1)]
        print(f"\ndecisions={len(all_lats)} p50={p50:.3f}s p95={p95:.3f}s "
              f"wall={time.time()-t0:.0f}s")
    wins = sum(1 for r in results if r["won"])
    print(f"wins: {wins}/{len(results)}")
    # death telemetry
    from collections import Counter
    print("deaths:", dict(Counter(r["death"] for r in results if not r["won"])))


if __name__ == "__main__":
    main()
