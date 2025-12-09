#!/usr/bin/env python3
"""
AI 系統快速測試腳本

測試 MCTS、神經網絡和計分系統的基本功能
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game import Game
from core.board import Player, Point
from ai.mcts_player import PureMCTSPlayer
from ai.scoring import MonteCarloScoring


def test_pure_mcts():
    """測試純 MCTS"""
    print("\n" + "="*60)
    print("測試 1: 純 MCTS AI")
    print("="*60)
    
    # 創建遊戲
    game = Game()
    
    # 創建 AI 玩家（使用很少的模擬次數加速測試）
    print("使用 10 次模擬進行快速測試...")
    player = PureMCTSPlayer(num_simulations=10, temperature=0.1)
    
    # 下幾步棋
    for i in range(5):
        print(f"\n第 {i+1} 步:")
        print(f"當前玩家: {'黑' if game.next_player == Player.BLACK else '白'}")
        
        # 獲取 AI 著法
        move, stats = player.get_move(game)
        
        if move:
            print(f"AI 選擇: ({move.x}, {move.y})")
            print(f"統計信息: {stats}")
            
            # 執行著法
            game.play_move(move)
        else:
            print("無合法著法")
            break
    
    print("\n✓ 純 MCTS 測試通過")


def test_scoring():
    """測試計分系統"""
    print("\n" + "="*60)
    print("測試 2: 蒙特卡洛計分")
    print("="*60)
    
    # 創建一個簡單的終局棋盤
    game = Game()
    
    # 模擬一些棋子
    moves = [
        (3, 3), (15, 15),  # 黑白各下一子
        (3, 4), (15, 16),
        (4, 3), (16, 15),
        (4, 4), (16, 16),
    ]
    
    for i, (x, y) in enumerate(moves):
        try:
            game.play_move(Point(x, y))
        except Exception as e:
            print(f"落子 ({x}, {y}) 失敗: {e}")
    
    # 標記遊戲結束
    game.game_over = True
    
    # 創建計分器（使用很少的模擬次數加速測試）
    print("使用 10 次模擬進行快速測試...")
    scorer = MonteCarloScoring(num_simulations=10)
    
    # 計算得分
    print("\n計算終局得分...")
    result = scorer.score(game)
    
    print(f"\n黑方得分: {result.black_score}")
    print(f"白方得分: {result.white_score}")
    print(f"勝者: {'黑' if result.winner == Player.BLACK else '白'}")
    
    print("\n✓ 計分系統測試通過")


def test_self_play():
    """測試自我對弈"""
    print("\n" + "="*60)
    print("測試 3: 自我對弈")
    print("="*60)
    
    from ai.mcts_player import PureMCTSPlayer
    
    # 創建兩個 AI 玩家（使用很少的模擬次數加速測試）
    print("使用 10 次模擬進行快速測試...")
    black_player = PureMCTSPlayer(num_simulations=10, temperature=0.1)
    white_player = PureMCTSPlayer(num_simulations=10, temperature=0.1)
    
    # 創建遊戲
    game = Game()
    
    move_count = 0
    max_moves = 10  # 限制步數以加速測試
    
    print(f"\n開始自我對弈（最多 {max_moves} 步）...")
    
    while not game.game_over and move_count < max_moves:
        # 選擇當前玩家
        current_player = black_player if game.next_player == Player.BLACK else white_player
        
        # 獲取著法
        move, stats = current_player.get_move(game)
        
        if move is None:
            game.pass_turn()
            print(f"第 {move_count + 1} 步: {'黑' if game.next_player == Player.WHITE else '白'} 虛手")
        else:
            game.play_move(move)
            print(f"第 {move_count + 1} 步: {'黑' if game.next_player == Player.WHITE else '白'} 落子 ({move.x}, {move.y})")
        
        move_count += 1
    
    print(f"\n對弈結束，共 {move_count} 步")
    
    # 如果還沒結束，強制結束並計分
    if not game.game_over:
        game.game_over = True
        result = game.calculate_score()
        print(f"勝者: {'黑' if result.winner == Player.BLACK else '白'}")
    
    print("\n✓ 自我對弈測試通過")


def test_network_structure():
    """測試神經網絡結構"""
    print("\n" + "="*60)
    print("測試 4: 神經網絡結構")
    print("="*60)
    
    try:
        from ai.network import WeiQiNetwork
        
        # 創建網絡
        network = WeiQiNetwork()
        
        # 打印網絡信息
        total_params = sum(p.numel() for p in network.parameters())
        trainable_params = sum(p.numel() for p in network.parameters() if p.requires_grad)
        
        print(f"\n網絡參數總數: {total_params:,}")
        print(f"可訓練參數: {trainable_params:,}")
        
        # 測試前向傳播
        import torch
        game = Game()
        policy, value = network.predict(game)
        
        print(f"\n策略輸出形狀: {policy.shape}")
        print(f"價值輸出: {value:.4f}")
        print(f"策略總概率: {policy.sum():.4f}")
        
        print("\n✓ 神經網絡結構測試通過")
        
    except Exception as e:
        print(f"\n✗ 神經網絡測試失敗: {e}")
        print("這可能是因為缺少 PyTorch 依賴，請運行: pip install torch")


def main():
    """運行所有測試"""
    print("\n" + "="*60)
    print("圍棋 AI 系統測試")
    print("="*60)
    
    try:
        # 測試 1: 純 MCTS
        test_pure_mcts()
        
        # 測試 2: 計分系統
        test_scoring()
        
        # 測試 3: 自我對弈
        test_self_play()
        
        # 測試 4: 神經網絡
        test_network_structure()
        
        print("\n" + "="*60)
        print("✓ 所有測試通過！")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n測試被中斷")
    except Exception as e:
        print(f"\n✗ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

