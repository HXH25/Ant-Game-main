# 强化学习AI训练方案

## 概述

本方案实现了一个两阶段的强化学习AI训练流程：

1. **模仿学习阶段**：训练模型模仿规则AI的行为
2. **强化学习阶段**：使用AlphaZero算法优化模型

## 目录结构

```
├── train_imitator.py        # 模仿学习训练脚本
├── train_alphazero.py       # 强化学习训练脚本
├── train_full.py            # 完整训练集成脚本
├── AI/ai_trained.py         # 使用训练好的模型的AI实现
└── checkpoints/             # 模型保存目录
```

## 环境要求

### 基础依赖
```bash
# 安装PyTorch (CPU版本)
pip install torch

# 安装其他依赖
pip install pettingzoo gymnasium numpy tqdm
```

### 项目依赖
- 项目本身的SDK模块
- Python 3.8+

## 训练流程

### 1. 执行完整训练

```bash
# 运行完整训练流程
python train_full.py
```

这将自动执行两个阶段的训练：
- 阶段1：模仿学习（约2-4小时）
- 阶段2：强化学习（约20-40小时）

### 2. 手动执行训练

#### 阶段1：模仿学习
```bash
# 收集规则AI数据并训练模仿模型
python train_imitator.py
```

#### 阶段2：强化学习
```bash
# 使用AlphaZero算法优化模型
python train_alphazero.py
```

## 训练参数

### 模仿学习参数
- `episodes`: 收集的游戏数量（默认200）
- `max_actions`: 最大动作数（默认96）
- `epochs`: 训练轮次（默认100）

### 强化学习参数
- `batches`: 训练批次（默认200）
- `episodes`: 每批次游戏数量（默认4）
- `search_iterations`: MCTS搜索迭代次数（默认24，CPU友好）
- `learning_rate`: 学习率（默认1e-3）
- `hidden_dim`: 网络隐藏层维度（默认128）

## 模型评估

训练完成后，会自动评估模型性能：
- 与启发式AI的胜率
- 平局率
- 平均回合数

## 使用训练好的模型

### 直接使用
```python
from AI.ai_trained import AI

# 创建AI实例
ai = AI(model_path="checkpoints/ai_mcts_imitated.npz")

# 使用AI进行游戏
# ...
```

### 打包使用
```bash
# 打包训练好的AI
bash zip_rule.sh  # 或创建专门的打包脚本
```

## 训练结果

训练完成后，模型会保存在以下位置：
- 模仿模型：`checkpoints/imitation_model.pth`
- 最终模型：`checkpoints/ai_mcts_imitated.npz`

## 预期性能

- **模仿阶段**：动作预测准确率 > 80%
- **强化学习阶段**：与规则AI对弈胜率 > 60%

## 注意事项

1. **训练时间**：完整训练可能需要24-48小时（CPU）
2. **内存要求**：建议至少4GB内存
3. **模型大小**：最终模型约1-2MB
4. **可扩展性**：可以通过调整参数来平衡训练时间和效果

## 故障排除

### 常见问题

1. **模型加载失败**：检查模型文件路径是否正确
2. **训练速度慢**：减少搜索迭代次数或批次大小
3. **内存不足**：减少每批次的游戏数量

### 解决方案

- 对于CPU训练，建议使用较小的搜索迭代次数（如24）
- 对于内存有限的系统，建议使用较小的批次大小
- 训练过程中可以监控GPU/CPU使用率，确保系统稳定

## 进阶配置

### 调整训练参数

在`train_alphazero.py`中修改`AlphaZeroTrainerConfig`：

```python
config = AlphaZeroTrainerConfig(
    batches=300,          # 增加训练批次
    search_iterations=32,  # 增加搜索深度
    hidden_dim=256,        # 增加模型容量
    # 其他参数...
)
```

### 数据增强

可以通过增加收集的游戏数量来提高模仿学习的效果：

```python
data = collect_rule_data(episodes=500, max_actions=96)
```

## 总结

本训练方案提供了一个完整的流程，从模仿规则AI到通过强化学习优化，最终训练出一个性能优于规则AI的智能体。通过调整参数和训练时间，可以进一步提高模型性能。

---

**训练愉快！** 🚀