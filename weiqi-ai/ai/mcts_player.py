"""
MCTS 玩家

整合 MCTS 和神經網絡，提供統一的 AI 接口
"""

from typing import Tuple, Optional
import numpy as np

from core.game import Game
from core.board import Point
from .mcts import MCTS
from .network import WeiQiNetwork, RandomNetwork


class MCTSPlayer:
    """
    基於 MCTS 的圍棋 AI 玩家
    
    支持三種模式：
    1. 純 MCTS（隨機模擬）
    2. MCTS + 隨機網絡（用於測試）
    3. MCTS + 訓練好的神經網絡（完整 AI）
    """
    
    def __init__(
        self,
        neural_network: Optional[WeiQiNetwork] = None,
        num_simulations: int = 800,
        temperature: float = 1.0
    ):
        """
        初始化 MCTS 玩家
        
        Args:
            neural_network: 神經網絡（None 表示純 MCTS）
            num_simulations: MCTS 模擬次數
            temperature: 溫度參數（控制探索程度）
        """
        self.neural_network = neural_network
        self.num_simulations = num_simulations
        self.temperature = temperature
        self.mcts = MCTS(neural_network=neural_network, num_simulations=num_simulations)
    
    def get_move(self, game_state: Game) -> Tuple[Optional[Point], dict]:
        """
        獲取 AI 的下一步著法
        
        Args:
            game_state: 當前遊戲狀態
        
        Returns:
            (著法, 統計信息)
            - 著法為 None 表示虛手
        """
        # 檢查是否有合法著法
        legal_moves = game_state.get_legal_moves()
        
        if not legal_moves:
            return None, {"reason": "no_legal_moves"}
        
        # 執行 MCTS 搜索
        move, stats = self.mcts.search(game_state, temperature=self.temperature)
        
        return move, stats
    
    def get_policy_distribution(self) -> np.ndarray:
        """
        獲取策略分佈（用於訓練數據生成）
        
        Returns:
            19x19 的概率分佈
        """
        return self.mcts.get_policy_distribution()


class PureMCTSPlayer(MCTSPlayer):
    """純 MCTS 玩家（不使用神經網絡）"""
    
    def __init__(self, num_simulations: int = 800, temperature: float = 1.0):
        super().__init__(
            neural_network=None,
            num_simulations=num_simulations,
            temperature=temperature
        )


class NeuralMCTSPlayer(MCTSPlayer):
    """神經網絡輔助的 MCTS 玩家"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        num_simulations: int = 800,
        temperature: float = 1.0
    ):
        """
        初始化神經網絡 MCTS 玩家
        
        Args:
            model_path: 模型權重路徑（None 表示使用隨機初始化）
            num_simulations: MCTS 模擬次數
            temperature: 溫度參數
        """
        # 創建或加載神經網絡
        if model_path:
            network = WeiQiNetwork()
            try:
                network.load(model_path)
                print(f"Loaded model from {model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
                print("Using randomly initialized network")
        else:
            # 使用隨機網絡（用於測試）
            network = RandomNetwork()
            print("Using random network")
        
        super().__init__(
            neural_network=network,
            num_simulations=num_simulations,
            temperature=temperature
        )


def create_player(
    mode: str = "pure_mcts",
    model_path: Optional[str] = None,
    num_simulations: int = 800,
    temperature: float = 1.0
) -> MCTSPlayer:
    """
    創建 AI 玩家
    
    Args:
        mode: 模式
            - "pure_mcts": 純 MCTS
            - "neural_mcts": 神經網絡輔助的 MCTS
        model_path: 模型路徑（僅用於 neural_mcts 模式）
        num_simulations: MCTS 模擬次數
        temperature: 溫度參數
    
    Returns:
        MCTSPlayer 實例
    """
    if mode == "pure_mcts":
        return PureMCTSPlayer(
            num_simulations=num_simulations,
            temperature=temperature
        )
    elif mode == "neural_mcts":
        return NeuralMCTSPlayer(
            model_path=model_path,
            num_simulations=num_simulations,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

