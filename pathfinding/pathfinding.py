import heapq
from itertools import count

Cell = tuple[int, int]

ORTHOGONAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIAGONAL = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def _heuristic(a: Cell, b: Cell, allow_diagonal: bool) -> float:
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    if allow_diagonal:
        return (dx + dy) + (2 ** 0.5 - 2) * min(dx, dy)
    return dx + dy

def a_star(
    width: int,
    height: int,
    mines,
    start: Cell,
    goal: Cell,
    allow_diagonal: bool = False,
) -> list[Cell] | None:

    mines = set(mines)

    def passable(c: Cell) -> bool:
        return 0 <= c[0] < width and 0 <= c[1] < height and c not in mines

    if not passable(start) or not passable(goal):
        return None

    moves = ORTHOGONAL + DIAGONAL if allow_diagonal else ORTHOGONAL
    tie = count()  # tie-breaker so the heap never compares cells
    open_heap = [(_heuristic(start, goal, allow_diagonal), next(tie), start)]
    came_from: dict[Cell, Cell] = {}
    g_score: dict[Cell, float] = {start: 0}
    closed: set[Cell] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]

        if current in closed:
            continue
        closed.add(current)

        for dx, dy in moves:
            nxt = (current[0] + dx, current[1] + dy)
            if not passable(nxt) or nxt in closed:
                continue
            if dx and dy and not (
                passable((current[0] + dx, current[1]))
                and passable((current[0], current[1] + dy))
            ):
                continue  # don't squeeze diagonally past a mine
            tentative = g_score[current] + (2 ** 0.5 if dx and dy else 1)
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                f = tentative + _heuristic(nxt, goal, allow_diagonal)
                heapq.heappush(open_heap, (f, next(tie), nxt))

    return None

def render(width: int, height: int, mines, path=None) -> str:
    mines, path = set(mines), path or []
    on_path = set(path)
    rows = []
    for y in range(height):
        row = ""
        for x in range(width):
            c = (x, y)
            if path and c == path[0]:
                row += "S"
            elif path and c == path[-1]:
                row += "G"
            elif c in mines:
                row += "#"
            elif c in on_path:
                row += "*"
            else:
                row += "."
        rows.append(row)
    return "\n".join(rows)