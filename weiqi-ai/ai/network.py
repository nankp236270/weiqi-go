"""
神經網絡模型

實現圍棋 AI 的神經網絡架構：
- 策略頭 (Policy Head): 預測每個位置的落子概率
- 價值頭 (Value Head): 評估當前局面的勝率

架構參考 AlphaGo Zero 的設計：
- 卷積神經網絡主體（ResNet 風格）
- 雙頭輸出（策略 + 價值）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple

from core.board import BOARD_SIZE, Player
from core.game import Game


# 網絡超參數
NUM_RESIDUAL_BLOCKS = 10  # 殘差塊數量
NUM_FILTERS = 128  # 卷積核數量
INPUT_CHANNELS = 17  # 輸入通道數（見 _encode_game_state）


class ResidualBlock(nn.Module):
    """殘差塊（ResNet 基本單元）"""
    
    def __init__(self, num_filters: int):
        super().__init__()
        
        self.conv1 = nn.Conv2d(num_filters, num_filters, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(num_filters)
        
        self.conv2 = nn.Conv2d(num_filters, num_filters, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(num_filters)
    
    def forward(self, x):
        residual = x
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = F.relu(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        
        out += residual  # 殘差連接
        out = F.relu(out)
        
        return out


class PolicyHead(nn.Module):
    """策略頭：預測每個位置的落子概率"""
    
    def __init__(self, num_filters: int, board_size: int = BOARD_SIZE):
        super().__init__()
        
        self.conv = nn.Conv2d(num_filters, 2, kernel_size=1)
        self.bn = nn.BatchNorm2d(2)
        self.fc = nn.Linear(2 * board_size * board_size, board_size * board_size)
    
    def forward(self, x):
        out = self.conv(x)
        out = self.bn(out)
        out = F.relu(out)
        
        out = out.view(out.size(0), -1)  # Flatten
        out = self.fc(out)
        
        return out  # 返回 logits（未經 softmax）


class ValueHead(nn.Module):
    """價值頭：評估當前局面的勝率"""
    
    def __init__(self, num_filters: int, board_size: int = BOARD_SIZE):
        super().__init__()
        
        self.conv = nn.Conv2d(num_filters, 1, kernel_size=1)
        self.bn = nn.BatchNorm2d(1)
        self.fc1 = nn.Linear(board_size * board_size, 256)
        self.fc2 = nn.Linear(256, 1)
    
    def forward(self, x):
        out = self.conv(x)
        out = self.bn(out)
        out = F.relu(out)
        
        out = out.view(out.size(0), -1)  # Flatten
        out = self.fc1(out)
        out = F.relu(out)
        out = self.fc2(out)
        out = torch.tanh(out)  # 輸出範圍 [-1, 1]
        
        return out


class WeiQiNetwork(nn.Module):
    """
    圍棋神經網絡
    
    架構：
    1. 輸入層：17 個通道的 19x19 特徵平面
    2. 卷積層 + 殘差塊
    3. 策略頭：輸出 361 個位置的概率分佈
    4. 價值頭：輸出 [-1, 1] 的勝率評估
    """
    
    def __init__(
        self, 
        num_residual_blocks: int = NUM_RESIDUAL_BLOCKS,
        num_filters: int = NUM_FILTERS,
        board_size: int = BOARD_SIZE
    ):
        super().__init__()
        
        self.board_size = board_size
        
        # 初始卷積層
        self.conv_input = nn.Conv2d(INPUT_CHANNELS, num_filters, kernel_size=3, padding=1)
        self.bn_input = nn.BatchNorm2d(num_filters)
        
        # 殘差塊
        self.residual_blocks = nn.ModuleList([
            ResidualBlock(num_filters) for _ in range(num_residual_blocks)
        ])
        
        # 策略頭和價值頭
        self.policy_head = PolicyHead(num_filters, board_size)
        self.value_head = ValueHead(num_filters, board_size)
    
    def forward(self, x):
        """
        前向傳播
        
        Args:
            x: 輸入張量，形狀為 (batch_size, INPUT_CHANNELS, board_size, board_size)
        
        Returns:
            (policy_logits, value)
            - policy_logits: 形狀 (batch_size, board_size * board_size)
            - value: 形狀 (batch_size, 1)
        """
        # 初始卷積
        out = self.conv_input(x)
        out = self.bn_input(out)
        out = F.relu(out)
        
        # 殘差塊
        for block in self.residual_blocks:
            out = block(out)
        
        # 雙頭輸出
        policy_logits = self.policy_head(out)
        value = self.value_head(out)
        
        return policy_logits, value
    
    def predict(self, game_state: Game) -> Tuple[np.ndarray, float]:
        """
        預測給定遊戲狀態的策略和價值
        
        Args:
            game_state: 當前遊戲狀態
        
        Returns:
            (policy, value)
            - policy: 19x19 的概率分佈數組
            - value: 勝率評估 [-1, 1]
        """
        self.eval()
        
        with torch.no_grad():
            # 編碼遊戲狀態
            state_tensor = self._encode_game_state(game_state)
            state_tensor = torch.FloatTensor(state_tensor).unsqueeze(0)  # 添加 batch 維度
            
            # 前向傳播
            policy_logits, value = self.forward(state_tensor)
            
            # 轉換為概率分佈
            policy_probs = F.softmax(policy_logits, dim=1)
            policy_probs = policy_probs.squeeze(0).numpy()  # (361,)
            policy_probs = policy_probs.reshape(self.board_size, self.board_size)  # (19, 19)
            
            value = value.item()
        
        return policy_probs, value
    
    def _encode_game_state(self, game_state: Game) -> np.ndarray:
        """
        將遊戲狀態編碼為神經網絡輸入
        
        特徵平面（17 個通道）：
        1-8: 當前玩家最近 8 步的棋子位置
        9-16: 對手最近 8 步的棋子位置
        17: 當前玩家顏色（全 1 表示黑，全 0 表示白）
        
        Args:
            game_state: 遊戲狀態
        
        Returns:
            形狀為 (17, 19, 19) 的 numpy 數組
        """
        features = np.zeros((INPUT_CHANNELS, self.board_size, self.board_size), dtype=np.float32)
        
        current_player = game_state.next_player
        opponent = Player.WHITE if current_player == Player.BLACK else Player.BLACK
        
        # 通道 1-8: 當前玩家的棋子（簡化版：只用第一個通道）
        for i in range(self.board_size):
            for j in range(self.board_size):
                if game_state.board.grid[i][j] == current_player:
                    features[0, i, j] = 1.0
        
        # 通道 9-16: 對手的棋子（簡化版：只用第九個通道）
        for i in range(self.board_size):
            for j in range(self.board_size):
                if game_state.board.grid[i][j] == opponent:
                    features[8, i, j] = 1.0
        
        # 通道 17: 當前玩家顏色
        if current_player == Player.BLACK:
            features[16, :, :] = 1.0
        
        return features
    
    def save(self, path: str):
        """保存模型權重"""
        torch.save(self.state_dict(), path)
    
    def load(self, path: str):
        """加載模型權重"""
        self.load_state_dict(torch.load(path, map_location='cpu'))


class RandomNetwork:
    """
    隨機網絡（用於測試和初始階段）
    
    返回均勻分佈的策略和隨機價值
    """
    
    def __init__(self, board_size: int = BOARD_SIZE):
        self.board_size = board_size
    
    def predict(self, game_state: Game) -> Tuple[np.ndarray, float]:
        """
        返回隨機預測
        
        Returns:
            (均勻分佈的策略, 隨機價值)
        """
        # 均勻策略
        policy = np.ones((self.board_size, self.board_size), dtype=np.float32)
        policy /= policy.sum()
        
        # 隨機價值
        value = np.random.uniform(-0.1, 0.1)
        
        return policy, value


def create_network(
    pretrained_path: str = None,
    use_random: bool = False
) -> WeiQiNetwork:
    """
    創建神經網絡實例
    
    Args:
        pretrained_path: 預訓練模型路徑（可選）
        use_random: 是否使用隨機網絡
    
    Returns:
        神經網絡實例
    """
    if use_random:
        return RandomNetwork()
    
    network = WeiQiNetwork()
    
    if pretrained_path:
        try:
            network.load(pretrained_path)
            print(f"Loaded pretrained model from {pretrained_path}")
        except Exception as e:
            print(f"Failed to load pretrained model: {e}")
            print("Using randomly initialized network")
    
    return network

