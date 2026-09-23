"""Hamiltonian cycle for the 6x6 interior of the 8x8 board.

Layout: boustrophedon (snake) variant that closes into a cycle.
Interior cells are 1..6 in x and y (outer ring x==0/7 or y==0/7 is wall).
The cycle visits all 36 interior cells exactly once and returns to start.

Construction (column-comb boustrophedon, valid for even width):
  - top row left->right: (1,1)..(6,1)
  - down right column: (6,2)..(6,6)
  - then snake pairs of columns right-to-left: up col 5, down col 4,
    up col 3, down col 2, up col 1, closing (1,2)->(1,1).
Each step is Manhattan-adjacent; last cell is adjacent to first.
"""

from collections import deque

SIZE = 8
LO, HI = 1, 6  # interior inclusive range

DIRS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def is_interior(cell):
    x, y = cell
    return LO <= x <= HI and LO <= y <= HI


def build_boustrophedon_cycle():
    cyc = []
    W, H = HI, HI  # 6
    # top row
    for x in range(LO, W + 1):
        cyc.append((x, LO))
    # down right column
    for y in range(LO + 1, H + 1):
        cyc.append((W, y))
    # snake remaining columns right-to-left in pairs
    x = W - 1
    going_up = True
    while x >= 3:
        if going_up:
            cyc.append((x, H))
            for y in range(H - 1, LO, -1):  # H-1 .. 2
                cyc.append((x, y))
        else:
            cyc.append((x, LO + 1))  # row 2
            for y in range(LO + 2, H + 1):  # 3 .. H
                cyc.append((x, y))
        going_up = not going_up
        x -= 1
    # finish columns 2 (down) and 1 (up); entry depends on parity.
    # With W=6 we exit the loop going_up=True after x=3,4,5 (3 cols),
    # meaning col 2 goes down, col 1 goes up. Assert generally below.
    # col 2 down:
    cyc.append((2, LO + 1))
    for y in range(LO + 2, H + 1):
        cyc.append((2, y))
    # step left to col 1 bottom, then up col 1 to row 2:
    cyc.append((1, H))
    for y in range(H - 1, LO, -1):
        cyc.append((1, y))
    return cyc


CYCLE = build_boustrophedon_cycle()
INDEX = {cell: i for i, cell in enumerate(CYCLE)}
NEXT = {cell: CYCLE[(i + 1) % len(CYCLE)] for i, cell in enumerate(CYCLE)}
PREV = {cell: CYCLE[(i - 1) % len(CYCLE)] for i, cell in enumerate(CYCLE)}


def cycle_successor(head):
    return NEXT.get(tuple(head))


def is_on_cycle_move(head, target):
    return tuple(target) == NEXT.get(tuple(head))


def cycle_distance(head, goal):
    """Steps along the cycle from head to goal (following NEXT). None if off-cycle."""
    h, g = tuple(head), tuple(goal)
    if h not in INDEX or g not in INDEX:
        return None
    return (INDEX[g] - INDEX[h]) % len(CYCLE)


def _bfs_reachable(start, goal, blocked):
    if start == goal:
        return True
    q = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS.values():
            n = (x + dx, y + dy)
            if not is_interior(n) or n in blocked or n in seen:
                continue
            if n == goal:
                return True
            seen.add(n)
            q.append(n)
    return False


def shortcut_safe(head, target_cell, body, food=None):
    """Tail-reachability + cycle-contiguity safety check after a hypothetical move.

    head: current head (x,y). target_cell: candidate next cell.
    body: current snake list head-first [(x,y),...].
    food: optional food cell; if target == food the tail does NOT vacate.

    Returns True iff ALL hold:
      1. target is interior (not a wall),
      2. no immediate collision (tail-vacate aware),
      3. BFS: after the move the tail is still reachable from the new head
         through non-body interior cells,
      4. contiguity: the shortcut jumps ahead along the cycle over a
         body-free arc (on-cycle moves pass trivially). Tail-reachability
         alone self-traps at length ~29 on edge seeds (e.g. 999999, 2, 0:
         greedy shortcuts die of body collision); the arc check keeps the
         body a contiguous cycle segment so pure-cycle fallback always exists.
    """
    head = tuple(head)
    target = tuple(target_cell)
    body = [tuple(c) for c in body]
    if not is_interior(target):
        return False  # wall
    eats = food is not None and target == tuple(food)
    if eats:
        new_body = [target] + body
    else:
        new_body = [target] + body[:-1] if body else [target]
    # immediate collision: target runs into body that does not vacate
    occupied_before = set(body if eats else (body[:-1] if body else []))
    if target in occupied_before:
        return False
    new_occupied = set(new_body)
    goal_tail = body[-1] if body else target  # old tail cell (vacated if not eats)
    blocked = set(new_occupied) - {goal_tail}
    # tail reachability through non-body interior cells
    if not _bfs_reachable(target, goal_tail, blocked):
        return False
    # cycle contiguity: skipped forward arc head->target must be body-free
    # (tail cell counts as free when it vacates).
    if head not in INDEX or target not in INDEX:
        return False
    arc_blocked = set(body if eats else body[:-1])
    n = len(CYCLE)
    i, j = INDEX[head], INDEX[target]
    free = n - len(set(body))  # free cells before the move
    d = (j - i) % n
    if d == 0 or d > max(free, 1):
        return False
    k = (i + 1) % n
    while k != j:
        if CYCLE[k] in arc_blocked:
            return False
        k = (k + 1) % n
    return True


def validate_cycle(cyc=None):
    cyc = cyc or CYCLE
    assert len(cyc) == 36, f"len={len(cyc)}"
    assert set(cyc) == {(x, y) for y in range(LO, HI + 1) for x in range(LO, HI + 1)}, "must cover interior exactly"
    for a, b in zip(cyc, cyc[1:] + cyc[:1]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, f"non-adjacent {a}->{b}"
    return True


if __name__ == "__main__":
    validate_cycle()
    print("cycle OK, len", len(CYCLE))
    print(CYCLE)
