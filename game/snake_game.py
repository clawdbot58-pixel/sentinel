"""8x8 Snake game: walls deadly, body deadly, 60-tick food timeout.

Deterministic food placement per seed. Plain Python, no deps.
"""
import random

SIZE = 8
FOOD_TIMEOUT = 60
WIN_FOODS = 4
# Walled border: outer ring (x==0/7 or y==0/7) is wall. Playable interior 1..6.
LO, HI = 1, 6
FILL_LENGTH = 36  # occupies every interior cell

DIRS = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}
ORDER = ["U", "D", "L", "R"]


class SnakeGame:
    def __init__(self, seed=0):
        self.seed = seed
        self.rng = random.Random(seed)
        # Start horizontal, head at (4,3), length 3
        self.snake = [(4, 3), (3, 3), (2, 3)]
        self.ticks = 0
        self.ticks_since_food = 0
        self.foods = 0
        self.alive = True
        self.death = None  # "wall" | "body" | "timeout"
        self.food = None
        self._place_food()

    def _empty_cells(self):
        occ = set(self.snake)
        return [(x, y) for y in range(LO, HI + 1) for x in range(LO, HI + 1)
                if (x, y) not in occ]

    def _place_food(self):
        empty = self._empty_cells()
        if not empty:
            self.food = None
            return
        self.food = self.rng.choice(empty)

    @property
    def head(self):
        return self.snake[0]

    def render(self):
        """Compact ASCII grid, 8x8. #=wall, H=head, o=body, F=food, .=empty."""
        grid = [["." for _ in range(SIZE)] for _ in range(SIZE)]
        for y in range(SIZE):
            for x in range(SIZE):
                if x == 0 or x == SIZE - 1 or y == 0 or y == SIZE - 1:
                    grid[y][x] = "#"
        if self.food is not None:
            fx, fy = self.food
            grid[fy][fx] = "F"
        for i, (x, y) in enumerate(self.snake):
            grid[y][x] = "H" if i == 0 else "o"
        return "\n".join("".join(row) for row in grid)

    def step(self, move):
        """Apply move (U/D/L/R). Returns (ate, died, cause)."""
        if not self.alive:
            return False, True, self.death
        dx, dy = DIRS[move]
        hx, hy = self.head
        nx, ny = hx + dx, hy + dy
        self.ticks += 1
        self.ticks_since_food += 1

        # Wall check: outer ring + outside board are deadly walls
        if not (LO <= nx <= HI and LO <= ny <= HI):
            self.alive = False
            self.death = "wall"
            return False, True, "wall"

        ate = (self.food is not None and (nx, ny) == self.food)
        # Body check: tail tip vacates unless growing
        body = set(self.snake if ate else self.snake[:-1])
        if (nx, ny) in body:
            self.alive = False
            self.death = "body"
            return False, True, "body"

        self.snake = [(nx, ny)] + (self.snake if ate else self.snake[:-1])
        if ate:
            self.foods += 1
            self.ticks_since_food = 0
            self._place_food()
        if self.ticks_since_food >= FOOD_TIMEOUT:
            self.alive = False
            self.death = "timeout"
            return ate, True, "timeout"
        return ate, False, None

    @property
    def won(self):
        return self.foods >= WIN_FOODS

    @property
    def filled(self):
        return len(self.snake) >= FILL_LENGTH

    def state_dict(self):
        return {
            "size": SIZE,
            "head": list(self.head),
            "snake": [list(p) for p in self.snake],
            "length": len(self.snake),
            "food": list(self.food) if self.food else None,
            "foods": self.foods,
            "ticks": self.ticks,
            "ticks_since_food": self.ticks_since_food,
            "timeout_in": FOOD_TIMEOUT - self.ticks_since_food,
            "alive": self.alive,
        }
