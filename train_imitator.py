from __future__ import annotations

import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import sys
from pathlib import Path
from tqdm import tqdm

# 添加项目根目录到路径
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from SDK.training.env import AntWarParallelEnv
from SDK.utils.features import FeatureExtractor
from AI.ai_rule import AI as RuleAI


class ImitationModel(nn.Module):
    """模仿学习模型"""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


def collect_rule_data(episodes: int = 100, max_actions: int = 96) -> list[dict]:
    """收集规则AI的数据"""
    print(f"开始收集规则AI数据，共{episodes}场游戏...")
    
    env = AntWarParallelEnv(seed=42, max_actions=max_actions)
    rule_agent = RuleAI()
    feature_extractor = FeatureExtractor(max_actions=max_actions)
    data = []
    
    for episode in tqdm(range(episodes), desc="收集数据"):
        observations, infos = env.reset(seed=episode)
        
        while env.agents:
            # 为玩家0使用规则AI
            bundles = infos["player_0"]["bundles"]
            
            # 找到规则AI会选择的操作
            chosen_bundle = rule_agent.choose_bundle(env.state, 0, bundles)
            
            # 找到对应的动作索引
            action_index = 0
            for i, bundle in enumerate(bundles):
                if bundle.operations == chosen_bundle.operations:
                    action_index = i
                    break
            
            # 收集数据
            obs = observations["player_0"]
            flat_obs = feature_extractor.flatten_observation(obs)
            
            data.append({
                "observation": flat_obs.tolist(),
                "action": action_index
            })
            
            # 执行动作
            actions = {
                "player_0": action_index,
                "player_1": 0  # 对手使用空操作
            }
            
            observations, rewards, terminations, truncations, infos = env.step(actions)
            
            if all(terminations.values()):
                break
    
    env.close()
    print(f"数据收集完成，共{len(data)}条样本")
    return data


def train_imitation_model(data: list[dict], input_dim: int, output_dim: int, epochs: int = 100):
    """训练模仿模型"""
    print("开始训练模仿模型...")
    
    # 准备数据
    inputs = []
    targets = []
    for item in data:
        inputs.append(item["observation"])
        targets.append(item["action"])
    
    inputs = torch.tensor(inputs, dtype=torch.float32)
    targets = torch.tensor(targets, dtype=torch.long)
    
    # 创建模型
    model = ImitationModel(input_dim, output_dim)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    
    # 训练循环
    best_accuracy = 0.0
    for epoch in tqdm(range(epochs), desc="训练模型"):
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        # 计算准确率
        with torch.no_grad():
            predictions = torch.argmax(outputs, dim=1)
            accuracy = (predictions == targets).float().mean().item()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}")
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(model.state_dict(), "checkpoints/imitation_model.pth")
    
    print(f"训练完成，最佳准确率: {best_accuracy:.4f}")
    return model


def main():
    """主函数"""
    # 创建检查点目录
    Path("checkpoints").mkdir(exist_ok=True)
    
    # 收集数据
    data = collect_rule_data(episodes=200, max_actions=96)
    
    # 保存数据
    with open("checkpoints/rule_data.json", "w") as f:
        json.dump(data, f)
    
    # 确定输入输出维度
    input_dim = len(data[0]["observation"])
    output_dim = 96  # max_actions
    
    # 训练模型
    model = train_imitation_model(data, input_dim, output_dim, epochs=100)
    
    print("模仿学习训练完成！")


if __name__ == "__main__":
    import sys
    main()