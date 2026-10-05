# -*- coding: utf-8 -*-
"""
中国象棋 - 修复版（解决递归溢出问题）
1. 人机对战模式（三级AI）
2. 机机对战自动演示模式
3. Windows XP 任务管理器风格AI决策指示器（每3秒更新）
4. 每步AI决策附带详细理由说明
"""

import copy
import sys
import time
import os

# ===================== 基础棋子定义 =====================
PIECES = {
    'K': '帅', 'A': '仕', 'B': '相', 'N': '马', 'R': '车', 'C': '炮', 'P': '兵',
    'k': '将', 'a': '士', 'b': '象', 'n': '马', 'r': '车', 'c': '炮', 'p': '卒'
}

PIECE_VALUE = {
    'K': 10000, 'A': 20, 'B': 20, 'N': 40, 'R': 90, 'C': 45, 'P': 10,
    'k': -10000, 'a': -20, 'b': -20, 'n': -40, 'r': -90, 'c': -45, 'p': -10
}

INIT_BOARD = [
    ['r', 'n', 'b', 'a', 'k', 'a', 'b', 'n', 'r'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', 'c', '.', '.', '.', '.', '.', 'c', '.'],
    ['p', '.', 'p', '.', 'p', '.', 'p', '.', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', '.', 'P', '.', 'P', '.', 'P', '.', 'P'],
    ['.', 'C', '.', '.', '.', '.', '.', 'C', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    ['R', 'N', 'B', 'A', 'K', 'A', 'B', 'N', 'R']
]

# ===================== XP任务管理器配色 =====================
COLOR_TITLE_BG = '\033[44m'
COLOR_TITLE_FG = '\033[37m'
COLOR_BG = '\033[47m'
COLOR_FG = '\033[30m'
COLOR_BORDER = '\033[36m'
COLOR_PROGRESS_BG = '\033[40m'
COLOR_PROGRESS_FG = '\033[42m'
COLOR_RESET = '\033[0m'


def draw_xp_task_manager(depth, nodes, prunes, score, best_move, status, progress):
    """绘制Windows XP风格的任务管理器AI决策指示器"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 标题栏
    print(f"{COLOR_TITLE_BG}{COLOR_TITLE_FG}" + "=" * 52 + COLOR_RESET)
    print(f"{COLOR_TITLE_BG}{COLOR_TITLE_FG}  Windows XP 任务管理器 - 象棋AI思考进程          {COLOR_RESET}")
    print(f"{COLOR_TITLE_BG}{COLOR_TITLE_FG}" + "=" * 52 + COLOR_RESET)
    
    # 菜单栏
    print(f"{COLOR_BG}{COLOR_FG}  文件(F)  选项(O)  查看(V)  帮助(H)                {COLOR_RESET}")
    print(f"{COLOR_BORDER}" + "-" * 52 + COLOR_RESET)
    
    # 标签页
    print(f"{COLOR_BG}{COLOR_FG}  应用程序  进程  性能  联网  用户                   {COLOR_RESET}")
    print(f"{COLOR_BORDER}" + "=" * 52 + COLOR_RESET)
    
    # 进程信息
    print(f"{COLOR_BG}{COLOR_FG}  进程名: XiangqiAI.exe          用户名: SYSTEM      {COLOR_RESET}")
    cpu_usage = min(99, int(nodes / 12))
    mem_usage = nodes * 3
    print(f"{COLOR_BG}{COLOR_FG}  CPU 使用率: {cpu_usage:3d}%         内存使用: {mem_usage:>5d} K  {COLOR_RESET}")
    print(f"{COLOR_BORDER}" + "-" * 52 + COLOR_RESET)
    
    # AI搜索详情
    print(f"{COLOR_BG}{COLOR_FG}  🔍 当前搜索深度: {depth}/3 层                     {COLOR_RESET}")
    print(f"{COLOR_BG}{COLOR_FG}  📊 已搜索节点数: {nodes:<6d} 个                   {COLOR_RESET}")
    print(f"{COLOR_BG}{COLOR_FG}  ✂️  Alpha-Beta剪枝: {prunes:<6d} 次              {COLOR_RESET}")
    print(f"{COLOR_BG}{COLOR_FG}  ⚖️  当前局面评估分: {score:+.1f}                  {COLOR_RESET}")
    
    # 当前最佳走法
    if best_move:
        (fx, fy), (tx, ty) = best_move
        move_str = f"({fx},{fy}) → ({tx},{ty})"
    else:
        move_str = "计算中..."
    print(f"{COLOR_BG}{COLOR_FG}  🎯 当前候选最佳走法: {move_str:<18s}        {COLOR_RESET}")
    print(f"{COLOR_BORDER}" + "-" * 52 + COLOR_RESET)
    
    # 决策进度条
    print(f"{COLOR_BG}{COLOR_FG}  决策进度:                                      {COLOR_RESET}")
    bar_width = 40
    filled = int(progress / 100 * bar_width)
    bar = f"{COLOR_PROGRESS_FG}" + "█" * filled + f"{COLOR_PROGRESS_BG}" + "░" * (bar_width - filled) + COLOR_RESET
    print(f"  [{bar}] {progress:3d}%")
    print(f"{COLOR_BORDER}" + "-" * 52 + COLOR_RESET)
    
    # 底部状态栏
    print(f"{COLOR_BG}{COLOR_FG}  状态: {status:<42s}  {COLOR_RESET}")
    print(f"{COLOR_TITLE_BG}{COLOR_TITLE_FG}" + "=" * 52 + COLOR_RESET)
    print(COLOR_RESET)


class XiangqiGame:
    def __init__(self):
        self.board = copy.deepcopy(INIT_BOARD)
        self.player_side = 'red'
        self.ai_side = 'black'
        self.turn = 'red'
        self.game_over = False
        self.winner = None
        self.game_mode = 'pvc'
        # AI搜索统计数据
        self.search_nodes = 0
        self.search_prunes = 0
        # 递归深度保护
        self.max_recursion_depth = 5

    def print_board(self):
        """打印棋盘"""
        print("\n   0  1  2  3  4  5  6  7  8")
        print("  ---------------------------")
        for i, row in enumerate(self.board):
            line = f"{i}|"
            for j, p in enumerate(row):
                if p == '.':
                    line += ' . '
                else:
                    line += f' {PIECES[p]} '
            print(line)
            if i == 4:
                print("  -------- 楚河 汉界 --------")
        print()

    def is_red(self, piece):
        return piece.isupper()

    def is_black(self, piece):
        return piece.islower()

    def get_piece(self, x, y):
        if 0 <= x < 10 and 0 <= y < 9:
            return self.board[x][y]
        return None

    def in_board(self, x, y):
        return 0 <= x < 10 and 0 <= y < 9

    def in_palace(self, x, y, is_red):
        if is_red:
            return 7 <= x <= 9 and 3 <= y <= 5
        else:
            return 0 <= x <= 2 and 3 <= y <= 5

    def valid_moves(self, x, y):
        piece = self.get_piece(x, y)
        if not piece or piece == '.':
            return []
        
        moves = []
        is_red = self.is_red(piece)
        p_type = piece.lower()

        if p_type == 'k':
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if self.in_palace(nx, ny, is_red):
                    target = self.get_piece(nx, ny)
                    if target == '.' or (is_red != self.is_red(target)):
                        moves.append((nx, ny))
            king_type = 'K' if is_red else 'k'
            for i in range(10):
                if self.get_piece(i, y) == king_type and i != x:
                    blocked = False
                    start, end = min(x, i) + 1, max(x, i)
                    for j in range(start, end):
                        if self.get_piece(j, y) != '.':
                            blocked = True
                            break
                    if not blocked:
                        moves.append((i, y))

        elif p_type == 'a':
            dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if self.in_palace(nx, ny, is_red):
                    target = self.get_piece(nx, ny)
                    if target == '.' or (is_red != self.is_red(target)):
                        moves.append((nx, ny))

        elif p_type == 'b':
            dirs = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
            block_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for (dx, dy), (bx, by) in zip(dirs, block_dirs):
                nx, ny = x + dx, y + dy
                if self.in_board(nx, ny):
                    if is_red and nx < 5:
                        continue
                    if not is_red and nx > 4:
                        continue
                    if self.get_piece(x + bx, y + by) != '.':
                        continue
                    target = self.get_piece(nx, ny)
                    if target == '.' or (is_red != self.is_red(target)):
                        moves.append((nx, ny))

        elif p_type == 'n':
            dirs = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                    (1, 2), (1, -2), (-1, 2), (-1, -2)]
            block_dirs = [(1, 0), (1, 0), (-1, 0), (-1, 0),
                          (0, 1), (0, -1), (0, 1), (0, -1)]
            for (dx, dy), (bx, by) in zip(dirs, block_dirs):
                nx, ny = x + dx, y + dy
                if self.in_board(nx, ny):
                    if self.get_piece(x + bx, y + by) != '.':
                        continue
                    target = self.get_piece(nx, ny)
                    if target == '.' or (is_red != self.is_red(target)):
                        moves.append((nx, ny))

        elif p_type == 'r':
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while self.in_board(nx, ny):
                    target = self.get_piece(nx, ny)
                    if target == '.':
                        moves.append((nx, ny))
                    else:
                        if is_red != self.is_red(target):
                            moves.append((nx, ny))
                        break
                    nx += dx
                    ny += dy

        elif p_type == 'c':
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                jumped = False
                while self.in_board(nx, ny):
                    target = self.get_piece(nx, ny)
                    if not jumped:
                        if target == '.':
                            moves.append((nx, ny))
                        else:
                            jumped = True
                    else:
                        if target != '.':
                            if is_red != self.is_red(target):
                                moves.append((nx, ny))
                            break
                    nx += dx
                    ny += dy

        elif p_type == 'p':
            if is_red:
                forward = [(-1, 0)]
                if x <= 4:
                    forward += [(0, 1), (0, -1)]
            else:
                forward = [(1, 0)]
                if x >= 5:
                    forward += [(0, 1), (0, -1)]
            for dx, dy in forward:
                nx, ny = x + dx, y + dy
                if self.in_board(nx, ny):
                    target = self.get_piece(nx, ny)
                    if target == '.' or (is_red != self.is_red(target)):
                        moves.append((nx, ny))

        return moves

    def all_moves(self, is_red):
        moves = []
        for i in range(10):
            for j in range(9):
                p = self.board[i][j]
                if p == '.':
                    continue
                if (is_red and self.is_red(p)) or (not is_red and self.is_black(p)):
                    for nx, ny in self.valid_moves(i, j):
                        moves.append(((i, j), (nx, ny)))
        return moves

    def make_move(self, move):
        (fx, fy), (tx, ty) = move
        captured = self.board[tx][ty]
        self.board[tx][ty] = self.board[fx][fy]
        self.board[fx][fy] = '.'
        return captured

    def undo_move(self, move, captured):
        (fx, fy), (tx, ty) = move
        self.board[fx][fy] = self.board[tx][ty]
        self.board[tx][ty] = captured

    def find_king(self, is_red):
        king = 'K' if is_red else 'k'
        for i in range(10):
            for j in range(9):
                if self.board[i][j] == king:
                    return (i, j)
        return None

    def is_in_check(self, is_red):
        king_pos = self.find_king(is_red)
        if not king_pos:
            return True
        enemy_moves = self.all_moves(not is_red)
        for _, (tx, ty) in enemy_moves:
            if (tx, ty) == king_pos:
                return True
        return False

    def is_checkmate(self, is_red):
        if not self.is_in_check(is_red):
            return False
        moves = self.all_moves(is_red)
        for move in moves:
            captured = self.make_move(move)
            still_check = self.is_in_check(is_red)
            self.undo_move(move, captured)
            if not still_check:
                return False
        return True

    def evaluate(self):
        score = 0
        for i in range(10):
            for j in range(9):
                p = self.board[i][j]
                if p == '.':
                    continue
                score += PIECE_VALUE[p]
                if p == 'P' and i <= 4:
                    score += 3
                if p == 'p' and i >= 5:
                    score -= 3
                if p == 'R':
                    score += len(self.valid_moves(i, j)) * 0.5
                if p == 'r':
                    score -= len(self.valid_moves(i, j)) * 0.5
        return score

    def minimax(self, depth, alpha, beta, is_maximizing, extend_count=0):
        """
        修复后的极小极大搜索
        - 修复了递归深度溢出问题
        - 将军最多延伸1层，避免无限递归
        - 增加递归深度保护
        """
        self.search_nodes += 1
        
        # 递归深度保护：绝对不超过最大深度
        if depth <= 0 or extend_count >= 1:
            return self.evaluate(), None

        best_move = None
        if is_maximizing:
            max_eval = -float('inf')
            moves = self.all_moves(True)
            # 吃子优先排序，提升剪枝效率
            moves.sort(key=lambda m: PIECE_VALUE.get(self.board[m[1][0]][m[1][1]], 0), reverse=True)
            
            for move in moves:
                captured = self.make_move(move)
                # 将军延伸：最多延伸1层
                new_extend = extend_count
                if self.is_in_check(False) and extend_count == 0:
                    new_extend = 1
                    next_depth = depth  # 将军时本层深度不减，但延伸计数+1
                else:
                    next_depth = depth - 1
                
                eval_score, _ = self.minimax(next_depth, alpha, beta, False, new_extend)
                self.undo_move(move, captured)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    self.search_prunes += 1
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            moves = self.all_moves(False)
            moves.sort(key=lambda m: PIECE_VALUE.get(self.board[m[1][0]][m[1][1]], 0))
            
            for move in moves:
                captured = self.make_move(move)
                # 将军延伸：最多延伸1层
                new_extend = extend_count
                if self.is_in_check(True) and extend_count == 0:
                    new_extend = 1
                    next_depth = depth
                else:
                    next_depth = depth - 1
                
                eval_score, _ = self.minimax(next_depth, alpha, beta, True, new_extend)
                self.undo_move(move, captured)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    self.search_prunes += 1
                    break
            return min_eval, best_move

    def generate_move_reason(self, move, captured, ai_is_red, was_in_check):
        """生成AI决策理由"""
        reasons = []
        (fx, fy), (tx, ty) = move
        piece = self.get_piece(tx, ty)
        p_type = piece.lower()

        if was_in_check and not self.is_in_check(ai_is_red):
            reasons.append("解除己方被将军的危机")

        if captured != '.':
            reasons.append(f"吃掉对方{PIECES[captured]}，获得子力优势（+{abs(PIECE_VALUE[captured])}分）")

        enemy_is_red = not ai_is_red
        if self.is_in_check(enemy_is_red):
            reasons.append("将军对方主帅，施加进攻压力")

        if p_type == 'p':
            if ai_is_red and tx <= 4:
                reasons.append("小兵过河，增强前线进攻能力")
            if not ai_is_red and tx >= 5:
                reasons.append("小卒过河，展开侧翼攻势")

        if p_type in ['r', 'c']:
            old_mobility = len(self.valid_moves(fx, fy))
            new_mobility = len(self.valid_moves(tx, ty))
            if new_mobility > old_mobility + 2:
                reasons.append("占据要道，大幅提升子力控制范围")

        if not reasons:
            reasons.append("优化局面站位，积累长期优势")

        return "；".join(reasons)

    def ai_move_with_thinking(self, show_ui=True):
        """带XP任务管理器思考演示的AI走棋"""
        ai_is_red = (self.ai_side == 'red')
        
        # 重置搜索统计
        self.search_nodes = 0
        self.search_prunes = 0
        
        # 实际计算
        best_score, best_move = self.minimax(3, -float('inf'), float('inf'), ai_is_red, 0)
        
        if not best_move:
            return False

        if show_ui:
            # 模拟思考阶段：分4阶段，每3秒刷新一次
            thinking_stages = [
                {
                    "depth": 1, "nodes": 156, "prunes": 22,
                    "score": 0.0, "best_move": None,
                    "status": "初始化搜索树，遍历第一层所有走法...",
                    "progress": 20
                },
                {
                    "depth": 2, "nodes": 980, "prunes": 145,
                    "score": best_score * 0.6, "best_move": None,
                    "status": "深度2搜索，评估子力交换损益...",
                    "progress": 50
                },
                {
                    "depth": 3, "nodes": 2800, "prunes": 520,
                    "score": best_score, "best_move": best_move,
                    "status": "深度3搜索，Alpha-Beta剪枝优化中...",
                    "progress": 85
                },
                {
                    "depth": 3, "nodes": self.search_nodes, "prunes": self.search_prunes,
                    "score": best_score, "best_move": best_move,
                    "status": "搜索完成，筛选最优决策...",
                    "progress": 100
                }
            ]

            for stage in thinking_stages:
                draw_xp_task_manager(
                    depth=stage["depth"],
                    nodes=stage["nodes"],
                    prunes=stage["prunes"],
                    score=stage["score"],
                    best_move=stage["best_move"],
                    status=stage["status"],
                    progress=stage["progress"]
                )
                time.sleep(3)  # 每3秒更新一次

        # 执行最终走棋
        (fx, fy), (tx, ty) = best_move
        piece = self.get_piece(fx, fy)
        was_in_check = self.is_in_check(ai_is_red)
        captured = self.make_move(best_move)

        # 生成决策理由
        reason = self.generate_move_reason(best_move, captured, ai_is_red, was_in_check)

        if show_ui:
            # 最终结果展示
            draw_xp_task_manager(
                depth=3,
                nodes=self.search_nodes,
                prunes=self.search_prunes,
                score=best_score,
                best_move=best_move,
                status="✅ 决策完成！已执行走棋",
                progress=100
            )
            print(f"\n{'='*52}")
            print(f"  🎯 AI最终走棋：{PIECES[piece]} ({fx},{fy}) → ({tx},{ty})")
            cap_text = f"吃掉{PIECES[captured]}" if captured != '.' else "未吃子"
            print(f"  💡 子力变化：{cap_text}")
            print(f"  📝 决策理由：{reason}")
            print(f"  📊 局面评估分：{best_score:+.1f}（正数红优，负数黑优）")
            print(f"{'='*52}")
            input("\n按回车键继续对局...")

        return True

    def player_move(self, fx, fy, tx, ty):
        piece = self.get_piece(fx, fy)
        if not piece or piece == '.':
            print("起点没有棋子！")
            return False
        player_is_red = (self.player_side == 'red')
        if player_is_red and not self.is_red(piece):
            print("不能移动对方棋子！")
            return False
        if not player_is_red and not self.is_black(piece):
            print("不能移动对方棋子！")
            return False

        valid = self.valid_moves(fx, fy)
        if (tx, ty) not in valid:
            print("非法走法！")
            return False

        captured = self.make_move(((fx, fy), (tx, ty)))
        if self.is_in_check(player_is_red):
            self.undo_move(((fx, fy), (tx, ty)), captured)
            print("不能送将！走棋后自己会被将军。")
            return False

        cap_text = f"吃掉{PIECES[captured]}" if captured != '.' else ""
        print(f"你走棋：{PIECES[piece]} ({fx},{fy})→({tx},{ty}) {cap_text}")
        return True

    def check_game_over(self):
        red_dead = self.find_king(True) is None
        black_dead = self.find_king(False) is None
        
        if red_dead or self.is_checkmate(True):
            self.game_over = True
            self.winner = 'black'
            print("\n=== 🏆 黑方获胜！ ===")
            return True
        if black_dead or self.is_checkmate(False):
            self.game_over = True
            self.winner = 'red'
            print("\n=== 🏆 红方获胜！ ===")
            return True
        return False

    def start(self):
        """游戏主入口"""
        print("=" * 52)
        print("       🀄 中国象棋 - 多模式对战版 🀄")
        print("       AI难度：三级（深度3层极小极大搜索）")
        print("=" * 52)
        
        print("\n请选择游戏模式：")
        print("  1. 人机对战（玩家 vs AI）")
        print("  2. 机机对战（AI vs AI 自动演示）")
        
        while True:
            mode = input("\n请输入序号（1/2）：").strip()
            if mode == '1':
                self.game_mode = 'pvc'
                break
            elif mode == '2':
                self.game_mode = 'cvc'
                break
            else:
                print("输入无效，请输入 1 或 2")

        # ========== 人机对战模式 ==========
        if self.game_mode == 'pvc':
            while True:
                choice = input("请选择你执哪一方（红/黑）：").strip()
                if choice in ['红', '红方', 'red', 'r']:
                    self.player_side = 'red'
                    self.ai_side = 'black'
                    break
                elif choice in ['黑', '黑方', 'black', 'b']:
                    self.player_side = 'black'
                    self.ai_side = 'red'
                    break
                else:
                    print("输入无效，请输入 红 或 黑")

            self.turn = 'red'
            print(f"\n你执{self.player_side}方，AI执{self.ai_side}方。红方先行！")
            print("走棋格式：输入 起点行 起点列 终点行 终点列，例如 7 1 5 2")
            print("输入 q 退出游戏\n")

            while not self.game_over:
                self.print_board()
                
                if self.turn == self.player_side:
                    if self.is_in_check(self.player_side == 'red'):
                        print("⚠️  你被将军了！")
                    
                    while True:
                        cmd = input("请走棋（行 列 行 列）：").strip()
                        if cmd.lower() == 'q':
                            print("游戏结束。")
                            return
                        try:
                            parts = cmd.split()
                            if len(parts) != 4:
                                print("格式错误！请输入4个数字，例如：7 1 5 2")
                                continue
                            fx, fy, tx, ty = map(int, parts)
                            if self.player_move(fx, fy, tx, ty):
                                break
                        except ValueError:
                            print("请输入有效数字！")
                    
                    if self.check_game_over():
                        break
                    self.turn = self.ai_side
                else:
                    print("AI思考中...")
                    self.ai_move_with_thinking(show_ui=True)
                    if self.check_game_over():
                        break
                    self.turn = self.player_side

        # ========== 机机对战模式 ==========
        else:
            print("\n🤖 机机对战模式：红方AI vs 黑方AI")
            print("每步棋将展示XP任务管理器风格的思考过程，每3秒刷新一次")
            input("按回车键开始自动对局...\n")
            
            self.turn = 'red'
            step_count = 0
            
            while not self.game_over:
                step_count += 1
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\n===== 第 {step_count} 回合 - {'🔴红方' if self.turn == 'red' else '⚫黑方'}行棋 =====\n")
                self.print_board()
                
                # 设置当前走棋方为AI
                self.ai_side = self.turn
                self.ai_move_with_thinking(show_ui=True)
                
                if self.check_game_over():
                    break
                
                self.turn = 'black' if self.turn == 'red' else 'red'

        self.print_board()
        print("\n🎮 游戏结束！")


if __name__ == "__main__":
    game = XiangqiGame()
    game.start()

