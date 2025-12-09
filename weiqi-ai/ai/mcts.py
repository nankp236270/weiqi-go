"""
蒙特卡洛樹搜索 (MCTS) 實現

這是圍棋 AI 的核心搜索算法，支持：
1. 純 MCTS（使用隨機模擬）
2. 神經網絡輔助的 MCTS（使用策略和價值網絡）
"""

import math
import random
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import numpy as np

from core.board import Board, Player, Point, BOARD_SIZE
from core.game import Game


# MCTS 超參數
C_PUCT = 1.5  # UCB 探索常數
NUM_SIMULATIONS = 800  # 每次決策的模擬次數
DIRICHLET_ALPHA = 0.03  # Dirichlet 噪聲參數（用於探索）
DIRICHLET_EPSILON = 0.25  # Dirichlet 噪聲混合比例


@dataclass
class MCTSNode:
    """MCTS 樹節點"""
    
    # 遊戲狀態
    game_state: Game
    parent: Optional['MCTSNode'] = None
    move: Optional[Point] = None  # 從父節點到此節點的著法
    
    # MCTS 統計
    visit_count: int = 0
    total_value: float = 0.0  # 累計價值（從當前玩家視角）
    
    # 子節點
    children: Dict[Tuple[int, int], 'MCTSNode'] = None
    
    # 神經網絡預測（如果可用）
    prior_prob: float = 0.0  # 先驗概率（來自策略網絡）
    
    def __post_init__(self):
        if self.children is None:
            self.children = {}
    
    @property
    def q_value(self) -> float:
        """平均價值（Q值）"""
        if self.visit_count == 0:
            return 0.0
        return self.total_value / self.visit_count
    
    @property
    def is_leaf(self) -> bool:
        """是否為葉節點"""
        return len(self.children) == 0
    
    @property
    def is_fully_expanded(self) -> bool:
        """是否已完全展開"""
        if self.game_state.game_over:
            return True
        legal_moves = self.game_state.get_legal_moves()
        return len(self.children) >= len(legal_moves)


class MCTS:
    """
    蒙特卡洛樹搜索引擎
    
    支持兩種模式：
    1. 純 MCTS：使用隨機模擬評估局面
    2. 神經網絡輔助：使用神經網絡的策略和價值預測
    """
    
    def __init__(self, neural_network=None, num_simulations: int = NUM_SIMULATIONS):
        """
        初始化 MCTS
        
        Args:
            neural_network: 可選的神經網絡（用於策略和價值預測）
            num_simulations: 每次搜索的模擬次數
        """
        self.neural_network = neural_network
        self.num_simulations = num_simulations
        self.root: Optional[MCTSNode] = None
    
    def search(self, game_state: Game, temperature: float = 1.0) -> Tuple[Point, Dict]:
        """
        執行 MCTS 搜索並返回最佳著法
        
        Args:
            game_state: 當前遊戲狀態
            temperature: 溫度參數（控制探索程度）
                - temperature = 0: 選擇訪問次數最多的著法（貪婪）
                - temperature > 0: 按訪問次數的分佈採樣
        
        Returns:
            (最佳著法, 統計信息字典)
        """
        # 創建根節點
        self.root = MCTSNode(game_state=game_state)
        
        # 執行多次模擬
        for _ in range(self.num_simulations):
            self._simulate()
        
        # 選擇最佳著法
        best_move, stats = self._select_move(temperature)
        
        return best_move, stats
    
    def _simulate(self):
        """執行一次 MCTS 模擬（選擇、展開、評估、回傳）"""
        node = self.root
        search_path = [node]
        
        # 1. 選擇階段：向下遍歷到葉節點
        while not node.is_leaf and node.is_fully_expanded:
            node = self._select_child(node)
            search_path.append(node)
        
        # 2. 展開階段：如果不是終局，展開一個新子節點
        if not node.game_state.game_over and not node.is_fully_expanded:
            node = self._expand(node)
            search_path.append(node)
        
        # 3. 評估階段：評估葉節點的價值
        value = self._evaluate(node)
        
        # 4. 回傳階段：向上更新所有節點的統計信息
        self._backpropagate(search_path, value)
    
    def _select_child(self, node: MCTSNode) -> MCTSNode:
        """
        使用 UCB 公式選擇最佳子節點
        
        UCB = Q + C_PUCT * P * sqrt(N_parent) / (1 + N_child)
        
        其中：
        - Q: 子節點的平均價值
        - P: 先驗概率（來自神經網絡）
        - N_parent: 父節點的訪問次數
        - N_child: 子節點的訪問次數
        """
        best_score = -float('inf')
        best_child = None
        
        for child in node.children.values():
            # UCB 分數
            q_value = child.q_value
            u_value = (C_PUCT * child.prior_prob * 
                      math.sqrt(node.visit_count) / (1 + child.visit_count))
            
            score = q_value + u_value
            
            if score > best_score:
                best_score = score
                best_child = child
        
        return best_child
    
    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        展開一個新的子節點
        
        如果有神經網絡，使用策略網絡預測的概率分佈
        否則，隨機選擇一個未展開的合法著法
        """
        # 獲取所有合法著法
        legal_moves = node.game_state.get_legal_moves()
        
        # 找出尚未展開的著法
        unexpanded_moves = [
            move for move in legal_moves
            if (move.x, move.y) not in node.children
        ]
        
        if not unexpanded_moves:
            return node
        
        # 如果有神經網絡，使用策略網絡選擇
        if self.neural_network is not None:
            move, prior_probs = self._select_move_with_network(
                node.game_state, unexpanded_moves
            )
        else:
            # 否則隨機選擇
            move = random.choice(unexpanded_moves)
            prior_probs = {(m.x, m.y): 1.0 / len(legal_moves) for m in legal_moves}
        
        # 創建新的遊戲狀態
        new_game = self._clone_and_play(node.game_state, move)
        
        # 創建子節點
        child = MCTSNode(
            game_state=new_game,
            parent=node,
            move=move,
            prior_prob=prior_probs.get((move.x, move.y), 0.0)
        )
        
        node.children[(move.x, move.y)] = child
        
        return child
    
    def _evaluate(self, node: MCTSNode) -> float:
        """
        評估葉節點的價值
        
        如果有神經網絡，使用價值網絡
        否則，使用隨機模擬（rollout）
        
        Returns:
            價值評估（從根節點玩家的視角，-1 到 1）
        """
        # 如果遊戲已結束，直接返回結果
        if node.game_state.game_over:
            result = node.game_state.calculate_score()
            root_player = self.root.game_state.next_player
            
            if result.winner == root_player:
                return 1.0
            else:
                return -1.0
        
        # 如果有神經網絡，使用價值網絡
        if self.neural_network is not None:
            value = self._evaluate_with_network(node.game_state)
        else:
            # 否則使用隨機模擬
            value = self._rollout(node.game_state)
        
        return value
    
    def _rollout(self, game_state: Game, max_moves: int = 200) -> float:
        """
        隨機模擬（rollout）直到遊戲結束
        
        Args:
            game_state: 當前遊戲狀態
            max_moves: 最大模擬步數
        
        Returns:
            模擬結果（從根節點玩家的視角）
        """
        # 克隆遊戲狀態
        sim_game = Game()
        sim_game.board = game_state.board.clone()
        sim_game.next_player = game_state.next_player
        sim_game.history = game_state.history.copy()
        sim_game.passes = game_state.passes
        sim_game.game_over = game_state.game_over
        
        root_player = self.root.game_state.next_player
        moves_played = 0
        
        # 隨機下棋直到遊戲結束或達到最大步數
        while not sim_game.game_over and moves_played < max_moves:
            legal_moves = sim_game.get_legal_moves()
            
            if not legal_moves:
                # 沒有合法著法，虛手
                sim_game.pass_turn()
            else:
                # 隨機選擇一個合法著法
                move = random.choice(legal_moves)
                try:
                    sim_game.play_move(move)
                except:
                    # 如果出錯，虛手
                    sim_game.pass_turn()
            
            moves_played += 1
        
        # 如果達到最大步數仍未結束，強制結束並計分
        if not sim_game.game_over:
            sim_game.game_over = True
        
        # 計算結果
        try:
            result = sim_game.calculate_score()
            if result.winner == root_player:
                return 1.0
            else:
                return -1.0
        except:
            # 如果計分失敗，返回平局
            return 0.0
    
    def _backpropagate(self, search_path: List[MCTSNode], value: float):
        """
        回傳：向上更新路徑上所有節點的統計信息
        
        Args:
            search_path: 從根到葉的節點路徑
            value: 葉節點的價值（從根節點玩家的視角）
        """
        for node in reversed(search_path):
            node.visit_count += 1
            node.total_value += value
            
            # 切換視角（對手的視角是相反的）
            value = -value
    
    def _select_move(self, temperature: float) -> Tuple[Point, Dict]:
        """
        根據訪問次數選擇最佳著法
        
        Args:
            temperature: 溫度參數
        
        Returns:
            (最佳著法, 統計信息)
        """
        if not self.root.children:
            # 沒有子節點，返回虛手
            return None, {"error": "No legal moves"}
        
        # 收集所有子節點的訪問次數
        moves = []
        visit_counts = []
        
        for (x, y), child in self.root.children.items():
            moves.append(Point(x, y))
            visit_counts.append(child.visit_count)
        
        # 根據溫度選擇著法
        if temperature == 0:
            # 貪婪選擇：選擇訪問次數最多的
            best_idx = np.argmax(visit_counts)
            best_move = moves[best_idx]
        else:
            # 按訪問次數的分佈採樣
            visit_counts = np.array(visit_counts, dtype=np.float64)
            probs = visit_counts ** (1.0 / temperature)
            probs /= probs.sum()
            
            best_idx = np.random.choice(len(moves), p=probs)
            best_move = moves[best_idx]
        
        # 統計信息
        total_visits = sum(visit_counts)
        stats = {
            "total_simulations": total_visits,
            "best_move_visits": visit_counts[best_idx],
            "best_move_win_rate": self.root.children[(best_move.x, best_move.y)].q_value,
            "num_legal_moves": len(moves)
        }
        
        return best_move, stats
    
    def _select_move_with_network(
        self, 
        game_state: Game, 
        legal_moves: List[Point]
    ) -> Tuple[Point, Dict[Tuple[int, int], float]]:
        """
        使用神經網絡選擇著法（策略網絡）
        
        Returns:
            (選中的著法, 所有合法著法的先驗概率字典)
        """
        # 獲取神經網絡的策略預測
        policy_probs, _ = self.neural_network.predict(game_state)
        
        # 只保留合法著法的概率
        legal_probs = {}
        for move in legal_moves:
            legal_probs[(move.x, move.y)] = policy_probs[move.y][move.x]
        
        # 歸一化
        total_prob = sum(legal_probs.values())
        if total_prob > 0:
            legal_probs = {k: v / total_prob for k, v in legal_probs.items()}
        else:
            # 如果所有概率都是0，使用均勻分佈
            uniform_prob = 1.0 / len(legal_moves)
            legal_probs = {(m.x, m.y): uniform_prob for m in legal_moves}
        
        # 按概率選擇
        moves = list(legal_probs.keys())
        probs = list(legal_probs.values())
        selected = random.choices(moves, weights=probs, k=1)[0]
        
        return Point(selected[0], selected[1]), legal_probs
    
    def _evaluate_with_network(self, game_state: Game) -> float:
        """
        使用神經網絡評估局面（價值網絡）
        
        Returns:
            價值評估（從當前玩家的視角）
        """
        _, value = self.neural_network.predict(game_state)
        
        # 轉換到根節點玩家的視角
        if game_state.next_player != self.root.game_state.next_player:
            value = -value
        
        return value
    
    def _clone_and_play(self, game_state: Game, move: Point) -> Game:
        """克隆遊戲狀態並執行著法"""
        new_game = Game()
        new_game.board = game_state.board.clone()
        new_game.next_player = game_state.next_player
        new_game.history = game_state.history.copy()
        new_game.passes = game_state.passes
        new_game.game_over = game_state.game_over
        new_game.captures_by_black = game_state.captures_by_black
        new_game.captures_by_white = game_state.captures_by_white
        
        new_game.play_move(move)
        
        return new_game
    
    def get_policy_distribution(self) -> np.ndarray:
        """
        獲取根節點的策略分佈（用於訓練）
        
        Returns:
            19x19 的概率分佈數組
        """
        policy = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        
        if not self.root or not self.root.children:
            return policy
        
        # 計算訪問次數分佈
        total_visits = sum(child.visit_count for child in self.root.children.values())
        
        for (x, y), child in self.root.children.items():
            policy[y][x] = child.visit_count / total_visits
        
        return policy

