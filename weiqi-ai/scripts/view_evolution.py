#!/usr/bin/env python3
"""
查看模型進化歷史和統計信息
"""

import os
import sys
import glob
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_file_size(filepath):
    """獲取文件大小（MB）"""
    size_bytes = os.path.getsize(filepath)
    return size_bytes / (1024 * 1024)


def get_file_time(filepath):
    """獲取文件修改時間"""
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)


def main():
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    
    print("=" * 70)
    print("圍棋 AI 模型進化歷史")
    print("=" * 70)
    print()
    
    # 讀取代數
    gen_file = models_dir / ".generation"
    if gen_file.exists():
        current_gen = int(gen_file.read_text().strip())
        print(f"📊 當前代數: 第 {current_gen} 代")
    else:
        print("📊 當前代數: 未開始訓練")
        current_gen = 0
    
    # 讀取最佳模型
    best_model_link = models_dir / "best_model.pth"
    if best_model_link.exists() and best_model_link.is_symlink():
        best_model = best_model_link.resolve()
        print(f"🏆 最佳模型: {best_model.name}")
        print(f"   大小: {get_file_size(best_model):.2f} MB")
        print(f"   時間: {get_file_time(best_model).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("🏆 最佳模型: 無")
    
    print()
    
    # 讀取進化歷史
    history_file = models_dir / "evolution_history.txt"
    if history_file.exists():
        print("=" * 70)
        print("進化歷史")
        print("=" * 70)
        
        with open(history_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            print(f"  {line.strip()}")
        
        print()
        print(f"總代數: {len(lines)}")
    else:
        print("進化歷史: 無")
    
    print()
    
    # 統計所有模型
    all_models = list(models_dir.glob("**/*.pth"))
    if all_models:
        print("=" * 70)
        print("模型統計")
        print("=" * 70)
        
        total_size = sum(get_file_size(m) for m in all_models)
        
        print(f"模型總數: {len(all_models)}")
        print(f"總大小: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
        print()
        
        # 按代數分組
        gen_dirs = sorted(models_dir.glob("gen_*"))
        success_dirs = [d for d in gen_dirs if not d.name.endswith("_failed")]
        failed_dirs = [d for d in gen_dirs if d.name.endswith("_failed")]
        
        print(f"成功訓練: {len(success_dirs)} 次")
        print(f"失敗嘗試: {len(failed_dirs)} 次")
        
        if success_dirs:
            print()
            print("成功的訓練:")
            for gen_dir in success_dirs[-10:]:  # 顯示最近 10 個
                models_in_dir = list(gen_dir.glob("*.pth"))
                if models_in_dir:
                    size = sum(get_file_size(m) for m in models_in_dir)
                    time = get_file_time(gen_dir)
                    print(f"  {gen_dir.name}: {len(models_in_dir)} 個模型, "
                          f"{size:.2f} MB, {time.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("未找到任何模型")
    
    print()
    
    # 訓練日誌統計
    logs_dir = base_dir / "logs"
    history_log = logs_dir / "training_history.txt"
    
    if history_log.exists():
        print("=" * 70)
        print("訓練日誌統計")
        print("=" * 70)
        
        with open(history_log, 'r') as f:
            lines = f.readlines()
        
        print(f"日誌行數: {len(lines)}")
        
        # 統計關鍵事件
        upgrades = [l for l in lines if "模型升級成功" in l]
        failures = [l for l in lines if "新模型較弱" in l]
        
        print(f"成功升級: {len(upgrades)} 次")
        print(f"升級失敗: {len(failures)} 次")
        
        if upgrades:
            print()
            print("最近的升級:")
            for line in upgrades[-5:]:
                print(f"  {line.strip()}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

