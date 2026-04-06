from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))


def run_command(command: str):
    """运行命令并显示输出"""
    print(f"执行命令: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    if result.returncode != 0:
        print(f"命令执行失败，返回码: {result.returncode}")
        sys.exit(1)


def main():
    """主训练流程"""
    print("=== 强化学习AI训练流程 ===")
    print("开始两阶段训练...")
    
    # 阶段1: 模仿学习
    print("\n=== 阶段1: 模仿学习 ===")
    print("训练模型模仿规则AI的行为...")
    run_command(f"python {REPO_ROOT}/train_imitator.py")
    
    # 阶段2: 强化学习优化
    print("\n=== 阶段2: 强化学习优化 ===")
    print("使用AlphaZero算法优化模型...")
    run_command(f"python {REPO_ROOT}/train_alphazero.py")
    
    print("\n=== 训练完成 ===")
    print("强化学习AI训练流程已完成！")
    print("训练好的模型保存在: checkpoints/ai_mcts_imitated.npz")
    
    # 验证模型
    print("\n=== 验证模型 ===")
    print("模型训练完成，您可以使用以下命令测试模型:")
    print("python SDK/train_example.py --seed 42 --max-actions 96")


if __name__ == "__main__":
    main()