#!/usr/bin/env python3
"""
围棋游戏自动化测试
验证棋盘逻辑、提子、打劫、AI等核心功能
"""

import sys
sys.path.insert(0, '.')

from board import Board
from ai import GoAI


def test_basic_play():
    """测试基本落子"""
    b = Board(9)
    assert b.play(4, 4, Board.BLACK) is None
    assert b.grid[4][4] == Board.BLACK
    assert b.play(4, 4, Board.WHITE) == 'occupied'
    print("✓ 基本落子测试通过")


def test_capture():
    """测试提子"""
    b = Board(9)
    # 白(4,4)只有1口气在(3,4)
    b.grid[4][3] = Board.BLACK
    b.grid[4][4] = Board.WHITE
    b.grid[4][5] = Board.BLACK
    b.grid[5][4] = Board.BLACK
    error = b.play(3, 4, Board.BLACK)
    assert error is None, f"提子失败: {error}"
    assert b.grid[3][4] == Board.BLACK
    assert b.grid[4][4] == Board.EMPTY
    print("✓ 提子测试通过")


def test_ko_rule():
    """测试打劫规则"""
    b = Board(9)
    # 先正常下几手
    b.play(4, 4, Board.BLACK)
    b.play(4, 5, Board.WHITE)
    # 模拟劫争：假设白刚在黑的位置(4,4)提了一子
    # 设置劫点为(4,4)——白不能立即回提
    b.ko_point = (4, 4)
    # 黑不能立即回提(4,4)（劫）
    error = b.play(4, 4, Board.BLACK)
    assert error == 'ko', f"打劫规则失效: {error}"
    # 黑pass后，劫解禁
    b.pass_turn(Board.BLACK)
    assert b.ko_point is None, "pass后应清除劫点"
    # 现在黑可以下其他位置
    error = b.play(3, 3, Board.BLACK)
    assert error is None, f"pass后应允许落子: {error}"
    print("✓ 打劫规则测试通过")


def test_suicide_rule():
    """测试自杀禁手"""
    b = Board(9)
    b.grid[3][3] = Board.BLACK
    b.grid[3][4] = Board.BLACK
    b.grid[4][3] = Board.BLACK
    b.grid[4][5] = Board.BLACK
    b.grid[5][3] = Board.BLACK
    b.grid[5][4] = Board.BLACK
    b.grid[5][5] = Board.BLACK
    error = b.play(4, 4, Board.WHITE)
    assert error == 'suicide', f"自杀规则失效: {error}"
    print("✓ 自杀禁手测试通过")


def test_group_liberties():
    """测试气的计算"""
    b = Board(9)
    b.grid[4][4] = Board.BLACK
    b.grid[4][5] = Board.BLACK
    group, libs = b._get_group(4, 4)
    assert len(group) == 2, f"组大小应为2，实际{len(group)}"
    assert len(libs) == 6, f"气数应为6，实际{len(libs)}"
    print("✓ 气的计算测试通过")


def test_legal_moves():
    """测试合法落子点检测"""
    b = Board(9)
    moves = b.get_legal_moves(Board.BLACK)
    assert len(moves) == 81, f"空盘应有81个合法点，实际{len(moves)}"
    b.play(4, 4, Board.BLACK)
    moves = b.get_legal_moves(Board.BLACK)
    assert len(moves) == 80, f"应剩80个合法点，实际{len(moves)}"
    print("✓ 合法落子点测试通过")


def test_board_display():
    """测试棋盘显示"""
    b = Board(5)
    b.play(2, 2, Board.BLACK)
    b.play(2, 3, Board.WHITE)
    output = b.to_str()
    assert '●' in output
    assert '○' in output
    assert '·' in output
    print("✓ 棋盘显示测试通过")


def test_ai_basic():
    """测试AI基本功能"""
    b = Board(9)
    ai = GoAI(b, Board.WHITE, 1)
    move = ai.best_move()
    assert move is not None
    assert 0 <= move[0] < 9 and 0 <= move[1] < 9
    print("✓ AI基本功能测试通过")


def test_ai_captures():
    """测试AI是否会吃子"""
    b = Board(9)
    b.grid[4][3] = Board.BLACK
    b.grid[4][4] = Board.WHITE
    b.grid[4][5] = Board.BLACK
    b.grid[5][4] = Board.BLACK
    ai = GoAI(b, Board.BLACK, 3)
    move = ai.best_move()
    assert move == (3, 4), f"AI应吃子(3,4)，实际选了{move}"
    print("✓ AI吃子策略测试通过")


def test_two_pass_end():
    """测试双pass结束"""
    b = Board(9)
    assert not b.is_game_over_by_pass()
    b.pass_turn(Board.BLACK)
    assert not b.is_game_over_by_pass()
    b.pass_turn(Board.WHITE)
    assert b.is_game_over_by_pass()
    print("✓ 双pass结束测试通过")


def test_full_game_flow():
    """测试完整对局流程（9路）"""
    b = Board(9)
    ai = GoAI(b, Board.WHITE, 2)
    b.play(4, 4, Board.BLACK)
    ai_move = ai.best_move()
    assert ai_move is not None
    b.play(ai_move[0], ai_move[1], Board.WHITE)
    b.play(3, 3, Board.BLACK)
    ai_move = ai.best_move()
    assert ai_move is not None
    b.play(ai_move[0], ai_move[1], Board.WHITE)
    black, white, empty = b.count_stones()
    assert black == 2 and white == 2 and empty == 77
    print("✓ 完整对局流程测试通过")


def test_coordinate_parse():
    """测试坐标边界"""
    b = Board(19)
    assert b.in_bounds(0, 0)
    assert b.in_bounds(18, 18)
    assert not b.in_bounds(-1, 0)
    assert not b.in_bounds(19, 0)
    print("✓ 坐标边界测试通过")


def run_all():
    print("\n" + "=" * 40)
    print("  围棋游戏 - 自动化测试")
    print("=" * 40 + "\n")

    tests = [
        test_basic_play,
        test_capture,
        test_ko_rule,
        test_suicide_rule,
        test_group_liberties,
        test_legal_moves,
        test_board_display,
        test_ai_basic,
        test_ai_captures,
        test_two_pass_end,
        test_full_game_flow,
        test_coordinate_parse,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 失败: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"  结果: {passed} 通过, {failed} 失败")
    print(f"{'=' * 40}\n")
    return failed == 0


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
