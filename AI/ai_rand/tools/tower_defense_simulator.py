from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional

# 添加项目根目录到Python路径
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# 导入游戏引擎
from SDK.backend.engine import GameState
from SDK.backend.model import Operation
from SDK.utils.constants import TowerType, OperationType, INITIAL_COINS

# 二级炮塔类型映射
SECONDARY_TOWER_TYPES = {
    11: TowerType.HEAVY_PLUS,
    12: TowerType.ICE,
    13: TowerType.BEWITCH,
    21: TowerType.QUICK_PLUS,
    22: TowerType.DOUBLE,
    23: TowerType.SNIPER,
    31: TowerType.MORTAR_PLUS,
    32: TowerType.PULSE,
    33: TowerType.MISSILE,
}

# 玩家0的防御塔区域（粉色区域）
DEFENSE_AREA_0 = {
    (6, 1), (7, 1), (4, 2), (6, 2), (8, 2), (4, 3), (5, 3), (6, 4), 
    (8, 4), (7, 5), (5, 6), (5, 7), (6, 7), (8, 7), (7, 8), (4, 9), 
    (5, 9), (6, 9), (7, 10), (5, 11), (6, 11), (8, 11), (5, 12), (7, 13), 
    (6, 14), (8, 14), (4, 15), (5, 15), (4, 16), (6, 16), (8, 16), (6, 17), (7, 17)
}

# 玩家1的防御塔区域（淡绿色区域）
DEFENSE_AREA_1 = {
    (11, 1), (12, 1), (9, 2), (11, 2), (13, 2), (13, 3), (14, 3), (9, 4), 
    (11, 4), (11, 5), (12, 6), (10, 7), (12, 7), (13, 7), (10, 8), (12, 9), 
    (13, 9), (14, 9), (10, 10), (10, 11), (12, 11), (13, 11), (12, 12), (11, 13), 
    (9, 14), (11, 14), (13, 15), (14, 15), (9, 16), (11, 16), (13, 16), (11, 17), (12, 17)
}


def get_defense_positions(player: int) -> List[Tuple[int, int]]:
    """获取指定玩家的防御塔可放置位置"""
    if player == 0:
        return list(DEFENSE_AREA_0)
    else:
        return list(DEFENSE_AREA_1)


def simulate_defense(tower_positions: List[Tuple[int, int]], tower_types: List[int], player: int, max_rounds: int = 100) -> Tuple[int, int]:
    """模拟防御，返回(基地掉血量, 击杀蚂蚁数)"""
    # 初始化游戏状态，使用随机种子增加多样性
    import random
    seed = random.randint(1, 10000)
    state = GameState.initial(seed=seed)
    
    # 为玩家设置足够的金币
    state.coins[player] = 1000
    
    # 建造炮塔
    built_towers = 0
    for i, (pos, tower_type) in enumerate(zip(tower_positions, tower_types)):
        # 检查位置是否在防御区域内
        defense_positions = get_defense_positions(player)
        if pos not in defense_positions:
            continue
        
        # 首先建造基础炮塔
        build_op = Operation(OperationType.BUILD_TOWER, pos[0], pos[1])
        if state.can_apply_operation(player, build_op):
            state.apply_operation_list(player, [build_op])
            built_towers += 1
        
        # 升级到指定的二级炮塔
        tower = state.tower_at(pos[0], pos[1])
        if tower:
            # 先升级到一级炮塔（如果需要）
            if tower.tower_type == 0:  # Basic塔
                # 升级到对应的一级炮塔
                primary_tower_type = tower_type // 10
                upgrade_op = Operation(OperationType.UPGRADE_TOWER, tower.tower_id, primary_tower_type)
                if state.can_apply_operation(player, upgrade_op):
                    state.apply_operation_list(player, [upgrade_op])
                    
                    # 然后升级到二级炮塔
                    tower = state.tower_at(pos[0], pos[1])
                    if tower:
                        upgrade_op = Operation(OperationType.UPGRADE_TOWER, tower.tower_id, int(SECONDARY_TOWER_TYPES[tower_type]))
                        if state.can_apply_operation(player, upgrade_op):
                            state.apply_operation_list(player, [upgrade_op])
    
    # 记录初始基地血量
    initial_base_hp = state.bases[player].hp
    
    # 模拟max_rounds回合
    ant_count = 0
    killed_ants = 0
    
    for round_num in range(max_rounds):
        # 按照3.5回合的周期生成蚂蚁（0, 4, 7, 11, 14, ...）
        if round_num == 0 or (round_num - 4) % 3.5 == 0:
            # 为敌方生成一只HP20的蚂蚁
            from SDK.backend.model import Ant
            from SDK.utils.constants import AntBehavior, AntKind, AntStatus
            
            if player == 0:
                # 为玩家1生成蚂蚁（从玩家1的基地出发）
                ant = Ant(round_num, 1, 16, 9, hp=20, level=0, behavior=AntBehavior.DEFAULT, kind=AntKind.WORKER)
            else:
                # 为玩家0生成蚂蚁（从玩家0的基地出发）
                ant = Ant(round_num, 0, 2, 9, hp=20, level=0, behavior=AntBehavior.DEFAULT, kind=AntKind.WORKER)
            
            state.ants.append(ant)
            ant_count += 1
        
        # 记录回合开始时的蚂蚁数量
        start_ant_count = len([ant for ant in state.ants if ant.hp > 0])
        
        # 执行回合
        state.resolve_turn([], [])
        
        # 记录回合结束时的蚂蚁数量
        end_ant_count = len([ant for ant in state.ants if ant.hp > 0])
        killed_ants += start_ant_count - end_ant_count
        
        # 检查游戏是否结束
        if state.terminal:
            break
    
    # 计算基地掉血量
    base_hp_loss = initial_base_hp - state.bases[player].hp
    # 确保掉血量不为负
    base_hp_loss = max(0, base_hp_loss)
    
    # 检查炮塔是否存在
    towers = [tower for tower in state.towers if tower.player == player]
    
    # 只在需要时输出详细信息
    if killed_ants == 0 and base_hp_loss > 0:
        print(f"  模拟结果: 生成{ant_count}只蚂蚁，击杀{killed_ants}只，基地掉血{base_hp_loss}")
        print(f"  炮塔数量: {len(towers)}，成功建造: {built_towers}")
        for i, tower in enumerate(towers):
            print(f"  炮塔{i+1}: 类型{tower.tower_type}，位置({tower.x},{tower.y})")
    
    return base_hp_loss, killed_ants


import random

def generate_random_combination(defense_positions, secondary_tower_ids):
    """生成随机的炮塔布置组合"""
    # 随机选择3个不同的位置
    positions = random.sample(defense_positions, 3)
    # 随机选择3个炮塔类型
    tower_types = [random.choice(secondary_tower_ids) for _ in range(3)]
    return positions, tower_types

def mutate_combination(positions, tower_types, defense_positions, secondary_tower_ids, mutation_rate=0.2):
    """变异组合"""
    new_positions = positions.copy()
    new_tower_types = tower_types.copy()
    
    # 随机变异位置
    for i in range(3):
        if random.random() < mutation_rate:
            # 选择一个新的位置，确保不与其他位置重复
            available_positions = [p for p in defense_positions if p not in new_positions]
            if available_positions:
                new_positions[i] = random.choice(available_positions)
    
    # 随机变异炮塔类型
    for i in range(3):
        if random.random() < mutation_rate:
            new_tower_types[i] = random.choice(secondary_tower_ids)
    
    return new_positions, new_tower_types

def crossover_combinations(parent1, parent2):
    """交叉两个组合"""
    pos1, type1 = parent1
    pos2, type2 = parent2
    
    # 交叉位置
    crossover_point = random.randint(1, 2)
    new_positions = pos1[:crossover_point] + pos2[crossover_point:]
    
    # 确保位置不重复
    if len(set(new_positions)) < 3:
        # 如果有重复，使用防御区域的位置
        defense_positions = get_defense_positions(0) + get_defense_positions(1)
        available_positions = [p for p in defense_positions if p not in new_positions]
        if available_positions:
            for i in range(3):
                for j in range(i+1, 3):
                    if new_positions[i] == new_positions[j]:
                        new_positions[j] = random.choice(available_positions)
                        available_positions.remove(new_positions[j])
    
    # 交叉炮塔类型
    crossover_point = random.randint(1, 2)
    new_tower_types = type1[:crossover_point] + type2[crossover_point:]
    
    return new_positions, new_tower_types

def genetic_algorithm_search(player: int = 0, max_rounds: int = 100, population_size: int = 50, generations: int = 50, mutation_rate: float = 0.2) -> Tuple[List[Tuple[int, int]], List[int], int, int]:
    """使用遗传算法搜索最优炮塔布置方案"""
    defense_positions = get_defense_positions(player)
    secondary_tower_ids = list(SECONDARY_TOWER_TYPES.keys())
    
    print(f"开始遗传算法搜索")
    print(f"种群大小: {population_size}")
    print(f"进化代数: {generations}")
    print("=" * 60)
    
    # 初始化种群
    population = []
    print("初始化种群中...")
    
    # 添加用户指定的初始个体
    if player == 0:
        # 玩家0的对称位置
        user_positions = [(6, 9), (4, 9), (8, 7)]
    else:
        # 玩家1的指定位置
        user_positions = [(12, 9), (14, 9), (10, 8)]
    
    # 检查位置是否在防御区域内
    valid_user_positions = [pos for pos in user_positions if pos in defense_positions]
    if len(valid_user_positions) == 3:
        print(f"  添加用户指定的初始个体: {valid_user_positions}")
        # 为用户指定的位置随机分配炮塔类型
        user_tower_types = [random.choice(secondary_tower_ids) for _ in range(3)]
        hp_loss, killed_ants = simulate_defense(valid_user_positions, user_tower_types, player, max_rounds)
        population.append((valid_user_positions, user_tower_types, hp_loss, killed_ants))
    
    # 生成剩余的随机个体
    for i in range(len(population), population_size):
        if i % 10 == 0:
            print(f"  生成第 {i+1}/{population_size} 个个体")
        positions, tower_types = generate_random_combination(defense_positions, secondary_tower_ids)
        hp_loss, killed_ants = simulate_defense(positions, tower_types, player, max_rounds)
        population.append((positions, tower_types, hp_loss, killed_ants))
    
    # 排序种群：优先按掉血量，然后按击杀数
    population.sort(key=lambda x: (x[2], -x[3]))
    best_hp_loss = population[0][2]
    best_killed_ants = population[0][3]
    best_positions = population[0][0]
    best_tower_types = population[0][1]
    
    # 计算初始种群平均掉血量和击杀数
    initial_avg_loss = sum([p[2] for p in population]) / len(population)
    initial_avg_killed = sum([p[3] for p in population]) / len(population)
    
    print("=" * 60)
    print(f"初始最优方案: 掉血 {best_hp_loss}，击杀 {best_killed_ants}只")
    print(f"初始种群平均: 掉血 {initial_avg_loss:.1f}，击杀 {initial_avg_killed:.1f}只")
    print("=" * 60)
    
    # 进化过程
    for generation in range(generations):
        # 计算进度百分比
        progress = (generation + 1) / generations * 100
        
        if generation % 5 == 0:
            print(f"\n第 {generation+1}/{generations} 代 (进度: {progress:.1f}%)")
        
        # 选择父代（精英保留）
        elite_size = population_size // 5
        new_population = population[:elite_size]
        
        # 生成新个体
        for i in range(elite_size, population_size):
            # 选择父母
            parent1 = random.choice(population[:population_size//2])
            parent2 = random.choice(population[:population_size//2])
            
            # 交叉
            child_positions, child_tower_types = crossover_combinations((parent1[0], parent1[1]), (parent2[0], parent2[1]))
            
            # 变异
            child_positions, child_tower_types = mutate_combination(child_positions, child_tower_types, defense_positions, secondary_tower_ids, mutation_rate)
            
            # 评估
            child_hp_loss, child_killed_ants = simulate_defense(child_positions, child_tower_types, player, max_rounds)
            new_population.append((child_positions, child_tower_types, child_hp_loss, child_killed_ants))
        
        # 更新种群
        population = new_population
        # 排序：优先按掉血量，然后按击杀数
        population.sort(key=lambda x: (x[2], -x[3]))
        
        # 计算当前种群平均掉血量和击杀数
        current_avg_loss = sum([p[2] for p in population]) / len(population)
        current_avg_killed = sum([p[3] for p in population]) / len(population)
        
        # 更新最优解
        if (population[0][2] < best_hp_loss) or (population[0][2] == best_hp_loss and population[0][3] > best_killed_ants):
            best_hp_loss = population[0][2]
            best_killed_ants = population[0][3]
            best_positions = population[0][0]
            best_tower_types = population[0][1]
            print(f"  ✅ 找到更优方案: 掉血 {best_hp_loss}，击杀 {best_killed_ants}只")
        
        # 每5代输出一次进度
        if generation % 5 == 0:
            print(f"  当前代最优: 掉血 {population[0][2]}，击杀 {population[0][3]}只")
            print(f"  当前代平均: 掉血 {current_avg_loss:.1f}，击杀 {current_avg_killed:.1f}只")
    
    print("\n" + "=" * 60)
    print("搜索完成！")
    print(f"最终最优方案: 掉血 {best_hp_loss}，击杀 {best_killed_ants}只")
    print(f"最优炮塔位置: {best_positions}")
    print(f"最优炮塔类型: {best_tower_types}")
    print("=" * 60)
    return best_positions, best_tower_types, best_hp_loss, best_killed_ants

def evaluate_tower_combinations(player: int = 0, max_rounds: int = 100) -> Tuple[List[Tuple[int, int]], List[int], int, int]:
    """评估所有可能的炮塔组合，返回掉血最少的方案"""
    # 使用遗传算法搜索
    return genetic_algorithm_search(player, max_rounds)


def print_tower_info(tower_type: int) -> str:
    """打印炮塔信息"""
    from SDK.utils.constants import TowerType
    
    # 炮塔类型名称映射
    tower_names = {
        TowerType.HEAVY_PLUS: "Heavy+",
        TowerType.ICE: "Ice",
        TowerType.BEWITCH: "Bewitch",
        TowerType.QUICK_PLUS: "Quick+",
        TowerType.DOUBLE: "Double",
        TowerType.SNIPER: "Sniper",
        TowerType.MORTAR_PLUS: "Mortar+",
        TowerType.PULSE: "Pulse",
        TowerType.MISSILE: "Missile",
    }
    
    tower_type_enum = SECONDARY_TOWER_TYPES.get(tower_type)
    if tower_type_enum:
        name = tower_names.get(tower_type_enum, f"未知类型 {tower_type}")
        # 从游戏引擎获取炮塔属性
        from SDK.backend.model import Tower
        tower = Tower(0, 0, 0, 0, tower_type_enum)
        return f"{name} (伤害: {tower.damage}, 间隔: {tower.speed}, 范围: {tower.attack_range})"
    return f"未知炮塔类型 (ID: {tower_type})"


def main():
    """主函数"""
    print("=== 二级炮塔防御效果模拟 ===")
    print("模拟条件: 100个回合，按3.5回合周期生产HP20的蚂蚁")
    
    # 评估玩家0的最优布置
    print("\n评估玩家0（基地位置: 2,9）的最优布置:")
    positions_0, tower_types_0, hp_loss_0, killed_ants_0 = evaluate_tower_combinations(player=0, max_rounds=100)
    print(f"最优方案: 基地掉血 {hp_loss_0}，击杀 {killed_ants_0}只")
    print("炮塔位置和类型:")
    for i, (pos, tower_type) in enumerate(zip(positions_0, tower_types_0)):
        print(f"  炮塔{i+1}: 位置 {pos}, {print_tower_info(tower_type)}")
    
    # 评估玩家1的最优布置
    print("\n评估玩家1（基地位置: 16,9）的最优布置:")
    positions_1, tower_types_1, hp_loss_1, killed_ants_1 = evaluate_tower_combinations(player=1, max_rounds=100)
    print(f"最优方案: 基地掉血 {hp_loss_1}，击杀 {killed_ants_1}只")
    print("炮塔位置和类型:")
    for i, (pos, tower_type) in enumerate(zip(positions_1, tower_types_1)):
        print(f"  炮塔{i+1}: 位置 {pos}, {print_tower_info(tower_type)}")


if __name__ == "__main__":
    main()