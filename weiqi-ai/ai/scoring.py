"""
神經網絡輔助的計分系統

使用以下方法進行終局計分：
1. 基於蒙特卡洛的計分（隨機模擬）
2. 基於神經網絡的計分（價值網絡預測）
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass

from core.board import Board, Player, Point, BOARD_SIZE
from core.game import Game, ScoreResult


@dataclass
class TerritoryAnalysis:
    """領地分析結果"""
    black_territory: int
    white_territory: int
    neutral_territory: int
    black_stones: int
    white_stones: int
    territory_map: np.ndarray  # 19x19，值為 1(黑), 2(白), 0(中立)


class MonteCarloScoring:
    """
    基於蒙特卡洛模擬的計分系統
    
    通過隨機模擬多次棋局，統計每個空點被哪一方佔據的頻率，
    從而判斷領地歸屬。
    """
    
    def __init__(self, num_simulations: int = 200):
        """
        Args:
            num_simulations: 模擬次數
        """
        self.num_simulations = num_simulations
    
    def score(self, game_state: Game) -> ScoreResult:
        """
        計算終局得分
        
        Args:
            game_state: 遊戲狀態（應該已經結束）
        
        Returns:
            ScoreResult
        """
        # 分析領地
        territory = self._analyze_territory(game_state.board)
        
        # 計算得分
        black_score = float(territory.black_stones + territory.black_territory)
        white_score = float(territory.white_stones + territory.white_territory) + 3.75  # 貼目
        
        # 判斷勝負
        winner = Player.BLACK if black_score > white_score else Player.WHITE
        
        return ScoreResult(
            black_score=black_score,
            white_score=white_score,
            winner=winner
        )
    
    def _analyze_territory(self, board: Board) -> TerritoryAnalysis:
        """
        使用蒙特卡洛模擬分析領地
        
        Args:
            board: 當前棋盤
        
        Returns:
            TerritoryAnalysis
        """
        # 統計每個空點被黑/白佔據的次數
        black_ownership = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int32)
        white_ownership = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int32)
        
        # 執行多次隨機模擬
        for _ in range(self.num_simulations):
            sim_board = board.clone()
            self._random_playout(sim_board)
            
            # 統計這次模擬的結果
            for i in range(BOARD_SIZE):
                for j in range(BOARD_SIZE):
                    if sim_board.grid[i][j] == Player.BLACK:
                        black_ownership[i][j] += 1
                    elif sim_board.grid[i][j] == Player.WHITE:
                        white_ownership[i][j] += 1
        
        # 根據統計結果判斷領地歸屬
        territory_map = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int32)
        black_territory = 0
        white_territory = 0
        neutral_territory = 0
        black_stones = 0
        white_stones = 0
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                current = board.grid[i][j]
                
                if current == Player.BLACK:
                    territory_map[i][j] = 1
                    black_stones += 1
                elif current == Player.WHITE:
                    territory_map[i][j] = 2
                    white_stones += 1
                else:
                    # 空點：根據模擬結果判斷歸屬
                    black_count = black_ownership[i][j]
                    white_count = white_ownership[i][j]
                    
                    # 如果某一方佔據超過 60%，則判定為該方領地
                    threshold = self.num_simulations * 0.6
                    
                    if black_count > threshold:
                        territory_map[i][j] = 1
                        black_territory += 1
                    elif white_count > threshold:
                        territory_map[i][j] = 2
                        white_territory += 1
                    else:
                        territory_map[i][j] = 0
                        neutral_territory += 1
        
        return TerritoryAnalysis(
            black_territory=black_territory,
            white_territory=white_territory,
            neutral_territory=neutral_territory,
            black_stones=black_stones,
            white_stones=white_stones,
            territory_map=territory_map
        )
    
    def _random_playout(self, board: Board, max_moves: int = 100):
        """
        在給定棋盤上執行隨機模擬
        
        Args:
            board: 棋盤（會被修改）
            max_moves: 最大步數
        """
        current_player = Player.BLACK
        consecutive_passes = 0
        moves_played = 0
        
        while consecutive_passes < 2 and moves_played < max_moves:
            # 找出所有空點
            empty_points = []
            for i in range(BOARD_SIZE):
                for j in range(BOARD_SIZE):
                    if board.grid[i][j] == Player.EMPTY:
                        empty_points.append(Point(j, i))
            
            if not empty_points:
                break
            
            # 隨機嘗試落子
            placed = False
            np.random.shuffle(empty_points)
            
            for point in empty_points[:20]:  # 只嘗試前 20 個點（加速）
                try:
                    board.place_stone(current_player, point)
                    placed = True
                    consecutive_passes = 0
                    break
                except:
                    continue
            
            if not placed:
                consecutive_passes += 1
            
            # 切換玩家
            current_player = Player.WHITE if current_player == Player.BLACK else Player.BLACK
            moves_played += 1


class NeuralScoring:
    """
    基於神經網絡的計分系統
    
    使用訓練好的神經網絡直接預測終局得分
    """
    
    def __init__(self, neural_network):
        """
        Args:
            neural_network: 訓練好的神經網絡
        """
        self.neural_network = neural_network
    
    def score(self, game_state: Game) -> ScoreResult:
        """
        使用神經網絡計算得分
        
        Args:
            game_state: 遊戲狀態
        
        Returns:
            ScoreResult
        """
        # 獲取神經網絡的價值預測
        _, value = self.neural_network.predict(game_state)
        
        # value 的範圍是 [-1, 1]，表示從當前玩家視角的勝率
        # 我們需要轉換為具體的得分
        
        # 簡化處理：使用傳統方法計算基礎分數
        territory = self._analyze_territory_simple(game_state.board)
        
        black_score = float(territory.black_stones + territory.black_territory)
        white_score = float(territory.white_stones + territory.white_territory) + 3.75
        
        # 使用神經網絡的預測調整結果
        # 如果神經網絡認為黑方優勢很大，略微增加黑方得分
        if game_state.next_player == Player.BLACK:
            black_score += value * 5.0
        else:
            white_score += value * 5.0
        
        winner = Player.BLACK if black_score > white_score else Player.WHITE
        
        return ScoreResult(
            black_score=black_score,
            white_score=white_score,
            winner=winner
        )
    
    def _analyze_territory_simple(self, board: Board) -> TerritoryAnalysis:
        """
        簡單的領地分析（使用 BFS）
        
        Args:
            board: 棋盤
        
        Returns:
            TerritoryAnalysis
        """
        visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        territory_map = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int32)
        
        black_stones = 0
        white_stones = 0
        black_territory = 0
        white_territory = 0
        neutral_territory = 0
        
        # 統計棋子
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if board.grid[i][j] == Player.BLACK:
                    black_stones += 1
                    territory_map[i][j] = 1
                elif board.grid[i][j] == Player.WHITE:
                    white_stones += 1
                    territory_map[i][j] = 2
        
        # 使用 BFS 分析空點領地
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if board.grid[i][j] == Player.EMPTY and not visited[i][j]:
                    area_points = []
                    touches_black = False
                    touches_white = False
                    
                    # BFS
                    queue = [Point(j, i)]
                    visited[i][j] = True
                    
                    while queue:
                        p = queue.pop(0)
                        area_points.append(p)
                        
                        for neighbor in board._get_neighbors(p):
                            nx, ny = neighbor.x, neighbor.y
                            
                            if board.grid[ny][nx] == Player.BLACK:
                                touches_black = True
                            elif board.grid[ny][nx] == Player.WHITE:
                                touches_white = True
                            elif not visited[ny][nx]:
                                visited[ny][nx] = True
                                queue.append(neighbor)
                    
                    # 判斷領地歸屬
                    if touches_black and not touches_white:
                        black_territory += len(area_points)
                        for p in area_points:
                            territory_map[p.y][p.x] = 1
                    elif touches_white and not touches_black:
                        white_territory += len(area_points)
                        for p in area_points:
                            territory_map[p.y][p.x] = 2
                    else:
                        neutral_territory += len(area_points)
        
        return TerritoryAnalysis(
            black_territory=black_territory,
            white_territory=white_territory,
            neutral_territory=neutral_territory,
            black_stones=black_stones,
            white_stones=white_stones,
            territory_map=territory_map
        )


def create_scorer(
    mode: str = "monte_carlo",
    neural_network = None,
    num_simulations: int = 200
):
    """
    創建計分器
    
    Args:
        mode: 計分模式
            - "monte_carlo": 蒙特卡洛模擬
            - "neural": 神經網絡輔助
        neural_network: 神經網絡（僅用於 neural 模式）
        num_simulations: 模擬次數（僅用於 monte_carlo 模式）
    
    Returns:
        計分器實例
    """
    if mode == "monte_carlo":
        return MonteCarloScoring(num_simulations=num_simulations)
    elif mode == "neural":
        if neural_network is None:
            raise ValueError("Neural network is required for neural scoring mode")
        return NeuralScoring(neural_network=neural_network)
    else:
        raise ValueError(f"Unknown scoring mode: {mode}")

