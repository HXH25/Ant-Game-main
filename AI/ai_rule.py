from __future__ import annotations

try:
    from common import BaseAgent
except ModuleNotFoundError as exc:
    if exc.name != "common":
        raise
    from AI.common import BaseAgent

from SDK.utils.actions import ActionBundle
from SDK.backend.state import BackendState
from SDK.backend.model import Operation
from SDK.utils.constants import OperationType, TowerType, HIGHLAND_CELLS, BASE_UPGRADE_COST


class RuleAgent(BaseAgent):
    def __init__(self, seed: int | None = None) -> None:
        super().__init__(seed)
        self.step = 0
        self.towers_built = 0
        self.towers_upgraded = 0
        self.base_upgraded = False
        self.producer_built = False
        self.producer_upgraded = False
    
    def get_symmetric_position(self, pos: tuple[int, int], player: int) -> tuple[int, int]:
        """获取对称位置"""
        if player == 0:
            return pos
        else:
            # 玩家1的对称位置
            x, y = pos
            return (18 - x, y)
    
    def is_valid_highland_position(self, pos: tuple[int, int], player: int) -> bool:
        """检查位置是否在玩家高地范围内"""
        return pos in HIGHLAND_CELLS[player]
    
    def find_tower_at(self, state: BackendState, player: int, pos: tuple[int, int]) -> int | None:
        """查找指定位置的炮塔ID"""
        for tower in state.towers:
            if tower.player == player and tower.x == pos[0] and tower.y == pos[1]:
                return tower.tower_id
        return None
    
    def create_build_tower_bundle(self, x: int, y: int) -> ActionBundle:
        """创建建造炮塔的操作包"""
        operation = Operation(
            op_type=OperationType.BUILD_TOWER,
            arg0=x,
            arg1=y
        )
        return ActionBundle(name=f"build@{x},{y}", operations=(operation,))
    
    def create_upgrade_tower_bundle(self, tower_id: int, tower_type: TowerType) -> ActionBundle:
        """创建升级炮塔的操作包"""
        operation = Operation(
            op_type=OperationType.UPGRADE_TOWER,
            arg0=tower_id,
            arg1=tower_type
        )
        return ActionBundle(name=f"upgrade#{tower_id}->{int(tower_type)}", operations=(operation,))
    
    def create_upgrade_base_bundle(self) -> ActionBundle:
        """创建升级基地护甲的操作包"""
        operation = Operation(
            op_type=OperationType.UPGRADE_GENERATED_ANT
        )
        return ActionBundle(name="upgrade-base", operations=(operation,))
    
    def create_empty_bundle(self) -> ActionBundle:
        """创建空操作包"""
        return ActionBundle(name="hold", operations=())
    
    def choose_bundle(self, state: BackendState, player: int, bundles: list[ActionBundle] | None = None) -> ActionBundle:
        # 步骤1: 在指定位置建炮塔
        if self.step == 0:
            # 严格按照指定位置建塔
            build_positions = [(5, 9), (8, 7), (8, 11)]
            
            # 首先检查是否已经建完3个炮塔
            built_count = 0
            for pos in build_positions:
                sym_pos = self.get_symmetric_position(pos, player)
                if self.find_tower_at(state, player, sym_pos) is not None:
                    built_count += 1
            
            # 如果都建了炮塔，继续下一个步骤
            if built_count >= 3:
                self.towers_built = 3
                self.step = 1
                self.towers_upgraded = 0
                return self.create_empty_bundle()
            
            # 遍历3个点，找到第一个没有炮塔的位置
            for pos in build_positions:
                sym_pos = self.get_symmetric_position(pos, player)
                
                # 检查位置是否在合法高地范围内
                if not self.is_valid_highland_position(sym_pos, player):
                    continue
                
                # 检查位置是否已有炮塔
                if self.find_tower_at(state, player, sym_pos) is None:
                    # 如果没钱，返回空操作
                    if state.coins[player] < 15:  # 建塔基础成本
                        return self.create_empty_bundle()
                    # 如果有钱，就建炮塔
                    else:
                        return self.create_build_tower_bundle(sym_pos[0], sym_pos[1])
            
            # 所有位置都检查过了，返回空操作
            return self.create_empty_bundle()
        
        # 步骤2: 升级炮塔为mortar
        elif self.step == 1:
            upgrade_positions = [(5, 9), (8, 7), (8, 11)]
            
            # 首先检查是否已经升级完3个炮塔
            if self.towers_upgraded >= 3:
                self.step = 2
                return self.create_empty_bundle()
            
            # 检查当前需要升级哪个位置的炮塔
            current_upgrade_index = self.towers_upgraded
            if current_upgrade_index < len(upgrade_positions):
                pos = upgrade_positions[current_upgrade_index]
                sym_pos = self.get_symmetric_position(pos, player)
                tower_id = self.find_tower_at(state, player, sym_pos)
                
                if tower_id is not None:
                    # 检查金币是否足够
                    if state.coins[player] >= 60:  # 二级炮塔升级成本
                        self.towers_upgraded += 1
                        return self.create_upgrade_tower_bundle(tower_id, TowerType.MORTAR)
                else:
                    # 如果炮塔不存在，跳过这个位置
                    self.towers_upgraded += 1
                    return self.create_empty_bundle()
            
            # 如果没有找到符合条件的升级操作，返回空操作
            return self.create_empty_bundle()
        
        # 步骤3: 升级基地护甲
        elif self.step == 2 and not self.base_upgraded:
            # 检查金币是否足够升级基地护甲
            if state.coins[player] >= BASE_UPGRADE_COST[0]:  # 第一级升级成本
                self.base_upgraded = True
                self.step = 3
                return self.create_upgrade_base_bundle()
            # 金币不足，返回空操作
            return self.create_empty_bundle()
        
        # 步骤4: 在(4,9)建炮塔
        elif self.step == 3 and not self.producer_built:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            # 检查位置是否在合法高地范围内
            if not self.is_valid_highland_position(sym_pos, player):
                return self.create_empty_bundle()
            # 检查位置是否已有炮塔
            if self.find_tower_at(state, player, sym_pos) is None:
                # 检查金币是否足够
                if state.coins[player] >= 15:  # 建塔基础成本
                    self.producer_built = True
                    self.step = 4
                    return self.create_build_tower_bundle(sym_pos[0], sym_pos[1])
            # 如果没有找到符合条件的建塔操作，返回空操作
            return self.create_empty_bundle()
        
        # 步骤5: 升级(4,9)的炮塔为producer
        elif self.step == 4 and not self.producer_upgraded:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            tower_id = self.find_tower_at(state, player, sym_pos)
            if tower_id is not None:
                # 检查金币是否足够
                if state.coins[player] >= 60:  # 二级炮塔升级成本
                    self.producer_upgraded = True
                    self.step = 5
                    return self.create_upgrade_tower_bundle(tower_id, TowerType.PRODUCER)
            # 如果没有找到符合条件的升级操作，返回空操作
            return self.create_empty_bundle()
        
        # 步骤6: 升级producer为能生产攻击型蚂蚁的炮塔
        elif self.step == 5:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            tower_id = self.find_tower_at(state, player, sym_pos)
            if tower_id is not None:
                # 检查金币是否足够
                if state.coins[player] >= 200:  # 三级炮塔升级成本
                    return self.create_upgrade_tower_bundle(tower_id, TowerType.PRODUCER_SIEGE)
            # 如果没有找到符合条件的升级操作，返回空操作
            return self.create_empty_bundle()
        
        # 所有步骤完成后，返回空操作
        return self.create_empty_bundle()


class AI(RuleAgent):
    """规则AI，严格按照指定步骤执行操作"""
    pass