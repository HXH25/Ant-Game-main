from __future__ import annotations

try:
    from common import BaseAgent
except ModuleNotFoundError as exc:
    if exc.name != "common":
        raise
    from AI.common import BaseAgent

import torch
import numpy as np
from pathlib import Path
from SDK.utils.actions import ActionBundle
from SDK.backend.state import BackendState
from SDK.alphazero import PolicyValueNet
from SDK.utils.features import FeatureExtractor


class TrainedAI(BaseAgent):
    """使用训练好的模型的AI"""
    def __init__(self, seed: int | None = None, model_path: str = "checkpoints/ai_mcts_imitated.npz"):
        super().__init__(seed)
        self.model_path = model_path
        self.model = None
        self.feature_extractor = FeatureExtractor(max_actions=96)
        self._load_model()
    
    def _load_model(self):
        """加载训练好的模型"""
        model_path = Path(self.model_path)
        if model_path.exists():
            print(f"加载模型: {self.model_path}")
            self.model = PolicyValueNet.from_checkpoint(self.model_path)
            print("模型加载成功！")
        else:
            print(f"警告: 模型文件 {self.model_path} 不存在")
            self.model = None
    
    def choose_bundle(self, state: BackendState, player: int, bundles: list[ActionBundle] | None = None) -> ActionBundle:
        """选择操作包"""
        if bundles is None:
            bundles = self.list_bundles(state, player)
        
        # 如果没有模型或只有一个操作包，返回空操作
        if self.model is None or len(bundles) <= 1:
            return bundles[0]
        
        # 生成观察
        mask = np.zeros(96, dtype=np.int8)
        mask[:len(bundles)] = 1
        observation = self.feature_extractor.encode_observation(state, player, mask)
        flat_obs = self.feature_extractor.flatten_observation(observation)
        
        # 使用模型预测
        with torch.no_grad():
            obs_tensor = torch.tensor(flat_obs, dtype=torch.float32).unsqueeze(0)
            policy, value = self.model(obs_tensor)
            policy = policy.squeeze(0).numpy()
        
        # 应用动作掩码
        masked_policy = policy[:len(bundles)]
        masked_policy = masked_policy * mask[:len(bundles)]
        
        # 选择概率最高的动作
        if np.sum(masked_policy) > 0:
            action_index = np.argmax(masked_policy)
        else:
            action_index = 0
        
        return bundles[action_index]


class AI(TrainedAI):
    """训练好的AI"""
    pass