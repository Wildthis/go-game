"""
围棋棋盘逻辑
支持标准19x19、9x9、13x13棋盘
实现提子、打劫、气、自杀规则等核心逻辑
"""

from __future__ import annotations
from copy import deepcopy
from typing import Optional


class Board:
    EMPTY = 0
    BLACK = 1
    WHITE = 2

    def __init__(self, size: int = 19):
        self.size = size
        self.grid: list[list[int]] = [[self.EMPTY] * size for _ in range(size)]
        self.ko_point: tuple[int, int] | None = None  # 打劫禁止点
        self.last_move: tuple[int, int] | None = None
        self.consecutive_passes = 0  # 连续pass计数

    def copy(self) -> Board:
        b = Board(self.size)
        b.grid = deepcopy(self.grid)
        b.ko_point = self.ko_point
        b.last_move = self.last_move
        b.consecutive_passes = self.consecutive_passes
        return b

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def _col_label(self, c: int) -> str:
        """列号转字母标签（跳过I）"""
        letters = []
        for i in range(ord('A'), ord('Z') + 1):
            ch = chr(i)
            if ch == 'I':
                continue
            letters.append(ch)
        return letters[c]

    def neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                result.append((nr, nc))
        return result

    def _get_group(self, r: int, c: int) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
        """返回棋子列表和其所有气"""
        color = self.grid[r][c]
        if color == self.EMPTY:
            return [], set()
        visited: set[tuple[int, int]] = set()
        stones: list[tuple[int, int]] = []
        liberties: set[tuple[int, int]] = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            stones.append((cr, cc))
            for nr, nc in self.neighbors(cr, cc):
                if self.grid[nr][nc] == self.EMPTY:
                    liberties.add((nr, nc))
                elif self.grid[nr][nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return stones, liberties

    def _remove_group(self, stones: list[tuple[int, int]]):
        for r, c in stones:
            self.grid[r][c] = self.EMPTY

    def _place_stone(self, r: int, c: int, color: int) -> Optional[str]:
        """
        尝试落子，返回错误信息或None
        错误信息: 'ko', 'suicide', 'occupied'
        """
        if not self.in_bounds(r, c):
            return 'out_of_bounds'
        if self.grid[r][c] != self.EMPTY:
            return 'occupied'

        # 临时放置
        self.grid[r][c] = color
        opp = self.WHITE if color == self.BLACK else self.BLACK

        # 检查是否提掉对方棋子
        # 关键：先收集相邻对手棋子的组，再去重
        captured_groups: set[tuple] = set()
        for nr, nc in self.neighbors(r, c):
            if self.grid[nr][nc] == opp:
                group, libs = self._get_group(nr, nc)
                if len(libs) == 0:
                    # 用排序后的元组去重
                    captured_groups.add(tuple(sorted(group)))

        captured = [list(g) for g in captured_groups]

        # 检查自杀
        my_group, my_libs = self._get_group(r, c)
        if len(my_libs) == 0 and not captured:
            self.grid[r][c] = self.EMPTY
            return 'suicide'

        # 执行提子
        for group in captured:
            self._remove_group(group)

        # 检查打劫
        if len(captured) == 1 and len(captured[0]) == 1 and len(my_libs) == 1:
            # 可能形成打劫
            self.ko_point = captured[0][0]
        else:
            self.ko_point = None

        return None

    def play(self, r: int, c: int, color: int) -> Optional[str]:
        """落子，返回错误信息或None"""
        if self.ko_point and (r, c) == self.ko_point:
            return 'ko'
        return self._place_stone(r, c, color)

    def pass_turn(self, color: int):
        """pass一手"""
        self.consecutive_passes += 1
        self.ko_point = None

    def is_game_over_by_pass(self) -> bool:
        """连续pass两次（双方各一次）即结束"""
        return self.consecutive_passes >= 2

    def count_stones(self) -> tuple[int, int, int]:
        """返回黑子数、白子数、空位"""
        black = sum(row.count(self.BLACK) for row in self.grid)
        white = sum(row.count(self.WHITE) for row in self.grid)
        empty = self.size * self.size - black - white
        return black, white, empty

    def to_str(self, show_coords: bool = True) -> str:
        """生成棋盘的文本表示"""
        lines: list[str] = []
        col_labels = '  '
        if show_coords:
            col_labels = '     ' + ' '.join(self._col_label(c) for c in range(self.size))
        lines.append(col_labels)

        for r in range(self.size):
            row_str = f'{r + 1:>2} ' if show_coords else '   '
            for c in range(self.size):
                cell = self.grid[r][c]
                if cell == self.EMPTY:
                    row_str += '· '
                elif cell == self.BLACK:
                    row_str += '● '
                else:
                    row_str += '○ '
            lines.append(row_str)

        return '\n'.join(lines)

    def get_legal_moves(self, color: int) -> list[tuple[int, int]]:
        """获取合法落子点（排除自杀和打劫）"""
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == self.EMPTY:
                    # 检查打劫
                    if self.ko_point and (r, c) == self.ko_point:
                        continue
                    # 模拟落子检查自杀
                    self.grid[r][c] = color
                    opp = self.WHITE if color == self.BLACK else self.BLACK
                    captured_any = False
                    for nr, nc in self.neighbors(r, c):
                        if self.grid[nr][nc] == opp:
                            group, libs = self._get_group(nr, nc)
                            if len(libs) == 0:
                                captured_any = True
                    my_group, my_libs = self._get_group(r, c)
                    if len(my_libs) > 0 or captured_any:
                        moves.append((r, c))
                    self.grid[r][c] = self.EMPTY
        return moves
