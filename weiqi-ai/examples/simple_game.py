#!/usr/bin/env python3
"""
簡單的人機對弈示例

演示如何使用 AI 進行人機對弈
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from core.board import Player, Point
from ai.mcts_player import PureMCTSPlayer


def print_board(game: Game):
    """打印棋盤"""
    print("\n   ", end="")
    for i in range(19):
        print(f"{i:2d}", end=" ")
    print()
    
    for i in range(19):
        print(f"{i:2d} ", end="")
        for j in range(19):
            if game.board.grid[i][j] == Player.EMPTY:
                print(" . ", end="")
            elif game.board.grid[i][j] == Player.BLACK:
                print(" X ", end="")
            else:
                print(" O ", end="")
        print()


def get_human_move() -> tuple:
    """獲取人類玩家的輸入"""
    while True:
        try:
            move_input = input("\n請輸入落子位置 (格式: x,y 或 'pass' 虛手): ").strip()
            
            if move_input.lower() == 'pass':
                return None
            
            x, y = map(int, move_input.split(','))
            
            if 0 <= x < 19 and 0 <= y < 19:
                return (x, y)
            else:
                print("坐標超出範圍，請重新輸入")
        except ValueError:
            print("輸入格式錯誤，請使用 'x,y' 格式")
        except KeyboardInterrupt:
            print("\n遊戲被中斷")
            sys.exit(0)


def main():
    """主函數"""
    print("="*60)
    print("圍棋人機對弈")
    print("="*60)
    
    # 選擇顏色
    while True:
        color = input("\n請選擇您的顏色 (black/white): ").strip().lower()
        if color in ['black', 'white']:
            break
        print("請輸入 'black' 或 'white'")
    
    human_color = Player.BLACK if color == 'black' else Player.WHITE
    ai_color = Player.WHITE if human_color == Player.BLACK else Player.BLACK
    
    print(f"\n您選擇了 {'黑棋' if human_color == Player.BLACK else '白棋'}")
    print(f"AI 使用 {'黑棋' if ai_color == Player.BLACK else '白棋'}")
    
    # 創建 AI 玩家
    print("\n正在初始化 AI...")
    ai_player = PureMCTSPlayer(num_simulations=400, temperature=0.1)
    print("✓ AI 初始化完成")
    
    # 創建遊戲
    game = Game()
    
    # 遊戲循環
    move_count = 0
    
    while not game.game_over:
        move_count += 1
        
        # 打印棋盤
        print_board(game)
        
        # 打印遊戲信息
        current_player = game.next_player
        print(f"\n第 {move_count} 步")
        print(f"當前玩家: {'黑棋 (X)' if current_player == Player.BLACK else '白棋 (O)'}")
        
        # 判斷是人類還是 AI
        if current_player == human_color:
            # 人類回合
            print("輪到您了！")
            move_input = get_human_move()
            
            if move_input is None:
                # 虛手
                game.pass_turn()
                print("您選擇虛手")
            else:
                x, y = move_input
                try:
                    game.play_move(Point(x, y))
                    print(f"您落子於 ({x}, {y})")
                except Exception as e:
                    print(f"落子失敗: {e}")
                    print("請重新輸入")
                    move_count -= 1
                    continue
        else:
            # AI 回合
            print("AI 正在思考...")
            move, stats = ai_player.get_move(game)
            
            if move is None:
                game.pass_turn()
                print("AI 選擇虛手")
            else:
                game.play_move(move)
                print(f"AI 落子於 ({move.x}, {move.y})")
                print(f"勝率評估: {stats.get('best_move_win_rate', 0):.2%}")
    
    # 遊戲結束
    print("\n" + "="*60)
    print("遊戲結束！")
    print("="*60)
    
    # 打印最終棋盤
    print_board(game)
    
    # 計算得分
    try:
        result = game.calculate_score()
        
        print(f"\n最終得分:")
        print(f"黑棋: {result.black_score:.2f}")
        print(f"白棋: {result.white_score:.2f}")
        
        winner_name = "黑棋" if result.winner == Player.BLACK else "白棋"
        
        if result.winner == human_color:
            print(f"\n🎉 恭喜！您獲勝了！({winner_name})")
        else:
            print(f"\n😔 很遺憾，AI 獲勝了。({winner_name})")
    except Exception as e:
        print(f"\n計分失敗: {e}")


if __name__ == "__main__":
    main()

