"""
围棋棋盘模块

实现棋盘的基本操作，包括落子、提子、自杀禁令等。
必须与 Go 后端的实现保持 100% 一致。
"""

from enum import IntEnum
from typing import List, Tuple, Set
from dataclasses import dataclass
import hashlib


# 棋盘大小
BOARD_SIZE = 19


class Player(IntEnum):
    """玩家/棋子类型"""
    EMPTY = 0
    BLACK = 1
    WHITE = 2


@dataclass
class Point:
    """棋盘上的一个坐标点"""
    x: int
    y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y


class BoardError(Exception):
    """棋盘操作错误的基类"""
    pass


class PointOutOfBoundsError(BoardError):
    """坐标超出棋盘范围"""
    pass


class PointNotEmptyError(BoardError):
    """该位置已有棋子"""
    pass


class SuicideMoveError(BoardError):
    """自杀手（非法）"""
    pass


class Board:
    """
    围棋棋盘
    
    使用 19x19 的二维数组表示棋盘状态。
    坐标系：左上角为 (0, 0)，右下角为 (18, 18)
    """

    def __init__(self):
        """创建一个空棋盘"""
        self.grid: List[List[Player]] = [
            [Player.EMPTY for _ in range(BOARD_SIZE)]
            for _ in range(BOARD_SIZE)
        ]

    def place_stone(self, player: Player, point: Point) -> int:
        """
        在指定位置落子
        
        Args:
            player: 落子的玩家（黑或白）
            point: 落子位置
            
        Returns:
            提掉的对方棋子数量
            
        Raises:
            PointOutOfBoundsError: 坐标超出范围
            PointNotEmptyError: 该位置已有棋子
            SuicideMoveError: 自杀手（非法）
        """
        # 1. 基础合法性检查
        if not self._is_on_board(point):
            raise PointOutOfBoundsError(f"Point ({point.x}, {point.y}) is outside the board")
        
        # 注意：grid[行][列]，而 Point.x 是列，Point.y 是行
        if self.grid[point.y][point.x] != Player.EMPTY:
            raise PointNotEmptyError(f"Point ({point.x}, {point.y}) is not empty")

        # 2. 试探性落子
        self.grid[point.y][point.x] = player

        # 3. 检查并移除对方被提的子
        opponent = self._get_opponent(player)
        captured_stones: List[Point] = []
        
        for neighbor in self._get_neighbors(point):
            if self.grid[neighbor.y][neighbor.x] == opponent:
                group, liberties = self._find_group_and_liberties(neighbor)
                if liberties == 0:
                    captured_stones.extend(group)
                    for stone in group:
                        self.grid[stone.y][stone.x] = Player.EMPTY

        # 4. 自杀禁令检查
        _, new_liberties = self._find_group_and_liberties(point)
        if new_liberties == 0:
            # 这是自杀手，回滚所有操作
            self.grid[point.y][point.x] = Player.EMPTY
            for stone in captured_stones:
                self.grid[stone.y][stone.x] = opponent
            raise SuicideMoveError("Suicide move is not allowed")

        return len(captured_stones)

    def _is_on_board(self, point: Point) -> bool:
        """检查坐标是否在棋盘范围内"""
        return 0 <= point.x < BOARD_SIZE and 0 <= point.y < BOARD_SIZE

    def _get_neighbors(self, point: Point) -> List[Point]:
        """获取一个点的所有合法邻居（上下左右）"""
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dx, dy in directions:
            x, y = point.x + dx, point.y + dy
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                neighbors.append(Point(x, y))
        
        return neighbors

    def _get_opponent(self, player: Player) -> Player:
        """获取对手的颜色"""
        if player == Player.BLACK:
            return Player.WHITE
        return Player.BLACK

    def _find_group_and_liberties(self, start_point: Point) -> Tuple[List[Point], int]:
        """
        使用 BFS 寻找一个点所在的棋块及其气数
        
        Args:
            start_point: 起始点
            
        Returns:
            (棋块中的所有点, 气的数量)
        """
        if self.grid[start_point.y][start_point.x] == Player.EMPTY:
            return [], 0

        player = self.grid[start_point.y][start_point.x]
        group: List[Point] = []
        visited_in_group: Set[Point] = {start_point}
        visited_liberties: Set[Point] = set()
        queue: List[Point] = [start_point]

        while queue:
            current = queue.pop(0)
            group.append(current)

            for neighbor in self._get_neighbors(current):
                neighbor_value = self.grid[neighbor.y][neighbor.x]
                
                if neighbor_value == Player.EMPTY:
                    visited_liberties.add(neighbor)
                elif neighbor_value == player and neighbor not in visited_in_group:
                    visited_in_group.add(neighbor)
                    queue.append(neighbor)

        return group, len(visited_liberties)

    def state_hash(self) -> str:
        """
        生成当前棋盘状态的唯一哈希值
        
        用于实现全局同形再现禁令（Ko 规则）
        """
        state_str = ''.join(
            str(int(self.grid[i][j]))
            for i in range(BOARD_SIZE)
            for j in range(BOARD_SIZE)
        )
        return hashlib.md5(state_str.encode()).hexdigest()

    def clone(self) -> 'Board':
        """创建棋盘的深拷贝"""
        new_board = Board()
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def to_list(self) -> List[List[int]]:
        """将棋盘转换为二维列表（用于 JSON 序列化）"""
        return [[int(self.grid[i][j]) for j in range(BOARD_SIZE)] for i in range(BOARD_SIZE)]

    @classmethod
    def from_list(cls, grid_list: List[List[int]]) -> 'Board':
        """从二维列表创建棋盘"""
        board = cls()
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                board.grid[i][j] = Player(grid_list[i][j])
        return board

    def __str__(self) -> str:
        """返回棋盘的字符串表示（用于调试）"""
        lines = ["   " + " ".join(f"{i:2d}" for i in range(BOARD_SIZE))]
        
        for i in range(BOARD_SIZE):
            row = f"{i:2d} "
            for j in range(BOARD_SIZE):
                if self.grid[i][j] == Player.EMPTY:
                    row += " . "
                elif self.grid[i][j] == Player.BLACK:
                    row += " X "
                else:
                    row += " O "
            lines.append(row)
        
        return "\n".join(lines)

