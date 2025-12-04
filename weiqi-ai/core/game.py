"""
围棋游戏状态管理模块

管理整个对局的状态，包括棋盘、历史记录、Ko 规则等。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from .board import Board, Player, Point, BOARD_SIZE


class KoViolationError(Exception):
    """违反 Ko 规则（全局同形再现）"""
    pass


@dataclass
class ScoreResult:
    """计分结果"""
    black_score: float
    white_score: float
    winner: Player


class Game:
    """
    围棋游戏状态管理
    
    负责管理对局的完整状态，包括：
    - 棋盘状态
    - 历史记录（用于 Ko 规则）
    - 当前轮次
    - 虚手计数
    - 提子统计
    """

    def __init__(self):
        """创建新游戏"""
        self.board = Board()
        self.history: Dict[str, bool] = {}
        self.next_player = Player.BLACK
        self.passes = 0
        self.game_over = False
        self.captures_by_black = 0
        self.captures_by_white = 0
        
        # 记录初始状态
        initial_hash = self.board.state_hash()
        self.history[initial_hash] = True

    def play_move(self, point: Point) -> None:
        """
        执行一步落子
        
        Args:
            point: 落子位置
            
        Raises:
            Exception: 游戏已结束
            BoardError: 落子非法（越界、非空、自杀）
            KoViolationError: 违反 Ko 规则
        """
        if self.game_over:
            raise Exception("Game is over")

        # 1. 克隆棋盘，在副本上操作
        temp_board = self.board.clone()

        # 2. 在克隆的棋盘上尝试落子
        captures = temp_board.place_stone(self.next_player, point)

        # 3. 检查 Ko 规则
        new_hash = temp_board.state_hash()
        if new_hash in self.history:
            raise KoViolationError("Move violates Ko rule (positional superko)")

        # 4. 所有检查通过，正式更新游戏状态
        self.board = temp_board
        self.history[new_hash] = True
        
        # 更新提子统计
        if self.next_player == Player.BLACK:
            self.captures_by_black += captures
        else:
            self.captures_by_white += captures
        
        # 切换玩家
        self.next_player = Player.WHITE if self.next_player == Player.BLACK else Player.BLACK
        
        # 重置虚手计数
        self.passes = 0

    def pass_turn(self) -> None:
        """
        执行虚手
        
        Raises:
            Exception: 游戏已结束
        """
        if self.game_over:
            raise Exception("Game is over")

        self.passes += 1
        self.next_player = Player.WHITE if self.next_player == Player.BLACK else Player.BLACK

        # 连续两次虚手，游戏结束
        if self.passes >= 2:
            self.game_over = True

    def calculate_score(self) -> ScoreResult:
        """
        计算最终得分（中国规则）
        
        简化实现：假设所有棋子都是活棋
        
        Returns:
            ScoreResult: 包含双方得分和胜者
            
        Raises:
            Exception: 游戏未结束
        """
        if not self.game_over:
            raise Exception("Game is not over yet")

        black_stones = 0
        white_stones = 0
        black_territory = 0
        white_territory = 0

        visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]

        # 1. 计算双方棋子数
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board.grid[i][j] == Player.BLACK:
                    black_stones += 1
                elif self.board.grid[i][j] == Player.WHITE:
                    white_stones += 1

        # 2. 使用 BFS 计算领地
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board.grid[i][j] == Player.EMPTY and not visited[i][j]:
                    queue = [Point(i, j)]
                    visited[i][j] = True
                    area = 0
                    touches_black = False
                    touches_white = False

                    while queue:
                        current = queue.pop(0)
                        area += 1

                        for neighbor in self.board._get_neighbors(current):
                            nx, ny = neighbor.x, neighbor.y
                            
                            if self.board.grid[nx][ny] == Player.BLACK:
                                touches_black = True
                            elif self.board.grid[nx][ny] == Player.WHITE:
                                touches_white = True
                            elif not visited[nx][ny]:
                                visited[nx][ny] = True
                                queue.append(neighbor)

                    # 只被一方包围的空点才算领地
                    if touches_black and not touches_white:
                        black_territory += area
                    elif touches_white and not touches_black:
                        white_territory += area

        # 3. 计算最终得分
        black_score = float(black_stones + black_territory)
        white_score = float(white_stones + white_territory) + 3.75  # 贴子

        # 4. 判断胜负（黑方需要 > 184.25 才能赢）
        winner = Player.BLACK if black_score > 184.25 else Player.WHITE

        return ScoreResult(
            black_score=black_score,
            white_score=white_score,
            winner=winner
        )

    def get_legal_moves(self) -> List[Point]:
        """
        获取当前所有合法的落子位置
        
        Returns:
            合法落子位置的列表
        """
        legal_moves = []
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                point = Point(i, j)
                
                # 跳过已有棋子的位置
                if self.board.grid[i][j] != Player.EMPTY:
                    continue
                
                # 尝试在该位置落子
                try:
                    temp_board = self.board.clone()
                    temp_board.place_stone(self.next_player, point)
                    
                    # 检查 Ko 规则
                    new_hash = temp_board.state_hash()
                    if new_hash not in self.history:
                        legal_moves.append(point)
                except:
                    # 如果落子失败（自杀手等），跳过
                    pass
        
        return legal_moves

    def to_dict(self) -> dict:
        """将游戏状态转换为字典（用于 JSON 序列化）"""
        return {
            "board": self.board.to_list(),
            "next_player": int(self.next_player),
            "passes": self.passes,
            "game_over": self.game_over,
            "captures_by_black": self.captures_by_black,
            "captures_by_white": self.captures_by_white
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Game':
        """从字典创建游戏状态"""
        game = cls()
        game.board = Board.from_list(data["board"])
        game.next_player = Player(data["next_player"])
        game.passes = data["passes"]
        game.game_over = data["game_over"]
        game.captures_by_black = data.get("captures_by_black", 0)
        game.captures_by_white = data.get("captures_by_white", 0)
        
        # 重建历史记录
        game.history = {game.board.state_hash(): True}
        
        return game

