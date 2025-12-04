#!/usr/bin/env python3
"""
简单的测试脚本，不需要 pytest
用于快速验证核心功能
"""

import sys
sys.path.insert(0, '.')

from core.board import Board, Player, Point
from core.game import Game

def test_board_basic():
    """测试基本棋盘功能"""
    print("测试 1: 创建空棋盘...")
    board = Board()
    assert all(board.grid[i][j] == Player.EMPTY for i in range(19) for j in range(19))
    print("✓ 通过")
    
    print("测试 2: 落子...")
    captures = board.place_stone(Player.BLACK, Point(3, 3))
    assert board.grid[3][3] == Player.BLACK
    assert captures == 0
    print("✓ 通过")
    
    print("测试 3: 提子...")
    board2 = Board()
    board2.grid[0][1] = Player.BLACK
    board2.grid[1][0] = Player.BLACK
    board2.grid[1][2] = Player.BLACK
    board2.grid[1][1] = Player.WHITE
    
    captures = board2.place_stone(Player.BLACK, Point(2, 1))
    assert captures == 1
    assert board2.grid[1][1] == Player.EMPTY
    print("✓ 通过")

def test_game_basic():
    """测试基本游戏功能"""
    print("\n测试 4: 创建新游戏...")
    game = Game()
    assert game.next_player == Player.BLACK
    assert not game.game_over
    print("✓ 通过")
    
    print("测试 5: 落子...")
    game.play_move(Point(3, 3))
    assert game.board.grid[3][3] == Player.BLACK
    assert game.next_player == Player.WHITE
    print("✓ 通过")
    
    print("测试 6: 虚手...")
    game2 = Game()
    game2.pass_turn()
    assert game2.passes == 1
    game2.pass_turn()
    assert game2.game_over
    print("✓ 通过")
    
    print("测试 7: 获取合法落子...")
    game3 = Game()
    legal_moves = game3.get_legal_moves()
    assert len(legal_moves) == 361
    print(f"✓ 通过 (找到 {len(legal_moves)} 个合法位置)")

def test_ko_rule():
    """测试 Ko 规则"""
    print("\n测试 8: Ko 规则...")
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
    assert game.board.grid[1][1] == Player.EMPTY
    
    # 白棋尝试立即提回（应该失败）
    from core.game import KoViolationError
    try:
        game.play_move(Point(1, 1))
        assert False, "应该抛出 KoViolationError"
    except KoViolationError:
        pass
    
    print("✓ 通过")

if __name__ == "__main__":
    print("=" * 50)
    print("运行 Weiqi AI 核心功能测试")
    print("=" * 50)
    
    try:
        test_board_basic()
        test_game_basic()
        test_ko_rule()
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

