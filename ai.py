"""
围棋AI - 基于规则+评估函数的初级人机对战
策略：
1. 避免自杀和打劫
2. 优先吃子（提子）
3. 优先救自己的棋子（气紧时）
4. 靠近已有棋子落子（局部战斗）
5. 避免过于远离棋局的点
6. 随机性增加趣味
"""

import random
from board import Board


class GoAI:
    def __init__(self, board: Board, color: int, difficulty: int = 1):
        """
        board: 当前棋盘
        color: AI执子的颜色
        difficulty: 难度 1-3
          1 = 纯随机合法点
          2 = 基本策略
          3 = 稍强的策略（更重视吃子和防守）
        """
        self.board = board
        self.color = color
        self.opp = Board.WHITE if color == Board.BLACK else Board.BLACK
        self.difficulty = difficulty

    def _evaluate_move(self, r: int, c: int) -> float:
        """给一个落子点打分，越高越好"""
        score = 0.0

        # 模拟落子
        self.board.grid[r][c] = self.color
        opp = self.opp

        # 1. 如果能提子，大幅加分
        captured_count = 0
        for nr, nc in self.board.neighbors(r, c):
            if self.board.grid[nr][nc] == opp:
                group, libs = self.board._get_group(nr, nc)
                if len(libs) == 0:
                    captured_count += len(group)
        score += captured_count * 50  # 吃子权重很高

        # 2. 落子后的气数
        _, my_libs = self.board._get_group(r, c)
        num_liberties = len(my_libs)
        score += num_liberties * 2  # 气越多越好

        # 3. 如果会自杀，直接否决
        if num_liberties == 0 and captured_count == 0:
            self.board.grid[r][c] = Board.EMPTY
            return -9999

        # 4. 靠近已有棋子（避免太空泛的落子）
        near_own = 0
        near_enemy = 0
        for nr, nc in self.board.neighbors(r, c):
            if self.board.grid[nr][nc] == self.color:
                near_own += 1
            elif self.board.grid[nr][nc] == opp:
                near_enemy += 1
        score += near_own * 3  # 靠近自己的棋子
        score += near_enemy * 1  # 轻微靠近对手

        # 5. 对角线接触也算
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                nr, nc = r + dr, c + dc
                if self.board.in_bounds(nr, nc):
                    if self.board.grid[nr][nc] == self.color:
                        score += 1
                    elif self.board.grid[nr][nc] == opp:
                        score += 0.5

        # 6. 中心偏好（布局阶段）
        center_r, center_c = self.board.size // 2, self.board.size // 2
        dist = abs(r - center_r) + abs(c - center_c)
        max_dist = self.board.size
        score += (max_dist - dist) * 0.3  # 略偏向中心

        # 7. 如果自己的某个棋子气很少，优先救它
        for nr, nc in self.board.neighbors(r, c):
            if self.board.grid[nr][nc] == self.color:
                group, libs = self.board._get_group(nr, nc)
                if len(libs) == 1:
                    score += 20  # 救危急棋子

        # 还原
        self.board.grid[r][c] = Board.EMPTY
        return score

    def best_move(self) -> tuple[int, int] | None:
        """选择最佳落子点"""
        legal_moves = self.board.get_legal_moves(self.color)

        if not legal_moves:
            return None

        # 难度1: 纯随机
        if self.difficulty == 1:
            return random.choice(legal_moves)

        # 计算所有合法点的分数
        scored_moves = []
        for r, c in legal_moves:
            s = self._evaluate_move(r, c)
            scored_moves.append((s, r, c))

        # 难度2: 选最好的，但有概率犯错
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        best_score = scored_moves[0][0]

        if self.difficulty == 2:
            # 70% 概率选最优，30% 随机
            if random.random() < 0.7:
                # 从分数接近最优的点中选
                candidates = [(s, r, c) for s, r, c in scored_moves if s >= best_score - 5]
                return random.choice(candidates)[1:]
            else:
                return random.choice(legal_moves)

        # 难度3: 更聪明地选
        if self.difficulty >= 3:
            # 按分数分组
            candidates = []
            threshold = best_score * 0.7
            for s, r, c in scored_moves:
                if s >= threshold:
                    candidates.append((s, r, c))
            if candidates:
                # 从候选中按分数加权随机选
                weights = [s + 1 for s, _, _ in candidates]  # +1避免0权重
                idx = random.choices(range(len(candidates)), weights=weights, k=1)[0]
                return candidates[idx][1], candidates[idx][2]
            return scored_moves[0][1], scored_moves[0][2]

        return scored_moves[0][1], scored_moves[0][2]
