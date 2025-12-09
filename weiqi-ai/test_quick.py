#!/usr/bin/env python3
"""
快速測試腳本 - 僅測試基本功能，不運行 MCTS

用於快速驗證安裝是否成功
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*60)
print("圍棋 AI 快速測試")
print("="*60)

# 測試 1: 導入核心模塊
print("\n測試 1: 導入核心模塊...")
try:
    from core.game import Game
    from core.board import Player, Point, BOARD_SIZE
    print("✓ 核心模塊導入成功")
except Exception as e:
    print(f"✗ 核心模塊導入失敗: {e}")
    sys.exit(1)

# 測試 2: 導入 AI 模塊
print("\n測試 2: 導入 AI 模塊...")
try:
    from ai.mcts import MCTS
    from ai.network import WeiQiNetwork
    from ai.mcts_player import PureMCTSPlayer
    from ai.scoring import MonteCarloScoring
    print("✓ AI 模塊導入成功")
except Exception as e:
    print(f"✗ AI 模塊導入失敗: {e}")
    sys.exit(1)

# 測試 3: 測試基本遊戲功能
print("\n測試 3: 測試基本遊戲功能...")
try:
    game = Game()
    game.play_move(Point(3, 3))
    game.play_move(Point(15, 15))
    print("✓ 基本遊戲功能正常")
except Exception as e:
    print(f"✗ 基本遊戲功能失敗: {e}")
    sys.exit(1)

# 測試 4: 測試神經網絡結構
print("\n測試 4: 測試神經網絡結構...")
try:
    import torch
    network = WeiQiNetwork()
    total_params = sum(p.numel() for p in network.parameters())
    print(f"✓ 神經網絡創建成功")
    print(f"  參數總數: {total_params:,}")
except Exception as e:
    print(f"✗ 神經網絡測試失敗: {e}")
    print("  這可能是因為缺少 PyTorch，請運行: pip install torch")

# 測試 5: 測試 FastAPI
print("\n測試 5: 測試 FastAPI...")
try:
    from fastapi import FastAPI
    from api.main import app
    print("✓ FastAPI 模塊正常")
except Exception as e:
    print(f"✗ FastAPI 測試失敗: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ 所有基本測試通過！")
print("="*60)
print("\n系統已準備就緒！")
print("\n下一步:")
print("  1. 運行完整測試（需要幾分鐘）:")
print("     python test_ai.py")
print("")
print("  2. 啟動 AI 服務:")
print("     export AI_MODE=pure_mcts")
print("     export NUM_SIMULATIONS=400")
print("     python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
print("")
print("  3. 人機對弈:")
print("     python examples/simple_game.py")
print("")

