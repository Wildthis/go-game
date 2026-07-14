#!/usr/bin/env python3
"""
围棋人机对战 - 命令行版本
玩家执黑先行，AI执白

用法:
    python main.py              # 19路棋盘，难度2
    python main.py 9            # 9路棋盘
    python main.py 19 1         # 19路，难度1
    python main.py 9 3          # 9路，难度3
"""

import sys
from board import Board
from ai import GoAI


def parse_coordinate(coord_str: str, size: int) -> tuple[int, int] | None:
    """将坐标字符串转为行列索引
    支持: 1A, 1a, A1, a1, 19x19格式
    """
    coord_str = coord_str.strip().upper()

    # 处理纯数字坐标 (1-based)
    if coord_str.isdigit():
        n = int(coord_str)
        if 1 <= n <= size * size:
            # 按行优先展开
            r = (n - 1) // size
            c = (n - 1) % size
            return r, c

    # 处理字母数字混合: A1, B3, 10C 等
    # 提取字母和数字部分
    letters = ''
    digits = ''
    for ch in coord_str:
        if ch.isalpha():
            letters += ch
        elif ch.isdigit():
            digits += ch

    if not letters or not digits:
        return None

    # 尝试解析
    col_letter = letters[0]  # 第一个字母
    row_num = int(digits)

    # 字母转列号: A=0, B=1, ..., T=19(跳过I)
    col_map = {}
    idx = 0
    for i in range(ord('A'), ord('Z') + 1):
        ch = chr(i)
        if ch == 'I':  # 围棋跳过I
            continue
        col_map[ch] = idx
        idx += 1

    if col_letter not in col_map:
        return None
    col = col_map[col_letter]

    # 行号 1-based
    row = row_num - 1

    if 0 <= row < size and 0 <= col < size:
        return row, col

    return None


def show_board(board: Board, last_move=None, ai_move=None):
    """显示棋盘"""
    print("\n" + "=" * (board.size * 3 + 10))
    print(f"  棋盘大小: {board.size}x{board.size}")
    print("=" * (board.size * 3 + 10))

    col_labels = '     '
    col_idx = 0
    for i in range(ord('A'), ord('Z') + 1):
        ch = chr(i)
        if ch == 'I':
            continue
        if col_idx >= board.size:
            break
        col_labels += f'{ch:^3}'
        col_idx += 1
    print(col_labels)

    black_count, white_count, empty = board.count_stones()

    for r in range(board.size):
        row_str = f'{r + 1:>2} '
        for c in range(board.size):
            cell = board.grid[r][c]
            marker = ''
            if last_move and (r, c) == last_move:
                marker = '*'
            elif ai_move and (r, c) == ai_move:
                marker = '!'

            if cell == Board.EMPTY:
                row_str += f'·{marker} '
            elif cell == Board.BLACK:
                row_str += f'●{marker} '
            else:
                row_str += f'○{marker} '
        print(row_str)

    print("-" * (board.size * 3 + 10))
    print(f"  黑子: {black_count}  白子: {white_count}  空位: {empty}")
    print("-" * (board.size * 3 + 10))


def main():
    size = 19
    difficulty = 2

    if len(sys.argv) > 1:
        try:
            size = int(sys.argv[1])
        except ValueError:
            print(f"无效棋盘大小: {sys.argv[1]}，使用默认19")

    if len(sys.argv) > 2:
        try:
            difficulty = int(sys.argv[2])
        except ValueError:
            print(f"无效难度: {sys.argv[2]}，使用默认2")

    if size not in (9, 13, 19):
        print(f"棋盘大小仅支持 9, 13, 19，默认使用19")
        size = 19

    print(f"\n{'='*40}")
    print(f"  围棋人机对战")
    print(f"  棋盘: {size}x{size}  难度: {difficulty}/3")
    print(f"  你执黑 ● 先行")
    print(f"  输入 help 查看帮助")
    print(f"{'='*40}")

    board = Board(size)
    ai = GoAI(board, Board.WHITE, difficulty)
    current_player = Board.BLACK  # 黑先

    last_human_move = None
    last_ai_move = None

    round_num = 0

    while True:
        # 检查是否应该结束
        if board.is_game_over_by_pass():
            winner = determine_winner(board)
            show_board(board, last_human_move, last_ai_move)
            print(f"\n双方连续pass，游戏结束！")
            print(f"最终结果: {winner}")
            break

        show_board(board, last_human_move, last_ai_move)

        if current_player == Board.BLACK:
            # 人类回合
            move_input = input(f"\n黑方回合 (第{round_num + 1}手) - 输入坐标(如 4D)、pass、resign: ").strip()

            if move_input.lower() == 'help':
                print_help()
                continue

            if move_input.lower() in ('pass', 'p'):
                board.pass_turn(Board.BLACK)
                print("黑方pass")
                current_player = Board.WHITE
                continue

            if move_input.lower() in ('resign', 'r', '认输'):
                show_board(board, last_human_move, last_ai_move)
                print("\n黑方认输，白方胜！")
                break

            pos = parse_coordinate(move_input, size)
            if pos is None:
                print("无效坐标，请输入 help 查看帮助")
                continue

            r, c = pos
            error = board.play(r, c, Board.BLACK)
            if error:
                err_msg = {'ko': '打劫！此处不能落子', 'suicide': '自杀禁手！', 'occupied': '此处已有棋子', 'out_of_bounds': '超出棋盘范围'}
                print(err_msg.get(error, f'非法落子: {error}'))
                continue

            last_human_move = (r, c)
            last_ai_move = None
            round_num += 1
            current_player = Board.WHITE

        else:
            # AI回合
            print(f"\n白方思考中...")
            ai_move_pos = ai.best_move()

            if ai_move_pos is None:
                board.pass_turn(Board.WHITE)
                print("白方pass (无合法落子)")
                current_player = Board.BLACK
                continue

            r, c = ai_move_pos
            error = board.play(r, c, Board.WHITE)
            if error:
                # AI不应该犯这种错，但以防万一
                print(f"AI落子出错: {error}，重新选择...")
                continue

            last_ai_move = (r, c)
            last_human_move = None
            round_num += 1
            print(f"白方落子: {format_coord(r, c)}")
            current_player = Board.BLACK

            # 检查人类是否该pass了
            if board.is_game_over_by_pass():
                winner = determine_winner(board)
                show_board(board, last_human_move, last_ai_move)
                print(f"\n双方连续pass，游戏结束！")
                print(f"最终结果: {winner}")
                break


def format_coord(r: int, c: int) -> str:
    """行列转坐标字符串"""
    col_map = []
    for i in range(ord('A'), ord('Z') + 1):
        ch = chr(i)
        if ch == 'I':
            continue
        col_map.append(ch)
    return f"{r + 1}{col_map[c]}"


def print_help():
    print("""
帮助信息:
  落子: 输入坐标，如 4D、10B、19T
  pass: 输入 pass 或 p (放弃一手)
  认输: 输入 resign 或 r (认输)
  退出: 输入 quit 或 q

坐标说明:
  行号 1-{size}，列标 A-H, J-T (跳过I)
  例如 4D = 第4行第4列
""")


def determine_winner(board: Board) -> str:
    """简单的数子法判定胜负"""
    black, white, _ = board.count_stones()
    komi = 7.5  # 贴7.5目

    if black > white + komi:
        return f"黑方胜！黑{black}子 vs 白{white}子 (贴{komi})"
    else:
        return f"白方胜！黑{black}子 vs 白{white}子 (贴{komi})"


if __name__ == '__main__':
    main()
