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
from SDK.utils.constants import OperationType, TowerType


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
    
    def find_tower_at(self, state: BackendState, player: int, pos: tuple[int, int]) -> int | None:
        """查找指定位置的炮塔ID"""
        for tower in state.towers:
            if tower.player == player and tower.x == pos[0] and tower.y == pos[1]:
                return tower.tower_id
        return None
    
    def choose_bundle(self, state: BackendState, player: int, bundles: list[ActionBundle] | None = None) -> ActionBundle:
        bundles = bundles or self.list_bundles(state, player)
        
        # 确保bundles[0]是空操作
        empty_bundle = bundles[0]
        
        # 步骤1: 在指定位置建炮塔
        if self.step == 0:
            # 严格按照指定位置建塔
            build_positions = [(5, 9), (8, 7), (8, 11)]
            # 按顺序检查每个位置
            for pos in build_positions:
                sym_pos = self.get_symmetric_position(pos, player)
                # 检查位置是否已有炮塔
                if self.find_tower_at(state, player, sym_pos) is None:
                    # 只查找指定位置的建造操作
                    for bundle in bundles:
                        # 确保bundle只包含指定位置的建塔操作
                        if len(bundle.operations) == 1:
                            op = bundle.operations[0]
                            if (op.op_type == OperationType.BUILD_TOWER and 
                                op.arg0 == sym_pos[0] and 
                                op.arg1 == sym_pos[1]):
                                self.towers_built += 1
                                if self.towers_built >= 3:
                                    self.step = 1
                                    self.towers_upgraded = 0
                                return bundle
            # 如果没有找到符合条件的建塔操作，返回空操作
            return empty_bundle
        
        # 步骤2: 升级炮塔为mortar
        elif self.step == 1:
            upgrade_positions = [(5, 9), (8, 7), (8, 11)]
            for pos in upgrade_positions:
                sym_pos = self.get_symmetric_position(pos, player)
                tower_id = self.find_tower_at(state, player, sym_pos)
                if tower_id is not None:
                    # 查找升级为mortar的操作
                    for bundle in bundles:
                        # 确保bundle只包含指定的升级操作
                        if len(bundle.operations) == 1:
                            op = bundle.operations[0]
                            if (op.op_type == OperationType.UPGRADE_TOWER and 
                                op.arg0 == tower_id and 
                                op.arg1 == TowerType.MORTAR):
                                self.towers_upgraded += 1
                                if self.towers_upgraded >= 3:
                                    self.step = 2
                                return bundle
            # 如果没有找到符合条件的升级操作，返回空操作
            return empty_bundle
        
        # 步骤3: 升级基地护甲
        elif self.step == 2 and not self.base_upgraded:
            # 查找升级基地护甲的操作
            for bundle in bundles:
                # 确保bundle只包含升级基地护甲的操作
                if len(bundle.operations) == 1:
                    op = bundle.operations[0]
                    if op.op_type == OperationType.UPGRADE_GENERATED_ANT:
                        self.base_upgraded = True
                        self.step = 3
                        return bundle
            # 如果没有找到符合条件的升级操作，返回空操作
            return empty_bundle
        
        # 步骤4: 在(4,9)建炮塔
        elif self.step == 3 and not self.producer_built:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            # 检查位置是否已有炮塔
            if self.find_tower_at(state, player, sym_pos) is None:
                # 查找建造炮塔的操作
                for bundle in bundles:
                    # 确保bundle只包含指定位置的建塔操作
                    if len(bundle.operations) == 1:
                        op = bundle.operations[0]
                        if (op.op_type == OperationType.BUILD_TOWER and 
                            op.arg0 == sym_pos[0] and 
                            op.arg1 == sym_pos[1]):
                            self.producer_built = True
                            self.step = 4
                            return bundle
            # 如果没有找到符合条件的建塔操作，返回空操作
            return empty_bundle
        
        # 步骤5: 升级(4,9)的炮塔为producer
        elif self.step == 4 and not self.producer_upgraded:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            tower_id = self.find_tower_at(state, player, sym_pos)
            if tower_id is not None:
                # 查找升级为producer的操作
                for bundle in bundles:
                    # 确保bundle只包含指定的升级操作
                    if len(bundle.operations) == 1:
                        op = bundle.operations[0]
                        if (op.op_type == OperationType.UPGRADE_TOWER and 
                            op.arg0 == tower_id and 
                            op.arg1 == TowerType.PRODUCER):
                            self.producer_upgraded = True
                            self.step = 5
                            return bundle
            # 如果没有找到符合条件的升级操作，返回空操作
            return empty_bundle
        
        # 步骤6: 升级producer为能生产攻击型蚂蚁的炮塔
        elif self.step == 5:
            pos = (4, 9)
            sym_pos = self.get_symmetric_position(pos, player)
            tower_id = self.find_tower_at(state, player, sym_pos)
            if tower_id is not None:
                # 查找升级为siege producer的操作
                for bundle in bundles:
                    # 确保bundle只包含指定的升级操作
                    if len(bundle.operations) == 1:
                        op = bundle.operations[0]
                        if (op.op_type == OperationType.UPGRADE_TOWER and 
                            op.arg0 == tower_id and 
                            op.arg1 == TowerType.PRODUCER_SIEGE):
                            return bundle
            # 如果没有找到符合条件的升级操作，返回空操作
            return empty_bundle
        
        # 所有步骤完成后，返回空操作
        return empty_bundle


class AI(RuleAgent):
    pass