"""Adapter between Snake game (walled 6x6 interior) and Sentinel.

ONE choice call per tick. Per legal move, code computes in code:
  - on_cycle: does this move follow the Hamiltonian cycle order?
  - shortcut_safe: tail reachability after the move (BFS, see cycle.py)
  - path_to_food: BFS distance to food after the move (interior, tail-vacate)
  - DEATH flag: wall (border) or body collision with tail-vacate rule
Frozen instruction enforces MANDATORY RANKING. Sentinel makes 100% of moves.
"""
import json
import time
import urllib.request
from collections import deque

from snake_game import SnakeGame, DIRS, ORDER, SIZE, LO, HI, FILL_LENGTH
from cycle import (
    NEXT, INDEX, CYCLE,
    is_on_cycle_move, cycle_successor, cycle_distance, shortcut_safe,
)

ENDPOINT = "http://127.0.0.1:8915/v1/systemone"

# Frozen instruction across all ticks (prefix-cache friendly).
INSTRUCTION = (
    "Follow the MANDATORY RANKING: cycle-following shortcut-safe moves "
    "toward food first; pure cycle moves second; never DEATH. "
    "Walls (border) and own body kill (DIES). "
    "A move marked TRAP (shortcut_safe=NO) breaks the cycle and traps you: "
    "NEVER pick TRAP, not even when it says EATS — food always returns "
    "within one cycle loop, patience is safe. "
    "Rank: 1) SAFE + on_cycle=YES + shortcut_safe=YES with short food-path first. "
    "2) Other SAFE + shortcut_safe=YES toward food (shorter food-path/cycle-dist). "
    "3) Pure cycle move (on_cycle=YES) always over any off-cycle or TRAP move. "
    "4) Never pick DIES. If every move DIES, pick any."
)


def sentinel_choice(state_text, criteria, instruction=INSTRUCTION, timeout=60):
    body = {
        "state": state_text,
        "model": "sentinel",
        "questions": {
            "move": {
                "type": "choice",
                "instructions": instruction,
                "criteria": criteria,
            }
        },
    }
    t0 = time.time()
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ans = json.loads(r.read())["answers"]["move"]
    dt = time.time() - t0
    return ans, dt


def _in_interior(cell):
    x, y = cell
    return LO <= x <= HI and LO <= y <= HI


def bfs_dist(start, goal, blocked):
    """BFS on interior only. blocked=set of body cells (start excluded)."""
    start, goal = tuple(start), tuple(goal)
    if start == goal:
        return 0
    blocked = set(blocked) - {start}
    q = deque([(start, 0)])
    seen = {start}
    while q:
        (x, y), d = q.popleft()
        for dx, dy in DIRS.values():
            n = (x + dx, y + dy)
            if not _in_interior(n):
                continue
            if n in blocked or n in seen:
                continue
            if n == goal:
                return d + 1
            seen.add(n)
            q.append((n, d + 1))
    return None


def move_facts(game):
    """Per-move facts computed in code. Returns dict move -> facts."""
    hx, hy = game.head
    head = (hx, hy)
    body = [tuple(c) for c in game.snake]
    food = tuple(game.food) if game.food else None
    cyc_now = cycle_distance(head, food) if food else 0
    facts = {}
    for m in ORDER:
        dx, dy = DIRS[m]
        n = (hx + dx, hy + dy)
        eats = food is not None and n == food
        # DEATH: wall (border/outside) first
        if not _in_interior(n):
            facts[m] = {"next": n, "dies": "wall", "eats": False,
                        "on_cycle": False, "shortcut_safe": False,
                        "dist": None, "cycle_dist": None, "closer": False}
            continue
        occupied = set(body if eats else body[:-1])
        if n in occupied:
            facts[m] = {"next": n, "dies": "body", "eats": eats,
                        "on_cycle": False, "shortcut_safe": False,
                        "dist": None, "cycle_dist": None, "closer": False}
            continue
        on_cyc = is_on_cycle_move(head, n)
        safe = shortcut_safe(head, n, body, food=game.food)
        # BFS food distance after the move
        if eats:
            dist = 0
        elif food is None:
            dist = 0
        else:
            after = set(body if eats else body[:-1]) | {n}
            blocked_food = set(after) - {n}
            dist = bfs_dist(n, food, blocked_food)
        cdist = cycle_distance(n, food) if food else 0
        closer = (cdist is not None and cyc_now is not None and cdist < cyc_now)
        facts[m] = {"next": n, "dies": None, "eats": eats,
                    "on_cycle": on_cyc, "shortcut_safe": safe,
                    "dist": dist, "cycle_dist": cdist, "closer": closer}
    return facts


def describe_move(m, f):
    n = f["next"]
    if f["dies"]:
        return f"{m} to {n}: DIES({f['dies']})"
    dist = "unreachable" if f["dist"] is None else str(f["dist"])
    cd = "?" if f["cycle_dist"] is None else str(f["cycle_dist"])
    oc = "YES" if f["on_cycle"] else "no"
    ss = "YES" if f["shortcut_safe"] else "NO"
    eats = ", EATS" if f["eats"] else ""
    closer = "toward-food" if f["closer"] else "not-closer"
    if not f["shortcut_safe"]:
        return (f"{m} to {n}: TRAP{eats}, on_cycle={oc}, "
                f"shortcut_safe={ss} (breaks cycle, AVOID), "
                f"food-path {dist}, cycle-dist {cd}, {closer}")
    return (f"{m} to {n}: SAFE{eats}, on_cycle={oc}, "
            f"shortcut_safe={ss}, food-path {dist}, cycle-dist {cd}, {closer}")


def build_state_text(game):
    sd = game.state_dict()
    succ = cycle_successor(game.head)
    return (
        f"8x8 Snake, walls=border, interior 1..6. Head {sd['head']}, food {sd['food']}, "
        f"length {sd['length']}/36, foods {sd['foods']}, "
        f"timeout in {sd['timeout_in']} ticks. Cycle-next from head: {list(succ) if succ else None}.\n"
        f"{game.render()}"
    )


def decide(game):
    """One Sentinel decision. Returns (move, answer, latency, facts)."""
    facts = move_facts(game)
    criteria = {m: describe_move(m, facts[m]) for m in ORDER}
    state_text = build_state_text(game)
    ans, dt = sentinel_choice(state_text, criteria)
    move = ans.get("choice", max(ans.get("probabilities", {}),
                                 key=ans.get("probabilities", {}).get))
    if move not in ORDER:  # safety: fall back to top probability key
        probs = ans.get("probabilities", {})
        move = max(probs, key=probs.get) if probs else "U"
    return move, ans, dt, facts
