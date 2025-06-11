"""
充电服务 - 整合充电流程管理
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from models.user import User
from models.charging_pile import ChargingPile, PileStatus
from models.charge_request import ChargeRequest, ChargeType, RequestStatus
from models.charge_record import ChargeRecord
from .billing_service import BillingService
from .scheduling_service import SchedulingService
from config import get_config
import time
import logging

logger = logging.getLogger(__name__)

class ChargingService:
    """充电服务类 - 协调充电流程"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.billing_service = BillingService()
        self.scheduling_service = SchedulingService()
        self.config = get_config()
        self.system_params = self.config.SYSTEM_PARAMS
    
    def submit_charge_request(self, user_id: int, charge_type: str, target_amount: float) -> Dict[str, any]:
        """
        提交充电请求
        
        Args:
            user_id: 用户ID
            charge_type: 充电类型 ('fast' 或 'trickle')
            target_amount: 目标充电量（度）
            
        Returns:
            请求结果信息
        """
        # 检查用户是否已有活跃请求
        existing_request = self.data_manager.get_user_active_request(user_id)
        if existing_request:
            return {
                'success': False,
                'message': '您已有活跃的充电请求',
                'code': 400
            }
        
        # 检查等候区容量
        waiting_requests = self.data_manager.get_waiting_requests()
        if len(waiting_requests) >= self.system_params['waiting_area_size']:
            return {
                'success': False,
                'message': '等候区已满，请稍后再试',
                'code': 400
            }
        
        # 创建充电请求
        request_id = self.data_manager.get_next_request_id()
        charge_type_enum = ChargeType.FAST if charge_type == 'fast' else ChargeType.TRICKLE
        
        request = ChargeRequest(
            id=request_id,
            user_id=user_id,
            charge_type=charge_type_enum,
            target_amount=target_amount
        )
        
        # 生成排队号码
        all_requests = self.data_manager.get_all_requests()
        existing_numbers = [r.queue_number for r in all_requests.values() if r.queue_number]
        queue_number = self.scheduling_service.generate_queue_number(charge_type_enum, existing_numbers)
        request.generate_queue_number(int(queue_number[1:]))
        
        # 计算预计等待时间
        available_piles = self.data_manager.get_available_piles()
        estimated_wait_time = self.scheduling_service.calculate_estimated_wait_time(request, available_piles)
        request.estimated_wait_time = estimated_wait_time
        
        # 保存请求
        self.data_manager.save_request(request)
        
        # 尝试立即分配充电桩
        self._try_assign_pile(request)
        
        return {
            'success': True,
            'data': {
                'request_id': request.id,
                'queue_number': request.queue_number,
                'estimated_start_time': (datetime.now().replace(second=0, microsecond=0) + 
                                       timedelta(minutes=int(estimated_wait_time))).isoformat()
            },
            'message': 'charging request submitted successfully'
        }
    
    def _try_assign_pile(self, request: ChargeRequest) -> bool:
        """
        尝试为请求分配充电桩
        
        Args:
            request: 充电请求
            
        Returns:
            是否分配成功
        """
        available_piles = self.data_manager.get_available_piles()
        best_pile = self.scheduling_service.find_optimal_pile(request, available_piles)
        
        if best_pile:
            success = self.scheduling_service.assign_pile_to_request(request, best_pile)
            if success:
                # 更新数据
                self.data_manager.save_request(request)
                self.data_manager.save_pile(best_pile)
                
                # 检查是否可以立即开始充电
                self._try_start_charging(best_pile)
                
                return True
        
        return False
    
    def _try_start_charging(self, pile: ChargingPile):
        """
        尝试开始充电（如果充电桩空闲且有队列）
        
        Args:
            pile: 充电桩
        """
        if pile.status == PileStatus.AVAILABLE and pile.queue:
            all_requests = self.data_manager.get_all_requests()
            next_request = self.scheduling_service.process_charging_queue(pile, all_requests)
            
            if next_request:
                # 更新数据
                self.data_manager.save_request(next_request)
                self.data_manager.save_pile(pile)
    
    def modify_charge_request(self, user_id: int, request_id: int, 
                            new_charge_type: str = None, 
                            new_target_amount: float = None) -> Dict[str, any]:
        """
        修改充电请求
        
        Args:
            user_id: 用户ID
            request_id: 请求ID
            new_charge_type: 新充电类型
            new_target_amount: 新目标充电量
            
        Returns:
            修改结果
        """
        request = self.data_manager.get_request(request_id)
        if not request or request.user_id != user_id:
            return {
                'success': False,
                'message': '未找到充电请求',
                'code': 404
            }
        
        # 检查是否可以修改
        if new_charge_type and not request.can_modify_type():
            return {
                'success': False,
                'message': '当前状态不允许修改充电类型',
                'code': 400
            }
        
        if new_target_amount and not request.can_modify_amount():
            return {
                'success': False,
                'message': '当前状态不允许修改充电量',
                'code': 400
            }
        
        # 执行修改
        if new_charge_type and new_charge_type != request.charge_type.value:
            # 修改充电类型需要重新排队
            old_pile = None
            if request.assigned_pile_id:
                old_pile = self.data_manager.get_pile(request.assigned_pile_id)
                if old_pile:
                    old_pile.remove_from_queue(request.id)
                    self.data_manager.save_pile(old_pile)
            
            # 更新请求类型
            request.charge_type = ChargeType.FAST if new_charge_type == 'fast' else ChargeType.TRICKLE
            request.status = RequestStatus.WAITING
            request.assigned_pile_id = None
            request.assigned_at = None
            
            # 重新生成排队号码
            all_requests = self.data_manager.get_all_requests()
            existing_numbers = [r.queue_number for r in all_requests.values() if r.queue_number and r.id != request.id]
            queue_number = self.scheduling_service.generate_queue_number(request.charge_type, existing_numbers)
            request.generate_queue_number(int(queue_number[1:]))
            
            # 重新分配充电桩
            self._try_assign_pile(request)
        
        if new_target_amount:
            request.target_amount = new_target_amount
            
            # 如果已分配充电桩，更新预计等待时间
            if request.assigned_pile_id:
                pile = self.data_manager.get_pile(request.assigned_pile_id)
                if pile:
                    wait_time_hours = self.scheduling_service._calculate_wait_time(request, pile)
                    request.estimated_wait_time = wait_time_hours * 60
        
        self.data_manager.save_request(request)
        
        return {
            'success': True,
            'message': '充电请求已修改',
            'data': request.to_dict()
        }
    
    def cancel_charge_request(self, user_id: int, request_id: int) -> Dict[str, any]:
        """
        取消充电请求
        
        Args:
            user_id: 用户ID
            request_id: 请求ID
            
        Returns:
            取消结果
        """
        request = self.data_manager.get_request(request_id)
        if not request or request.user_id != user_id:
            return {
                'success': False,
                'message': '未找到充电请求',
                'code': 404
            }
        
        if not request.can_cancel():
            return {
                'success': False,
                'message': '当前状态不允许取消',
                'code': 400
            }
        
        # 如果正在充电，需要生成充电记录
        if request.status == RequestStatus.CHARGING:
            self._stop_charging_and_generate_record(request, 'cancelled')
        
        # 从充电桩队列中移除
        if request.assigned_pile_id:
            pile = self.data_manager.get_pile(request.assigned_pile_id)
            if pile:
                pile.remove_from_queue(request.id)
                self.data_manager.save_pile(pile)
                
                # 尝试开始下一个充电
                self._try_start_charging(pile)
        
        # 更新请求状态
        request.cancel()
        self.data_manager.save_request(request)
        
        return {
            'success': True,
            'message': '充电请求已取消'
        }
    
    def stop_charging(self, user_id: int, request_id: int) -> Dict[str, any]:
        """
        结束充电
        
        Args:
            user_id: 用户ID
            request_id: 请求ID
            
        Returns:
            结束结果
        """
        request = self.data_manager.get_request(request_id)
        if not request or request.user_id != user_id:
            return {
                'success': False,
                'message': '未找到充电请求',
                'code': 404
            }
        
        if request.status != RequestStatus.CHARGING:
            return {
                'success': False,
                'message': '当前没有正在进行的充电',
                'code': 400
            }
        
        # 停止充电并生成记录
        record = self._stop_charging_and_generate_record(request, 'completed')
        
        return {
            'success': True,
            'message': '充电已结束',
            'data': {
                'record_id': record.id,
                'end_time': record.end_time.isoformat(),
                'total_energy': record.energy_amount,
                'total_cost': record.total_cost
            }
        }
    
    def _stop_charging_and_generate_record(self, request: ChargeRequest, reason: str) -> ChargeRecord:
        """
        停止充电并生成充电记录
        
        Args:
            request: 充电请求
            reason: 停止原因 ('completed', 'cancelled', 'interrupted')
            
        Returns:
            充电记录
        """
        pile = self.data_manager.get_pile(request.assigned_pile_id)
        
        # 停止充电桩
        start_time = pile.stop_charging()
        
        # 计算实际充电量（简化处理，实际应根据充电进度）
        if reason == 'completed':
            actual_amount = request.target_amount
        else:
            # 估算已充电量
            duration = request.get_charging_duration()
            actual_amount = min(request.target_amount, duration * pile.power)
        
        # 计算费用
        cost_info = self.billing_service.calculate_charging_cost(
            actual_amount, request.start_time, datetime.now()
        )
        
        # 更新请求状态
        if reason == 'completed':
            request.complete_charging(
                actual_amount, cost_info['total_cost'], 
                cost_info['charge_cost'], cost_info['service_cost']
            )
        elif reason == 'cancelled':
            request.cancel()
        else:
            request.interrupt(
                actual_amount, cost_info['total_cost'],
                cost_info['charge_cost'], cost_info['service_cost']
            )
        
        # 创建充电记录
        record_id = self.data_manager.get_next_record_id()
        record = ChargeRecord.create_from_request(
            record_id, request, pile, actual_amount,
            cost_info['charge_cost'], cost_info['service_cost'],
            cost_info['average_rate']
        )
        
        # 更新用户统计
        user = self.data_manager.get_user(request.user_id)
        if user:
            user.add_charge_record(actual_amount, cost_info['total_cost'])
            self.data_manager.save_user(user)
        
        # 保存数据
        self.data_manager.save_request(request)
        self.data_manager.save_pile(pile)
        self.data_manager.save_record(record)
        
        # 尝试开始下一个充电
        self._try_start_charging(pile)
        
        return record
    
    def get_user_current_status(self, user_id: int) -> Dict[str, any]:
        """
        获取用户当前充电状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户状态信息
        """
        request = self.data_manager.get_user_active_request(user_id)
        
        if not request:
            return {
                'has_active_charging': False,
                'active_pile': '',
                'charged_amount': 0,
                'progress_percent': 0,
                'start_time': '',
                'estimated_end_time': ''
            }
        
        if request.status == RequestStatus.CHARGING:
            pile = self.data_manager.get_pile(request.assigned_pile_id)
            
            # 计算当前充电量（简化处理）
            duration = request.get_charging_duration()
            current_amount = min(request.target_amount, duration * pile.power)
            progress = request.get_progress_percent()
            
            # 估算结束时间
            remaining_amount = request.target_amount - current_amount
            remaining_hours = remaining_amount / pile.power if pile.power > 0 else 0
            estimated_end = datetime.now() + timedelta(hours=remaining_hours)
            
            return {
                'has_active_charging': True,
                'active_pile': pile.name,
                'charged_amount': round(current_amount, 2),
                'progress_percent': round(progress, 1),
                'start_time': request.start_time.isoformat(),
                'estimated_end_time': estimated_end.isoformat()
            }
        else:
            return {
                'has_active_charging': False,
                'queue_status': request.to_dict()
            }
    
    def get_user_statistics(self, user_id: int) -> Dict[str, any]:
        """
        获取用户统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        user = self.data_manager.get_user(user_id)
        if not user:
            return {
                'charge_count': 0,
                'total_energy': 0.0,
                'total_cost': 0.0
            }
        
        return {
            'charge_count': user.total_charge_count,
            'total_energy': round(user.total_energy, 2),
            'total_cost': round(user.total_cost, 2)
        }
    
    def get_pile_by_id(self, pile_id: int) -> Optional[ChargingPile]:
        """根据ID获取充电桩"""
        return self.data_manager.get_pile_by_id(pile_id)
    
    def get_next_charging_request(self, pile_id: int) -> Optional[ChargeRequest]:
        """获取充电桩的下一个充电请求"""
        try:
            # 获取分配给该充电桩的充电请求
            query = """
            SELECT * FROM charge_requests 
            WHERE pile_id = %s AND status = 'queued'
            ORDER BY created_at ASC LIMIT 1
            """
            request_data = self.data_manager.db_manager.execute_query(query, (pile_id,), fetch_one=True)
            
            if request_data:
                return ChargeRequest(
                    id=request_data['id'],
                    username=request_data['username'],
                    charge_type=ChargeType(request_data['charge_type']),
                    energy_amount=float(request_data['energy_amount']),
                    status=RequestStatus(request_data['status']),
                    pile_id=request_data['pile_id'],
                    queue_number=request_data['queue_number'],
                    position=request_data['position'],
                    estimated_start_time=request_data['estimated_start_time'],
                    estimated_wait_minutes=request_data['estimated_wait_minutes']
                )
            return None
        except Exception as e:
            logger.error(f"获取下一个充电请求失败: {e}")
            return None
    
    def update_charging_progress(self, pile_id: int, charged_amount: float, progress_percent: float):
        """更新充电进度"""
        pile = self.get_pile_by_id(pile_id)
        if pile and pile.current_user:
            # 更新充电进度，这里简化处理
            # 实际应该更新对应的充电记录
            logger.debug(f"充电桩 {pile_id} 充电进度更新: {progress_percent:.1f}%, {charged_amount:.2f}度")
    
    def complete_charging(self, pile_id: int, username: str, charged_amount: float,
                       start_time: datetime, end_time: datetime,
                       status: str, reason: str = ''):
        """完成充电"""
        pile = self.get_pile_by_id(pile_id)
        if not pile:
            logger.error(f"找不到充电桩: {pile_id}")
            return
        
        # 更新充电桩状态
        pile.status = PileStatus.AVAILABLE
        pile.current_user = None
        
        # 更新统计信息
        pile.total_charges += 1
        pile.total_energy += charged_amount
        duration = (end_time - start_time).total_seconds() / 3600
        pile.total_hours += duration
        
        # 创建充电记录
        record = ChargeRecord(
            id=f"REC_{int(time.time() * 1000)}",
            username=username,
            pile_id=pile_id,
            start_time=start_time,
            end_time=end_time,
            energy_amount=charged_amount,
            total_cost=self.billing_service.calculate_cost(charged_amount, start_time, duration),
            status=ChargeRecord.COMPLETED if status == "COMPLETED" else ChargeRecord.CANCELLED
        )
        
        self.data_manager.add_charge_record(record)
        
        # 更新对应的充电请求状态
        for req in self.data_manager.charge_requests.values():
            if req.username == username and req.status == RequestStatus.CHARGING:
                req.status = RequestStatus.COMPLETED if status == "COMPLETED" else RequestStatus.CANCELLED
                break
        
        logger.info(f"充电完成: 用户={username}, 充电桩={pile_id}, 充电量={charged_amount:.2f}度, 费用={self.billing_service.calculate_cost(charged_amount, start_time, duration):.2f}元")

    def process_charging_requests(self):
        """处理充电请求队列"""
        try:
            # 获取所有可用的充电桩
            query = """
            SELECT * FROM charging_piles 
            WHERE status = 'AVAILABLE'
            ORDER BY id
            """
            available_piles = self.data_manager.db_manager.execute_query(query)
            
            for pile_data in available_piles:
                pile_id = pile_data['id']
                
                # 获取分配给该充电桩的下一个充电请求
                next_request = self.get_next_charging_request(pile_id)
                if next_request:
                    # 更新请求状态为充电中
                    update_query = """
                    UPDATE charge_requests 
                    SET status = 'charging', 
                        started_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    """
                    self.data_manager.db_manager.execute_update(update_query, (next_request.id,))
                    
                    # 更新充电桩状态
                    update_pile_query = """
                    UPDATE charging_piles 
                    SET status = 'CHARGING', 
                        current_user = %s 
                    WHERE id = %s
                    """
                    self.data_manager.db_manager.execute_update(update_pile_query, (next_request.username, pile_id))
                    
                    logger.info(f"充电桩 {pile_id} 开始为用户 {next_request.username} 充电")
        except Exception as e:
            logger.error(f"处理充电请求队列失败: {e}") 