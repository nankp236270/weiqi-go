"""
FastAPI 主应用

提供 AI 决策和计分的 API 端点。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import random
import os

from core.board import Board, Player, Point
from core.game import Game
from ai.mcts_player import create_player
from ai.scoring import create_scorer

app = FastAPI(
    title="Weiqi AI Service",
    description="围棋 AI 服务，提供 AI 决策和计分功能（支持 MCTS + 神经网络）",
    version="1.0.0"
)

# ==================== 全局配置 ====================

# AI 配置
AI_MODE = os.environ.get("AI_MODE", "pure_mcts")  # pure_mcts 或 neural_mcts
MODEL_PATH = os.environ.get("MODEL_PATH", None)  # 神经网络模型路径
NUM_SIMULATIONS = int(os.environ.get("NUM_SIMULATIONS", "400"))  # MCTS 模拟次数

# 计分配置
SCORING_MODE = os.environ.get("SCORING_MODE", "monte_carlo")  # monte_carlo 或 neural
SCORING_SIMULATIONS = int(os.environ.get("SCORING_SIMULATIONS", "200"))  # 计分模拟次数

# 创建全局 AI 玩家和计分器
print(f"Initializing AI with mode: {AI_MODE}")
print(f"MCTS simulations: {NUM_SIMULATIONS}")

try:
    ai_player = create_player(
        mode=AI_MODE,
        model_path=MODEL_PATH,
        num_simulations=NUM_SIMULATIONS,
        temperature=0.1  # 低温度，偏向最佳着法
    )
    print("✓ AI player initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize AI player: {e}")
    print("Falling back to pure MCTS")
    ai_player = create_player(
        mode="pure_mcts",
        num_simulations=NUM_SIMULATIONS,
        temperature=0.1
    )

print(f"Initializing scorer with mode: {SCORING_MODE}")

try:
    if SCORING_MODE == "neural" and hasattr(ai_player, 'neural_network') and ai_player.neural_network:
        scorer = create_scorer(
            mode="neural",
            neural_network=ai_player.neural_network
        )
    else:
        scorer = create_scorer(
            mode="monte_carlo",
            num_simulations=SCORING_SIMULATIONS
        )
    print("✓ Scorer initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize scorer: {e}")
    print("Falling back to monte carlo scoring")
    scorer = create_scorer(
        mode="monte_carlo",
        num_simulations=SCORING_SIMULATIONS
    )


# ==================== 请求/响应模型 ====================

class MoveRequest(BaseModel):
    """AI 落子请求"""
    board: List[List[int]] = Field(..., description="19x19 棋盘状态")
    next_player: int = Field(..., description="下一个玩家 (1=黑, 2=白)")
    history: List[str] = Field(default_factory=list, description="历史状态哈希列表")


class MoveResponse(BaseModel):
    """AI 落子响应"""
    x: int = Field(..., description="落子的 x 坐标")
    y: int = Field(..., description="落子的 y 坐标")
    confidence: float = Field(..., description="置信度 (0-1)")
    simulations: Optional[int] = Field(None, description="MCTS 模拟次数")
    win_rate: Optional[float] = Field(None, description="预估胜率")


class ScoreRequest(BaseModel):
    """计分请求"""
    board: List[List[int]] = Field(..., description="19x19 棋盘状态")


class ScoreResponse(BaseModel):
    """计分响应"""
    black_score: float
    white_score: float
    winner: int = Field(..., description="胜者 (1=黑, 2=白)")


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "service": "Weiqi AI",
        "version": "1.0.0",
        "status": "running",
        "ai_mode": AI_MODE,
        "num_simulations": NUM_SIMULATIONS,
        "scoring_mode": SCORING_MODE
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/v1/ai/move", response_model=MoveResponse)
async def get_ai_move(request: MoveRequest):
    """
    获取 AI 的下一步落子
    
    使用 MCTS（蒙特卡洛树搜索）算法，可选神经网络辅助
    """
    try:
        # 1. 重建游戏状态
        game = Game()
        game.board = Board.from_list(request.board)
        game.next_player = Player(request.next_player)
        
        # 重建历史记录
        for hash_str in request.history:
            game.history[hash_str] = True
        
        # 2. 使用 MCTS 获取 AI 着法
        move, stats = ai_player.get_move(game)
        
        if move is None:
            raise HTTPException(
                status_code=400,
                detail="No legal moves available. Game might be over."
            )
        
        # 3. 返回结果
        return MoveResponse(
            x=move.x,
            y=move.y,
            confidence=stats.get("best_move_visits", 0) / max(stats.get("total_simulations", 1), 1),
            simulations=stats.get("total_simulations"),
            win_rate=stats.get("best_move_win_rate")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid board state: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/v1/game/score", response_model=ScoreResponse)
async def calculate_score(request: ScoreRequest):
    """
    计算终局得分
    
    使用蒙特卡洛模拟或神经网络辅助计分
    中国规则（子空皆地），黑方贴 3.75 子
    """
    try:
        # 1. 重建游戏状态
        game = Game()
        game.board = Board.from_list(request.board)
        game.game_over = True  # 标记为已结束
        
        # 2. 使用高级计分器计算得分
        result = scorer.score(game)
        
        return ScoreResponse(
            black_score=result.black_score,
            white_score=result.white_score,
            winner=int(result.winner)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid board state: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== 调试端点 ====================

@app.post("/v1/debug/legal-moves")
async def get_legal_moves(request: MoveRequest):
    """
    获取所有合法落子位置（调试用）
    """
    try:
        game = Game()
        game.board = Board.from_list(request.board)
        game.next_player = Player(request.next_player)
        
        for hash_str in request.history:
            game.history[hash_str] = True
        
        legal_moves = game.get_legal_moves()
        
        return {
            "count": len(legal_moves),
            "moves": [{"x": m.x, "y": m.y} for m in legal_moves]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/ai/info")
async def get_ai_info():
    """
    获取 AI 配置信息
    """
    return {
        "ai_mode": AI_MODE,
        "model_path": MODEL_PATH,
        "num_simulations": NUM_SIMULATIONS,
        "scoring_mode": SCORING_MODE,
        "scoring_simulations": SCORING_SIMULATIONS,
        "has_neural_network": hasattr(ai_player, 'neural_network') and ai_player.neural_network is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
