#!/usr/bin/env python3
"""
訓練腳本

運行強化學習訓練循環
"""

import argparse
import os
import sys

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.network import WeiQiNetwork
from training.trainer import ReinforcementLearningLoop


def main():
    parser = argparse.ArgumentParser(description="訓練圍棋 AI")
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="訓練迭代次數（默認：10）"
    )
    
    parser.add_argument(
        "--self-play-games",
        type=int,
        default=50,
        help="每次迭代的自我對弈遊戲數（默認：50）"
    )
    
    parser.add_argument(
        "--eval-games",
        type=int,
        default=10,
        help="每次迭代的評估遊戲數（默認：10）"
    )
    
    parser.add_argument(
        "--simulations",
        type=int,
        default=400,
        help="MCTS 模擬次數（默認：400）"
    )
    
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="學習率（默認：0.001）"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="批次大小（默認：32）"
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="每次訓練的輪數（默認：10）"
    )
    
    parser.add_argument(
        "--save-dir",
        type=str,
        default="models",
        help="模型保存目錄（默認：models）"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="訓練設備（默認：cpu）"
    )
    
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="從檢查點恢復訓練（提供模型路徑）"
    )
    
    args = parser.parse_args()
    
    # 創建保存目錄
    os.makedirs(args.save_dir, exist_ok=True)
    
    # 創建或加載網絡
    if args.resume:
        print(f"Loading model from {args.resume}")
        network = WeiQiNetwork()
        network.load(args.resume)
    else:
        print("Creating new network")
        network = WeiQiNetwork()
    
    # 創建訓練循環
    rl_loop = ReinforcementLearningLoop(
        initial_network=network,
        num_simulations=args.simulations,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        device=args.device
    )
    
    # 運行訓練
    print("\n" + "="*60)
    print("訓練配置")
    print("="*60)
    print(f"迭代次數: {args.iterations}")
    print(f"自我對弈遊戲數: {args.self_play_games}")
    print(f"評估遊戲數: {args.eval_games}")
    print(f"MCTS 模擬次數: {args.simulations}")
    print(f"學習率: {args.learning_rate}")
    print(f"批次大小: {args.batch_size}")
    print(f"訓練輪數: {args.epochs}")
    print(f"保存目錄: {args.save_dir}")
    print(f"設備: {args.device}")
    print("="*60 + "\n")
    
    try:
        rl_loop.run(
            num_iterations=args.iterations,
            num_self_play_games=args.self_play_games,
            num_eval_games=args.eval_games,
            save_dir=args.save_dir
        )
    except KeyboardInterrupt:
        print("\n\n訓練被中斷")
        
        # 保存當前模型
        checkpoint_path = os.path.join(args.save_dir, "checkpoint_interrupted.pth")
        rl_loop.best_network.save(checkpoint_path)
        print(f"已保存檢查點到 {checkpoint_path}")


if __name__ == "__main__":
    main()

