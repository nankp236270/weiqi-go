"""
围棋规则引擎核心模块

这个模块实现了围棋的所有核心规则，必须与 Go 后端保持 100% 一致。
"""

from .board import Board, Player, Point
from .game import Game

__all__ = ['Board', 'Player', 'Point', 'Game']

