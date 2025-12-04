"""
测试游戏模块

这些测试用例应该与 Go 版本的测试保持一致。
"""

import pytest
from core.game import Game, KoViolationError
from core.board import Player, Point


def test_new_game():
    """测试新游戏的初始状态"""
    game = Game()
    
    assert game.next_player == Player.BLACK
    assert not game.game_over
    assert game.passes == 0
    assert len(game.history) == 1


def test_play_move_valid():
    """测试合法的落子"""
    game = Game()
    point = Point(3, 3)
    
    game.play_move(point)
    
    assert game.board.grid[point.x][point.y] == Player.BLACK
    assert game.next_player == Player.WHITE
    assert game.passes == 0


def test_play_move_invalid():
    """测试非法落子"""
    game = Game()
    point = Point(3, 3)
    
    # 第一次落子成功
    game.play_move(point)
    
    # 尝试在同一位置再次落子
    from core.board import PointNotEmptyError
    with pytest.raises(PointNotEmptyError):
        game.play_move(point)
    
    # 确认轮次没有改变
    assert game.next_player == Player.WHITE


def test_ko_rule_simple():
    """测试简单的劫争（Ko）规则"""
    game = Game()
    
    # 设置劫争局面
    game.board.grid[0][1] = Player.BLACK
    game.board.grid[1][0] = Player.BLACK
    game.board.grid[2][1] = Player.BLACK
    
    game.board.grid[0][2] = Player.WHITE
    game.board.grid[1][1] = Player.WHITE
    game.board.grid[1][3] = Player.WHITE
    game.board.grid[2][2] = Player.WHITE
    
    game.history[game.board.state_hash()] = True
    game.next_player = Player.BLACK
    
    # 黑棋提劫
    game.play_move(Point(1, 2))
    
    # 验证白子被提掉
    assert game.board.grid[1][1] == Player.EMPTY
    assert game.captures_by_black == 1
    
    # 白棋尝试立即提回来（应该违反 Ko 规则）
    with pytest.raises(KoViolationError):
        game.play_move(Point(1, 1))
    
    # 验证棋盘状态没有改变
    assert game.board.grid[1][1] == Player.EMPTY
    assert game.next_player == Player.WHITE


def test_ko_rule_allowed_after_other_move():
    """测试在其他地方落子后可以重新提劫"""
    game = Game()
    
    # 设置劫争局面
    game.board.grid[0][1] = Player.BLACK
    game.board.grid[1][0] = Player.BLACK
    game.board.grid[2][1] = Player.BLACK
    
    game.board.grid[0][2] = Player.WHITE
    game.board.grid[1][1] = Player.WHITE
    game.board.grid[1][3] = Player.WHITE
    game.board.grid[2][2] = Player.WHITE
    
    game.history[game.board.state_hash()] = True
    game.next_player = Player.BLACK
    
    # 黑棋提劫
    game.play_move(Point(1, 2))
    
    # 白棋在其他地方落子
    game.play_move(Point(10, 10))
    
    # 黑棋在其他地方落子
    game.play_move(Point(10, 11))
    
    # 现在白棋可以提回劫了
    game.play_move(Point(1, 1))
    
    assert game.board.grid[1][1] == Player.WHITE


def test_pass_turn():
    """测试虚手功能"""
    game = Game()
    
    # 第一次虚手
    game.pass_turn()
    
    assert game.passes == 1
    assert game.next_player == Player.WHITE
    assert not game.game_over
    
    # 第二次虚手（连续虚手）
    game.pass_turn()
    
    assert game.passes == 2
    assert game.game_over


def test_pass_turn_reset_after_move():
    """测试落子后虚手计数重置"""
    game = Game()
    
    # 虚手一次
    game.pass_turn()
    assert game.passes == 1
    
    # 落子
    game.play_move(Point(3, 3))
    
    # 虚手计数应该被重置
    assert game.passes == 0


def test_capture_tracking():
    """测试提子计数"""
    game = Game()
    
    # 设置提子场景
    game.board.grid[0][1] = Player.BLACK
    game.board.grid[1][0] = Player.BLACK
    game.board.grid[1][2] = Player.BLACK
    game.board.grid[1][1] = Player.WHITE
    
    game.history[game.board.state_hash()] = True
    game.next_player = Player.BLACK
    
    # 黑棋落子提掉白子
    game.play_move(Point(2, 1))
    
    # 验证白子被提掉
    assert game.board.grid[1][1] == Player.EMPTY
    
    # 验证提子计数
    assert game.captures_by_black == 1
    assert game.captures_by_white == 0


def test_calculate_score_game_not_over():
    """测试游戏未结束时不能计分"""
    game = Game()
    
    with pytest.raises(Exception):
        game.calculate_score()


def test_calculate_score_empty_board():
    """测试空棋盘的计分"""
    game = Game()
    game.game_over = True
    
    result = game.calculate_score()
    
    # 空棋盘：白方有贴子，所以白方应该赢
    assert result.winner == Player.WHITE


def test_get_legal_moves():
    """测试获取合法落子位置"""
    game = Game()
    
    # 新游戏应该有 361 个合法位置
    legal_moves = game.get_legal_moves()
    assert len(legal_moves) == 361
    
    # 落一子后应该减少一个
    game.play_move(Point(3, 3))
    legal_moves = game.get_legal_moves()
    assert len(legal_moves) == 360

