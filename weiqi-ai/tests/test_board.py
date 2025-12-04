"""
测试棋盘模块

这些测试用例应该与 Go 版本的测试保持一致。
"""

import pytest
from core.board import Board, Player, Point
from core.board import PointOutOfBoundsError, PointNotEmptyError, SuicideMoveError


def test_new_board():
    """测试新棋盘是否为空"""
    board = Board()
    for i in range(19):
        for j in range(19):
            assert board.grid[i][j] == Player.EMPTY


def test_place_stone_valid_move():
    """测试合法的落子"""
    board = Board()
    point = Point(5, 5)
    
    captures = board.place_stone(Player.BLACK, point)
    
    assert captures == 0
    assert board.grid[point.x][point.y] == Player.BLACK


def test_place_stone_not_empty():
    """测试在已有棋子的位置落子"""
    board = Board()
    point = Point(10, 10)
    
    # 第一次落子
    board.place_stone(Player.BLACK, point)
    
    # 尝试在同一位置再次落子
    with pytest.raises(PointNotEmptyError):
        board.place_stone(Player.WHITE, point)


def test_capture_single_stone():
    """测试提掉单个子"""
    board = Board()
    
    # 设置一个被包围的白子
    # . X .
    # X O X
    # . X .
    board.grid[0][1] = Player.BLACK
    board.grid[1][0] = Player.BLACK
    board.grid[1][2] = Player.BLACK
    board.grid[1][1] = Player.WHITE
    
    # 黑棋在 (2,1) 落子，完成包围并提子
    captures = board.place_stone(Player.BLACK, Point(2, 1))
    
    assert captures == 1
    assert board.grid[1][1] == Player.EMPTY


def test_capture_multiple_stones():
    """测试提掉一个棋块"""
    board = Board()
    
    # 设置一个被包围的白棋块
    # X X X .
    # X O O X
    # X X X .
    board.grid[0][0] = Player.BLACK
    board.grid[0][1] = Player.BLACK
    board.grid[0][2] = Player.BLACK
    board.grid[1][0] = Player.BLACK
    board.grid[1][2] = Player.BLACK
    board.grid[2][0] = Player.BLACK
    board.grid[2][2] = Player.BLACK
    
    board.grid[1][1] = Player.WHITE
    board.grid[2][1] = Player.WHITE
    
    # 黑棋在 (3,1) 落子，提掉白棋块
    captures = board.place_stone(Player.BLACK, Point(3, 1))
    
    assert captures == 2
    assert board.grid[1][1] == Player.EMPTY
    assert board.grid[2][1] == Player.EMPTY


def test_suicide_simple():
    """测试简单的自杀手（非法）"""
    board = Board()
    
    # . X .
    # X . X
    # . X .
    board.grid[0][1] = Player.BLACK
    board.grid[1][0] = Player.BLACK
    board.grid[1][2] = Player.BLACK
    board.grid[2][1] = Player.BLACK
    
    # 白棋试图在 (1,1) 这个禁入点落子
    with pytest.raises(SuicideMoveError):
        board.place_stone(Player.WHITE, Point(1, 1))
    
    # 确认棋盘没有被改变
    assert board.grid[1][1] == Player.EMPTY


def test_suicide_with_capture_allowed():
    """测试看似自杀但因提子而合法的落子"""
    board = Board()
    
    # . B W .
    # B W . W
    # . B W .
    board.grid[0][1] = Player.BLACK
    board.grid[1][0] = Player.BLACK
    board.grid[2][1] = Player.BLACK
    
    board.grid[0][2] = Player.WHITE
    board.grid[1][1] = Player.WHITE
    board.grid[1][3] = Player.WHITE
    board.grid[2][2] = Player.WHITE
    
    # 黑棋在 (2,1) 落子，提掉白棋块
    captures = board.place_stone(Player.BLACK, Point(2, 1))
    
    assert captures == 1
    assert board.grid[2][1] == Player.BLACK
    assert board.grid[1][1] == Player.EMPTY


def test_state_hash():
    """测试棋盘状态哈希"""
    board1 = Board()
    board2 = Board()
    
    # 空棋盘的哈希应该相同
    assert board1.state_hash() == board2.state_hash()
    
    # 落子后哈希应该不同
    board1.place_stone(Player.BLACK, Point(3, 3))
    assert board1.state_hash() != board2.state_hash()
    
    # 相同的棋盘状态应该有相同的哈希
    board2.place_stone(Player.BLACK, Point(3, 3))
    assert board1.state_hash() == board2.state_hash()


def test_clone():
    """测试棋盘克隆"""
    board1 = Board()
    board1.place_stone(Player.BLACK, Point(3, 3))
    
    board2 = board1.clone()
    
    # 克隆的棋盘应该有相同的状态
    assert board2.grid[3][3] == Player.BLACK
    
    # 修改克隆不应影响原棋盘
    board2.place_stone(Player.WHITE, Point(4, 4))
    assert board1.grid[4][4] == Player.EMPTY
    assert board2.grid[4][4] == Player.WHITE

