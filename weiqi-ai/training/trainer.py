"""
神經網絡訓練器

實現強化學習訓練循環：
1. 自我對弈生成數據
2. 訓練神經網絡
3. 評估新模型
4. 更新最佳模型
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
from typing import List, Tuple
from datetime import datetime

from ai.network import WeiQiNetwork
from ai.mcts_player import NeuralMCTSPlayer, PureMCTSPlayer
from training.self_play import TrainingExample, SelfPlayGenerator, DataAugmentation
from core.game import Game
from core.board import Player


class WeiQiDataset(Dataset):
    """圍棋訓練數據集"""
    
    def __init__(self, examples: List[TrainingExample]):
        self.examples = examples
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # 使用 .copy() 確保數組是連續的，避免負步長問題
        state = torch.FloatTensor(example.state.copy())
        policy = torch.FloatTensor(example.policy.copy()).flatten()  # (19, 19) -> (361,)
        value = torch.FloatTensor([example.value])
        
        return state, policy, value


class WeiQiTrainer:
    """
    圍棋神經網絡訓練器
    
    實現完整的訓練循環
    """
    
    def __init__(
        self,
        network: WeiQiNetwork,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        num_epochs: int = 10,
        device: str = 'cpu'
    ):
        """
        Args:
            network: 神經網絡
            learning_rate: 學習率
            batch_size: 批次大小
            num_epochs: 訓練輪數
            device: 設備 ('cpu' 或 'cuda')
        """
        self.network = network
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.device = torch.device(device)
        
        self.network.to(self.device)
        
        # 優化器
        self.optimizer = optim.Adam(
            self.network.parameters(),
            lr=learning_rate,
            weight_decay=1e-4
        )
        
        # 損失函數
        self.policy_loss_fn = nn.CrossEntropyLoss()
        self.value_loss_fn = nn.MSELoss()
    
    def train(
        self,
        training_examples: List[TrainingExample],
        augment_data: bool = True,
        verbose: bool = True
    ) -> dict:
        """
        訓練神經網絡
        
        Args:
            training_examples: 訓練樣本
            augment_data: 是否進行數據增強
            verbose: 是否打印訓練信息
        
        Returns:
            訓練統計信息
        """
        # 數據增強
        if augment_data:
            if verbose:
                print(f"Augmenting data: {len(training_examples)} -> ", end="")
            training_examples = DataAugmentation.augment_dataset(training_examples)
            if verbose:
                print(f"{len(training_examples)} examples")
        
        # 創建數據集和數據加載器
        dataset = WeiQiDataset(training_examples)
        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0
        )
        
        # 訓練循環
        self.network.train()
        
        total_loss_history = []
        policy_loss_history = []
        value_loss_history = []
        
        for epoch in range(self.num_epochs):
            epoch_total_loss = 0.0
            epoch_policy_loss = 0.0
            epoch_value_loss = 0.0
            num_batches = 0
            
            total_batches = len(dataloader)
            for batch_idx, (states, target_policies, target_values) in enumerate(dataloader):
                # 移動到設備
                states = states.to(self.device)
                target_policies = target_policies.to(self.device)
                target_values = target_values.to(self.device)
                
                # 前向傳播
                policy_logits, predicted_values = self.network(states)
                
                # 計算損失
                policy_loss = self.policy_loss_fn(policy_logits, target_policies)
                value_loss = self.value_loss_fn(predicted_values, target_values)
                
                # 總損失（加權和）
                total_loss = policy_loss + value_loss
                
                # 反向傳播
                self.optimizer.zero_grad()
                total_loss.backward()
                self.optimizer.step()
                
                # 記錄損失
                epoch_total_loss += total_loss.item()
                epoch_policy_loss += policy_loss.item()
                epoch_value_loss += value_loss.item()
                num_batches += 1
                
                # 顯示進度（每 50 個批次或最後一個批次）
                if verbose and (batch_idx % 50 == 0 or batch_idx == total_batches - 1):
                    progress = (batch_idx + 1) / total_batches * 100
                    avg_loss = epoch_total_loss / num_batches
                    print(f"  Batch {batch_idx + 1}/{total_batches} ({progress:.1f}%) - "
                          f"Loss: {avg_loss:.4f}", flush=True)
            
            # 計算平均損失
            avg_total_loss = epoch_total_loss / num_batches
            avg_policy_loss = epoch_policy_loss / num_batches
            avg_value_loss = epoch_value_loss / num_batches
            
            total_loss_history.append(avg_total_loss)
            policy_loss_history.append(avg_policy_loss)
            value_loss_history.append(avg_value_loss)
            
            if verbose:
                print(f"Epoch {epoch + 1}/{self.num_epochs}: "
                      f"Total Loss = {avg_total_loss:.4f}, "
                      f"Policy Loss = {avg_policy_loss:.4f}, "
                      f"Value Loss = {avg_value_loss:.4f}")
        
        return {
            "total_loss": total_loss_history,
            "policy_loss": policy_loss_history,
            "value_loss": value_loss_history
        }
    
    def save_checkpoint(self, filepath: str, metadata: dict = None):
        """
        保存訓練檢查點
        
        Args:
            filepath: 保存路徑
            metadata: 額外的元數據
        """
        checkpoint = {
            "model_state_dict": self.network.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "metadata": metadata or {}
        }
        
        torch.save(checkpoint, filepath)
        print(f"Saved checkpoint to {filepath}")
    
    def load_checkpoint(self, filepath: str):
        """
        加載訓練檢查點
        
        Args:
            filepath: 檢查點路徑
        """
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.network.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        
        print(f"Loaded checkpoint from {filepath}")
        
        return checkpoint.get("metadata", {})


class ReinforcementLearningLoop:
    """
    強化學習訓練循環
    
    實現 AlphaGo Zero 風格的訓練流程：
    1. 自我對弈生成數據
    2. 訓練神經網絡
    3. 評估新模型 vs 舊模型
    4. 如果新模型更好，更新最佳模型
    """
    
    def __init__(
        self,
        initial_network: WeiQiNetwork = None,
        num_simulations: int = 400,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        num_epochs: int = 10,
        device: str = 'cpu'
    ):
        """
        Args:
            initial_network: 初始網絡（None 表示隨機初始化）
            num_simulations: MCTS 模擬次數
            learning_rate: 學習率
            batch_size: 批次大小
            num_epochs: 每次訓練的輪數
            device: 設備
        """
        self.num_simulations = num_simulations
        self.device = device
        
        # 創建或使用初始網絡
        if initial_network is None:
            self.best_network = WeiQiNetwork()
        else:
            self.best_network = initial_network
        
        # 創建訓練器
        self.trainer = WeiQiTrainer(
            network=self.best_network,
            learning_rate=learning_rate,
            batch_size=batch_size,
            num_epochs=num_epochs,
            device=device
        )
        
        self.iteration = 0
    
    def run_iteration(
        self,
        num_self_play_games: int = 100,
        num_eval_games: int = 20,
        win_rate_threshold: float = 0.55,
        save_dir: str = "models",
        verbose: bool = True
    ) -> dict:
        """
        運行一次訓練迭代
        
        Args:
            num_self_play_games: 自我對弈遊戲數量
            num_eval_games: 評估遊戲數量
            win_rate_threshold: 新模型需要達到的勝率閾值
            save_dir: 模型保存目錄
            verbose: 是否打印詳細信息
        
        Returns:
            迭代統計信息
        """
        self.iteration += 1
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Iteration {self.iteration}")
            print(f"{'='*60}\n")
        
        # 1. 自我對弈生成數據
        if verbose:
            print("Step 1: Self-play data generation")
        
        player = NeuralMCTSPlayer(
            model_path=None,  # 使用當前最佳模型
            num_simulations=self.num_simulations
        )
        player.neural_network = self.best_network
        
        generator = SelfPlayGenerator(player=player)
        training_examples = generator.generate_games(
            num_games=num_self_play_games,
            save_dir=os.path.join(save_dir, "training_data"),
            verbose=verbose
        )
        
        # 2. 訓練新模型
        if verbose:
            print("\nStep 2: Training new model")
        
        new_network = WeiQiNetwork()
        new_network.load_state_dict(self.best_network.state_dict())  # 從最佳模型開始
        
        new_trainer = WeiQiTrainer(
            network=new_network,
            learning_rate=self.trainer.optimizer.param_groups[0]['lr'],
            batch_size=self.trainer.batch_size,
            num_epochs=self.trainer.num_epochs,
            device=self.device
        )
        
        train_stats = new_trainer.train(
            training_examples=training_examples,
            augment_data=True,
            verbose=verbose
        )
        
        # 3. 評估新模型 vs 舊模型
        if verbose:
            print("\nStep 3: Evaluating new model vs best model")
        
        new_wins, best_wins, draws = self._evaluate_models(
            new_network=new_network,
            best_network=self.best_network,
            num_games=num_eval_games,
            verbose=verbose
        )
        
        new_win_rate = new_wins / (new_wins + best_wins + draws)
        
        if verbose:
            print(f"\nEvaluation results:")
            print(f"  New model wins: {new_wins}")
            print(f"  Best model wins: {best_wins}")
            print(f"  Draws: {draws}")
            print(f"  New model win rate: {new_win_rate:.2%}")
        
        # 4. 更新最佳模型
        if new_win_rate >= win_rate_threshold:
            if verbose:
                print(f"\n✓ New model is better! Updating best model.")
            
            self.best_network.load_state_dict(new_network.state_dict())
            self.trainer.network = self.best_network
            
            # 保存新的最佳模型
            os.makedirs(save_dir, exist_ok=True)
            model_path = os.path.join(save_dir, f"best_model_iter{self.iteration}.pth")
            self.best_network.save(model_path)
            
            model_updated = True
        else:
            if verbose:
                print(f"\n✗ New model is not better. Keeping best model.")
            
            model_updated = False
        
        # 返回統計信息
        return {
            "iteration": self.iteration,
            "num_training_examples": len(training_examples),
            "train_stats": train_stats,
            "eval_new_wins": new_wins,
            "eval_best_wins": best_wins,
            "eval_draws": draws,
            "new_win_rate": new_win_rate,
            "model_updated": model_updated
        }
    
    def _evaluate_models(
        self,
        new_network: WeiQiNetwork,
        best_network: WeiQiNetwork,
        num_games: int,
        verbose: bool = True
    ) -> Tuple[int, int, int]:
        """
        評估兩個模型的對弈
        
        Returns:
            (new_wins, best_wins, draws)
        """
        new_wins = 0
        best_wins = 0
        draws = 0
        
        for game_idx in range(num_games):
            # 交替先手
            if game_idx % 2 == 0:
                black_network = new_network
                white_network = best_network
                new_is_black = True
            else:
                black_network = best_network
                white_network = new_network
                new_is_black = False
            
            # 創建玩家（使用較少的模擬次數加速評估）
            black_player = NeuralMCTSPlayer(num_simulations=200)
            black_player.neural_network = black_network
            
            white_player = NeuralMCTSPlayer(num_simulations=200)
            white_player.neural_network = white_network
            
            # 對弈
            game = Game()
            move_count = 0
            
            while not game.game_over and move_count < 400:
                current_player = black_player if game.next_player == Player.BLACK else white_player
                
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
                    if new_is_black:
                        new_wins += 1
                    else:
                        best_wins += 1
                else:
                    if new_is_black:
                        best_wins += 1
                    else:
                        new_wins += 1
            except:
                draws += 1
            
            if verbose:
                print(f"  Game {game_idx + 1}/{num_games} finished")
        
        return new_wins, best_wins, draws
    
    def run(
        self,
        num_iterations: int,
        num_self_play_games: int = 100,
        num_eval_games: int = 20,
        save_dir: str = "models"
    ):
        """
        運行完整的訓練循環
        
        Args:
            num_iterations: 迭代次數
            num_self_play_games: 每次迭代的自我對弈遊戲數
            num_eval_games: 每次迭代的評估遊戲數
            save_dir: 保存目錄
        """
        print(f"Starting reinforcement learning loop")
        print(f"Total iterations: {num_iterations}")
        print(f"Self-play games per iteration: {num_self_play_games}")
        print(f"Evaluation games per iteration: {num_eval_games}")
        print(f"Save directory: {save_dir}\n")
        
        for i in range(num_iterations):
            stats = self.run_iteration(
                num_self_play_games=num_self_play_games,
                num_eval_games=num_eval_games,
                save_dir=save_dir,
                verbose=True
            )
            
            print(f"\nIteration {stats['iteration']} summary:")
            print(f"  Training examples: {stats['num_training_examples']}")
            print(f"  Final training loss: {stats['train_stats']['total_loss'][-1]:.4f}")
            print(f"  New model win rate: {stats['new_win_rate']:.2%}")
            print(f"  Model updated: {stats['model_updated']}")
        
        print(f"\n{'='*60}")
        print(f"Training complete!")
        print(f"{'='*60}")

