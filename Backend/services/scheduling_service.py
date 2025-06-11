"""
调度服务 - 实现智能充电桩调度算法
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from models.charging_pile import ChargingPile, PileType, PileStatus
from models.charge_request import ChargeRequest, ChargeType, RequestStatus
from config import get_config

class SchedulingService:
    """调度服务类"""
    
    def __init__(self):
        self.config = get_config()
        self.system_params = self.config.SYSTEM_PARAMS
    
    def find_optimal_pile(self, request: ChargeRequest, available_piles: List[ChargingPile]) -> Optional[ChargingPile]:
        """
        为充电请求找到最优充电桩
        
        实现需求中的调度策略：完成充电所需时长（等待时间+自己充电时间）最短
        
        Args:
            request: 充电请求
            available_piles: 可用的充电桩列表
            
        Returns:
            最优充电桩，如果没有合适的则返回None
        """
        if not available_piles:
            return None
        
        # 过滤出匹配类型的充电桩
        matching_piles = self._filter_matching_piles(request, available_piles)
        
        if not matching_piles:
            return None
        
        # 计算每个充电桩的总完成时间
        best_pile = None
        min_completion_time = float('inf')
        
        for pile in matching_piles:
            completion_time = self._calculate_completion_time(request, pile)
            
            if completion_time < min_completion_time:
                min_completion_time = completion_time
                best_pile = pile
        
        return best_pile
    
    def _filter_matching_piles(self, request: ChargeRequest, piles: List[ChargingPile]) -> List[ChargingPile]:
        """
        过滤出匹配充电类型的充电桩
        
        Args:
            request: 充电请求
            piles: 充电桩列表
            
        Returns:
            匹配的充电桩列表
        """
        matching_piles = []
        
        for pile in piles:
            # 检查充电桩类型是否匹配
            if request.charge_type == ChargeType.FAST and pile.pile_type == PileType.FAST:
                matching_piles.append(pile)
            elif request.charge_type == ChargeType.TRICKLE and pile.pile_type == PileType.TRICKLE:
                matching_piles.append(pile)
        
        # 进一步过滤：只要可以加入队列的充电桩
        available_piles = [pile for pile in matching_piles if pile.can_join_queue()]
        
        return available_piles
    
    def _calculate_completion_time(self, request: ChargeRequest, pile: ChargingPile) -> float:
        """
        计算在指定充电桩完成充电的总时间（小时）
        
        总时间 = 等待时间 + 自己充电时间
        
        Args:
            request: 充电请求
            pile: 充电桩
            
        Returns:
            总完成时间（小时）
        """
        # 计算自己的充电时间
        own_charging_time = request.target_amount / pile.power
        
        # 计算等待时间
        wait_time = self._calculate_wait_time(request, pile)
        
        return wait_time + own_charging_time
    
    def _calculate_wait_time(self, request: ChargeRequest, pile: ChargingPile) -> float:
        """
        计算在指定充电桩的等待时间（小时）
        
        等待时间 = 当前充电剩余时间 + 队列中所有车辆的充电时间
        
        Args:
            request: 充电请求
            pile: 充电桩
            
        Returns:
            等待时间（小时）
        """
        wait_time = 0.0
        
        # 如果充电桩正在使用，需要等待当前充电完成
        if pile.status == PileStatus.CHARGING:
            # 这里简化处理，假设当前充电还需要平均时间
            # 实际实现中需要从当前充电请求中获取准确的剩余时间
            wait_time += self._estimate_current_charging_remaining_time(pile)
        
        # 加上队列中所有请求的充电时间
        # 注意：这里需要从数据存储中获取队列中的请求信息
        # 暂时简化为平均充电时间 * 队列长度
        average_charging_time = request.target_amount / pile.power  # 使用当前请求的充电时间作为估算
        wait_time += len(pile.queue) * average_charging_time
        
        return wait_time
    
    def _estimate_current_charging_remaining_time(self, pile: ChargingPile) -> float:
        """
        估算当前充电的剩余时间（小时）
        
        Args:
            pile: 充电桩
            
        Returns:
            剩余时间（小时）
        """
        if pile.status != PileStatus.CHARGING or not pile.charge_start_time:
            return 0.0
        
        # 简化估算：假设平均还需要30分钟
        # 实际实现中应该根据当前充电请求的进度计算
        return 0.5
    
    def generate_queue_number(self, charge_type: ChargeType, existing_numbers: List[str]) -> str:
        """
        生成排队号码
        
        Args:
            charge_type: 充电类型
            existing_numbers: 已存在的号码列表
            
        Returns:
            新的排队号码
        """
        prefix = 'F' if charge_type == ChargeType.FAST else 'T'
        
        # 找出同类型的最大序号
        max_number = 0
        for number in existing_numbers:
            if number.startswith(prefix):
                try:
                    num = int(number[1:])
                    max_number = max(max_number, num)
                except ValueError:
                    continue
        
        return f"{prefix}{max_number + 1}"
    
    def assign_pile_to_request(self, request: ChargeRequest, pile: ChargingPile) -> bool:
        """
        将充电桩分配给充电请求
        
        Args:
            request: 充电请求
            pile: 充电桩
            
        Returns:
            是否分配成功
        """
        if not pile.can_join_queue():
            return False
        
        # 将请求添加到充电桩队列
        success = pile.add_to_queue(request.id)
        
        if success:
            # 更新请求状态
            request.assign_pile(pile.id)
            
            # 更新预计等待时间
            wait_time_hours = self._calculate_wait_time(request, pile)
            request.estimated_wait_time = wait_time_hours * 60  # 转换为分钟
        
        return success
    
    def process_charging_queue(self, pile: ChargingPile, all_requests: Dict[int, ChargeRequest]) -> Optional[ChargeRequest]:
        """
        处理充电桩队列，开始下一个充电任务
        
        Args:
            pile: 充电桩
            all_requests: 所有充电请求的字典 {request_id: request}
            
        Returns:
            开始充电的请求，如果没有则返回None
        """
        if pile.status != PileStatus.AVAILABLE or not pile.queue:
            return None
        
        # 获取队列中的下一个请求
        next_request_id = pile.get_next_in_queue()
        if not next_request_id or next_request_id not in all_requests:
            return None
        
        next_request = all_requests[next_request_id]
        
        # 检查请求是否仍然有效
        if not next_request.is_active():
            # 无效请求，从队列中移除
            pile.remove_from_queue(next_request_id)
            return self.process_charging_queue(pile, all_requests)  # 递归处理下一个
        
        # 开始充电
        pile.status = PileStatus.CHARGING
        pile.current_user = next_request.username
        pile.charge_start_time = datetime.now()
        
        next_request.start_charging()
        
        return next_request
    
    def handle_fault_redistribution(self, fault_pile: ChargingPile, 
                                  available_piles: List[ChargingPile],
                                  affected_requests: List[ChargeRequest],
                                  strategy: str = 'priority') -> Dict[str, any]:
        """
        处理故障时的车辆重新调度
        
        Args:
            fault_pile: 故障充电桩
            available_piles: 可用的充电桩列表
            affected_requests: 受影响的充电请求列表
            strategy: 调度策略 ('priority' 或 'time_order')
            
        Returns:
            调度结果信息
        """
        redistributed_count = 0
        failed_requests = []
        
        if strategy == 'priority':
            # 优先级调度：优先为故障充电桩队列提供调度
            result = self._priority_redistribution(fault_pile, available_piles, affected_requests)
        else:
            # 时间顺序调度：按排队号码先后顺序重新调度
            result = self._time_order_redistribution(fault_pile, available_piles, affected_requests)
        
        return result
    
    def _priority_redistribution(self, fault_pile: ChargingPile, 
                               available_piles: List[ChargingPile],
                               affected_requests: List[ChargeRequest]) -> Dict[str, any]:
        """
        优先级调度：暂停等候区叫号，优先为故障队列中的车辆分配
        
        Args:
            fault_pile: 故障充电桩
            available_piles: 可用的充电桩列表
            affected_requests: 受影响的充电请求列表
            
        Returns:
            调度结果
        """
        redistributed_count = 0
        failed_requests = []
        
        # 过滤出同类型的充电桩
        matching_piles = [pile for pile in available_piles 
                         if pile.pile_type == fault_pile.pile_type]
        
        for request in affected_requests:
            # 为每个受影响的请求找到最优充电桩
            best_pile = self.find_optimal_pile(request, matching_piles)
            
            if best_pile and self.assign_pile_to_request(request, best_pile):
                redistributed_count += 1
            else:
                failed_requests.append(request)
        
        return {
            'strategy': 'priority',
            'redistributed_count': redistributed_count,
            'failed_count': len(failed_requests),
            'affected_cars': len(affected_requests),
            'redistributionTime': datetime.now().isoformat()
        }
    
    def _time_order_redistribution(self, fault_pile: ChargingPile,
                                 available_piles: List[ChargingPile],
                                 affected_requests: List[ChargeRequest]) -> Dict[str, any]:
        """
        时间顺序调度：将故障队列与其他同类型充电桩中的车辆合并，按排队号码重新调度
        
        Args:
            fault_pile: 故障充电桩
            available_piles: 可用的充电桩列表
            affected_requests: 受影响的充电请求列表
            
        Returns:
            调度结果
        """
        # 获取所有同类型充电桩中未开始充电的请求
        # 这里需要从数据存储中获取，暂时简化处理
        
        redistributed_count = 0
        
        # 按排队号码排序
        affected_requests.sort(key=lambda x: x.queue_number or '')
        
        # 重新分配
        matching_piles = [pile for pile in available_piles 
                         if pile.pile_type == fault_pile.pile_type]
        
        for request in affected_requests:
            best_pile = self.find_optimal_pile(request, matching_piles)
            
            if best_pile and self.assign_pile_to_request(request, best_pile):
                redistributed_count += 1
        
        return {
            'strategy': 'time_order',
            'redistributed_count': redistributed_count,
            'affected_cars': len(affected_requests),
            'redistributionTime': datetime.now().isoformat()
        }
    
    def update_queue_positions(self, waiting_requests: List[ChargeRequest]):
        """
        更新等候区中车辆的排队位置和预计等待时间
        
        Args:
            waiting_requests: 等候区中的充电请求列表
        """
        # 按充电类型分组
        fast_requests = [r for r in waiting_requests if r.charge_type == ChargeType.FAST]
        trickle_requests = [r for r in waiting_requests if r.charge_type == ChargeType.TRICKLE]
        
        # 按创建时间排序
        fast_requests.sort(key=lambda x: x.created_at)
        trickle_requests.sort(key=lambda x: x.created_at)
        
        # 更新位置
        for i, request in enumerate(fast_requests):
            request.queue_position = i + 1
        
        for i, request in enumerate(trickle_requests):
            request.queue_position = i + 1
    
    def calculate_estimated_wait_time(self, request: ChargeRequest, 
                                    available_piles: List[ChargingPile]) -> float:
        """
        计算预计等待时间
        
        Args:
            request: 充电请求
            available_piles: 可用充电桩列表
            
        Returns:
            预计等待时间（分钟）
        """
        matching_piles = self._filter_matching_piles(request, available_piles)
        
        if not matching_piles:
            return 0.0
        
        # 找到等待时间最短的充电桩
        min_wait_time = float('inf')
        
        for pile in matching_piles:
            wait_time = self._calculate_wait_time(request, pile)
            min_wait_time = min(min_wait_time, wait_time)
        
        return min_wait_time * 60  # 转换为分钟

    def calculate_pile_wait_time(self, pile: ChargingPile, request_energy: float) -> float:
        """计算指定充电桩的等待时间（小时）"""
        total_time = 0.0
        
        # 如果充电桩正在充电，加上当前充电剩余时间
        if pile.status == PileStatus.CHARGING:
            # 获取当前充电请求
            if pile.current_request_id:
                current_request = self.data_manager.get_request(pile.current_request_id)
                if current_request and pile.charge_start_time:
                    # 计算剩余时间
                    elapsed_time = (datetime.now() - pile.charge_start_time).total_seconds() / 3600
                    total_time = current_request.target_amount / pile.power - elapsed_time
        
        # 加上队列中所有请求的充电时间
        for request_id in pile.queue:
            request = self.data_manager.get_request(request_id)
            if request:
                total_time += request.target_amount / pile.power
        
        # 加上当前请求的充电时间
        total_time += request_energy / pile.power
        
        return max(0.0, total_time)

    def get_best_pile(self, request: ChargeRequest) -> Optional[ChargingPile]:
        """获取最佳充电桩"""
        # 获取对应类型的所有充电桩
        available_piles = [
            pile for pile in self.data_manager.get_piles_by_type(request.charge_type)
            if pile.status != PileStatus.FAULT and pile.is_active
        ]
        
        if not available_piles:
            return None
        
        # 计算每个充电桩的等待时间
        pile_wait_times = []
        for pile in available_piles:
            wait_time = self.calculate_pile_wait_time(pile, request.target_amount)
            pile_wait_times.append((pile, wait_time))
        
        # 按等待时间排序
        pile_wait_times.sort(key=lambda x: x[1])
        
        # 返回等待时间最短的充电桩
        return pile_wait_times[0][0] if pile_wait_times else None 