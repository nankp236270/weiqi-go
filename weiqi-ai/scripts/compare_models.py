#!/usr/bin/env python3
"""
模型比較工具

比較兩個訓練好的模型的強度
"""

import sys
import os
import argparse

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from core.board import Player, Point
from ai.mcts_player import NeuralMCTSPlayer, PureMCTSPlayer


def compare_models(model1_path, model2_path, num_games=20, simulations=400):
    """
    比較兩個模型的強度
    
    Args:
        model1_path: 模型 1 的路徑（None 表示純 MCTS）
        model2_path: 模型 2 的路徑（None 表示純 MCTS）
        num_games: 對弈局數
        simulations: MCTS 模擬次數
    """
    print("="*60)
    print("模型比較")
    print("="*60)
    
    # 創建玩家
    print("\n初始化玩家...")
    
    if model1_path:
        print(f"玩家 1: 神經網絡 MCTS ({model1_path})")
        player1 = NeuralMCTSPlayer(model_path=model1_path, num_simulations=simulations)
    else:
        print(f"玩家 1: 純 MCTS")
        player1 = PureMCTSPlayer(num_simulations=simulations)
    
    if model2_path:
        print(f"玩家 2: 神經網絡 MCTS ({model2_path})")
        player2 = NeuralMCTSPlayer(model_path=model2_path, num_simulations=simulations)
    else:
        print(f"玩家 2: 純 MCTS")
        player2 = PureMCTSPlayer(num_simulations=simulations)
    
    print(f"\n將進行 {num_games} 局對弈...")
    print(f"MCTS 模擬次數: {simulations}")
    print("")
    
    # 統計
    wins1 = 0
    wins2 = 0
    draws = 0
    
    # 對弈
    for game_idx in range(num_games):
        print(f"對弈 {game_idx + 1}/{num_games}...", end=" ", flush=True)
        
        # 交替先手
        if game_idx % 2 == 0:
            black_player = player1
            white_player = player2
            player1_is_black = True
        else:
            black_player = player2
            white_player = player1
            player1_is_black = False
        
        # 創建遊戲
        game = Game()
        move_count = 0
        max_moves = 400
        
        # 對弈循環
        while not game.game_over and move_count < max_moves:
            # 選擇當前玩家
            current_player = black_player if game.next_player == Player.BLACK else white_player
            
            # 獲取著法
            move, _ = current_player.get_move(game)
            
            if move is None:
                game.pass_turn()
            else:
                try:
                    game.play_move(move)
                except:
                    game.pass_turn()
            
            move_count += 1
        
        # 判斷勝負
        if not game.game_over:
            game.game_over = True
        
        try:
            result = game.calculate_score()
            winner = result.winner
            
            if winner == Player.BLACK:
                if player1_is_black:
                    wins1 += 1
                    print("玩家 1 勝")
                else:
                    wins2 += 1
                    print("玩家 2 勝")
            else:
                if player1_is_black:
                    wins2 += 1
                    print("玩家 2 勝")
                else:
                    wins1 += 1
                    print("玩家 1 勝")
        except:
            draws += 1
            print("平局")
    
    # 打印結果
    print("\n" + "="*60)
    print("比較結果")
    print("="*60)
    
    win_rate1 = wins1 / num_games
    win_rate2 = wins2 / num_games
    
    print(f"\n玩家 1 勝: {wins1}/{num_games} ({win_rate1*100:.1f}%)")
    print(f"玩家 2 勝: {wins2}/{num_games} ({win_rate2*100:.1f}%)")
    print(f"平局: {draws}/{num_games} ({draws/num_games*100:.1f}%)")
    
    # 輸出勝率（供腳本使用）
    print(f"\nModel 1 win rate: {win_rate1:.3f}")
    print(f"Model 2 win rate: {win_rate2:.3f}")
    
    # 判斷哪個更強
    if wins1 > wins2:
        print(f"\n🏆 玩家 1 更強！")
        advantage = (wins1 - wins2) / num_games * 100
        print(f"   優勢: {advantage:.1f}%")
    elif wins2 > wins1:
        print(f"\n🏆 玩家 2 更強！")
        advantage = (wins2 - wins1) / num_games * 100
        print(f"   優勢: {advantage:.1f}%")
    else:
        print(f"\n🤝 兩者實力相當")
    
    return win_rate1


def main():
    parser = argparse.ArgumentParser(description="比較兩個圍棋 AI 模型的強度")
    
    parser.add_argument(
        "--model1",
        type=str,
        default=None,
        help="模型 1 的路徑（不指定則使用純 MCTS）"
    )
    
    parser.add_argument(
        "--model2",
        type=str,
        default=None,
        help="模型 2 的路徑（不指定則使用純 MCTS）"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=20,
        help="對弈局數（默認：20）"
    )
    
    parser.add_argument(
        "--simulations",
        type=int,
        default=400,
        help="MCTS 模擬次數（默認：400）"
    )
    
    args = parser.parse_args()
    
    if not args.model1 and not args.model2:
        print("錯誤: 至少需要指定一個模型")
        print("示例:")
        print("  # 比較訓練好的模型與純 MCTS")
        print("  python scripts/compare_models.py --model1 models/best_model_iter20.pth")
        print("")
        print("  # 比較兩個訓練好的模型")
        print("  python scripts/compare_models.py \\")
        print("    --model1 models/best_model_iter20.pth \\")
        print("    --model2 models/best_model_iter50.pth")
        sys.exit(1)
    
    try:
        compare_models(
            model1_path=args.model1,
            model2_path=args.model2,
            num_games=args.games,
            simulations=args.simulations
        )
    except KeyboardInterrupt:
        print("\n\n比較被中斷")
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

