from __future__ import annotations

import os
import sys
from pathlib import Path
import torch
import numpy as np

# 解决OpenMP错误
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目根目录到路径
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from SDK.training.alphazero import AlphaZeroTrainerConfig, AlphaZeroSelfPlayTrainer
from SDK.training.env import env as create_env
from SDK.alphazero import PolicyValueNet, PolicyValueNetConfig, build_policy_value_net
from SDK.utils.features import FeatureExtractor


class ImitationInitializer:
    """从模仿模型初始化PolicyValueNet"""
    @staticmethod
    def initialize_from_imitation(imitation_model_path: str, feature_extractor: FeatureExtractor, max_actions: int):
        """从模仿模型初始化PolicyValueNet"""
        # 加载模仿模型
        output_dim = max_actions
        
        # 创建PolicyValueNet
        policy_value_net = build_policy_value_net(
            feature_extractor=feature_extractor,
            action_dim=max_actions,
            config=PolicyValueNetConfig(
                hidden_dim=128,
                hidden_dim2=64,
                seed=42
            )
        )
        
        # 加载模仿模型权重
        try:
            import torch
            imitation_state_dict = torch.load(imitation_model_path)
            print("加载模仿模型权重...")
            
            # 调整权重以适应PolicyValueNet结构
            # 将PyTorch模型权重转换为NumPy数组
            policy_value_net.w1 = imitation_state_dict['network.0.weight'].cpu().numpy().T
            policy_value_net.b1 = imitation_state_dict['network.0.bias'].cpu().numpy()
            policy_value_net.w2 = imitation_state_dict['network.2.weight'].cpu().numpy().T
            policy_value_net.b2 = imitation_state_dict['network.2.bias'].cpu().numpy()
            policy_value_net.policy_w = imitation_state_dict['network.4.weight'].cpu().numpy().T
            policy_value_net.policy_b = imitation_state_dict['network.4.bias'].cpu().numpy()
            
            # 价值头使用随机初始化
            print("模仿模型权重加载成功！")
        except Exception as e:
            print(f"加载模仿模型失败: {e}")
            print("使用随机初始化...")
        
        return policy_value_net


def train_alpha_zero():
    """训练AlphaZero模型"""
    print("开始AlphaZero训练...")
    
    # 配置
    config = AlphaZeroTrainerConfig(
        batches=200,          # 训练批次
        episodes=4,           # 每批次游戏数量
        learning_rate=1e-3,   # 学习率
        search_iterations=24, # MCTS搜索迭代次数（CPU友好）
        max_actions=96,       # 最大动作数
        hidden_dim=128,       # 网络隐藏层维度
        hidden_dim2=64,       # 第二隐藏层维度
        checkpoint_path="checkpoints/ai_mcts_imitated.npz",  # 检查点保存路径
        resume_from=None      # 从哪里恢复训练
    )
    
    # 创建特征提取器
    feature_extractor = FeatureExtractor(max_actions=config.max_actions)
    
    # 从模仿模型初始化
    imitation_model_path = "checkpoints/imitation_model.pth"
    initial_model = ImitationInitializer.initialize_from_imitation(
        imitation_model_path, 
        feature_extractor, 
        config.max_actions
    )
    
    # 环境工厂
    def env_factory(seed):
        return create_env(seed=seed, max_actions=config.max_actions)
    
    # 创建训练器
    trainer = AlphaZeroSelfPlayTrainer(env_factory, config)
    
    # 使用初始模型
    trainer.model = initial_model
    
    # 训练
    print("开始自我对弈训练...")
    history, summaries = trainer.train()
    
    # 保存最终模型
    checkpoint_path = trainer.save_checkpoint()
    print(f"训练完成，模型保存到: {checkpoint_path}")
    
    # 评估
    print("评估模型性能...")
    metrics = trainer.evaluate_against_heuristic(num_episodes=10)
    print(f"评估结果: {metrics}")
    
    return trainer


def main():
    """主函数"""
    import signal
    
    # 创建检查点目录
    Path("checkpoints").mkdir(exist_ok=True)
    
    # 定义信号处理函数
    def signal_handler(signal, frame):
        print("\n收到终止信号，保存当前模型...")
        try:
            trainer.save_checkpoint()
            print("模型已保存！")
        except:
            print("保存模型失败，但训练数据已保存。")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 训练AlphaZero模型
    trainer = train_alpha_zero()
    
    print("强化学习训练完成！")


if __name__ == "__main__":
    main()