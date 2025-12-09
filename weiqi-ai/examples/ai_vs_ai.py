#!/usr/bin/env python3
"""
AI vs AI 對弈示例

演示兩個 AI 互相對弈
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from core.board import Player, Point
from ai.mcts_player import PureMCTSPlayer


def print_board_simple(game: Game):
    """簡單打印棋盤"""
    print("\n   ", end="")
    for i in range(19):
        print(f"{i%10}", end=" ")
    print()
    
    for i in range(19):
        print(f"{i:2d} ", end="")
        for j in range(19):
            if game.board.grid[i][j] == Player.EMPTY:
                print(".", end=" ")
            elif game.board.grid[i][j] == Player.BLACK:
                print("X", end=" ")
            else:
                print("O", end=" ")
        print()


def main():
    """主函數"""
    print("="*60)
    print("AI vs AI 對弈")
    print("="*60)
    
    # 創建兩個 AI 玩家
    print("\n正在初始化 AI...")
    
    # AI 1: 使用較多的模擬次數（更強）
    ai1 = PureMCTSPlayer(num_simulations=400, temperature=0.1)
    print("✓ AI 1 初始化完成 (400 次模擬)")
    
    # AI 2: 使用較少的模擬次數（較弱）
    ai2 = PureMCTSPlayer(num_simulations=200, temperature=0.1)
    print("✓ AI 2 初始化完成 (200 次模擬)")
    
    # 創建遊戲
    game = Game()
    
    # 遊戲循環
    move_count = 0
    max_moves = 200  # 限制最大步數
    
    print("\n開始對弈...")
    
    while not game.game_over and move_count < max_moves:
        move_count += 1
        
        # 選擇當前 AI
        if game.next_player == Player.BLACK:
            current_ai = ai1
            ai_name = "AI 1 (黑)"
        else:
            current_ai = ai2
            ai_name = "AI 2 (白)"
        
        # 獲取 AI 著法
        print(f"\n第 {move_count} 步: {ai_name} 思考中...", end="", flush=True)
        move, stats = current_ai.get_move(game)
        
        if move is None:
            game.pass_turn()
            print(f" 虛手")
        else:
            game.play_move(move)
            win_rate = stats.get('best_move_win_rate', 0)
            print(f" 落子 ({move.x}, {move.y}), 勝率: {win_rate:.2%}")
        
        # 每 10 步打印一次棋盤
        if move_count % 10 == 0:
            print_board_simple(game)
    
    # 遊戲結束
    print("\n" + "="*60)
    print("遊戲結束！")
    print("="*60)
    
    # 打印最終棋盤
    print_board_simple(game)
    
    # 計算得分
    if not game.game_over:
        game.game_over = True
    
    try:
        result = game.calculate_score()
        
        print(f"\n最終得分:")
        print(f"黑棋 (AI 1): {result.black_score:.2f}")
        print(f"白棋 (AI 2): {result.white_score:.2f}")
        
        if result.winner == Player.BLACK:
            print(f"\n🏆 AI 1 (黑棋) 獲勝！")
        else:
            print(f"\n🏆 AI 2 (白棋) 獲勝！")
        
        print(f"\n總步數: {move_count}")
    except Exception as e:
        print(f"\n計分失敗: {e}")


if __name__ == "__main__":
    main()

