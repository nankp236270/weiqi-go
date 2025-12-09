"""
訓練模塊

包含自我對弈、數據增強、神經網絡訓練等功能
"""

from .self_play import (
    SelfPlayGenerator,
    TrainingExample,
    DataAugmentation,
    load_training_data,
    merge_training_data
)
from .trainer import (
    WeiQiTrainer,
    WeiQiDataset,
    ReinforcementLearningLoop
)

__all__ = [
    'SelfPlayGenerator',
    'TrainingExample',
    'DataAugmentation',
    'load_training_data',
    'merge_training_data',
    'WeiQiTrainer',
    'WeiQiDataset',
    'ReinforcementLearningLoop'
]

