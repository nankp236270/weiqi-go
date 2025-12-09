"""
自我對弈數據生成器

通過 AI 自我對弈生成訓練數據，用於強化學習
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
import pickle
import os
from datetime import datetime

from core.game import Game
from core.board import Player, Point, BOARD_SIZE
from ai.mcts_player import MCTSPlayer


@dataclass
class TrainingExample:
    """訓練樣本"""
    state: np.ndarray  # 遊戲狀態編碼 (17, 19, 19)
    policy: np.ndarray  # MCTS 策略分佈 (19, 19)
    value: float  # 最終結果（從當前玩家視角，+1 勝，-1 負）


class SelfPlayGenerator:
    """
    自我對弈數據生成器
    
    讓 AI 與自己對弈，收集訓練數據
    """
    
    def __init__(
        self,
        player: MCTSPlayer,
        temperature_threshold: int = 30
    ):
        """
        Args:
            player: MCTS 玩家
            temperature_threshold: 溫度閾值（前 N 步使用高溫度探索）
        """
        self.player = player
        self.temperature_threshold = temperature_threshold
    
    def generate_game(self) -> Tuple[List[TrainingExample], Dict]:
        """
        生成一局自我對弈遊戲
        
        Returns:
            (訓練樣本列表, 遊戲統計信息)
        """
        game = Game()
        examples = []
        move_count = 0
        
        # 記錄遊戲過程
        game_history = []
        
        while not game.game_over:
            move_count += 1
            
            # 前 N 步使用高溫度（增加探索）
            temperature = 1.0 if move_count <= self.temperature_threshold else 0.1
            
            # 保存當前狀態
            state = self._encode_state(game)
            
            # 獲取 AI 著法
            move, stats = self.player.get_move(game)
            
            if move is None:
                # 虛手
                game.pass_turn()
                game_history.append({
                    "move": "pass",
                    "player": game.next_player,
                    "stats": stats
                })
            else:
                # 獲取 MCTS 的策略分佈
                policy = self.player.get_policy_distribution()
                
                # 記錄訓練樣本（暫時不知道結果，稍後填充）
                examples.append({
                    "state": state,
                    "policy": policy,
                    "player": game.next_player
                })
                
                # 執行著法
                try:
                    game.play_move(move)
                    game_history.append({
                        "move": (move.x, move.y),
                        "player": game.next_player,
                        "stats": stats
                    })
                except Exception as e:
                    print(f"Error playing move: {e}")
                    game.pass_turn()
            
            # 防止無限循環
            if move_count > 400:
                game.game_over = True
                break
        
        # 計算最終結果
        try:
            result = game.calculate_score()
            winner = result.winner
        except:
            # 如果計分失敗，判定為平局
            winner = None
        
        # 為所有樣本填充結果值
        training_examples = []
        for example in examples:
            if winner is None:
                value = 0.0
            elif example["player"] == winner:
                value = 1.0
            else:
                value = -1.0
            
            training_examples.append(TrainingExample(
                state=example["state"],
                policy=example["policy"],
                value=value
            ))
        
        # 統計信息
        stats = {
            "num_moves": move_count,
            "winner": int(winner) if winner else 0,
            "num_training_examples": len(training_examples)
        }
        
        return training_examples, stats
    
    def generate_games(
        self,
        num_games: int,
        save_dir: str = None,
        verbose: bool = True
    ) -> List[TrainingExample]:
        """
        生成多局自我對弈遊戲
        
        Args:
            num_games: 遊戲局數
            save_dir: 保存目錄（可選）
            verbose: 是否打印進度
        
        Returns:
            所有訓練樣本的列表
        """
        all_examples = []
        
        for game_idx in range(num_games):
            if verbose:
                print(f"Generating game {game_idx + 1}/{num_games}...")
            
            examples, stats = self.generate_game()
            all_examples.extend(examples)
            
            if verbose:
                print(f"  Moves: {stats['num_moves']}, "
                      f"Winner: {stats['winner']}, "
                      f"Examples: {stats['num_training_examples']}")
            
            # 定期保存
            if save_dir and (game_idx + 1) % 10 == 0:
                self._save_examples(all_examples, save_dir, game_idx + 1)
        
        # 最終保存
        if save_dir:
            self._save_examples(all_examples, save_dir, num_games)
        
        if verbose:
            print(f"\nGenerated {len(all_examples)} training examples from {num_games} games")
        
        return all_examples
    
    def _encode_state(self, game: Game) -> np.ndarray:
        """
        編碼遊戲狀態為神經網絡輸入格式
        
        特徵平面（17 個通道）：
        1-8: 當前玩家最近 8 步的棋子位置
        9-16: 對手最近 8 步的棋子位置
        17: 當前玩家顏色
        
        Args:
            game: 遊戲狀態
        
        Returns:
            形狀為 (17, 19, 19) 的數組
        """
        features = np.zeros((17, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        
        current_player = game.next_player
        opponent = Player.WHITE if current_player == Player.BLACK else Player.BLACK
        
        # 通道 1: 當前玩家的棋子
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if game.board.grid[i][j] == current_player:
                    features[0, i, j] = 1.0
        
        # 通道 9: 對手的棋子
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if game.board.grid[i][j] == opponent:
                    features[8, i, j] = 1.0
        
        # 通道 17: 當前玩家顏色
        if current_player == Player.BLACK:
            features[16, :, :] = 1.0
        
        return features
    
    def _save_examples(self, examples: List[TrainingExample], save_dir: str, game_count: int):
        """保存訓練樣本"""
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_{timestamp}_games{game_count}.pkl"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump(examples, f)
        
        print(f"Saved {len(examples)} examples to {filepath}")


class DataAugmentation:
    """
    數據增強
    
    通過旋轉和翻轉增加訓練數據的多樣性
    """
    
    @staticmethod
    def augment(example: TrainingExample) -> List[TrainingExample]:
        """
        對一個訓練樣本進行數據增強
        
        生成 8 個變體：
        - 原始
        - 旋轉 90°, 180°, 270°
        - 水平翻轉
        - 水平翻轉 + 旋轉 90°, 180°, 270°
        
        Args:
            example: 原始訓練樣本
        
        Returns:
            增強後的樣本列表（包含原始樣本）
        """
        augmented = []
        
        state = example.state
        policy = example.policy
        value = example.value
        
        # 1. 原始
        augmented.append(example)
        
        # 2. 旋轉 90°（使用 .copy() 避免負步長）
        augmented.append(TrainingExample(
            state=np.rot90(state, k=1, axes=(1, 2)).copy(),
            policy=np.rot90(policy, k=1).copy(),
            value=value
        ))
        
        # 3. 旋轉 180°
        augmented.append(TrainingExample(
            state=np.rot90(state, k=2, axes=(1, 2)).copy(),
            policy=np.rot90(policy, k=2).copy(),
            value=value
        ))
        
        # 4. 旋轉 270°
        augmented.append(TrainingExample(
            state=np.rot90(state, k=3, axes=(1, 2)).copy(),
            policy=np.rot90(policy, k=3).copy(),
            value=value
        ))
        
        # 5. 水平翻轉
        augmented.append(TrainingExample(
            state=np.flip(state, axis=2).copy(),
            policy=np.flip(policy, axis=1).copy(),
            value=value
        ))
        
        # 6. 水平翻轉 + 旋轉 90°
        flipped = np.flip(state, axis=2).copy()
        flipped_policy = np.flip(policy, axis=1).copy()
        augmented.append(TrainingExample(
            state=np.rot90(flipped, k=1, axes=(1, 2)).copy(),
            policy=np.rot90(flipped_policy, k=1).copy(),
            value=value
        ))
        
        # 7. 水平翻轉 + 旋轉 180°
        augmented.append(TrainingExample(
            state=np.rot90(flipped, k=2, axes=(1, 2)).copy(),
            policy=np.rot90(flipped_policy, k=2).copy(),
            value=value
        ))
        
        # 8. 水平翻轉 + 旋轉 270°
        augmented.append(TrainingExample(
            state=np.rot90(flipped, k=3, axes=(1, 2)).copy(),
            policy=np.rot90(flipped_policy, k=3).copy(),
            value=value
        ))
        
        return augmented
    
    @staticmethod
    def augment_dataset(examples: List[TrainingExample]) -> List[TrainingExample]:
        """
        對整個數據集進行增強
        
        Args:
            examples: 原始訓練樣本列表
        
        Returns:
            增強後的樣本列表
        """
        augmented = []
        
        for example in examples:
            augmented.extend(DataAugmentation.augment(example))
        
        return augmented


def load_training_data(filepath: str) -> List[TrainingExample]:
    """
    加載訓練數據
    
    Args:
        filepath: 數據文件路徑
    
    Returns:
        訓練樣本列表
    """
    with open(filepath, 'rb') as f:
        examples = pickle.load(f)
    
    return examples


def merge_training_data(filepaths: List[str]) -> List[TrainingExample]:
    """
    合併多個訓練數據文件
    
    Args:
        filepaths: 數據文件路徑列表
    
    Returns:
        合併後的訓練樣本列表
    """
    all_examples = []
    
    for filepath in filepaths:
        examples = load_training_data(filepath)
        all_examples.extend(examples)
    
    return all_examples

