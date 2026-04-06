import torch
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from SDK.training.env import AntWarParallelEnv
from SDK.utils.features import FeatureExtractor
from AI.ai_rule import AI as RuleAI

# 加载模仿模型
class ImitationModel(torch.nn.Module):
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.network = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, output_dim),
            torch.nn.Softmax(dim=-1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

def test_imitation_model():
    """测试模仿模型"""
    print("开始测试模仿模型...")
    
    # 加载模型
    model_path = Path("checkpoints/imitation_model.pth")
    if not model_path.exists():
        print("错误：模型文件不存在！")
        return
    
    # 创建环境和特征提取器
    env = AntWarParallelEnv(seed=42, max_actions=96)
    feature_extractor = FeatureExtractor(max_actions=96)
    rule_agent = RuleAI()
    
    # 确定输入输出维度
    observations, infos = env.reset(seed=42)
    obs = observations["player_0"]
    flat_obs = feature_extractor.flatten_observation(obs)
    input_dim = len(flat_obs)
    output_dim = 96
    
    # 加载模型
    model = ImitationModel(input_dim, output_dim)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    print("模型加载成功！")
    
    # 测试模型
    correct_count = 0
    total_count = 0
    
    for episode in range(10):
        observations, infos = env.reset(seed=episode)
        
        while env.agents:
            # 规则AI的选择
            bundles = infos["player_0"]["bundles"]
            chosen_bundle = rule_agent.choose_bundle(env.state, 0, bundles)
            
            # 找到规则AI的动作索引
            rule_action = 0
            for i, bundle in enumerate(bundles):
                if bundle.operations == chosen_bundle.operations:
                    rule_action = i
                    break
            
            # 模型的预测
            obs = observations["player_0"]
            flat_obs = feature_extractor.flatten_observation(obs)
            obs_tensor = torch.tensor(flat_obs, dtype=torch.float32).unsqueeze(0)
            
            with torch.no_grad():
                output = model(obs_tensor)
                model_action = torch.argmax(output).item()
            
            # 比较预测结果
            if model_action == rule_action:
                correct_count += 1
            total_count += 1
            
            # 执行动作
            actions = {
                "player_0": rule_action,  # 使用规则AI的动作
                "player_1": 0
            }
            
            observations, rewards, terminations, truncations, infos = env.step(actions)
            
            if all(terminations.values()):
                break
    
    env.close()
    
    # 计算准确率
    accuracy = correct_count / total_count if total_count > 0 else 0
    print(f"测试完成！")
    print(f"总测试样本数: {total_count}")
    print(f"正确预测数: {correct_count}")
    print(f"准确率: {accuracy:.4f}")
    
    return accuracy

if __name__ == "__main__":
    test_imitation_model()
