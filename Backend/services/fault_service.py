"""
故障服务 - 处理充电桩故障相关功能
"""

from typing import Dict, List, Optional
from datetime import datetime
from models.charging_pile import ChargingPile, PileStatus
from models.charge_request import ChargeRequest, RequestStatus
from .scheduling_service import SchedulingService
from config import get_config

class FaultService:
    """故障服务类"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.scheduling_service = SchedulingService()
        self.config = get_config()
    
    def set_pile_fault(self, pile_id: int, fault_reason: str) -> Dict[str, any]:
        """
        设置充电桩故障
        
        Args:
            pile_id: 充电桩ID
            fault_reason: 故障原因
            
        Returns:
            设置结果
        """
        pile = self.data_manager.get_pile(pile_id)
        if not pile:
            return {
                'success': False,
                'message': '充电桩不存在',
                'code': 404
            }
        
        # 如果正在充电，需要停止当前充电
        if pile.status == PileStatus.CHARGING:
            self._handle_charging_interruption(pile)
        
        # 设置故障
        pile.set_fault(fault_reason)
        self.data_manager.save_pile(pile)
        
        # 获取受影响的请求
        affected_requests = self._get_affected_requests(pile)
        
        return {
            'success': True,
            'data': {
                'pile_id': pile_id,
                'is_fault': True,
                'fault_reason': fault_reason,
                'affected_requests': len(affected_requests),
                'update_time': datetime.now().isoformat()
            },
            'message': '充电桩故障已设置'
        }
    
    def repair_pile(self, pile_id: int) -> Dict[str, any]:
        """
        充电桩故障恢复
        
        Args:
            pile_id: 充电桩ID
            
        Returns:
            恢复结果
        """
        pile = self.data_manager.get_pile(pile_id)
        if not pile:
            return {
                'success': False,
                'message': '充电桩不存在',
                'code': 404
            }
        
        if not pile.fault_info.is_fault:
            return {
                'success': False,
                'message': '充电桩当前没有故障',
                'code': 400
            }
        
        # 故障恢复
        pile.repair()
        self.data_manager.save_pile(pile)
        
        # 处理故障恢复后的重新调度
        self._handle_fault_recovery_redistribution(pile)
        
        return {
            'success': True,
            'data': {
                'pile_id': pile_id,
                'is_fault': False,
                'repair_time': pile.fault_info.repair_time.isoformat(),
                'update_time': datetime.now().isoformat()
            },
            'message': '充电桩已恢复正常'
        }
    
    def execute_fault_dispatch_strategy(self, pile_id: int, strategy: str) -> Dict[str, any]:
        """
        执行故障调度策略
        
        Args:
            pile_id: 故障充电桩ID
            strategy: 调度策略 ('priority' 或 'time_order')
            
        Returns:
            调度结果
        """
        fault_pile = self.data_manager.get_pile(pile_id)
        if not fault_pile:
            return {
                'success': False,
                'message': '充电桩不存在',
                'code': 404
            }
        
        if not fault_pile.fault_info.is_fault:
            return {
                'success': False,
                'message': '充电桩当前没有故障',
                'code': 400
            }
        
        # 获取可用的同类型充电桩
        available_piles = self.data_manager.get_available_piles()
        matching_piles = [pile for pile in available_piles 
                         if pile.pile_type == fault_pile.pile_type and pile.id != pile_id]
        
        # 获取受影响的请求
        affected_requests = self._get_affected_requests(fault_pile)
        
        if not affected_requests:
            return {
                'success': True,
                'data': {
                    'strategy': strategy,
                    'affected_cars': 0,
                    'redistributed_count': 0
                },
                'message': '没有受影响的车辆需要重新调度'
            }
        
        # 执行重新调度
        result = self.scheduling_service.handle_fault_redistribution(
            fault_pile, matching_piles, affected_requests, strategy
        )
        
        # 保存更新后的数据
        for request in affected_requests:
            self.data_manager.save_request(request)
        
        for pile in matching_piles:
            self.data_manager.save_pile(pile)
        
        return {
            'success': True,
            'data': result,
            'message': '故障调度策略已执行'
        }
    
    def get_fault_piles_info(self) -> Dict[str, any]:
        """
        获取所有故障充电桩信息
        
        Returns:
            故障充电桩信息
        """
        all_piles = self.data_manager.get_all_piles()
        fault_piles = []
        
        for pile in all_piles.values():
            if pile.fault_info.is_fault:
                affected_requests = self._get_affected_requests(pile)
                fault_piles.append({
                    'pile_id': pile.id,
                    'pile_name': pile.name,
                    'fault_reason': pile.fault_info.reason,
                    'fault_time': pile.fault_info.fault_time.isoformat() if pile.fault_info.fault_time else '',
                    'queue_count': len(affected_requests)
                })
        
        return {
            'success': True,
            'data': {
                'fault_piles': fault_piles,
                'total_fault_count': len(fault_piles)
            },
            'message': 'success'
        }
    
    def _handle_charging_interruption(self, pile: ChargingPile):
        """
        处理充电中断
        
        Args:
            pile: 故障的充电桩
        """
        if pile.current_request_id:
            request = self.data_manager.get_request(pile.current_request_id)
            if request and request.status == RequestStatus.CHARGING:
                # 停止充电并生成记录
                from .charging_service import ChargingService
                charging_service = ChargingService(self.data_manager)
                charging_service._stop_charging_and_generate_record(request, 'interrupted')
    
    def _get_affected_requests(self, pile: ChargingPile) -> List[ChargeRequest]:
        """
        获取受故障影响的充电请求
        
        Args:
            pile: 故障充电桩
            
        Returns:
            受影响的请求列表
        """
        affected_requests = []
        all_requests = self.data_manager.get_all_requests()
        
        for request_id in pile.queue:
            if request_id in all_requests:
                request = all_requests[request_id]
                if request.is_active():
                    affected_requests.append(request)
        
        return affected_requests
    
    def _handle_fault_recovery_redistribution(self, recovered_pile: ChargingPile):
        """
        处理故障恢复后的重新调度
        
        Args:
            recovered_pile: 恢复的充电桩
        """
        # 获取其他同类型充电桩中的未开始充电的车辆
        all_piles = self.data_manager.get_all_piles()
        same_type_piles = [pile for pile in all_piles.values() 
                          if pile.pile_type == recovered_pile.pile_type and 
                          pile.id != recovered_pile.id and 
                          not pile.fault_info.is_fault]
        
        # 收集所有未开始充电的请求
        queued_requests = []
        all_requests = self.data_manager.get_all_requests()
        
        for pile in same_type_piles:
            for request_id in pile.queue:
                if request_id in all_requests:
                    request = all_requests[request_id]
                    if request.status == RequestStatus.QUEUED:
                        queued_requests.append(request)
        
        if queued_requests:
            # 按排队号码排序
            queued_requests.sort(key=lambda x: x.queue_number or '')
            
            # 重新分配（包括恢复的充电桩）
            available_piles = same_type_piles + [recovered_pile]
            
            # 先清空现有队列
            for pile in same_type_piles:
                pile.queue.clear()
                self.data_manager.save_pile(pile)
            
            # 重新分配请求
            for request in queued_requests:
                best_pile = self.scheduling_service.find_optimal_pile(request, available_piles)
                if best_pile:
                    self.scheduling_service.assign_pile_to_request(request, best_pile)
                    self.data_manager.save_request(request)
                    self.data_manager.save_pile(best_pile) 