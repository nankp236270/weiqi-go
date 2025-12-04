"""
FastAPI 主应用

提供 AI 决策和计分的 API 端点。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import random

from core.board import Board, Player, Point
from core.game import Game

app = FastAPI(
    title="Weiqi AI Service",
    description="围棋 AI 服务，提供 AI 决策和计分功能",
    version="0.1.0"
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
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/v1/ai/move", response_model=MoveResponse)
async def get_ai_move(request: MoveRequest):
    """
    获取 AI 的下一步落子
    
    当前实现：随机选择一个合法的落子位置
    未来会升级为 MCTS + 神经网络
    """
    try:
        # 1. 重建游戏状态
        game = Game()
        game.board = Board.from_list(request.board)
        game.next_player = Player(request.next_player)
        
        # 重建历史记录
        for hash_str in request.history:
            game.history[hash_str] = True
        
        # 2. 获取所有合法落子位置
        legal_moves = game.get_legal_moves()
        
        if not legal_moves:
            raise HTTPException(
                status_code=400,
                detail="No legal moves available. Game might be over."
            )
        
        # 3. 随机选择一个合法位置（简单 AI）
        chosen_move = random.choice(legal_moves)
        
        return MoveResponse(
            x=chosen_move.x,
            y=chosen_move.y,
            confidence=1.0 / len(legal_moves)  # 均匀分布的置信度
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid board state: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/v1/game/score", response_model=ScoreResponse)
async def calculate_score(request: ScoreRequest):
    """
    计算终局得分
    
    使用中国规则（子空皆地），黑方贴 3.75 子
    """
    try:
        # 1. 重建游戏状态
        game = Game()
        game.board = Board.from_list(request.board)
        game.game_over = True  # 标记为已结束
        
        # 2. 计算得分
        result = game.calculate_score()
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

